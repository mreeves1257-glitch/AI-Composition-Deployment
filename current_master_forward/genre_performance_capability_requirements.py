"""Per-registration articulation/timing/control capability requirements.

This module does not synthesize unsupported expression. It converts the selected
profile + generated event intent into a contract that target resources must later
prove they can execute. A matching patch name alone is not production certification.

V1.1 scopes profile prose to the instrument/role it actually describes. Event-level
articulations remain authoritative. This prevents, for example, guitar slide/mute
requirements from leaking into drum or bass registrations merely because those words
occur in the same genre-level articulation sentence.
"""
from __future__ import annotations
import hashlib, json, re

PLAN_ID='GENRE_PERFORMANCE_CAPABILITY_REQUIREMENTS_V1'

ARTICULATION_MAP={
 'kick':('KICK_HIT',), 'snare':('SNARE_HIT',), 'brush_snare':('BRUSH_ARTICULATION',),
 'ride':('RIDE_CYMBAL_TIME',), 'brush_ride':('BRUSH_ARTICULATION','RIDE_CYMBAL_TIME'),
 'hat':('HIHAT_TIMEKEEPING',), 'tom_fill':('TOM_HIT_VARIATION',), 'crash':('CRASH_CYMBAL',),
 'hand_percussion':('HAND_PERCUSSION_STROKE_VARIATION',),
 'banjo_roll':('BANJO_ROLL_REPETITION_VARIATION',), 'banjo_strum':('BANJO_STRUM',),
 'mandolin_chop':('MANDOLIN_CHOP_SHORT',),
 'clave_strike':('CLAVE_DISTINCT_STRIKE',), 'bongo_martillo':('BONGO_MARTILLO',),
 'cowbell_pulse':('COWBELL_STROKE_VARIATION',), 'shaker_subdivision':('SHAKER_ALTERNATING_STROKES',),
 'timbale_cascara':('TIMBALE_CASCARA',), 'timbale_fill':('TIMBALE_FILL_VARIATION',),
 'pedal_steel_glide_intent':('PEDAL_STEEL_GLIDE_OR_BEND',),
 'surdo_open':('SURDO_OPEN_MUTED',), 'surdo_muted':('SURDO_OPEN_MUTED',),
 'caixa_samba':('CAIXA_SAMBA_STROKE',), 'repinique_call':('REPINIQUE_CALL_CUE',),
 'repinique_support':('REPINIQUE_SUPPORT_STROKE',), 'tamborim_teleco_teco':('TAMBORIM_FAST_TIMELINE_STROKE',),
 'agogo_high_low':('AGOGO_HIGH_LOW_BELLS',),
 'sustain':('SUSTAIN',), 'legato':('LEGATO_TRANSITIONS',), 'staccato':('SHORT_STACCATO',),
 'tenuto':('TENUTO_SUSTAIN_CONTROL',), 'accent':('ACCENT_VARIATION',),
 'pizzicato':('PIZZICATO',), 'tremolo':('TREMOLO',),
 'genre_lead':('EXPRESSIVE_LEAD_ATTACK_RELEASE',),
 'counterline':('COUNTERLINE_ATTACK_RELEASE',), 'genre_harmony':('HARMONY_ATTACK_RELEASE',),
 'genre_bass':('BASS_ATTACK_RELEASE',), 'support_bass':('BASS_ATTACK_RELEASE',),
 'noise_texture':('TEXTURE_AUTOMATION_CAPABLE',),
}

CRITICAL_BY_CAP={
 'PEDAL_STEEL_GLIDE_OR_BEND','BANJO_ROLL_REPETITION_VARIATION','MANDOLIN_CHOP_SHORT',
 'BRUSH_ARTICULATION','SURDO_OPEN_MUTED','AGOGO_HIGH_LOW_BELLS','TAMBORIM_FAST_TIMELINE_STROKE',
 'TIMBALE_CASCARA','BONGO_MARTILLO','CLAVE_DISTINCT_STRIKE'
}

PROFILE_CAP_PATTERNS=[
 (r'\blegato\b','LEGATO_TRANSITIONS'),(r'\bstaccato\b','SHORT_STACCATO'),
 (r'\btremolo\b','TREMOLO'),(r'\bpizzicato\b|\bpizz\b','PIZZICATO'),
 (r'\bgliss|\bslide','GLISSANDO_SLIDE'),(r'\bmuted?\b|\bmutes?\b','MUTED_ARTICULATION'),
 (r'\baccent','ACCENT_VARIATION'),(r'\bvibrato\b','VIBRATO_CONTROL'),
 (r'\bbrush','BRUSH_ARTICULATION'),(r'\bsustain','SUSTAIN'),
 (r'\battack','ATTACK_VARIATION'),(r'\bchop\b','SHORT_CHOP'),
 (r'\bbends?\b|\bscoops?\b','PITCH_BEND_OR_SCOOP'),
]

CONTROL_PATTERNS=[
 (r'\bexpression\b','EXPRESSION_CC_OR_EQUIVALENT'),(r'\bvibrato\b','VIBRATO_CONTROL'),
 (r'\bsustain pedal|\bpedal-aware|\bpedal-shaped','SUSTAIN_PEDAL_CONTROL'),
 (r'\bpitch bend|\bbend','PITCH_BEND_OR_ARTICULATION_TRANSITION'),
 (r'\bfilter|cutoff|resonance','FILTER_AUTOMATION'),(r'\bautomation\b','PARAMETER_AUTOMATION'),
 (r'\bvelocity\b','VELOCITY_RESPONSE'),(r'\bnote length|duration','NOTE_LENGTH_RESPONSE'),
]

PERCUSSION_WORDS=('drum','kick','snare','hat','ride','crash','tom','conga','bongo','shaker','clave','cowbell','timbale','agogo','caixa','surdo','tamborim','repinique','timpani','percussion')
WIND_WORDS=('trumpet','trombone','horn','sax','clarinet','flute','oboe','bassoon','tuba','wind','brass')
STRING_WORDS=('violin','viola','cello','fiddle','strings')
KEY_WORDS=('piano','electric_piano','clav','keyboard','keys')
PLUCK_WORDS=('banjo','mandolin')


def _sha(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def _source_genre(track, events, fallback):
    gs={e.get('component_genre') for e in events if str(e.get('track_id'))==str(track) and e.get('component_genre')}
    return next(iter(gs)) if len(gs)==1 else fallback


def _families(instrument_id, role=''):
    iid=str(instrument_id or '').lower(); role=str(role or '').lower(); out=set()
    if any(w in iid for w in PERCUSSION_WORDS): out.add('PERCUSSION')
    if 'guitar' in iid or 'pedal_steel' in iid: out.add('GUITAR')
    if iid in ('banjo','mandolin'): out.update(('PLUCKED','GUITAR'))
    # Avoid treating bassoon as bass simply because of its spelling.
    if iid in ('electric_bass','electric_bass_guitar','double_bass','synth_bass') or iid.endswith('_bass'):
        out.add('BASS')
    if any(w in iid for w in KEY_WORDS): out.add('KEYS')
    if any(w in iid for w in WIND_WORDS): out.add('WIND_BRASS')
    if any(w in iid for w in STRING_WORDS) or iid in ('double_bass','strings'):
        out.add('STRINGS')
    if iid.startswith('synth_') or iid in ('synth_chord','synth_pad','synth_lead','synth_arp','synth_pulse'):
        out.add('SYNTH')
    if iid in ('noise_fx',): out.add('TEXTURE')
    if iid in ('choir',): out.add('VOICE')
    if 'lead' in role or 'melody' in role or 'counter' in role: out.add('ROLE_LEAD')
    if 'harmony' in role or 'chord' in role or 'comp' in role: out.add('ROLE_HARMONY')
    if 'bass' in role: out.add('ROLE_BASS')
    if not out.intersection({'PERCUSSION','TEXTURE'}): out.add('PITCHED')
    if out.intersection({'GUITAR','BASS','KEYS','WIND_BRASS','STRINGS','SYNTH','PLUCKED','VOICE'}): out.add('MELODIC')
    return out


def _target_groups(fragment):
    t=(fragment or '').lower(); groups=set()
    if re.search(r'\bguitars?\b|\bstrum|\bpick(?:ing)?\b|\bsteel\b',t): groups.add('GUITAR')
    if re.search(r'\bbanjo\b|\bmandolin\b',t): groups.add('PLUCKED')
    if re.search(r'\bbass\b',t): groups.add('BASS')
    if re.search(r'\bpiano\b|\bkeys?\b|\bkeyboard\b|\bclav\b|\bcomping\b',t): groups.add('KEYS')
    if re.search(r'\bhorns?\b|\bbrass\b|\btrumpet\b|\btrombone\b|\bsax|\bclarinet\b|\bflute\b|\bwoodwind\b|\btongu',t): groups.add('WIND_BRASS')
    if re.search(r'\bstrings?\b|\bfiddle\b|\bviolin\b|\bviola\b|\bcello\b|\bbow',t): groups.add('STRINGS')
    if re.search(r'\bdrums?\b|\bpercussion\b|\bbrush|\bstick\b|\bbackbeat\b|\bhi-?hat\b|\bcymbal\b',t): groups.add('PERCUSSION')
    if re.search(r'\bsynth|\bpad\b|\barpeggiat|\bgated\b',t): groups.add('SYNTH')
    if re.search(r'\btexture|\bgranular\b|\bnoise\b',t): groups.add('TEXTURE')
    if re.search(r'\bleads?\b|\bmelody\b|\bvocal-like\b',t): groups.add('ROLE_LEAD')
    if re.search(r'\bharmony\b|\bchords?\b',t): groups.add('ROLE_HARMONY')
    return groups


def _cap_compatible(cap, families):
    if cap in ('LEGATO_TRANSITIONS','SHORT_STACCATO','SUSTAIN'):
        return 'PITCHED' in families
    if cap=='ACCENT_VARIATION': return True
    if cap=='GLISSANDO_SLIDE': return 'PITCHED' in families and bool(families.intersection({'GUITAR','WIND_BRASS','STRINGS','SYNTH'}))
    if cap=='MUTED_ARTICULATION': return 'PITCHED' in families and bool(families.intersection({'GUITAR','WIND_BRASS','STRINGS','KEYS'}))
    if cap=='PITCH_BEND_OR_SCOOP': return 'PITCHED' in families and bool(families.intersection({'GUITAR','WIND_BRASS','STRINGS','SYNTH','VOICE'}))
    if cap in ('TREMOLO','PIZZICATO','SHORT_CHOP'):
        return bool(families.intersection({'STRINGS','GUITAR','PLUCKED','KEYS'}))
    if cap=='VIBRATO_CONTROL': return bool(families.intersection({'WIND_BRASS','STRINGS','GUITAR','SYNTH','VOICE'}))
    if cap=='BRUSH_ARTICULATION': return 'PERCUSSION' in families
    if cap=='ATTACK_VARIATION': return True
    return True


def _profile_caps(text, instrument_id, role, source_genre=None):
    families=_families(instrument_id,role); caps=set(); inherited_targets=set(); iid=str(instrument_id or '').lower()
    # Semicolon resets target scope; comma continues it unless a new target appears.
    tokens=re.split(r'([;,])',str(text or ''))
    reset=True
    for token in tokens:
        if token==';': inherited_targets=set(); reset=True; continue
        if token==',': reset=False; continue
        frag=token.strip()
        if not frag: continue
        explicit=_target_groups(frag)
        if explicit: inherited_targets=explicit
        targets=explicit or inherited_targets
        # Known profile sentences whose unqualified 'section' language belongs to a
        # specific ensemble family, not to every pitched instrument in the genre.
        if not targets and source_genre=='Big Band': targets={'WIND_BRASS'}
        applies=(not targets) or bool(families.intersection(targets))
        if not applies: continue
        low=frag.lower()
        for pat,cap in PROFILE_CAP_PATTERNS:
            if not re.search(pat,low) or not _cap_compatible(cap,families): continue
            # Bluegrass profile prose lists picking/bowing/chop together; the
            # executable mandolin-chop event is the authoritative chop requirement.
            if source_genre=='Bluegrass-related' and cap=='SHORT_CHOP' and iid!='mandolin': continue
            caps.add(cap)
    return caps


def _control_compatible(cap, families):
    if cap=='VELOCITY_RESPONSE': return True
    if cap=='SUSTAIN_PEDAL_CONTROL': return 'KEYS' in families
    if cap=='FILTER_AUTOMATION': return bool(families.intersection({'SYNTH','TEXTURE'}))
    if cap=='PARAMETER_AUTOMATION': return bool(families.intersection({'SYNTH','TEXTURE','PERCUSSION'}))
    if cap=='VIBRATO_CONTROL': return bool(families.intersection({'WIND_BRASS','STRINGS','GUITAR','SYNTH','VOICE'}))
    if cap=='PITCH_BEND_OR_ARTICULATION_TRANSITION': return bool(families.intersection({'GUITAR','WIND_BRASS','STRINGS','SYNTH','VOICE'}))
    if cap in ('EXPRESSION_CC_OR_EQUIVALENT','NOTE_LENGTH_RESPONSE'):
        return 'PITCHED' in families or bool(families.intersection({'SYNTH','TEXTURE'}))
    return True


def _timing_class(text):
    t=(text or '').lower(); out=[]
    if re.search(r'rubato|tempo breathing|elastic',t): out.append('SHARED_RUBATO_OR_TEMPO_BREATHING')
    if re.search(r'swing|triplet feel',t): out.append('SHARED_SWING_FEEL')
    if re.search(r'laid[- ]back|behind the beat',t): out.append('SHARED_LAID_BACK_FEEL')
    if re.search(r'steady|stable|strict|grid|dance pulse',t): out.append('STABLE_SHARED_PULSE')
    if re.search(r'interlock|shared groove|ensemble|humanized',t): out.append('ENSEMBLE_SHARED_GROOVE')
    if re.search(r'no independent random|not random|coherent',t): out.append('NO_INDEPENDENT_RANDOM_JITTER')
    return out or ['PROFILE_TIMING_TEXT_REQUIRES_INTERPRETATION']


def build(genre, profile, registrations, events, profile_registry=None):
    profile_registry=profile_registry or {genre:profile}; entries=[]
    for reg in registrations:
        track=reg.get('track_id'); iid=reg.get('instrument_id'); role=reg.get('role')
        source_genre=_source_genre(track,events,genre); sp=profile_registry.get(source_genre,profile)
        te=[e for e in events if str(e.get('track_id'))==str(track)]
        labels=sorted({str(e.get('articulation')) for e in te if e.get('articulation')})
        caps=set()
        for lab in labels:
            caps.update(ARTICULATION_MAP.get(lab,('EVENT_ARTICULATION_'+re.sub(r'[^A-Z0-9]+','_',lab.upper()).strip('_'),)))
        caps.update(_profile_caps(sp.get('articulation_behavior'),iid,role,source_genre))
        cc_text=str(sp.get('continuous_performance_control') or '')
        families=_families(iid,role)
        controls={cap for pat,cap in CONTROL_PATTERNS if re.search(pat,cc_text.lower()) and _control_compatible(cap,families)}
        if 'PEDAL_STEEL_GLIDE_OR_BEND' in caps: controls.add('PITCH_BEND_OR_ARTICULATION_TRANSITION')
        critical=sorted(c for c in caps if c in CRITICAL_BY_CAP)
        entries.append({
          'registration_id':reg.get('registration_id'),'track_id':track,'instrument_id':iid,'role':role,
          'source_genre':source_genre,'source_profile_id':sp.get('profile_id'),
          'event_articulation_labels':labels,'required_articulation_capabilities':sorted(caps),
          'critical_articulation_capabilities':critical,
          'timing_intent_text':sp.get('timing_humanization_behavior'),'timing_behavior_classes':_timing_class(sp.get('timing_humanization_behavior')),
          'continuous_control_intent_text':sp.get('continuous_performance_control'),'required_continuous_controls':sorted(controls),
          'profile_articulation_intent_text':sp.get('articulation_behavior'),
          'profile_capability_scope':'INSTRUMENT_ROLE_SCOPED_PLUS_EVENT_AUTHORITATIVE',
          'target_capability_status':'REQUIRES_TARGET_CAPABILITY_VERIFICATION',
        })
    plan={'status':'PASS','plan_id':PLAN_ID,'genre':genre,'profile_id':profile.get('profile_id'),
          'registration_count':len(entries),'entries':entries,
          'policy':'PATCH_NAME_IS_INSUFFICIENT_TARGET_MUST_VERIFY_REQUIRED_PERFORMANCE_CAPABILITIES'}
    plan['plan_sha256']=_sha({k:v for k,v in plan.items() if k!='plan_sha256'})
    return plan


def validate(plan, registrations):
    if not isinstance(plan,dict) or plan.get('status')!='PASS' or plan.get('plan_id')!=PLAN_ID: raise ValueError('PERFORMANCE_CAPABILITY_PLAN_INVALID')
    a={(x.get('registration_id'),str(x.get('track_id'))) for x in plan.get('entries',[])}
    b={(x.get('registration_id'),str(x.get('track_id'))) for x in registrations}
    if a!=b: raise ValueError('PERFORMANCE_CAPABILITY_REGISTRATION_MISMATCH')
    if _sha({k:v for k,v in plan.items() if k!='plan_sha256'})!=plan.get('plan_sha256'): raise ValueError('PERFORMANCE_CAPABILITY_HASH_MISMATCH')
    return plan