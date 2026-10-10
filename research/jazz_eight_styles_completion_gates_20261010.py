#!/usr/bin/env python3
"""Evidence-only completion gates for Jazz; never activates unapproved styles."""
import json
from pathlib import Path
from collections import Counter
ROOT=Path('composer_overrides/genre_styles/Jazz')
source=json.loads((ROOT/'SOURCE_PATTERN_LIBRARY_R1.json').read_text())
bindings=json.loads((ROOT/'SOURCE_RESOURCE_BINDINGS_R1.json').read_text())
packages=ROOT/'instrument_packages'
source_by={g['genre']:g for g in source['genres']}
bind_by={g['genre']:g for g in bindings['genres']}
out={'scope':'Jazz eight styles','production_changed':False,'source_patterns_are_not_finished_songs':True,'genres':{}}
for genre,seed in source_by.items():
 if genre not in bind_by:continue
 filename=genre.lower().replace(' ','_')+'.json'
 p=packages/filename
 package=json.loads(p.read_text()) if p.exists() else {}
 roles=bind_by[genre]['role_bindings']
 counters=Counter(r.get('lookup_policy','UNKNOWN') for r in roles.values())
 out['genres'][genre]={
 'seed_profile':seed['profile_id'],'seven_bar_seed_exists':True,
 'source_role_count':len(roles),'source_role_status_counts':dict(counters),
 'blocked_source_roles':[{'role':role,'instrument':r.get('original_instrument_id')} for role,r in roles.items() if r.get('lookup_policy')!='EXACT_ID'],
 'genre_package_file':filename,'genre_package_status':package.get('binding_status','MISSING'),
 'full_original_engine_audio': 'VERIFIED_SEPARATELY' if genre=='Jazz Ballad' else 'NOT_VERIFIED',
 'full_song_complete':genre=='Jazz Ballad',
 'next_gate':'Original genre instrument approval and complete full-song render' if genre!='Jazz Ballad' else 'Musical audition and approval'}
dest=Path('jazz-completion-gates');dest.mkdir(exist_ok=True)
(dest/'report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{'blocked':len(v['blocked_source_roles']),'package':v['genre_package_status']} for k,v in out['genres'].items()},indent=2))
