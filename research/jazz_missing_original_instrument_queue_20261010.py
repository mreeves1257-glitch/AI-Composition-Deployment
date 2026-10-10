#!/usr/bin/env python3
"""Group blocked Jazz instrument assignments into six concurrent source-verification lanes."""
import json,sys
from collections import defaultdict
from pathlib import Path
src=Path('composer_overrides/genre_styles/Jazz/SOURCE_RESOURCE_BINDINGS_R1.json')
genres=json.loads(src.read_text())['genres']
queue=defaultdict(list)
for item in genres:
 for role,spec in item['role_bindings'].items():
  if spec.get('lookup_policy')=='BLOCKED_UNVERIFIED':
   queue[spec['original_instrument_id']].append({'genre':item['genre'],'role':role})
root=Path('jazz-six-original-instrument-lanes');root.mkdir(exist_ok=True)
for instrument,affected in sorted(queue.items()):
 payload={'required_original_instrument_id':instrument,'affected_styles':affected,'count':len(affected),'source_required':'EXACT_ORIGINAL_RECORDED_SFZ','candidate_preflight':'PENDING','binding_activation':'BLOCKED_UNTIL_VERIFIED','synthetic_substitutes_forbidden':True,'existing_ballad_resources_unchanged':True,'live_system_unchanged':True}
 (root/(instrument+'.json')).write_text(json.dumps(payload,indent=2)+'\n')
 print(instrument,len(affected),flush=True)
assert len(queue)==6,queue.keys()
(root/'manifest.json').write_text(json.dumps({'independent_source_lanes':6,'blocked_assignments':sum(map(len,queue.values())),'status':'SOURCE_VERIFICATION_QUEUE_ESTABLISHED'},indent=2)+'\n')
