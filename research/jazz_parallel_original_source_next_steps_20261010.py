#!/usr/bin/env python3
"""Produce parallel, non-destructive source-onboarding tickets for all Jazz styles."""
import json
from pathlib import Path
root=Path('composer_overrides/genre_styles/Jazz')
patterns=json.loads((root/'SOURCE_PATTERN_LIBRARY_R1.json').read_text())
bindings=json.loads((root/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
by={x['genre']:x for x in bindings['genres']}
out=Path('jazz-parallel-source-tickets');out.mkdir(exist_ok=True)
manifest={'genre_family':'Jazz','tickets':[],'automatic_instrument_substitution':False,'approved_mixer_modified':False}
for entry in patterns['genres']:
 name=entry['genre']
 if name not in by:continue
 role_map=by[name]['role_bindings']
 ticket={'genre':name,'status':'ISOLATED_SOURCE_ONBOARDING_NOT_LIVE','profile_id':entry['profile_id'],'tasks':[]}
 for role,resource in role_map.items():
  status=resource.get('lookup_policy')
  if status=='EXACT_ID':
   ticket['tasks'].append({'role':role,'instrument':resource['original_instrument_id'],'action':'VERIFY_PINNED_SFZ_SAMPLES_AND_NOTE_ZONE','binding_id':resource.get('binding_id'),'resource_id':resource.get('resource_id'),'status':'REFERENCE_PINNED_NOT_AUDIO_APPROVED'})
  else:
   ticket['tasks'].append({'role':role,'instrument':resource['original_instrument_id'],'action':'FIND_LICENSED_ORIGINAL_RECORDED_SFZ_NO_SYNTHETIC_SUBSTITUTE','status':'SOURCE_MISSING_OR_NOT_APPROVED'})
 ticket['remaining_work']=['Verify exact original recording and permitted license for each part','Verify SFZ note coverage and isolated audible stems','Implement full original genre-specific musical arrangement','Render through unchanged 3D mixer','Audition and approve full-length MP3']
 file=out/(name.lower().replace(' ','_')+'.json')
 file.write_text(json.dumps(ticket,indent=2)+'\n')
 manifest['tickets'].append({'genre':name,'file':file.name,'tasks':len(ticket['tasks'])})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
