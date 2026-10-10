#!/usr/bin/env python3
"""Independent Jazz Fusion full-length score proposal from its authored source seed.

Musical development is provisional and isolated: no live event promotion,
no instrument substitution, no approved mixer changes.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,'composer_overrides')
from genre_styles.source_pattern_library import compile_original_source_seed
plan=compile_original_source_seed('Jazz Fusion')
original=plan['symbolic_note_events']
# Four 28-bar acts, each with intro, two statements and a closing cadence.
# Deliberate contrasts in register, density, velocity, and section length.
acts=[('OPENING',0,0,0.78),('DEVELOPMENT',12,3,0.93),('SOLO_SPACE',-12,7,0.82),('FINAL_RETURN',0,0,1.0)]
events=[]
beats_per_bar=float(plan['quarter_beats_per_bar'])
phrase_bars=7
for act_index,(act,transpose,offset,energy) in enumerate(acts):
 for phrase in range(4):
  for source in original:
   note=dict(source)
   role=note['role']
   local_bar=int(float(note['start_beat'])//beats_per_bar)
   # Preserve percussion pitches. Register changes are confined to pitched parts.
   if note['pattern_kind']!='DRUM_ABSOLUTE':
    delta=transpose if role=='HARMONY' else (12 if act_index==3 and phrase==2 and role=='BASS' else 0)
    proposed=int(note['midi'])+delta
    declared=next(r['playable_midi_range'] for r in plan['roles'] if r['role']==role)
    if declared[0]<=proposed<=declared[1]:note['midi']=proposed
   if act_index==2 and role in ('KICK','SNARE') and local_bar%2==1 and phrase%2==0:continue
   start=float(source['start_beat'])+((act_index*4+phrase)*phrase_bars)*beats_per_bar
   note['start_beat']=round(start,5)
   note['velocity']=max(1,min(127,round(int(note['velocity'])*energy+(phrase%2)*3)))
   note['development_act']=act
   note['development_phrase']=phrase
   events.append(note)
events.sort(key=lambda e:(e['start_beat'],e['role'],e['midi']))
assert len(events)>len(original)*10
out=Path('jazz-fusion-full-length-proposal');out.mkdir(exist_ok=True)
result={'genre':'Jazz Fusion','status':'FULL_LENGTH_SYMBOLIC_ARRANGEMENT_PROPOSAL_NOT_AUDITIONED','bars':112,'tempo_bpm':plan['tempo_bpm'],'roles':[r['role'] for r in plan['roles']],'events':events,'original_recorded_programs_preserved':True,'mixer_unchanged':True,'production_enabled':False}
(out/'score.json').write_text(json.dumps(result,indent=2)+'\n')
print('JAZZ_FUSION_112_BAR_ISOLATED_SCORE_READY',len(events),'events',len(original),'seed events')
