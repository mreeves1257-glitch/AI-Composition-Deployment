"""Safe all-genre bridge for Composer Musical Reasoning Engine v0.1.

The frozen reasoning engine remains advisory and unchanged. This bridge converts
its abstract decisions into bounded genre-arranger instructions. Genre profile,
style package, note generator, instrument identity, renderer and 3D mixer retain
their existing authority.
"""
from __future__ import annotations
from pathlib import Path
import copy, hashlib, json, sys
from typing import Any

ROOT=Path(__file__).resolve().parent
REASONING_DIR=ROOT/'experimental_reasoning'
if str(REASONING_DIR) not in sys.path:
    sys.path.insert(0,str(REASONING_DIR))
from reasoning_engine_v0_1 import (
    ComposerState, MusicalGoal, MusicalIdeaMemory, InstrumentMemory,
    reason, validate as validate_reasoning,
)

BRIDGE_ID='GENRE_REASONING_BRIDGE_V1_ALL_55'


def _sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()


def _semantic_section(raw:str, form:str|None=None)->str:
    n=str(raw or '').strip().upper().replace('-','_').replace(' ','_')
    if 'INTRO' in n: return 'intro'
    if 'PRE' in n and 'CHORUS' in n: return 'prechorus'
    if 'CHORUS' in n or 'SHOUT' in n: return 'chorus'
    if 'BRIDGE' in n or n=='B': return 'bridge'
    if 'BREAK' in n: return 'breakdown'
    if 'SOLO' in n or 'FEATURE' in n: return 'solo'
    if 'OUTRO' in n or 'CODA' in n or 'ENDING' in n: return 'outro'
    if 'VERSE' in n: return 'verse'
    if n.startswith('A'): return 'verse'
    return 'verse' if str(form or '').lower() in ('verse_chorus','aba') else 'verse'


def _has_bass(palette:list[str])->bool:
    return any('bass' in str(x).lower() for x in palette)


def _kick_target(name:str, profile:dict[str,Any], palette:list[str], tags:list[str])->float:
    ptxt=' '.join(str(profile.get(k,'')) for k in ('percussion_behavior_if_applicable','groove_behavior','dynamic_behavior')).lower()
    n=name.lower()
    if not any('drum' in str(x).lower() or 'kick' in str(x).lower() for x in palette): return 0.0
    if any(k in n for k in ('classical','new age','ambient','spiritual')): return 0.0
    if any(k in n for k in ('jazz ballad','cool jazz','bossa','bolero')) or 'brush' in ptxt or 'light percussion' in ptxt: return 0.25
    if any(k in n for k in ('swing','bebop','dixieland','jazz waltz','jazz fusion','big band')): return 0.45
    if any(k in n for k in ('country','bluegrass','waltz','two-step')): return 0.65
    if any(k in n for k in ('rock','funk','soul','rhythm and blues','r&b','house','techno','trance','disco','afro','reggaeton','garage','breakbeat')): return 1.0
    return 0.7


def _infer_role(role:str)->str:
    r=role.lower()
    if 'bass' in r: return 'FOUNDATION_BASS'
    if any(x in r for x in ('drum','conga','bongo','clav','cowbell','timbale','surdo','shaker','agogo','repinique','caixa','tamborim')): return 'FOUNDATION_PERCUSSION'
    if any(x in r for x in ('lead','sax','trumpet','trombone','clarinet','flute','violin','fiddle','steel','marimba')): return 'FOREGROUND_CAPABLE'
    if any(x in r for x in ('piano','guitar','clav','synth','strings','choir','banjo','mandolin','organ')): return 'HARMONIC_SUPPORT'
    return 'SUPPORT'


def _role_map(package:dict[str,Any]|None,palette:list[str])->dict[str,str]:
    if package and package.get('role_map'): return dict(package['role_map'])
    return {r:_infer_role(r) for r in palette}


def _foreground(package:dict[str,Any]|None,palette:list[str])->list[str]:
    if package and package.get('foreground_rotation'): return list(package['foreground_rotation'])
    rm=_role_map(package,palette)
    leads=[r for r in palette if rm.get(r)=='FOREGROUND_CAPABLE']
    if leads: return leads
    return [r for r in palette if not rm.get(r,'').startswith('FOUNDATION')][:2] or list(palette[:1])


def _sections_from_ctx(ctx:dict[str,Any], bars:int, phrase_bars:int)->list[dict[str,Any]]:
    sections=copy.deepcopy((ctx.get('form') or {}).get('sections') or [])
    if sections: return sections
    return [{'name':'A','start_bar':1,'length_bars':max(1,int(bars))}]


def build_schedule(name:str, profile:dict[str,Any], palette:list[str], generation_plan:dict[str,Any], ctx:dict[str,Any], package:dict[str,Any]|None=None, sections:list[dict[str,Any]]|None=None)->dict[str,Any]:
    sections=copy.deepcopy(sections or _sections_from_ctx(ctx,int(ctx.get('bars') or generation_plan.get('bars') or 1),int(generation_plan.get('phrase_bars',4))))
    tags=list(generation_plan.get('semantic_tags') or [])
    role_map=_role_map(package,palette); leads=_foreground(package,palette)
    histories={r:InstrumentMemory(r,meaningful_windows=1,total_windows=1,featured_windows=0,last_role=role_map.get(r)) for r in palette}
    idea=None; occurrence={}; packets=[]; compact=[]; previous_energy=None; previous_semantic=None; previous_end=0
    for idx,section in enumerate(sections):
        sem=_semantic_section(section.get('name'),generation_plan.get('form'))
        occurrence[sem]=occurrence.get(sem,0)+1
        start=max(1,int(section.get('start_bar',previous_end+1))); length=max(1,int(section.get('length_bars',1))); end=start+length-1
        if idea is None:
            idea=MusicalIdeaMemory(
                idea_id=f'{name}_PRIMARY_IDEA', origin_section=sem,
                origin_instrument=(leads[0] if leads else None), contour_signature='GENRE_PRIMARY_CONTOUR',
                rhythm_signature='GENRE_PRIMARY_RHYTHM', harmonic_relation=str(generation_plan.get('harmony_family','GENRE_AUTHORITY')),
                expressive_character='GENRE_DEFINED', introduced_bar=start-1,last_seen_bar=end,
                appearances=1,transformations=0,last_carrier=(leads[0] if leads else None))
            prior_ideas=()
        else:
            prior_ideas=(idea,)
        goal=MusicalGoal(
            instrument_balance=1.0,
            bass_richness=1.0 if _has_bass(palette) else 0.0,
            kick_impact=_kick_target(name,profile,palette,tags),
        )
        state=ComposerState(
            genre=name,profile_id=profile['profile_id'],section=sem,section_occurrence=occurrence[sem],
            previous_section=previous_semantic,
            next_section=_semantic_section(sections[idx+1].get('name'),generation_plan.get('form')) if idx+1<len(sections) else None,
            bars_elapsed=start-1,bars_in_section=0,section_bars_total=length,
            previous_energy=previous_energy,active_instruments=tuple(palette),
            instrument_history=tuple(histories.values()),musical_idea_history=prior_ideas,
        )
        packet=reason(state=state,semantic_tags=tags,generation_plan=generation_plan,goal=goal)
        validate_reasoning(packet); packets.append(packet)
        d=packet['decisions']; memory=d['musical_memory']; preferred=memory.get('preferred_next_carrier')
        if preferred not in leads:
            preferred=leads[idx%len(leads)] if leads else None
        row={
            'section_index':idx,'source_section':section.get('name'),'section_function':sem,
            'occurrence':occurrence[sem],'start_bar':start,'length_bars':length,'end_bar':end,
            'energy':float(d['energy']['target']),'energy_motion':d['energy']['motion'],
            'density':int(d['density']['target_level_1_to_5']),
            'memory_action':memory.get('action') or memory.get('status'),
            'preferred_foreground_carrier':preferred,
            'transition_mode':d['transition'].get('mode'),
            'spatial_transition':d['spatial_choreography'].get('transition'),
            'decision_sha256':packet['decision_sha256'],
        }
        compact.append(row)
        for r in palette:
            old=histories[r]; cls=role_map.get(r,'SUPPORT')
            meaningful=old.meaningful_windows + (1 if cls.startswith('FOUNDATION') or r==preferred else 0)
            histories[r]=InstrumentMemory(r,meaningful_windows=meaningful,total_windows=old.total_windows+1,
                                          featured_windows=old.featured_windows+(1 if r==preferred else 0),last_role=cls)
        if idea is not None:
            trans=idea.transformations + (1 if str(row['memory_action']).startswith(('TRANSFORM','DEVELOP','RECALL')) else 0)
            idea=MusicalIdeaMemory(idea_id=idea.idea_id,origin_section=idea.origin_section,origin_instrument=idea.origin_instrument,
                contour_signature=idea.contour_signature,rhythm_signature=idea.rhythm_signature,harmonic_relation=idea.harmonic_relation,
                expressive_character=idea.expressive_character,introduced_bar=idea.introduced_bar,last_seen_bar=end,
                appearances=idea.appearances+1,transformations=trans,last_carrier=preferred or idea.last_carrier)
        previous_energy=row['energy']; previous_semantic=sem; previous_end=end
    manifest={'status':'PASS','bridge_id':BRIDGE_ID,'engine_id':'COMPOSER_MUSICAL_REASONING_ENGINE_V0_1',
              'genre':name,'profile_id':profile['profile_id'],'section_count':len(compact),
              'schedule':compact,'packet_hashes':[p['decision_sha256'] for p in packets],
              'authority':'GENRE_FILTERED_ADVISORY_DECISIONS','note_authority':False,'instrument_identity_authority':False}
    manifest['manifest_sha256']=_sha(manifest)
    return {'manifest':manifest,'packets':packets}


def decision_for_bar(schedule:dict[str,Any]|None, bar_one_based:int)->dict[str,Any]|None:
    if not schedule: return None
    rows=(schedule.get('schedule') if schedule.get('bridge_id') else schedule.get('manifest',{}).get('schedule')) or []
    for row in rows:
        if int(row['start_bar']) <= int(bar_one_based) <= int(row['end_bar']): return row
    return rows[-1] if rows else None


def attach_to_generation_plan(plan:dict[str,Any], reasoning:dict[str,Any])->dict[str,Any]:
    out=copy.deepcopy(plan); m=reasoning['manifest']
    out['musical_reasoning_bridge']={
        'bridge_id':m['bridge_id'],'engine_id':m['engine_id'],'manifest_sha256':m['manifest_sha256'],
        'section_count':m['section_count'],'schedule':copy.deepcopy(m['schedule']),
        'authority':'GENRE_FILTERED_ADVISORY_DECISIONS'
    }
    return out


def shape_anchor_events(name:str,events:list[dict[str,Any]],reasoning:dict[str,Any],meter:float)->dict[str,Any]:
    """Very conservative reasoning realization for a proven anchor (Big Band).
    No notes, timing, instrument identity, ownership, or event count are changed.
    """
    out=[]
    for raw in events:
        e=copy.deepcopy(raw); bar=int(float(e.get('start_beat',0))//max(.001,meter))+1
        d=decision_for_bar(reasoning['manifest'],bar)
        if d:
            delta=max(-3,min(3,round((float(d['energy'])-.5)*6)))
            e['velocity']=max(1,min(127,int(e.get('velocity',64))+delta))
            e['reasoning_bridge_id']=BRIDGE_ID; e['reasoning_section_function']=d['section_function']
            e['reasoning_memory_action']=d['memory_action']; e['reasoning_energy']=d['energy']; e['reasoning_density']=d['density']
        out.append(e)
    return {'events':out,'manifest':{'status':'PASS','genre':name,'bridge_id':BRIDGE_ID,'event_count_unchanged':len(out)==len(events),
        'instrument_identity_changed':False,'timing_changed':False,'pitch_changed':False,'mode':'ANCHOR_CONSERVATIVE_DYNAMIC_SHAPING'}}


def apply_classical_plan(profile:dict[str,Any],plan:dict[str,Any],parts:list[str])->tuple[dict[str,Any],dict[str,Any]]:
    """Apply the user-approved Classical reasoning trial behavior to a plan."""
    if plan.get('reasoning_bridge_applied')==BRIDGE_ID:
        return copy.deepcopy(plan),copy.deepcopy(plan.get('musical_reasoning_manifest') or {})
    out=copy.deepcopy(plan)
    ctx={'form':{'sections':copy.deepcopy(out['sections'])},'bars':len(out['bars'])}
    gp={'form':'aba','phrase_bars':8,'semantic_tags':['functional','lyrical','counterline','wide_dynamic','legato'],
        'melody_development_bars':out.get('melody_development_bars',16),'literal_melody_reuse_after_bars':out.get('literal_melody_reuse_after_bars',16),
        'harmony_family':'functional'}
    sec=[]
    for s in out['sections']:
        n=s['name']; mapped='VERSE' if n in ('A','A_RETURN') else 'BRIDGE' if n=='B' else 'OUTRO' if n=='CODA' else n
        sec.append({'name':mapped,'start_bar':s['start_bar'],'length_bars':s['length_bars'],'original_name':n})
    reasoning=build_schedule('Classical',profile,parts,gp,ctx,None,sections=sec)
    rows=reasoning['manifest']['schedule']
    for idx,s in enumerate(out['sections']):
        row=rows[idx]; start=s['start_bar']; end=start+s['length_bars']-1
        bars=[b for b in out['bars'] if start<=b['bar']<=end]
        reason_peak=58+round(34*float(row['energy']))
        for b in bars:
            b['dynamic_peak']=round(int(b['dynamic_peak'])*.72+reason_peak*.28)
            b['reasoning_energy']=row['energy']; b['reasoning_density']=row['density']; b['reasoning_motion']=row['energy_motion']; b['reasoning_memory_action']=row['memory_action']
            if row['energy_motion']=='BUILD' and b['section']!='CODA': b['bass_style']='moving'
            elif row['energy_motion']=='PULL_BACK': b['bass_style']='sustained'
        if s['name']=='A_RETURN' and str(row['memory_action']) in ('TRANSFORM_AND_RECALL','RECALL_AS_RESPONSE_OR_COUNTER_IDEA','DEVELOP_BEFORE_INTRODUCING_ANOTHER_MAJOR_IDEA'):
            for b in bars:
                local=b['bar']-start
                if local>=s['length_bars']//2:
                    b['motif_operation']='development'; b['melody_development_bar']=(int(b['melody_development_bar'])+5)%16
                    if (local//4)%2==0: b['lead']='flute'
                else: b['motif_operation']='return'
    out['reasoning_bridge_applied']=BRIDGE_ID; out['musical_reasoning_manifest']=copy.deepcopy(reasoning['manifest'])
    return out,reasoning['manifest']
