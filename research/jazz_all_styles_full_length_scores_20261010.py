#!/usr/bin/env python3
"""Build eight independent 112-bar Jazz score drafts, without changing any original source."""
import json,sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,'composer_overrides')
from genre_styles.source_pattern_library import compile_original_source_seed
genres=['Swing','Jazz Ballad','Big Band','Jazz Waltz','Bebop','Cool Jazz','Dixieland','Jazz Fusion']
out=Path('jazz-eight-full-length-scores');out.mkdir(exist_ok=True)
manifest={'status':'ISOLATED_SCORE_DRAFTS_NOT_AUDIO','mixer_unchanged':True,'production_unchanged':True,'styles':[]}
for name in genres:
 plan=compile_original_source_seed(name)
 seed=plan['symbolic_note_events']
 meter=Fraction(plan['quarter_beats_per_bar'])
 score=[]
 for act in range(4):
  for phrase in range(4):
   for original in seed:
    e=dict(original)
    local_bar=int(Fraction(e['start_beat'])//meter)
    # Different musical arcs per style, without inventing or replacing its source instruments.
    if act==2 and e['role'] in ('KICK','SNARE','BRUSH') and (local_bar+phrase)%3==0:
     continue
    if act==0 and phrase==0 and e['role'] in ('HAT','RIDE') and local_bar%2:
     continue
    e['start_beat']=str(Fraction(e['start_beat'])+(act*4+phrase)*7*meter)
    e['velocity']=max(1,min(127,round(e['velocity']*([.8,.95,.84,1.0][act])+(phrase%2)*2)))
    e['act']=['INTRODUCTION','DEVELOPMENT','SPARSE_CONTRAST','RETURN'][act]
    e['phrase']=phrase
    score.append(e)
 score.sort(key=lambda e:(Fraction(e['start_beat']),e['role'],e['midi']))
 assert score and max(Fraction(e['start_beat'])+Fraction(e['duration_beats']) for e in score)<=112*meter
 data={'genre':name,'bars':112,'tempo_bpm':plan['tempo_bpm'],'quarter_beats_per_bar':str(meter),'status':'UNRENDERED_UNAUDITIONED_FULL_LENGTH_SYMBOLIC_DRAFT','events':score,'original_source_seed_preserved':True,'original_instrument_ids_preserved':True,'production_enabled':False}
 file=out/(name.lower().replace(' ','_')+'.json')
 file.write_text(json.dumps(data,indent=2)+'\n')
 manifest['styles'].append({'genre':name,'bars':112,'events':len(score),'filename':file.name})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
