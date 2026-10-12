"""Isolated substitute renderer for archived Composer MIDI. Does not edit source/master."""
import argparse,ctypes,ctypes.util,io,json,wave,zipfile,hashlib,os
from pathlib import Path
import mido,numpy as np
LIB=ctypes.CDLL(os.environ.get('AI_COMP_FLUIDSYNTH_LIBRARY') or ctypes.util.find_library('fluidsynth') or 'libfluidsynth.so.3')
def fn(name,restype,args):
 f=getattr(LIB,name);f.restype=restype;f.argtypes=args;return f
ptr=ctypes.c_void_p; I=ctypes.c_int; C=ctypes.c_char_p
new_settings=fn('new_fluid_settings',ptr,[])
setnum=fn('fluid_settings_setnum',I,[ptr,C,ctypes.c_double])
setint=fn('fluid_settings_setint',I,[ptr,C,I])
new_synth=fn('new_fluid_synth',ptr,[ptr]);load=fn('fluid_synth_sfload',I,[ptr,C,I]);program=fn('fluid_synth_program_change',I,[ptr,I,I]);on=fn('fluid_synth_noteon',I,[ptr,I,I,I]);off=fn('fluid_synth_noteoff',I,[ptr,I,I]);cc=fn('fluid_synth_cc',I,[ptr,I,I,I]);write=fn('fluid_synth_write_float',I,[ptr,I,ptr,I,I,ptr,I,I]);delete=fn('delete_fluid_synth',None,[ptr]);delset=fn('delete_fluid_settings',None,[ptr])
SR=22050

def render_track(mid,track_idx,sf2,out,kind,program=0,bank=None,note_map=None,tuning_reference_hz=440):
 settings=new_settings();setnum(settings,b'synth.sample-rate',SR);setnum(settings,b'synth.gain',0.35);setint(settings,b'synth.reverb.active',0);setint(settings,b'synth.chorus.active',0)
 synth=new_synth(settings)
 try:
  soundfont_id=load(synth,str(sf2).encode(),1)
  if soundfont_id<0:raise ValueError('SOUNDFONT_LOAD_FAILED')
  channel=9 if kind=='drums' else 0
  selected_bank=int(bank if bank is not None else (128 if kind=='drums' else 0))
  select=fn('fluid_synth_program_select',I,[ptr,I,I,I,I])
  if select(synth,channel,soundfont_id,selected_bank,int(program))!=0:
   raise ValueError('EXACT_SOUNDFONT_PRESET_MISSING')
  from musical_tuning import validate_reference, apply_fluid_tuning
  validate_reference(tuning_reference_hz)
  if kind!='drums':apply_fluid_tuning(LIB,synth,[channel],tuning_reference_hz)
  note_map={int(k):int(v) for k,v in (note_map or {}).items()}
  if any(not 0<=k<=127 or not 0<=v<=127 for k,v in note_map.items()):raise ValueError('INVALID_DRUM_NOTE_MAPPING')
  tempo=500000;seconds=0;events=[]
  # all original conductor tempo changes incorporated via global tick-to-seconds mapping
  tempos=[];tick=0
  for msg in mid.tracks[0]:
   tick+=msg.time
   if msg.type=='set_tempo':tempos.append((tick,msg.tempo))
  ticks=0;prev=0;sec=0;current=500000;ti=0
  for msg in mid.tracks[track_idx]:
   ticks+=msg.time
   while ti<len(tempos) and tempos[ti][0]<=ticks:
    at,t=tempos[ti];sec+=mido.tick2second(at-prev,mid.ticks_per_beat,current);prev=at;current=t;ti+=1
   when=sec+mido.tick2second(ticks-prev,mid.ticks_per_beat,current)
   if msg.type in ('note_on','note_off','control_change','pitchwheel'):events.append((when,msg))
  n=int((max((x[0] for x in events),default=0)+1.0)*SR);output=np.zeros((n,2),np.float32);pos=0
  for when,msg in events+[(n/SR,None)]:
   target=min(n,int(when*SR));count=max(0,target-pos)
   if count:
    l=np.empty(count,np.float32);r=np.empty(count,np.float32);write(synth,count,l.ctypes.data,0,1,r.ctypes.data,0,1);output[pos:target,0]=l;output[pos:target,1]=r;pos=target
   if msg is not None:
    if msg.type=='note_on' and msg.velocity:on(synth,channel,note_map.get(msg.note,msg.note),msg.velocity)
    elif msg.type in ('note_off','note_on'):off(synth,channel,note_map.get(msg.note,msg.note))
    elif msg.type=='control_change' and msg.control not in (0,32):cc(synth,channel,msg.control,msg.value)
    elif msg.type=='pitchwheel':
     pitch=fn('fluid_synth_pitch_bend',I,[ptr,I,I]);pitch(synth,channel,msg.pitch+8192)
  peak=float(np.max(np.abs(output))) if n else 0
  pcm=(np.clip(output,-1,1)*32767).astype('<i2')
  with wave.open(str(out),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
  return {'track':track_idx,'kind':kind,'peak':peak,'frames':n,'notes':sum(x.type=='note_on' and x.velocity>0 for _,x in events),'wav':out.name,
          'soundfont_bank':selected_bank,'program_zero_based':int(program),'note_map':note_map,'preset_selection':'EXACT_NO_FALLBACK'}
 finally:delete(synth);delset(settings)

def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);p.add_argument('--limit',type=int,default=4);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 sf2=Path(__file__).parent/'working_copy/replacement_instruments/TimGM6mb.sf2';reports=[]
 with zipfile.ZipFile(a.archive) as z:
  mids=[x for x in z.namelist() if x.startswith('ISOLATED_WORKING_COPY/AI_Comp_Outputs/render_handoff/') and x.endswith('.mid')]
  for name in mids[:a.limit]:
   mid=mido.MidiFile(file=io.BytesIO(z.read(name)));ident=Path(name).stem;folder=out/ident;folder.mkdir(exist_ok=True);tracks=[]
   for i,t in enumerate(mid.tracks):
    label=next((m.name for m in t if m.type=='track_name'),'').upper()
    kind='drums' if label in ('KICK','SNARE','HAT','TOMS','CRASH','RIDE','PERCUSSION') else 'guitar' if label in ('GUITAR','RHYTHM_GUITAR','LEAD_GUITAR') else None
    if kind:tracks.append(render_track(mid,i,sf2,folder/(label.lower()+'.wav'),kind))
   reports.append({'source_midi':name,'tracks':tracks,'status':'RENDERED_SUBSTITUTE_STEMS' if tracks else 'NO_MATCHING_GUITAR_DRUM_TRACKS'})
 (out/'verification.json').write_text(json.dumps({'source_archive_sha256':hashlib.sha256(Path(a.archive).read_bytes()).hexdigest(),'soundfont_sha256':hashlib.sha256(sf2.read_bytes()).hexdigest(),'status':'ISOLATED_SUBSTITUTE_STEMS_ONLY_NOT_3D_MASTER','results':reports},indent=2))
 print(json.dumps({'midi_files_checked':len(reports),'stems':sum(len(x['tracks']) for x in reports),'report':str(out/'verification.json')}))
if __name__=='__main__':main()
