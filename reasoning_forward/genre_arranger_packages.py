"""Dedicated executable arranger packages for the 53 non-anchor AI Composer genres.

Architecture:
  genre profile + v3 qualitative contract -> dedicated style package
  -> role/foreground/section arrangement -> existing shared renderer chain.

Classical and Big Band are protected anchors and deliberately remain on their
proven specialized arrangers. This module does not contain audio rendering.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import copy, hashlib, json, re

ROOT=Path(__file__).resolve().parent
OVERLAY_PATH=ROOT/'genre_v3_safe_overlay.json'
PACKAGE_DIR=ROOT/'genre_style_packages'
PACKAGE_INDEX_PATH=PACKAGE_DIR/'index.json'
PROTECTED_ANCHORS={'Classical','Big Band'}

PERCUSSION_TOKENS=('drums','conga','bongo','clave','cowbell','timbale','surdo','caixa','repinique','tamborim','agogo','shaker')
BASS_TOKENS=('bass',)
LEAD_TOKENS=('lead_guitar','alto_sax','tenor_sax','baritone_sax','trumpet','trombone','clarinet','flute','violin','synth_lead','synth_arp','marimba','pedal_steel')
HARMONY_TOKENS=('piano','guitar','clav','synth_chord','strings','choir','synth_pad','banjo','mandolin')
TEXTURE_TOKENS=('noise_fx','synth_pad','choir','strings')


def _sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()


def _overlay()->dict[str,Any]:
    return json.loads(OVERLAY_PATH.read_text())


def _static_package(name:str)->dict[str,Any]:
    # Runtime authority is the single validated v3 overlay already present in the
    # Composer. Per-genre JSON files are archival/convenience exports only.
    data=(_overlay().get('genres') or {}).get(name)
    if not isinstance(data,dict):
        raise ValueError('DEDICATED_GENRE_PACKAGE_MISSING::'+name)
    return data


def _text(value:Any)->str:
    if isinstance(value,dict): return ' '.join(_text(v) for v in value.values())
    if isinstance(value,list): return ' '.join(_text(v) for v in value)
    return str(value or '')


def _role_class(role:str, palette:list[str])->str:
    r=role.lower()
    if any(t in r for t in PERCUSSION_TOKENS): return 'FOUNDATION_PERCUSSION'
    if any(t in r for t in BASS_TOKENS): return 'FOUNDATION_BASS'
    if any(t in r for t in LEAD_TOKENS): return 'FOREGROUND_CAPABLE'
    if any(t in r for t in TEXTURE_TOKENS): return 'TEXTURAL_SUPPORT'
    if any(t in r for t in HARMONY_TOKENS): return 'HARMONIC_SUPPORT'
    return 'SUPPORT'


def _lead_candidates(palette:list[str])->list[str]:
    leads=[r for r in palette if _role_class(r,palette)=='FOREGROUND_CAPABLE']
    if leads: return leads
    # Solo/small-instrument profiles still need an explicit owner.
    musical=[r for r in palette if _role_class(r,palette) not in ('FOUNDATION_PERCUSSION','FOUNDATION_BASS')]
    return musical[:2] or palette[:1]


def _section_strategy(grammar:dict[str,Any], performance:dict[str,Any])->str:
    txt=(_text(grammar)+' '+_text(performance)).lower()
    if any(k in txt for k in ('build','break','drop','peak','layer')): return 'ENERGY_ARC'
    if any(k in txt for k in ('call','response','handoff','foreground')): return 'ROLE_HANDOFF'
    if any(k in txt for k in ('through-composed','through composed','motif','development')): return 'DEVELOPMENT_ARC'
    if any(k in txt for k in ('verse','chorus','hook')): return 'FORM_CONTRAST'
    return 'PHRASE_CONTRAST'


def build_package(name:str, profile:dict[str,Any], tmpl:str, palette:list[str], generation_plan:dict[str,Any], ctx:dict[str,Any]|None=None)->dict[str,Any]:
    if name in PROTECTED_ANCHORS:
        raise ValueError('PROTECTED_ANCHOR_USES_SPECIALIZED_ARRANGER::'+name)
    data=_static_package(name)
    if data.get('profile_id') != profile.get('profile_id'):
        raise ValueError('DEDICATED_GENRE_PACKAGE_PROFILE_MISMATCH::'+name)
    grammar=copy.deepcopy(data.get('musical_grammar') or {})
    required=('form_model','harmony_model','melody_model','rhythm_groove_model','bass_model','percussion_model','phrase_model','transition_model','development_model','cadence_ending_model')
    missing=[k for k in required if not grammar.get(k)]
    if missing:
        raise ValueError('DEDICATED_GENRE_PACKAGE_GRAMMAR_INCOMPLETE::'+name+'::'+','.join(missing))
    role_map={r:_role_class(r,palette) for r in palette}
    leads=_lead_candidates(palette)
    package={
        'package_version':'DEDICATED_GENRE_ARRANGER_V1',
        'genre_name':name,
        'profile_id':profile['profile_id'],
        'family':data.get('family'),
        'template':tmpl,
        'palette':list(palette),
        'role_map':role_map,
        'foreground_rotation':leads,
        'single_foreground_owner':True,
        'section_strategy':_section_strategy(grammar,data.get('performance') or {}),
        'musical_grammar':grammar,
        'performance':copy.deepcopy(data.get('performance') or {}),
        'production':copy.deepcopy(data.get('production') or {}),
        'variant_resolution':copy.deepcopy(data.get('variant_resolution') or {}),
        'generation_plan_sha256':(generation_plan or {}).get('plan_sha256'),
        'rules':{
            'no_generic_arranger_fallback':True,
            'profile_precedes_notes':True,
            'one_foreground_owner_per_phrase':True,
            'support_yields_to_foreground':True,
            'foundation_is_not_foreground':True,
            'transitions_are_section_aware':True,
            'preserve_independent_instrument_registration':True,
        },
    }
    package['package_id']='ARRANGER_'+re.sub(r'[^A-Za-z0-9]+','_',name).strip('_').upper()+'_V1'
    package['package_sha256']=_sha(package)
    return package


def _bar_of(event:dict[str,Any], meter:float)->int:
    return max(0,int(float(event.get('start_beat',0.0))//max(.0001,meter)))


def _owner_for_bar(package:dict[str,Any], bar:int, phrase_bars:int)->str|None:
    leads=package.get('foreground_rotation') or []
    if not leads: return None
    phrase=max(1,int(phrase_bars or 4))
    return leads[(bar//phrase)%len(leads)]


def arrange_events(name:str, events:list[dict[str,Any]], package:dict[str,Any], *, meter:float, phrase_bars:int, total_bars:int, reasoning_schedule:dict[str,Any]|None=None)->dict[str,Any]:
    """Apply the genre package as executable arrangement authority.

    When a reasoning schedule is supplied, v0.1 decisions are translated only
    through package-compatible controls: foreground handoff, support density,
    bounded energy shaping, transformed-recall articulation and transitions.
    Pitch, instrument identity and renderer authority remain unchanged.
    """
    if name in PROTECTED_ANCHORS: raise ValueError('ANCHOR_MUST_NOT_USE_PACKAGE_RUNTIME')
    if package.get('genre_name')!=name: raise ValueError('ARRANGER_PACKAGE_GENRE_MISMATCH')
    role_map=package['role_map']; strategy=package.get('section_strategy')
    from genre_reasoning_bridge import decision_for_bar, BRIDGE_ID
    out=[]; suppressed=0; ownership={}; reasoning_hits=0
    for raw in events:
        e=copy.deepcopy(raw)
        role=str(e.get('instrument_id',''))
        cls=role_map.get(role,'SUPPORT')
        bar=_bar_of(e,meter)
        decision=decision_for_bar(reasoning_schedule,bar+1) if reasoning_schedule else None
        owner=_owner_for_bar(package,bar,phrase_bars)
        if decision and decision.get('preferred_foreground_carrier') in (package.get('foreground_rotation') or []):
            owner=decision['preferred_foreground_carrier']
        ownership[str(bar)]=owner
        phase=(bar/max(1,total_bars-1)) if total_bars else 0.0
        if phase < .25: section='ESTABLISH'
        elif phase < .50: section='DEVELOP'
        elif phase < .75: section='CONTRAST'
        else: section='RETURN_CLIMAX'
        e['genre_arranger_package_id']=package['package_id']
        e['genre_arranger_package_sha256']=package['package_sha256']
        e['arrangement_section']=section
        e['foreground_owner']=owner
        if decision:
            reasoning_hits+=1
            e['reasoning_bridge_id']=BRIDGE_ID
            e['reasoning_section_function']=decision['section_function']
            e['reasoning_energy']=decision['energy']
            e['reasoning_density']=decision['density']
            e['reasoning_memory_action']=decision['memory_action']
            e['reasoning_transition_mode']=decision.get('transition_mode')
            # Bounded energy shape. This is intentionally small; genre performance
            # realization and the mixer retain downstream dynamic authority.
            e['velocity']=max(1,min(127,int(e.get('velocity',64))+max(-4,min(4,round((float(decision['energy'])-.5)*8)))))
        if role==owner:
            e['section_role_state']='FOREGROUND'
            e['velocity']=min(127,int(e.get('velocity',64))+5)
            if decision and str(decision.get('memory_action','')).startswith(('TRANSFORM','RECALL','DEVELOP')):
                e['articulation']='genre_foreground_transformed_recall'
            elif e.get('articulation') in (None,'genre_lead','counterline'):
                e['articulation']='genre_foreground_phrase'
        elif cls.startswith('FOUNDATION'):
            e['section_role_state']='FOUNDATION'
        elif cls=='HARMONIC_SUPPORT':
            e['section_role_state']='HARMONIC_SUPPORT'
            slot=int(round((float(e.get('start_beat',0.0))%max(.0001,meter))*4))
            density=int(decision.get('density',3)) if decision else 3
            # Low-density sections create more breathing room; high-density builds
            # preserve support. This replaces a fixed one-size-fits-all thinning rule.
            suppress=False
            if owner and density<=2: suppress=(slot%2==1)
            elif owner and density==3 and section in ('DEVELOP','CONTRAST'): suppress=(slot%4==3)
            elif owner and density==4 and section=='CONTRAST': suppress=(slot%8==7)
            if suppress:
                suppressed+=1; continue
            e['velocity']=max(1,int(e.get('velocity',64))-4)
        elif cls=='TEXTURAL_SUPPORT':
            e['section_role_state']='TEXTURAL_SUPPORT'
            if decision and int(decision.get('density',3))<=1 and bar%2==1:
                suppressed+=1; continue
            e['velocity']=max(1,int(e.get('velocity',64))-5)
        elif cls=='FOREGROUND_CAPABLE':
            e['section_role_state']='COUNTERLINE'
            density=int(decision.get('density',3)) if decision else 3
            # Non-owner melodic instruments answer rather than continuously double.
            if owner and role!=owner and ((density<=2 and bar%2==1) or (density>=3 and bar%3==2)):
                suppressed+=1; continue
            e['velocity']=max(1,int(e.get('velocity',64))-7)
            if e.get('articulation')=='genre_lead': e['articulation']='genre_counterline'
        else:
            e['section_role_state']='SUPPORT'
        if (bar+1)%max(1,int(phrase_bars or 4))==0:
            e['phrase_boundary']=True
            if decision: e['reasoning_spatial_transition']=decision.get('spatial_transition')
            if e['section_role_state'] in ('HARMONIC_SUPPORT','TEXTURAL_SUPPORT'):
                e['duration_beats']=min(float(e.get('duration_beats',.5)),max(.08,meter*.65))
        out.append(e)
    out.sort(key=lambda x:(float(x.get('start_beat',0)),str(x.get('track_id','')),int(x.get('midi',0))))
    manifest={
        'status':'PASS','genre':name,'package_id':package['package_id'],'package_sha256':package['package_sha256'],
        'input_event_count':len(events),'output_event_count':len(out),'suppressed_support_events':suppressed,
        'foreground_ownership_by_bar':ownership,'section_strategy':strategy,
        'reasoning_bridge_active':bool(reasoning_schedule),'reasoning_event_hits':reasoning_hits,
        'rule':'DEDICATED_GENRE_PACKAGE_OWNS_ARRANGEMENT_BEFORE_SEPARATOR',
    }
    return {'events':out,'manifest':manifest}


def validate_all_packages(profiles:dict[str,dict[str,Any]], family_template, palettes:dict[str,list[str]], compile_plan=None)->dict[str,Any]:
    rows=[]
    for name,profile in sorted(profiles.items()):
        if name in PROTECTED_ANCHORS: continue
        if profile.get('resolution_policy')!='AUTOMATIC_BASELINE_ALLOWED':
            # Controlled custom/hybrid profiles still receive a package record when
            # an overlay exists; their component resolver remains the note authority.
            try:
                _static_package(name)
            except ValueError:
                continue
        tmpl=family_template(name); palette=list(palettes.get(tmpl,palettes.get('hybrid',[])))
        fake={'plan_sha256':'STRUCTURAL_VALIDATION'}
        pkg=build_package(name,profile,tmpl,palette,fake,None)
        rows.append({'genre':name,'package_id':pkg['package_id'],'profile_id':pkg['profile_id'],'roles':len(pkg['role_map']),'grammar_fields':len(pkg['musical_grammar'])})
    return {'status':'PASS','package_count':len(rows),'packages':rows}