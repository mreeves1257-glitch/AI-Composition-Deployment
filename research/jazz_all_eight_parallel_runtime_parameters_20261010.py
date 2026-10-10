#!/usr/bin/env python3
"""Install isolated genre-owned parameter packs for all eight Jazz styles in one run.

No live promotion; missing original SFZ bindings are explicitly marked pending.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,'composer_overrides')
from genre_styles.source_pattern_library import compile_original_source_seed
root=Path('composer_overrides/genre_styles/Jazz')
bindings=json.loads((root/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
out=Path('jazz-eight-parameter-packs');out.mkdir(exist_ok=True)
summary=[]
for row in bindings['genres']:
 genre=row['genre']
 plan=compile_original_source_seed(genre)
 roles={}
 for role,spec in row['role_bindings'].items():
  exact=spec.get('lookup_policy')=='EXACT_ID'
  roles[role]={'original_instrument_id':spec['original_instrument_id'],'source_lookup_policy':spec.get('lookup_policy'),'recorded_source_status':'EXACT_PROGRAM_REFERENCE' if exact else 'PENDING_ORIGINAL_RECORDED_SOURCE','render_enabled':exact,'allow_synthetic_substitution':False}
 settings={'schema':'JAZZ_STYLE_PARALLEL_PARAMETER_PACK_V1','genre':genre,'meter':plan['meter'],'tempo_bpm':plan['tempo_bpm'],'bars':112,'section_sequence':['INTRODUCTION','DEVELOPMENT','SPARSE_CONTRAST','RETURN'],'original_source_pattern':'Jazz/SOURCE_PATTERN_LIBRARY_R1.json','shared_interpreter':True,'separate_genre_parameters':True,'roles':roles,'original_instrument_must_match':True,'mixer':'EXISTING_3D_MIXER_UNCHANGED','pipeline':['COMPOSER','MIDI','GENRE_INTERPRETER','ORIGINAL_INSTRUMENT_RENDERER','3D_MIXER','FINISHED_MUSIC'],'allow_partial_render':False,'activate_when_all_sources_verified':True,'production_enabled':False,'parameter_pack_ready':True}
 filename=genre.lower().replace(' ','_')+'.json'
 (out/filename).write_text(json.dumps(settings,indent=2)+'\n')
 summary.append({'genre':genre,'parameter_pack':filename,'roles':len(roles),'pending_original_sources':sum(v['recorded_source_status'].startswith('PENDING') for v in roles.values())})
(out/'manifest.json').write_text(json.dumps({'styles':summary,'all_eight_configured':True,'audio_claimed':False},indent=2)+'\n')
print(json.dumps(summary,indent=2))
