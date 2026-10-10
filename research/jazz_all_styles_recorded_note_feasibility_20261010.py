#!/usr/bin/env python3
"""Isolated Jazz source note-range feasibility; never changes original arrangements."""
import json,sys
from pathlib import Path
sys.path.insert(0,'composer_overrides')\nsys.path.insert(0,'composer/runtime')
from genre_styles.source_pattern_library import compile_original_source_seed
registry={} # Symbolic-only fast pass; installed sources verified separately in recorded-bank CI
candidates={'acoustic_bass':('double_bass',35,55),'kick_drum_soft':('kick_drum_rock:brush_drums',36,36),'brush_snare':('snare_drum:brush_drums',38,38),'electric_piano':('electric_piano',0,127),'ride_cymbal':('ride_cymbal',51,51)}
genres=['Swing','Jazz Ballad','Big Band','Jazz Waltz','Bebop','Cool Jazz','Dixieland','Jazz Fusion']
report={'genre_family':'Jazz','isolated_only':True,'no_automatic_substitution':True,'genres':{}}
for genre in genres:
 plan=compile_original_source_seed(genre)
 rows=[]
 for role in plan['roles']:
  notes=[x['midi'] for x in plan['symbolic_note_events'] if x['role']==role['role']]
  candidate=candidates.get(role['instrument_id'])
  row={'role':role['role'],'requested_instrument':role['instrument_id'],'notes':len(notes),'min_midi':min(notes),'max_midi':max(notes)}
  if candidate:
   binding,lo,hi=candidate
   row.update(candidate=binding,source_exists='SEPARATE_INSTALLED_SOURCE_PROOF',notes_outside_conservative_range=sorted(set(n for n in notes if not lo<=n<=hi)),candidate_is_not_approved=True)
  else:row['missing_exact_source']=True
  rows.append(row)
 report['genres'][genre]=rows
out=Path('jazz-source-feasibility');out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({g:[{'role':r['role'],'unmapped':r.get('missing_exact_source',False),'out_of_range':len(r.get('notes_outside_conservative_range',[]))} for r in rows] for g,rows in report['genres'].items()}))
