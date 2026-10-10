#!/usr/bin/env python3
"""Render 112-bar Jazz Fusion draft with exact original SFZ programs and unchanged 3D mixer."""
import json,hashlib,math,sys
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
sys.path.insert(0,'composer/runtime')
from sfz_renderer_adapter import render_midi
from standalone_3d_mixer import run_job
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
score=json.loads(Path('jazz-fusion-full-length-proposal/score.json').read_text())
assert score['genre']=='Jazz Fusion' and score['bars']==112 and not score['production_enabled']
registry=json.loads(Path('composer/runtime/target_registry.json').read_text())['targets']['INTERNAL']['instrument_bindings']
handoff=prepare_source_pattern_composer_handoff(compile_original_source_seed('Jazz Fusion'),target_bindings=registry)
roles=handoff['routing']['roles']
assert len(roles)==5 and all(x['status']=='EXACT_PROGRAM_REFERENCE_ONLY' for x in roles)
spec=spec_from_file_location('midi_writer',Path('research/render_isolated_rock_recorded_stems_20261010.py'))
writer=module_from_spec(spec);spec.loader.exec_module(writer)
root=Path('jazz-fusion-112bar-recorded-audio');root.mkdir(exist_ok=True)
stems=[];profiles=[];resolved=[];all_events=[]
ids={'electric_bass_guitar','electric_piano','kick_drum_rock','snare_drum','hi_hat'}
for r in roles:
 role=r['role'];binding=registry[r['binding_id']]
 original_id=r['original_instrument_id']
 assert original_id in ids
 notes=[e for e in score['events'] if e['role']==role]
 assert notes
 candidate=[]
 for e in notes:
  assert e['instrument_id']==original_id and 0<=e['midi']<=127
  if e['pattern_kind']=='DRUM_ABSOLUTE':
   assert e['midi'] in r['percussion_allowed_midi_notes']
  candidate.append({'track_id':role,'instrument_id':r['binding_id'],'start_beat':float(e['start_beat']),'duration_beats':float(e['duration_beats']),'midi':e['midi'],'velocity':e['velocity']})
 all_events.extend(candidate)
 midi=root/(role.lower()+'.mid');wav=root/(role.lower()+'.wav')
 midi.write_bytes(writer.midi_track(candidate,score['tempo_bpm']))
 rendered=render_midi(binding,midi,wav,sample_rate=22050)
 assert rendered['audio_rendered'] and math.isfinite(rendered['peak_linear']) and rendered['peak_linear']>0,(role,rendered)
 stems.append({'track_id':role,'wav_path':str(wav.resolve())})
 profiles.append({'track_id':role,'instrument_id':original_id,'role':role})
 resolved.append({'track_id':role,'resource':binding})
 print('RECORDED_STEM_PASS',role,len(candidate),flush=True)
engine={'genre':'Jazz Fusion','modules':{'instrument':{'profiles':profiles},'target':{'resolved_resources':resolved},'performance':{'events':all_events},'theory':{'composition_fingerprint':hashlib.sha256(json.dumps(all_events,sort_keys=True).encode()).hexdigest()}}}
job=root/'mixer_job.json';job.write_text(json.dumps({'engine_result':engine,'stems':stems},indent=2))
mix=run_job(job,root/'mixed')
assert mix['status']=='AUDIO_RENDER_PASS' and mix['audio_rendered'],mix
import shutil
final=root/'JAZZ_FUSION_112BAR_ORIGINAL_RECORDED_3D.wav';shutil.copy2(mix['wav_path'],final)
(root/'manifest.json').write_text(json.dumps({'genre':'Jazz Fusion','bars':112,'events':len(all_events),'stems':len(stems),'diagnostic_only':True,'original_mixer_unchanged':True,'wav':final.name},indent=2)+'\n')
print('JAZZ_FUSION_FULL_LENGTH_ORIGINAL_RECORDED_3D_PASS',final,flush=True)
