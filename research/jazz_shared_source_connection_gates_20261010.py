#!/usr/bin/env python3
"""Fail-closed validation of all Jazz instrument connections. No rebindings."""
import json,sys
from pathlib import Path
root=Path('composer_overrides/genre_styles/Jazz')
bindings=json.loads((root/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
packages=root/'instrument_packages'
readiness=json.loads((root/'JAZZ_CONNECTION_READINESS_R1.json').read_text())
errors=[]
report=[]
readiness_by={g['genre']:g for g in readiness['genre_connections']}
for g in bindings['genres']:
 name=g['genre']; slug=name.lower().replace(' ','_')
 path=packages/(slug+'.json')
 if not path.exists():errors.append(f'{name}: missing package');continue
 pkg=json.loads(path.read_text())
 for role,spec in g['role_bindings'].items():
  role_entry=pkg.get('roles',{}).get(role)
  if not role_entry:
   errors.append(f'{name}/{role}: missing package role');continue
  if role_entry.get('instrument_id')!=spec['original_instrument_id']:
   errors.append(f'{name}/{role}: original instrument identity changed')
  if role_entry.get('source_binding_status')=='BLOCKED_UNVERIFIED' and spec['lookup_policy']=='EXACT_ID':
   errors.append(f'{name}/{role}: stale blocked state')
 for role in readiness_by[name]['roles']:
  if role['original_instrument_id'] not in [v['original_instrument_id'] for v in g['role_bindings'].values()]:
   errors.append(f'{name}: readiness contains unknown source identity')
 report.append({'genre':name,'role_count':len(g['role_bindings']),'unverified_original_ids':[v['original_instrument_id'] for v in g['role_bindings'].values() if v['lookup_policy']!='EXACT_ID'],'fully_connected':False})
# A source ID match is not enough to assert live rendering; no production enablement here.
if errors:
 print(json.dumps({'ok':False,'errors':errors},indent=2));sys.exit(1)
print(json.dumps({'ok':True,'genres':report,'production_enabled':False},indent=2))
