#!/usr/bin/env python3
"""Render isolated genuine recorded rhythm stems for six unfinished Jazz styles.

Preserves symbolic original IDs; candidate aliases are NOT installed in genre routing.
"""
import json,os,sys,math
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,'composer/runtime')
from sfz_renderer_adapter import render_midi
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('writer',Path('research/render_isolated_rock_recorded_stems_20261010.py'))
writer=module_from_spec(spec);spec.loader.exec_module(writer)
style=os.environ['JAZZ_STYLE']
assert style in ('Swing','Big Band','Jazz Waltz','Bebop','Cool Jazz','Dixieland')
score=json.loads((Path('jazz-eight-full-length-scores')/(style.lower().replace(' ','_')+'.json')).read_text())
registry=json.loads(Path('composer/runtime/target_registry.json').read_text())['targets']['INTERNAL']['instrument_bindings']
mapping={'BASS':('acoustic_bass','double_bass',35,55),'KICK':('kick_drum_soft','kick_drum_rock:brush_drums',36,36),'RIDE':('ride_cymbal','ride_cymbal',51,51)}
out=Path('jazz-six-recorded-rhythm-stems')/style.lower().replace(' ','_');out.mkdir(parents=True,exist_ok=True)
result=[]
for role,(original,binding,low,high) in mapping.items():
 notes=[e for e in score['events'] if e['role']==role]
 assert notes and all(e['instrument_id']==original and low<=e['midi']<=high for e in notes),(style,role)
 events=[{'midi':e['midi'],'velocity':e['velocity'],'start_beat':float(Fraction(e['start_beat'])),'duration_beats':float(Fraction(e['duration_beats']))} for e in notes]
 midi=out/(role.lower()+'.mid');wav=out/(role.lower()+'.wav')
 midi.write_bytes(writer.midi_track(events,score['tempo_bpm']))
 render=render_midi(registry[binding],midi,wav,sample_rate=22050)
 assert render['audio_rendered'] and math.isfinite(render['peak_linear']) and render['peak_linear']>0,(style,role,render)
 result.append({'role':role,'original_instrument_id':original,'audition_candidate_binding':binding,'notes':len(notes),'wav':wav.name,'verified_non_silent':True})
 print('RECORDED_RHYTHM_STEM_PASS',style,role,len(notes),flush=True)
(out/'manifest.json').write_text(json.dumps({'genre':style,'bars':112,'original_instrument_ids_unchanged':True,'recorded_candidate_stems':result,'unresolved_harmony_not_replaced':True,'candidate_aliases_not_installed':True,'approved_mixer_unchanged':True,'not_finished_music':True},indent=2)+'\n')
