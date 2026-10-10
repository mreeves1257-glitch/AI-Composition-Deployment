#!/usr/bin/env python3
"""Read-only Jazz full-song readiness across every style, with explicit gates."""
import json,sys
from pathlib import Path
sys.path.insert(0,'composer_overrides')
from genre_styles.source_pattern_library import compile_original_source_seed
ROOT=Path('composer_overrides/genre_styles/Jazz')
bindings=json.loads((ROOT/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
out=Path('jazz-full-song-readiness');out.mkdir(exist_ok=True)
summary={'scope':'all eight Jazz styles','diagnostic_only':True,'live_composer_unchanged':True,'styles':[]}
for row in bindings['genres']:
 genre=row['genre']
 plan=compile_original_source_seed(genre)
 unresolved=[k for k,v in row['role_bindings'].items() if v.get('lookup_policy')!='EXACT_ID']
 package=ROOT/'instrument_packages'/(genre.lower().replace(' ','_')+'.json')
 pkg=json.loads(package.read_text()) if package.exists() else {}
 gates={
  'genre':genre,'symbolic_note_events':len(plan['symbolic_note_events']),
  'unresolved_source_roles':unresolved,
  'original_instrument_package':pkg.get('binding_status','MISSING'),
  'independent_full_length_composition_implemented':genre=='Jazz Ballad',
  'independent_full_length_original_recording_render_verified':genre=='Jazz Ballad',
  'approved_live_connection':False,
  'can_render_unmodified_original_source_pattern_as_complete_song':False,
 }
 (out/(genre.lower().replace(' ','_')+'.json')).write_text(json.dumps(gates,indent=2)+'\n')
 summary['styles'].append(gates)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps([{'genre':x['genre'],'blocked_roles':len(x['unresolved_source_roles']),'full_song_verified':x['independent_full_length_original_recording_render_verified']} for x in summary['styles']],indent=2))
