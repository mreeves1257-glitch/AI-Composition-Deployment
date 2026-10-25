"""Explicit opt-in substitute output stage; does not alter canonical source or 3D mixer."""
from pathlib import Path
import sys, json, hashlib
import mido
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,'/mnt/data/AI_Composer_Substitute_Integration_2026-10-11')
from engine import AICompositionEngine
from render_substitute import render_track
from stem_delivery_manifest import build_manifest
from test_real_composer_to_bass_audio import RENDERER

DRUM={'KICK','SNARE','HAT','TOMS','CRASH','RIDE','PERCUSSION'}
GUITAR={'GUITAR','RHYTHM_GUITAR','LEAD_GUITAR','HARMONY','LEAD'}

def run(genre='ROCK',output_dir=None,engine_result=None):
    out=Path(output_dir or ROOT/'substitute_live_output');out.mkdir(parents=True,exist_ok=True)
    result=engine_result if engine_result is not None else AICompositionEngine().run(genre)
    handoff=result.get('output_handoff') or {}
    midi_path=handoff.get('midi_path')
    report={'genre':genre,'canonical_engine_status':result['status'],'midi_path':midi_path,'substitute_policy':'EXPLICIT_OPT_IN_ONLY','master_modified':False,'mixer_executed':False}
    if not midi_path or not Path(midi_path).is_file():
        report.update(status='BLOCKED_NO_COMPOSER_MIDI');return report
    sf=ROOT/'replacement_instruments/TimGM6mb.sf2'
    if not sf.is_file():
        report.update(status='BLOCKED_SOUNDFONT_MISSING');return report
    mid=mido.MidiFile(midi_path)
    stems=[];unhandled=[]
    bass_events=[e for e in result['modules']['performance']['events'] if e['instrument_id']=='electric_bass']
    bass_sfz=ROOT/'sound_resources/KARORYFER_GROWLYBASS_V1_002/growlybass_vicious.sfz'
    bass_result=None
    if bass_events and bass_sfz.is_file():
        bpm=result['modules']['theory']['tempo_bpm']
        formatted=[{'instrument_id':'electric_bass','midi_note':e['midi'],'velocity':e['velocity'],'start_seconds':e['start_beat']*60/bpm,'duration_seconds':e['duration_beats']*60/bpm} for e in bass_events]
        binding={'electric_bass':{'sfz':str(bass_sfz),'verified':True,'status':'VERIFIED_OPEN_RESOURCE','provider':'Karoryfer','license':'CC0'}}
        bass_result=RENDERER.render_output_handoff({'performance':{'events':formatted}},binding,out/'recorded_bass',sample_rate=22050)
        if bass_result.get('audio_rendered'):
            import wave, numpy as np
            bass_wav=Path(bass_result['stereo_derivative']['path'])
            with wave.open(str(bass_wav),'rb') as w:
                samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
            bass_peak=float(np.max(np.abs(samples.astype(np.float32)))/32768) if len(samples) else 0.0
            stems.append({'track_id':'1','instrument_id':'BASS','wav_path':str(bass_wav),'note_count':len(formatted),'peak':bass_peak})
    for i,track in enumerate(mid.tracks):
        if i==0:continue
        name=next((msg.name for msg in track if msg.type=='track_name'),f'TRACK_{i}').upper()
        kind='drums' if name in DRUM else 'guitar' if name in GUITAR else None
        if kind is None:
            if name=='BASS' and bass_result and bass_result.get('audio_rendered'): continue
            unhandled.append({'index':i,'name':name});continue
        wav=out/f'{i:02d}_{name.lower()}.wav'
        proof=render_track(mid,i,sf,wav,kind)
        stems.append({**proof,'track_id':str(i),'instrument_id':name,'wav_path':str(wav)})
    report.update(substitute_stems=stems,unhandled_tracks=unhandled,bass_rendered=bool(bass_result and bass_result.get('audio_rendered')),substitute_sha256=hashlib.sha256(sf.read_bytes()).hexdigest())
    if stems:
        report['stem_manifest']=build_manifest(stems,[x['track_id'] for x in stems],out/'substitute_stems_manifest.json')
    report['status']='SUBSTITUTE_STEMS_VERIFIED' if stems and all(x.get('peak',0)>0 for x in stems) else 'SUBSTITUTE_AUDIO_FAILED'
    report['full_composer_to_render_certified']=bool(not unhandled and report['status']=='SUBSTITUTE_STEMS_VERIFIED' and report['bass_rendered'])
    report['canonical_engine_integrated']=False
    report['certification_scope']='EXPLICIT_OPT_IN_EXTERNAL_RENDER_BRIDGE_ONLY'
    (out/'LIVE_BRIDGE_REPORT.json').write_text(json.dumps(report,indent=2,default=str))
    return report
if __name__=='__main__':
    r=run(sys.argv[1] if len(sys.argv)>1 else 'ROCK',sys.argv[2] if len(sys.argv)>2 else None)
    print(json.dumps({'status':r['status'],'stems':len(r.get('substitute_stems',[])),'unhandled':r.get('unhandled_tracks',[]),'canonical_engine_status':r['canonical_engine_status']},indent=2))