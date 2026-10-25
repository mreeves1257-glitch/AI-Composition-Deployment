"""Compile genre mix-prominence intent into per-registration hierarchy/depth roles.

V1 is intentionally categorical. It does not invent manufacturer fader values.
It tells later target/render stages which separated registrations are foreground,
foundation, present, support, background, texture, or preserved. Numeric gain/pan/
reverb calibration remains a listening/target-resource step.
"""
from __future__ import annotations
import hashlib, json, re

PLAN_ID='GENRE_MIX_PROMINENCE_PLAN_V1'
CATEGORIES={
    'FOREGROUND': {'depth_zone':'FRONT','relative_level_intent':'HIGHEST_MUSICAL_PRIORITY'},
    'FOUNDATION': {'depth_zone':'FRONT_MID','relative_level_intent':'STRUCTURAL_PRIORITY'},
    'PRESENT': {'depth_zone':'MID','relative_level_intent':'CLEAR_AND_DISTINCT'},
    'SUPPORT': {'depth_zone':'MID_BACK','relative_level_intent':'AUDIBLE_NOT_DOMINANT'},
    'BACKGROUND': {'depth_zone':'BACK','relative_level_intent':'SPATIAL_SUPPORT'},
    'TEXTURE': {'depth_zone':'BACK','relative_level_intent':'LOW_PRIORITY_COLOR'},
    'PRESERVE_EXISTING': {'depth_zone':'PRESERVE','relative_level_intent':'DO_NOT_CHANGE_APPROVED_PATH'},
}

DANCE_LOW_END={
 'ROCK','Jazz Fusion','Funk','Contemporary R&B','House','Techno','Trance',
 'Breakbeat-related','Garage-related','Mexican Reggaeton','Chugg / #chugg',
 'Afro House','Trip-Hop','Contemporary Trip-Hop / Trip-Hop Revival','DISCO'
}
JAZZ={'Swing','Jazz Ballad','Big Band','Jazz Waltz','Bebop','Cool Jazz','Dixieland','Jazz Fusion'}
COUNTRY={'Traditional Country','Country Rock','Country Ballad','Country Shuffle','Two-Step','Country Waltz','Bluegrass-related'}
LATIN={'Bossa Nova','Samba','Salsa','Mambo','Rumba','Cha-Cha','Bolero'}
ATMOSPHERIC={'New Age','Ambient Electronic','Downtempo','Spiritual'}
RNB_SOUL={'Rhythm and Blues','Soul','Contemporary R&B','Neo-Soul-related','Funk'}

PERC_ROLES={'KICK','SNARE','HAT','RIDE','TOMS','CRASH','PERC','BONGOS','CLAVES','COWBELL','TIMBALES','SHAKER','SURDO','CAIXA','REPINIQUE','TAMBORIM','AGOGO'}
BACKGROUND_IDS={'synth_pad','strings','choir','noise_fx'}


def _sha(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def _base_role(role):
    role=re.sub(r'^S\d+_','',str(role or ''))
    return role

def _source_genre_for_track(track, events, fallback):
    gs={e.get('component_genre') for e in events if str(e.get('track_id'))==str(track) and e.get('component_genre')}
    return next(iter(gs)) if len(gs)==1 else fallback

def _classify(genre, role, iid, drum_member=None):
    r=_base_role(role).upper(); iid=str(iid)
    # User-approved Classical routing must not be rebalanced by this new generic stage.
    if genre=='Classical': return 'PRESERVE_EXISTING'
    if genre=='PIANIST': return 'FOREGROUND'

    # Foreground melodic identity.
    if r=='LEAD':
        return 'PRESENT' if genre=='Ambient Electronic' else 'FOREGROUND'

    # Low-end foundation.
    if r=='BASS' or 'BASS'==iid.upper() or iid in ('electric_bass','electric_bass_guitar','double_bass','synth_bass'):
        return 'FOUNDATION'

    # Core drum hierarchy depends on genre family.
    dm=(drum_member or '').lower()
    if r=='KICK' or dm=='kick':
        if genre in DANCE_LOW_END or genre in {'Afrobeats','Rhythm and Blues','Soul'}: return 'FOUNDATION'
        if genre in JAZZ or genre in COUNTRY or genre in {'Bossa Nova','Bolero'}: return 'SUPPORT'
        return 'PRESENT'
    if r=='RIDE' or dm=='ride':
        return 'FOUNDATION' if genre in {'Swing','Big Band','Bebop','Jazz Waltz','Cool Jazz','Dixieland'} else 'SUPPORT'
    if r=='SNARE' or dm=='snare':
        return 'PRESENT' if genre in {'ROCK','Funk','Rhythm and Blues','Soul','Jazz Fusion','Garage-related','Breakbeat-related'} else 'SUPPORT'
    if r in {'HAT','TOMS','CRASH'} or dm in {'hat','tom','crash'}:
        return 'SUPPORT'

    # Latin/Samba percussion is structural rather than generic background decoration.
    if r in {'SURDO'}: return 'FOUNDATION'
    if r in {'CAIXA','REPINIQUE','TAMBORIM','AGOGO'}:
        return 'PRESENT' if genre=='Samba' else 'SUPPORT'
    if r in {'PERC','BONGOS','CLAVES','COWBELL','TIMBALES'}:
        if genre=='Rumba': return 'FOREGROUND'
        if genre in {'Salsa','Mambo','Cha-Cha'}: return 'PRESENT'
        if genre in {'Bossa Nova','Bolero'}: return 'BACKGROUND'
        if genre in {'Afrobeats','Afro House'}: return 'PRESENT'
        return 'SUPPORT'
    if r=='SHAKER':
        return 'PRESENT' if genre in {'Samba','Afrobeats','Afro House'} else 'SUPPORT'

    # Harmony / accompaniment.
    if r=='HARMONY':
        if genre in {'PIANIST'}: return 'FOREGROUND'
        if genre in {'Bossa Nova'}: return 'PRESENT'
        if genre in {'Salsa','Mambo','Cha-Cha','Funk','Neo-Soul-related','Rhythm and Blues','Soul'}: return 'PRESENT'
        if genre in ATMOSPHERIC: return 'SUPPORT'
        return 'SUPPORT'

    # Explicit supporting sections / counterlines.
    if r.startswith('SUPPORT_'):
        if genre=='Big Band' and any(x in r for x in ('SAX','TRUMPET','TROMBONE')): return 'PRESENT'
        if genre in {'Salsa','Mambo','Cha-Cha'} and any(x in r for x in ('TRUMPET','TROMBONE','SAX')): return 'PRESENT'
        return 'SUPPORT'

    # Instrument-family color rules.
    if iid in BACKGROUND_IDS:
        if iid=='noise_fx': return 'TEXTURE'
        return 'BACKGROUND'
    if iid in {'pedal_steel_guitar'}:
        return 'PRESENT' if genre in {'Traditional Country','Country Ballad','Country Waltz'} else 'SUPPORT'
    if iid in {'banjo','mandolin','acoustic_guitar','electric_guitar','clav','electric_piano','piano'}:
        if genre=='Bluegrass-related': return 'PRESENT'
        return 'SUPPORT'
    if iid in {'alto_sax','tenor_sax','baritone_sax','trumpet','trumpet_c','trombone','tenor_trombone','clarinet','clarinet_bb','flute','concert_flute','violin'}:
        return 'PRESENT'
    if r in PERC_ROLES: return 'SUPPORT'
    return 'SUPPORT'


def build(genre, profile, registrations, events, profile_registry=None):
    if not registrations: raise ValueError('MIX_PROMINENCE_NO_REGISTRATIONS')
    profile_registry=profile_registry or {genre:profile}
    entries=[]
    for reg in registrations:
        source_genre=_source_genre_for_track(reg.get('track_id'),events,genre)
        source_profile=profile_registry.get(source_genre,profile)
        category=_classify(source_genre,reg.get('role'),reg.get('instrument_id'),reg.get('drum_member'))
        meta=CATEGORIES[category]
        entries.append({
            'registration_id':reg.get('registration_id'),'track_id':reg.get('track_id'),
            'instrument_id':reg.get('instrument_id'),'role':reg.get('role'),
            'source_genre':source_genre,'source_profile_id':source_profile.get('profile_id'),
            'prominence_class':category,'depth_zone':meta['depth_zone'],
            'relative_level_intent':meta['relative_level_intent'],
            'profile_mix_prominence_intent':source_profile.get('mix_prominence_intent'),
            'numeric_gain_status':'LISTENING_CALIBRATION_REQUIRED',
            'pan_status':'TARGET_OR_GENRE_MAP_REQUIRED',
            'reverb_depth_status':'TARGET_OR_GENRE_MAP_REQUIRED',
        })
    packet={
      'status':'PASS','plan_id':PLAN_ID,'genre':genre,'profile_id':profile.get('profile_id'),
      'policy':'PROFILE_AUTHORITATIVE_CATEGORICAL_HIERARCHY_NO_UNVERIFIED_FACTORY_NUMBERS',
      'registration_count':len(entries),'entries':entries,
      'class_counts':{k:sum(e['prominence_class']==k for e in entries) for k in CATEGORIES},
      'numeric_gain_status':'NOT_APPLIED_PENDING_LISTENING_CALIBRATION',
      'class_definition':CATEGORIES,
    }
    packet['plan_sha256']=_sha({k:v for k,v in packet.items() if k!='plan_sha256'})
    return packet

def validate(plan, registrations):
    if not isinstance(plan,dict) or plan.get('plan_id')!=PLAN_ID or plan.get('status')!='PASS':
        raise ValueError('MIX_PROMINENCE_PLAN_INVALID')
    expected={(r.get('registration_id'),r.get('track_id')) for r in registrations}
    actual={(e.get('registration_id'),e.get('track_id')) for e in plan.get('entries',[])}
    if expected!=actual: raise ValueError('MIX_PROMINENCE_REGISTRATION_MISMATCH')
    if any(e.get('prominence_class') not in CATEGORIES for e in plan.get('entries',[])):
        raise ValueError('MIX_PROMINENCE_CLASS_INVALID')
    check={k:v for k,v in plan.items() if k!='plan_sha256'}
    if _sha(check)!=plan.get('plan_sha256'): raise ValueError('MIX_PROMINENCE_HASH_MISMATCH')
    return plan