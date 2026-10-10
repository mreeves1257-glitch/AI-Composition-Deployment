#!/usr/bin/env python3
"""Cross-check every Jazz missing role against EXISTING recorded sources only.

Does not bind candidates, alter approved Ballad, or authorize substitution.
"""
import json
from pathlib import Path
root=Path('composer_overrides/genre_styles/Jazz')
bindings=json.loads((root/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
lib=json.loads((root/'instrument_library.json').read_text())
out=Path('jazz-source-crosscheck');out.mkdir(exist_ok=True)
report={'genres':[],'status':'CANDIDATES_ONLY_NOT_AUTO_BOUND','original_ballad_unchanged':True}
for genre in bindings['genres']:
 roles=[]
 for role,record in genre['role_bindings'].items():
  if record.get('lookup_policy')=='EXACT_ID':continue
  instrument=record['original_instrument_id']
  # Exact original instrument identity is mandatory; similar instruments aren't silently substituted.
  matches=[]
  for key,value in lib.items():
   if isinstance(value,dict) and (key==instrument or value.get('original_instrument_id')==instrument):
    matches.append(key)
  roles.append({'role':role,'required_original_instrument_id':instrument,'candidate_exact_original_id_matches':matches,'status':'PENDING_INDEPENDENT_SOURCE_VERIFICATION'})
 report['genres'].append({'genre':genre['genre'],'missing_roles':roles})
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{'genre':g['genre'],'pending':len(g['missing_roles'])} for g in report['genres']],indent=2))
