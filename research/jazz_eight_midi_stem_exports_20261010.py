#!/usr/bin/env python3
"""Produce real playable-standard MIDI stem files for all Jazz score drafts.

No audio substitutions, changes to genre bindings, mixer, or live deployment.
"""
import json,sys
from fractions import Fraction
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
sys.path.insert(0,'composer/runtime')
spec=spec_from_file_location('midi_writer',Path('research/render_isolated_rock_recorded_stems_20261010.py'))
writer=module_from_spec(spec);spec.loader.exec_module(writer)
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
  payload=writer.midi_track(midi_events,data['tempo_bpm'])
  assert payload.startswith(b'MThd') and b'MTrk' in payload
  dest=out/(role.lower()+'.mid');dest.write_bytes(payload)
  exported.append({'role':role,'midi':dest.name,'notes':len(notes)})
 (out/'manifest.json').write_text(json.dumps({'genre':genre,'tempo_bpm':data['tempo_bpm'],'bars':112,'stems':exported,'source_score':file.name,'audio_rendered':False,'instrument_assignments_unchanged':True,'mixer_unchanged':True},indent=2)+'\n')
 manifest.append({'genre':genre,'stem_count':len(exported),'note_count':sum(e['notes'] for e in exported)})
assert len(manifest)==8
(root/'manifest.json').write_text(json.dumps({'styles':manifest,'midi_export_complete':True,'audio_rendered':False},indent=2)+'\n')
print(json.dumps(manifest,indent=2))
