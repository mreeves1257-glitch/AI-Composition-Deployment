"""Evidence-backed large-ensemble population and chair expansion.

This layer is intentionally narrow: only genres with sufficiently documented
large formations are expanded. Small/flexible genres remain untouched.

Physical population is not treated as linear gain. For massed sections (notably
orchestral strings), population is metadata for later ensemble rendering and
balance; it does not clone identical notes into a louder stack.
"""
from __future__ import annotations

import copy
from collections import defaultdict

NOTE_PC={'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}

ARCHITECTURES = {
    'Classical': {
        'formation_id':'CLASSICAL_FULL_ORCHESTRA_LPO_BEETHOVEN9_2026_REFERENCE',
        'mode':'POPULATION_REFERENCE_ONLY',
        'source_note':'London Philharmonic Orchestra, Beethoven Ninth, 28 Mar 2026 personnel roster; used as a full-orchestra population reference, not a universal Classical headcount.',
        'physical_population_reference': {
            'VIOLIN_I':16,'VIOLIN_II':14,'VIOLA':12,'CELLO':10,'DOUBLE_BASS':8,
            'FLUTE_SECTION':4,'OBOE_SECTION':4,'CLARINET_SECTION':4,'BASSOON_SECTION':4,
            'FRENCH_HORN':5,'TRUMPET':3,'TROMBONE_FAMILY':3,'TIMPANI':1,'PERCUSSION':4,
        },
        'string_ratio':'16:14:12:10:8',
        'render_policy':'SECTION_POPULATION_METADATA_DO_NOT_CLONE_IDENTICAL_STRING_NOTES',
        'current_composer_section_mapping': {
            'VIOLIN_I':16,'VIOLIN_II':14,'VIOLA':12,'CELLO':10,'DOUBLE_BASS':8,
            'FLUTE':4,'OBOE':4,'CLARINET':4,'BASSOON':4,'FRENCH_HORN':5,
            'TRUMPET':3,'TROMBONE':3,'TIMPANI':1,
            # Current generic Classical path retains its TUBA section; this LPO
            # reference performance did not include tuba, so no fake population
            # number is assigned here.
        },
    },
    'Big Band': {
        'formation_id':'BIG_BAND_STANDARD_17_BERKLEE',
        'mode':'ACTIVE_CHAIR_EXPANSION',
        'source_note':'Berklee Jazz Arranging: five saxophones, four trumpets, four trombones, full rhythm section.',
        'physical_player_count':17,
        'sections': {
            'SAXES':[
                ('ALTO_SAX_1','alto_sax'),('ALTO_SAX_2','alto_sax'),
                ('TENOR_SAX_1','tenor_sax'),('TENOR_SAX_2','tenor_sax'),
                ('BARITONE_SAX','baritone_sax')],
            'TRUMPETS':[(f'TRUMPET_{i}','trumpet') for i in range(1,5)],
            'TROMBONES':[(f'TROMBONE_{i}','trombone') for i in range(1,5)],
            'RHYTHM':[('PIANO','piano'),('GUITAR','electric_guitar'),('BASS','double_bass'),('DRUMS','drums_ride')],
        },
        'section_buses':['SAXES','TRUMPETS','TROMBONES','RHYTHM'],
    },
    'Salsa': {
        'formation_id':'SALSA_BERKLEE_EGUIE_CASTRILLO_10_INSTRUMENTAL',
        'mode':'ACTIVE_CHAIR_EXPANSION',
        'source_note':'Berklee Eguie Castrillo Salsa Orchestra roster: flute, two trumpets, tenor sax, trombone, piano, electric bass, congas, bongo/percussion, timbales.',
        'physical_player_count':10,
        'sections': {
            'HORNS':[('FLUTE_1','flute'),('TRUMPET_1','trumpet'),('TRUMPET_2','trumpet'),('TENOR_SAX_1','tenor_sax'),('TROMBONE_1','trombone')],
            'RHYTHM':[('PIANO','piano'),('BASS','electric_bass')],
            'PERCUSSION':[('CONGA_1','conga'),('BONGO_1','bongo_family'),('TIMBALES_1','timbales')],
        },
        'shared_auxiliary_roles':{'claves':'PERCUSSION_SHARED','cowbell':'PERCUSSION_SHARED'},
        'section_buses':['HORNS','RHYTHM','PERCUSSION'],
    },
    'Mambo': {
        'formation_id':'MAMBO_MACHITO_AFRO_CUBAN_ORCHESTRA_SMITHSONIAN_REFERENCE_20',
        'mode':'ACTIVE_CHAIR_EXPANSION',
        'source_note':'Smithsonian Folkways Mambo personnel: five trumpets; three alto, three tenor, one baritone sax; piano, upright bass, maracas, bongos, two congas, timbales, drums.',
        'physical_player_count':20,
        'sections': {
            'SAXES':[(f'ALTO_SAX_{i}','alto_sax') for i in range(1,4)] + [(f'TENOR_SAX_{i}','tenor_sax') for i in range(1,4)] + [('BARITONE_SAX_1','baritone_sax')],
            'TRUMPETS':[(f'TRUMPET_{i}','trumpet') for i in range(1,6)],
            'RHYTHM':[('PIANO','piano'),('BASS','double_bass'),('DRUMS','drums')],
            'PERCUSSION':[('MARACAS_1','shaker'),('BONGO_1','bongo_family'),('CONGA_1','conga'),('CONGA_2','conga'),('TIMBALES_1','timbales')],
        },
        'resource_proxy_note':'MARACAS_1 currently uses the existing shaker identity as an explicit family proxy; no maracas-specific resource is claimed.',
        'section_buses':['SAXES','TRUMPETS','RHYTHM','PERCUSSION'],
    },

    'Samba': {
        'formation_id':'SAMBA_BATERIA_10_PLAYER_COMPOSER_REFERENCE',
        'mode':'ACTIVE_CHAIR_EXPANSION',
        'source_note':'Current Composer Samba formation built from the researched bateria roles already in the genre profile: three distinct surdo functions plus caixa, repinique, tamborim, agogo and ganza/shaker, with bass and electric piano retained as the harmonic/rhythm core.',
        'physical_player_count':10,
        'sections': {
            'RHYTHM':[('PIANO','electric_piano'),('BASS','electric_bass')],
            'BATERIA':[('SURDO_1','surdo'),('SURDO_2','surdo'),('SURDO_3','surdo'),
                       ('CAIXA_1','caixa'),('REPINIQUE_1','repinique'),('TAMBORIM_1','tamborim'),
                       ('AGOGO_1','agogo_bells'),('GANZA_1','shaker')],
        },
        'resource_proxy_note':'GANZA_1 uses the existing shaker identity as the current resource family proxy.',
        'section_buses':['RHYTHM','BATERIA'],
    },
    'Spiritual': {
        'formation_id':'SPIRITUAL_CHOIR_AND_STRING_SECTIONS_V1',
        'mode':'ACTIVE_CHAIR_EXPANSION',
        'source_note':'Section assignment for the current Composer Spiritual palette. Choir and strings are expanded as musical sections, not as invented fixed headcounts; piano and flute remain individual players.',
        'physical_player_count':'SCALABLE_SECTIONAL_FORMATION',
        'sections': {
            'CHOIR':[('SOPRANO_SECTION','choir'),('ALTO_SECTION','choir'),('TENOR_SECTION','choir'),('BASS_VOICE_SECTION','choir')],
            'STRINGS':[('VIOLIN_I_SECTION','strings'),('VIOLIN_II_SECTION','strings'),('VIOLA_SECTION','strings'),('CELLO_SECTION','strings')],
            'RHYTHM':[('PIANO','piano')],
            'COLOR':[('FLUTE_1','flute')],
        },
        'population_policy':'NO_FAKE_HEADCOUNT; choir/string section sizes remain scalable until a documented formation is selected.',
        'section_buses':['CHOIR','STRINGS','RHYTHM','COLOR'],
    },
}

# Conservative practical ranges used only to keep generated section voicings in
# believable registers during this first chair-expansion pilot.
RANGES={
    'alto_sax':(49,81),'tenor_sax':(44,76),'baritone_sax':(36,69),
    'trumpet':(55,82),'trombone':(40,72),'flute':(60,96),
}


def get_spec(genre):
    spec=ARCHITECTURES.get(genre)
    return copy.deepcopy(spec) if spec else None


def _pcs(chord):
    return {NOTE_PC[n] for n in chord.get('notes',[]) if n in NOTE_PC}


def _nearest_chord_tone(target, pcs, bounds):
    lo,hi=bounds
    choices=[n for n in range(lo,hi+1) if n%12 in pcs]
    if not choices:
        return max(lo,min(hi,int(target)))
    return min(choices,key=lambda n:(abs(n-target),n))


def _voice_event(source, player_id, instrument_id, target, pcs, section, population=1, source_rule='ensemble_chair_expansion'):
    e=copy.deepcopy(source)
    e['track_id']=player_id
    e['player_id']=player_id
    e['instrument_id']=instrument_id
    e['ensemble_section']=section
    e['physical_player_population']=population
    e['ensemble_expansion_rule']=source_rule
    e['midi']=_nearest_chord_tone(target,pcs,RANGES.get(instrument_id,(24,108)))
    return e


def _bar_pcs(ctx, event):
    meter=int(ctx['meter']['numerator'])
    beat=float(event.get('start_beat',0))
    bar=max(0,min(len(ctx['harmony']['chords'])-1,int(beat//meter)))
    return _pcs(ctx['harmony']['chords'][bar])


def _big_band_pcs(ctx,event):
    meter=int(ctx['meter']['numerator'])
    beat=float(event.get('start_beat',0))
    bar=max(0,min(len(ctx['harmony']['chords'])-1,int(beat//meter)))
    chord=ctx['harmony']['chords'][bar]
    root=NOTE_PC[chord['root']]
    quality=str(chord.get('quality','major')).lower()
    roman=str(chord.get('roman',''))
    if 'minor' in quality or quality.startswith('m'):
        intervals=(0,3,7,10,2)
    elif roman.startswith('V'):
        intervals=(0,4,7,10,2)
    else:
        intervals=(0,4,7,9,2)
    return {(root+i)%12 for i in intervals}


def _expand_big_band(events, ctx):
    """Expand arranger functions into chairs while preserving one foreground owner.

    Unlike V2, section expansion does not promote every chair to equal musical
    status.  Lead chairs carry the top line; harmonizers and background chairs are
    explicitly subordinate.  Single-chair solo features remain single-chair.
    """
    out=[]

    def emit_chair(source,pid,inst,target,pcs,section,role,velocity_delta=0):
        x=_voice_event(source,pid,inst,target,pcs,section)
        x['musical_role']=role
        x['chair_function']=role
        x['velocity']=max(1,min(127,int(source.get('velocity',64))+velocity_delta))
        x['foreground_owner']=source.get('foreground_owner')
        x['arrangement_role']=source.get('arrangement_role')
        x['assignment_epoch']=source.get('assignment_epoch')
        return x

    for e in events:
        iid=e.get('instrument_id')
        pcs=_big_band_pcs(ctx,e)
        # True solo chair: do not inflate a soloist into an entire section.
        if e.get('single_chair'):
            pid=e.get('lead_chair')
            if not pid:
                raise ValueError('BIG_BAND_SINGLE_CHAIR_REQUIRES_LEAD_CHAIR')
            section='SAXES' if 'SAX' in pid else ('TRUMPETS' if 'TRUMPET' in pid else 'TROMBONES')
            inst=iid
            x=copy.deepcopy(e)
            x.update(track_id=pid,player_id=pid,ensemble_section=section,physical_player_population=1,
                     musical_role='FOREGROUND_LEAD',chair_function='SOLO_CHAIR')
            out.append(x)
            continue

        if iid=='alto_sax':
            anchor=int(e['midi'])
            chairs=[('ALTO_SAX_1','alto_sax',0),('ALTO_SAX_2','alto_sax',-4),
                    ('TENOR_SAX_1','tenor_sax',-7),('TENOR_SAX_2','tenor_sax',-10),
                    ('BARITONE_SAX','baritone_sax',-16)]
            fg=e.get('arrangement_role')=='FOREGROUND_LEAD'
            for idx,(pid,inst,off) in enumerate(chairs):
                if fg and idx==0:
                    role='FOREGROUND_LEAD'; dv=0
                elif e.get('arrangement_role') in ('BACKGROUND','SECONDARY_RESPONSE'):
                    role='SECTION_LEADER_BACKGROUND' if idx==0 else 'BACKGROUND_HARMONIZER'; dv=(-2 if idx==0 else -7-idx)
                elif e.get('arrangement_role')=='SUPPORTING_SECTION':
                    role='COUPLED_SECTION_LEADER' if idx==0 else 'COUPLED_HARMONIZER'; dv=(-4 if idx==0 else -8-idx)
                else:
                    role='SECTION_HARMONIZER'; dv=(-4 if idx else 0)
                out.append(emit_chair(e,pid,inst,anchor+off,pcs,'SAXES',role,dv))
        elif iid in ('tenor_sax','baritone_sax'):
            # Generic section identities are absorbed by explicit sax expansion;
            # true solo-chair events were handled above.
            continue
        elif iid=='trumpet':
            anchor=int(e['midi'])
            fg=e.get('arrangement_role')=='FOREGROUND_LEAD'
            for i,off in enumerate((0,-3,-7,-10),1):
                if fg and i==1:
                    role='FOREGROUND_LEAD'; dv=0
                elif e.get('arrangement_role')=='BACKGROUND':
                    role='SECTION_LEADER_BACKGROUND' if i==1 else 'BACKGROUND_HARMONIZER'; dv=(-3 if i==1 else -8-i)
                else:
                    role='SECTION_HARMONIZER'; dv=(-4 if i==1 else -7-i)
                out.append(emit_chair(e,f'TRUMPET_{i}','trumpet',anchor+off,pcs,'TRUMPETS',role,dv))
        elif iid=='trombone':
            anchor=int(e['midi'])
            fg=e.get('arrangement_role')=='FOREGROUND_LEAD'
            for i,off in enumerate((0,-4,-7,-12),1):
                if fg and i==1:
                    role='FOREGROUND_LEAD'; dv=0
                elif e.get('arrangement_role') in ('BACKGROUND','SUPPORTING_SECTION'):
                    role='SECTION_LEADER_BACKGROUND' if i==1 else 'BACKGROUND_HARMONIZER'; dv=(-3 if i==1 else -8-i)
                else:
                    role='SECTION_HARMONIZER'; dv=(-4 if i==1 else -7-i)
                x=emit_chair(e,f'TROMBONE_{i}','trombone',anchor+off,pcs,'TROMBONES',role,dv)
                if i==4: x['chair_function_detail']='BASS_TROMBONE_ROLE_USING_CURRENT_TROMBONE_RESOURCE'
                out.append(x)
        else:
            x=copy.deepcopy(e)
            if iid=='piano': x.update(player_id='PIANO',ensemble_section='RHYTHM',physical_player_population=1,musical_role='FOUNDATION')
            elif iid=='electric_guitar': x.update(player_id='GUITAR',ensemble_section='RHYTHM',physical_player_population=1,musical_role='FOUNDATION')
            elif iid=='double_bass': x.update(player_id='BASS',ensemble_section='RHYTHM',physical_player_population=1,musical_role='FOUNDATION')
            elif 'drums' in str(iid): x.update(player_id='DRUMS',ensemble_section='RHYTHM',physical_player_population=1,musical_role='FOUNDATION')
            out.append(x)
    return out


def validate_big_band_hierarchy(events):
    horn=[e for e in events if e.get('ensemble_section') in ('SAXES','TRUMPETS','TROMBONES')]
    missing=[e for e in horn if not e.get('foreground_owner')]
    owners_by_onset={}
    leads_by_onset={}
    for e in horn:
        k=round(float(e.get('start_beat',0)),3)
        owners_by_onset.setdefault(k,set()).add(e.get('foreground_owner'))
        if e.get('musical_role')=='FOREGROUND_LEAD':
            leads_by_onset.setdefault(k,[]).append(e.get('player_id'))
    conflicting={str(k):sorted(o for o in v if o) for k,v in owners_by_onset.items() if len({o for o in v if o})>1}
    multiple_leads={str(k):v for k,v in leads_by_onset.items() if len(set(v))>1}
    epochs=sorted({str(e.get('assignment_epoch')) for e in horn if e.get('assignment_epoch')})
    result={'status':'PASS' if not missing and not conflicting and not multiple_leads else 'FAIL',
            'horn_event_count':len(horn),'missing_owner_count':len(missing),
            'conflicting_owner_onsets':conflicting,'multiple_foreground_lead_onsets':multiple_leads,
            'assignment_epochs':epochs,
            'foreground_lead_players':sorted({e.get('player_id') for e in horn if e.get('musical_role')=='FOREGROUND_LEAD'})}
    if result['status']!='PASS':
        raise ValueError('BIG_BAND_HIERARCHY_VALIDATION_FAILED::'+repr(result))
    return result

def _expand_salsa(events, ctx):
    out=[]
    for e in events:
        iid=e.get('instrument_id'); pcs=_bar_pcs(ctx,e)
        if iid=='trumpet':
            anchor=int(e['midi'])
            out.append(_voice_event(e,'TRUMPET_1','trumpet',anchor,pcs,'HORNS'))
            out.append(_voice_event(e,'TRUMPET_2','trumpet',anchor-5,pcs,'HORNS'))
        else:
            x=copy.deepcopy(e)
            mapping={'flute':('FLUTE_1','HORNS'),'tenor_sax':('TENOR_SAX_1','HORNS'),'trombone':('TROMBONE_1','HORNS'),
                     'piano':('PIANO','RHYTHM'),'electric_bass':('BASS','RHYTHM'),'conga':('CONGA_1','PERCUSSION'),
                     'bongo_family':('BONGO_1','PERCUSSION'),'timbales':('TIMBALES_1','PERCUSSION')}
            if iid in mapping:
                pid,section=mapping[iid]; x.update(player_id=pid,ensemble_section=section,physical_player_population=1)
            elif iid in ('claves','cowbell'):
                x.update(player_id='PERCUSSION_SHARED',ensemble_section='PERCUSSION',physical_player_population=0,shared_player_role=True)
            out.append(x)
    return out


def _expand_mambo(events, ctx):
    out=[]
    for e in events:
        iid=e.get('instrument_id'); pcs=_bar_pcs(ctx,e)
        if iid=='alto_sax':
            anchor=int(e['midi'])
            chairs=[('ALTO_SAX_1','alto_sax',0),('ALTO_SAX_2','alto_sax',-3),('ALTO_SAX_3','alto_sax',-7),
                    ('TENOR_SAX_1','tenor_sax',-10),('TENOR_SAX_2','tenor_sax',-14),('TENOR_SAX_3','tenor_sax',-17),
                    ('BARITONE_SAX_1','baritone_sax',-24)]
            for pid,inst,off in chairs: out.append(_voice_event(e,pid,inst,anchor+off,pcs,'SAXES'))
        elif iid in ('tenor_sax','baritone_sax'):
            continue
        elif iid=='trumpet':
            anchor=int(e['midi'])
            for i,off in enumerate((0,-3,-7,-10,-12),1):
                out.append(_voice_event(e,f'TRUMPET_{i}','trumpet',anchor+off,pcs,'TRUMPETS'))
        elif iid=='conga':
            x1=copy.deepcopy(e); x1.update(track_id='CONGA_1',player_id='CONGA_1',ensemble_section='PERCUSSION',physical_player_population=1)
            x2=copy.deepcopy(e); x2.update(track_id='CONGA_2',player_id='CONGA_2',ensemble_section='PERCUSSION',physical_player_population=1,
                                         start_beat=float(e['start_beat'])+0.06,velocity=max(1,int(e.get('velocity',64))-5),midi=int(e.get('midi',62))+1)
            out.extend((x1,x2))
        else:
            x=copy.deepcopy(e)
            mapping={'piano':('PIANO','RHYTHM'),'double_bass':('BASS','RHYTHM'),'drums':('DRUMS','RHYTHM'),
                     'shaker':('MARACAS_1','PERCUSSION'),'bongo_family':('BONGO_1','PERCUSSION'),'timbales':('TIMBALES_1','PERCUSSION')}
            if iid in mapping:
                pid,section=mapping[iid]; x.update(player_id=pid,ensemble_section=section,physical_player_population=1)
                if iid=='shaker': x['source_instrument_role']='maracas'; x['resource_proxy']='shaker'
            out.append(x)
    return out



def _expand_samba(events, ctx):
    out=[]
    for e in events:
        iid=e.get('instrument_id')
        if iid=='surdo':
            base=int(e.get('midi',36))
            for pid,note,vel_delta,time_delta in (
                ('SURDO_1',base,0,0.0),
                ('SURDO_2',max(24,base-2),-4,0.02),
                ('SURDO_3',min(84,base+2),-7,0.04),
            ):
                x=copy.deepcopy(e)
                x.update(track_id=pid,player_id=pid,ensemble_section='BATERIA',
                         physical_player_population=1,ensemble_expansion_rule='samba_three_surdo_assignment',
                         midi=note,start_beat=float(e.get('start_beat',0))+time_delta,
                         velocity=max(1,min(127,int(e.get('velocity',64))+vel_delta)))
                out.append(x)
        else:
            x=copy.deepcopy(e)
            mapping={
                'electric_piano':('PIANO','RHYTHM'),
                'electric_bass':('BASS','RHYTHM'),
                'caixa':('CAIXA_1','BATERIA'),
                'repinique':('REPINIQUE_1','BATERIA'),
                'tamborim':('TAMBORIM_1','BATERIA'),
                'agogo_bells':('AGOGO_1','BATERIA'),
                'shaker':('GANZA_1','BATERIA'),
            }
            if iid in mapping:
                pid,section=mapping[iid]
                x.update(player_id=pid,
                         track_id=pid if iid not in ('electric_piano','electric_bass') else x.get('track_id',pid),
                         ensemble_section=section,physical_player_population=1)
                if iid=='shaker':
                    x['source_instrument_role']='ganza'
                    x['resource_proxy']='shaker'
            out.append(x)
    return out


def _expand_sectional_pad(events, ctx, instrument_id, section_name, voices):
    groups=defaultdict(list)
    passthrough=[]
    for e in events:
        if e.get('instrument_id')==instrument_id:
            groups[round(float(e.get('start_beat',0)),6)].append(e)
        else:
            passthrough.append(copy.deepcopy(e))
    out=passthrough
    for start,group in groups.items():
        group=sorted(group,key=lambda e:int(e.get('midi',60)))
        template=group[-1]
        pcs=_bar_pcs(ctx,template)
        anchor=max(int(e.get('midi',60)) for e in group)
        for player_id,offset in voices:
            x=_voice_event(template,player_id,instrument_id,anchor+offset,pcs,section_name,
                           population=1,source_rule='scalable_section_assignment')
            x['start_beat']=start
            x['physical_player_population_reference']='SCALABLE_SECTION_NOT_FIXED_HEADCOUNT'
            x['ensemble_section_proxy']=True
            out.append(x)
    return out


def _expand_spiritual(events, ctx):
    mapped=[]
    for e in events:
        x=copy.deepcopy(e)
        iid=x.get('instrument_id')
        if iid=='piano':
            x.update(player_id='PIANO',ensemble_section='RHYTHM',physical_player_population=1)
        elif iid=='flute':
            x.update(player_id='FLUTE_1',ensemble_section='COLOR',physical_player_population=1)
        mapped.append(x)

    mapped=_expand_sectional_pad(
        mapped,ctx,'strings','STRINGS',
        [('VIOLIN_I_SECTION',0),('VIOLIN_II_SECTION',-5),('VIOLA_SECTION',-12),('CELLO_SECTION',-19)]
    )
    mapped=_expand_sectional_pad(
        mapped,ctx,'choir','CHOIR',
        [('SOPRANO_SECTION',0),('ALTO_SECTION',-5),('TENOR_SECTION',-12),('BASS_VOICE_SECTION',-19)]
    )
    return mapped

def expand_events(genre, events, ctx=None):
    spec=get_spec(genre)
    source=copy.deepcopy(list(events))
    if not spec or spec.get('mode')!='ACTIVE_CHAIR_EXPANSION':
        return {'status':'PASS','genre':genre,'events':source,'spec':spec,
                'source_event_count':len(source),'expanded_event_count':len(source),'expansion_applied':False}
    if ctx is None:
        raise ValueError('ENSEMBLE_ARCHITECTURE_CONTEXT_REQUIRED')
    hierarchy_validation=None
    if genre=='Big Band':
        out=_expand_big_band(source,ctx)
        hierarchy_validation=validate_big_band_hierarchy(out)
    elif genre=='Salsa': out=_expand_salsa(source,ctx)
    elif genre=='Mambo': out=_expand_mambo(source,ctx)
    elif genre=='Samba': out=_expand_samba(source,ctx)
    elif genre=='Spiritual': out=_expand_spiritual(source,ctx)
    else: out=source
    out=[e for e in out if float(e.get('duration_beats',0))>0]
    out.sort(key=lambda e:(float(e.get('start_beat',0)),str(e.get('track_id')),int(e.get('midi',0))))
    players=sorted({e.get('player_id') for e in out if e.get('player_id') and not e.get('shared_player_role')})
    result={'status':'PASS','genre':genre,'events':out,'spec':spec,
            'source_event_count':len(source),'expanded_event_count':len(out),
            'expansion_applied':True,'active_player_ids':players,'active_player_count':len(players)}
    if hierarchy_validation is not None:
        result['big_band_hierarchy_validation']=hierarchy_validation
    return result


def classical_section_population(player_id):
    pid=str(player_id or '').upper()
    mapping=(('VIOLIN_I_',16),('VIOLIN_II_',14),('VIOLA_',12),('CELLO_',10),('DOUBLE_BASS_',8),
             ('FLUTE_',4),('OBOE_',4),('CLARINET_',4),('BASSOON_',4),('HORN_',5),('TRUMPET_',3),('TROMBONE_',3),('TIMPANI_',1))
    for prefix,pop in mapping:
        if pid.startswith(prefix): return pop
    return None