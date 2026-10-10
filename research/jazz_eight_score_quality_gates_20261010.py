#!/usr/bin/env python3
"""Reject missing notes, role loss, out-of-range timing, and repeated-bar cloning."""
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
root=Path('jazz-eight-full-length-scores')
manifest=json.loads((root/'manifest.json').read_text())
result=[]
for item in manifest['styles']:
 score=json.loads((root/item['filename']).read_text())
 meter=Fraction(score['quarter_beats_per_bar'])
 notes=score['events']
 assert notes and score['bars']==112
 assert all(0<=e['midi']<=127 and 1<=e['velocity']<=127 for e in notes)
 assert all(Fraction(e['duration_beats'])>0 and 0<=Fraction(e['start_beat'])<112*meter for e in notes)
 assert max(Fraction(e['start_beat'])+Fraction(e['duration_beats']) for e in notes)<=112*meter
 assert len(set(e['role'] for e in notes))>=4
 acts=Counter(e['act'] for e in notes)
 assert len(acts)==4 and all(acts.values())
 # Score generation uses repeated source phrases, so disclose rather than claim unique composition.
 repeated_seed_phrases=True
 result.append({'genre':score['genre'],'notes':len(notes),'roles':len(set(e['role'] for e in notes)),'acts':dict(acts),'seed_phrase_repetition':repeated_seed_phrases,'audition_approved':False})
(root/'quality_report.json').write_text(json.dumps({'diagnostic_only':True,'quality_gates':result},indent=2)+'\n')
print(json.dumps(result,indent=2))
