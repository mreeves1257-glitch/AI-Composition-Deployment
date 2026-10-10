#!/usr/bin/env python3
"""Produce real playable-standard MIDI stem files for all Jazz score drafts.

No audio substitutions, changes to genre bindings, mixer, or live deployment.
"""
import json,sys
from fractions import Fraction
from pathlib import Path
def vlq(n):
 parts=[n&127];n>>=7
 while n: parts.insert(0,(n&127)|128);n>>=7
 return bytes(parts)
def midi_track(events,bpm):
 tempo=round(60000000/bpm)
 commands=[(0,0,b'\\xff\\x51\\x03'+tempo.to_bytes(3,'big'))]
 for e in events:
  note=int(e['midi']);vel=int(e['velocity'])
  start=round(e['start_beat']*480);end=round((e['start_beat']+e['duration_beats'])*480)
  assert 0<=note<=127 and 1<=vel<=127 and end>start
  commands.extend([(start,1,bytes([0x90,note,vel])),(end,0,bytes([0x80,note,0]))])
 commands.sort(key=lambda x:(x[0],x[1]))
 track=bytearray();last=0
 for tick,_,msg in commands:track.extend(vlq(tick-last));track.extend(msg);last=tick
 track.extend(b'\\x00\\xff\\x2f\\x00')
 return b'MThd'+(6).to_bytes(4,'big')+b'\\x00\\x00\\x00\\x01\\x01\\xe0'+b'MTrk'+len(track).to_bytes(4,'big')+bytes(track)
scores=Path('jazz-eight-full-length-scores')
root=Path('jazz-eight-midi-stems');root.mkdir(exist_ok=True)
manifest=[]
for file in sorted(scores.glob('*.json')):
 if file.name=='manifest.json':continue
 data=json.loads(file.read_text())
 assert data['bars']==112 and not data['production_enabled']
 genre=data['genre']
 out=root/file.stem;out.mkdir(exist_ok=True)
 roles=sorted({e['role'] for e in data['events']})
 exported=[]
 for role in roles:
  notes=[e for e in data['events'] if e['role']==role]
  midi_events=[{'midi':e['midi'],'velocity':e['velocity'],'start_beat':float(Fraction(e['start_beat'])),'duration_beats':float(Fraction(e['duration_beats']))} for e in notes]
  payload=midi_track(midi_events,data['tempo_bpm'])
  assert payload.startswith(b'MThd') and b'MTrk' in payload
  dest=out/(role.lower()+'.mid');dest.write_bytes(payload)
  exported.append({'role':role,'midi':dest.name,'notes':len(notes)})
 (out/'manifest.json').write_text(json.dumps({'genre':genre,'tempo_bpm':data['tempo_bpm'],'bars':112,'stems':exported,'source_score':file.name,'audio_rendered':False,'instrument_assignments_unchanged':True,'mixer_unchanged':True},indent=2)+'\n')
 manifest.append({'genre':genre,'stem_count':len(exported),'note_count':sum(e['notes'] for e in exported)})
assert len(manifest)==8
(root/'manifest.json').write_text(json.dumps({'styles':manifest,'midi_export_complete':True,'audio_rendered':False},indent=2)+'\n')
print(json.dumps(manifest,indent=2))
