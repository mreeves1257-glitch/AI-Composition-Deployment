#!/usr/bin/env python3
"""Compare six missing Jazz source identities to installed recorded sources.

No changes to binding identities, program mappings, or live system.
"""
import json
from pathlib import Path
source=Path('composer_overrides/genre_styles/Jazz/SOURCE_RESOURCE_BINDINGS_R1.json')
catalog=json.loads(Path('composer_overrides/genre_styles/Jazz/instrument_library.json').read_text())['instruments']
genres=json.loads(source.read_text())['genres']
known={}
for name,item in catalog.items():
 known.setdefault(item['role'],[]).append({'catalog_key':name,'actual_instrument_id':item['instrument_id'],'resource_id':item['resource_id'],'sfz':item['sfz']})
out=Path('jazz-source-identity-feasibility');out.mkdir(exist_ok=True)
candidate_roles={'acoustic_bass':['ACOUSTIC_BASS'],'kick_drum_soft':['SOFT_KICK'],'brush_snare':['BRUSH_SNARE'],'piano':['ACCOMPANIMENT'],'horn_section':[],'banjo':[]}
report=[]
for target,semantic in candidate_roles.items():
 matches=[]
 for tag in semantic:matches+=known.get(tag,[])
 affected=[{'genre':g['genre'],'role':role} for g in genres for role,spec in g['role_bindings'].items() if spec['original_instrument_id']==target and spec['lookup_policy']=='BLOCKED_UNVERIFIED']
 report.append({'requested_id':target,'affected_assignments':affected,'existing_recorded_candidates':matches,'semantic_role_compatible':bool(matches),'exact_original_id_match':any(x['actual_instrument_id']==target for x in matches),'automatic_aliasing_permitted':False,'binding_status':'UNCHANGED_BLOCKED_UNVERIFIED'})
(out/'report.json').write_text(json.dumps({'sources':report,'status':'EVIDENCE_ONLY_NO_REBINDING'},indent=2)+'\n')
print(json.dumps([{'source':r['requested_id'],'assignments':len(r['affected_assignments']),'candidates':len(r['existing_recorded_candidates'])} for r in report],indent=2))
