"""Classical chamber pilot: explicit form -> phrases -> notes -> expression.

Scope: tonal chamber miniature in minor with a relative-major middle.
This is a bounded implementation of the existing Classical profile, not a
replacement for all classical traditions or the other 54 Composer profiles.
"""
import copy
import hashlib
import json
import math
import random

PROFILE_ID = 'CLASSICAL_COMMON_PRACTICE_TONAL_CHAMBER_V2'
# Orchestra is no longer a fixed quartet. The default score uses 21 independent
# players/desks across 13 canonical instruments. Multiple players may share one
# instrument track, so the score can exceed MIDI's distinct-channel count without
# collapsing them into one musical voice. There is no artificial player maximum.
DEFAULT_PLAYER_ROSTER = [
    ('VIOLIN_I_1','violin'), ('VIOLIN_I_2','violin'), ('VIOLIN_II_1','violin'),
    ('VIOLA_1','viola'), ('VIOLA_2','viola'),
    ('CELLO_1','cello'), ('CELLO_2','cello'),
    ('DOUBLE_BASS_1','double_bass'), ('DOUBLE_BASS_2','double_bass'),
    ('FLUTE_1','concert_flute'), ('FLUTE_2','concert_flute'),
    ('OBOE_1','oboe'),
    ('CLARINET_1','clarinet_bb'), ('CLARINET_2','clarinet_bb'),
    ('BASSOON_1','bassoon'),
    ('HORN_1','horn_f'), ('HORN_2','horn_f'),
    ('TRUMPET_1','trumpet_c'), ('TROMBONE_1','tenor_trombone'),
    ('TUBA_1','bass_tuba'), ('TIMPANI_1','timpani'),
]
PARTS = list(dict.fromkeys(instrument for _,instrument in DEFAULT_PLAYER_ROSTER))
RANGES = {
    'violin':(55,96), 'viola':(48,88), 'cello':(36,81), 'double_bass':(28,67),
    'concert_flute':(60,98), 'oboe':(58,91), 'clarinet_bb':(50,94), 'bassoon':(34,75),
    'horn_f':(35,77), 'trumpet_c':(55,82), 'tenor_trombone':(40,72),
    'bass_tuba':(28,58), 'timpani':(40,55),
}
ROLE_INSTRUMENT = {'double_bass':'double_bass','violin':'violin',
                   'flute':'concert_flute','clarinet':'clarinet_bb'}
CORE_PLAYER = {'double_bass':'DOUBLE_BASS_1','violin':'VIOLIN_I_1',
               'flute':'FLUTE_1','clarinet':'CLARINET_1'}
TRACKS = {iid:iid.upper() for iid in PARTS}
# Semitones from tonic. Dominant has a raised leading tone in minor.
CHORDS = {
    'minor': {'i': (0,3,7), 'i6': (3,7,12), 'iv': (5,8,12),
              'VI': (8,12,15), 'ii°': (2,5,8), 'V': (7,11,14),
              'V7': (7,11,14,17)},
    'major': {'I': (0,4,7), 'I6': (4,7,12), 'ii': (2,5,9),
              'IV': (5,9,12), 'V': (7,11,14), 'V7': (7,11,14,17),
              'vi': (9,12,16)},
}
SCALES = {'minor': (0,2,3,5,7,8,10), 'major': (0,2,4,5,7,9,11)}
MOTIFS = ((0,2,1,3,2,0,1,0), (2,1,0,2,3,1,2,0), (0,1,3,2,4,2,1,0))
RHYTHMS = (((0,1),(1,.5),(1.5,.5),(2,1)),
           ((0,.5),(.5,.5),(1,1),(2,.5),(2.5,.5)),
           ((0,1.5),(1.5,.5),(2,1)))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def nearest(pc_set, target, bounds):
    choices = [n for n in range(bounds[0], bounds[1]+1) if n % 12 in pc_set]
    if not choices:
        raise ValueError('CLASSICAL_UNPLAYABLE_RANGE')
    return min(choices, key=lambda n: (abs(n-target), n))

def make_plan(seed=0, mode='normal', bpm=76):
    if mode not in ('normal', 'quick') or not 45 <= bpm <= 150:
        raise ValueError('CLASSICAL_INVALID_MODE_OR_TEMPO')
    tonic = (7,2,9)[seed % 3]  # G, D, A minor, recorded in the plan.
    rng=random.Random(seed)
    theme=list(MOTIFS[0]) if seed==0 else [0]
    while len(theme)<8:
        theme.append(max(0,min(6,theme[-1]+rng.choice((-2,-1,1,2)))))
    lengths = (32,16,16,8) if mode == 'normal' else (8,8,8,4)
    names = ('A', 'B', 'A_RETURN', 'CODA')
    sections=[]; bars=[]; phrases=[]; cursor=0
    for section_name, count in zip(names, lengths):
        sections.append({'name': section_name, 'start_bar': cursor+1, 'length_bars': count})
        for local in range(0,count,8):
            length=min(8,count-local); number=local//8
            middle=section_name=='B'; quality='major' if middle else 'minor'
            key=(tonic+3)%12 if middle else tonic
            if middle:
                romans=['I','vi','ii','V','I6','IV','V7','I']
            elif section_name=='CODA':
                romans=['i','VI','iv','V','i6','iv','V7','i'][-length:]
            elif number % 2 == 0 and local+length < count:
                romans=['i','i6','iv','V','i','VI','iv','V']
            else:
                romans=['i','iv','ii°','V','i6','iv','V7','i']
            cadence='HC' if romans[-1]=='V' else 'AUTHENTIC'
            pid=f'{section_name}_P{number+1}'
            operation = ('contrast' if middle else 'augmentation' if section_name=='CODA'
                         else 'return' if section_name=='A_RETURN'
                         else 'development' if number>=2 else 'statement')
            phrases.append({'id':pid,'start_bar':cursor+local+1,'length_bars':length,
                            'cadence':cadence,'motif_operation':operation})
            for j,roman in enumerate(romans[:length]):
                index=cursor+local+j
                bars.append({'bar':index+1,'section':section_name,'phrase_id':pid,
                             'phrase_position':j,'phrase_length':length,'tonic_pc':key,
                             'quality':quality,'roman':roman,'cadence':cadence if j==length-1 else None,
                             'motif_operation':operation,'motif_index':seed%len(MOTIFS),
                             'motif_degrees':list(theme),
                             'melody_development_bar':index%16,
                             'lead':'flute' if middle else 'violin',
                             'bass_style':'moving' if middle or operation=='development' else 'sustained',
                             'dynamic_peak':82 if operation=='development' else 74 if middle else 70,
                             'articulation':'tenuto' if section_name=='CODA' else 'legato'})
        cursor+=count
    tempo_map=[]
    for bar in bars:
        j=bar['phrase_position']; length=bar['phrase_length']; b=(bar['bar']-1)*3
        factor=0.94 if j==length-2 else 0.87 if j==length-1 else 1.0
        if bar['section']=='B':factor*=1.04
        if bar['section']=='CODA':factor*=max(.72,1-.025*j)
        tempo_map.append({'start_beat':b,'bpm':round(bpm*factor,3)})
    return {'schema':'CLASSICAL_EXECUTABLE_PLAN_1','meter':'3/4','bpm':bpm,
            'tonic_pc':tonic,'quality':'minor','sections':sections,'phrases':phrases,
            'bars':bars,'tempo_map':tempo_map,'seed':seed,
            'melody_development_bars':16,'literal_melody_reuse_after_bars':16,
            'preferred_player_band':[16,24],'player_limit_policy':'NO_ARTIFICIAL_GLOBAL_CAP',
            'orchestral_player_roster':[{'player_id':pid,'instrument_id':iid} for pid,iid in DEFAULT_PLAYER_ROSTER]}

def validate_plan(plan):
    if plan['schema']!='CLASSICAL_EXECUTABLE_PLAN_1' or plan['meter']!='3/4':
        raise ValueError('CLASSICAL_PLAN_SCHEMA_UNSUPPORTED')
    if len(plan['bars']) != sum(s['length_bars'] for s in plan['sections']):
        raise ValueError('CLASSICAL_FORM_LENGTH_MISMATCH')
    ids={p['id'] for p in plan['phrases']}
    for i,bar in enumerate(plan['bars']):
        if bar['bar']!=i+1 or bar['phrase_id'] not in ids:
            raise ValueError('CLASSICAL_PHRASE_LINK_BROKEN')
        if bar['roman'] not in CHORDS[bar['quality']]:
            raise ValueError('CLASSICAL_HARMONY_UNSUPPORTED')
        if bar['bass_style'] not in ('moving','sustained') or bar['lead'] not in ('violin','flute'):
            raise ValueError('CLASSICAL_PART_PLAN_UNSUPPORTED')

def realize(plan):
    validate_plan(plan)
    events=[]; previous={'violin':74,'flute':79,'clarinet':65,'double_bass':43}
    roster=plan.get('orchestral_player_roster') or [{'player_id':p,'instrument_id':i} for p,i in DEFAULT_PLAYER_ROSTER]
    player_previous={}
    def add(role,bar,offset,duration,note,velocity,articulation,dynamic,source):
        instrument=ROLE_INSTRUMENT[role]
        lo,hi=RANGES[instrument]
        if not lo<=note<=hi or duration<=0 or offset+duration>3.00001:
            raise ValueError('CLASSICAL_NOTE_OUTSIDE_PLAN')
        player_id=CORE_PLAYER[role]
        events.append({'track_id':TRACKS[instrument],'instrument_id':instrument,'player_id':player_id,'midi':int(note),
                       'start_beat':(bar['bar']-1)*3+offset,'duration_beats':round(duration,5),
                       'velocity':max(25,min(110,int(velocity))),'dynamic':dynamic,
                       'articulation':articulation,'section':bar['section'],
                       'phrase_id':bar['phrase_id'],'plan_bar':bar['bar'],'source_rule':source})
        previous[role]=note; player_previous[player_id]=note
    def add_player(player_id,instrument,bar,offset,duration,note,velocity,articulation,dynamic,source):
        lo,hi=RANGES[instrument]
        if not lo<=note<=hi or duration<=0 or offset+duration>3.00001:
            raise ValueError('CLASSICAL_NOTE_OUTSIDE_PLAN')
        events.append({'track_id':TRACKS[instrument],'instrument_id':instrument,'player_id':player_id,'midi':int(note),
                       'start_beat':(bar['bar']-1)*3+offset,'duration_beats':round(duration,5),
                       'velocity':max(20,min(110,int(velocity))),'dynamic':dynamic,
                       'articulation':articulation,'section':bar['section'],
                       'phrase_id':bar['phrase_id'],'plan_bar':bar['bar'],'source_rule':source})
        player_previous[player_id]=note
    for bar in plan['bars']:
        j=bar['phrase_position']; length=bar['phrase_length']; key=bar['tonic_pc']
        chord=CHORDS[bar['quality']][bar['roman']]; pcs={(key+x)%12 for x in chord}
        final=bar['cadence'] is not None; operation=bar['motif_operation']
        arc=math.sin(math.pi*j/max(1,length-1)); vel=bar['dynamic_peak']-13+int(12*arc)
        dynamic='p' if bar['section']=='CODA' else 'mf' if vel>=73 else 'mp'
        # Bass follows the explicit harmonic inversion and phrase treatment.
        bass_note=nearest({(key+chord[0])%12},45,RANGES['double_bass'])
        if bar['bass_style']=='moving' and not final:
            add('double_bass',bar,0,1.85,bass_note,vel-13,'tenuto',dynamic,'bass_harmonic_root')
            nxt=plan['bars'][min(bar['bar'],len(plan['bars'])-1)]
            target=(nxt['tonic_pc']+CHORDS[nxt['quality']][nxt['roman']][0])%12
            # Keep the moving bass inside the sounding harmony until a
            # prepared/resolved passing-tone planner is available.
            choices=pcs-{bass_note%12} or pcs
            approach=nearest(choices,nearest({target},bass_note,RANGES['double_bass']),RANGES['double_bass'])
            add('double_bass',bar,2,.85,approach,vel-19,'tenuto',dynamic,'bass_chordal_connection')
        else:add('double_bass',bar,0,2.85,bass_note,vel-15,'tenuto',dynamic,'bass_harmonic_support')
        # A sustained interior voice; choose a nearby chord tone rather than reset register.
        # Inner and answering voices are voiced after the melody is known.
        lead=bar['lead']; motif=bar['motif_degrees']; scale=SCALES[bar['quality']]
        rhythm=RHYTHMS[(j+(1 if operation=='contrast' else 0))%len(RHYTHMS)]
        if operation=='augmentation':rhythm=((0,1.5),(1.5,1.5))
        if final:rhythm=((0,3),)
        for k,(offset,duration) in enumerate(rhythm):
            dev=int(bar.get('melody_development_bar',(bar['bar']-1)%16))
            degree=motif[(j*2+k+dev)%len(motif)]
            # Sixteen-bar development window: transform/rotate the motif before
            # literal reuse is eligible. Four-bar motifs remain motifs, not loops.
            if dev%4==1: degree=(degree+1)%7
            elif dev%4==2: degree=(6-degree)%7
            elif dev%4==3: degree=(degree+2+(dev//4))%7
            if operation=='contrast':degree=6-degree
            elif operation=='development':degree=(degree+(j//2)+dev//4)%7
            target=72+key+scale[degree]
            while target>RANGES[ROLE_INSTRUMENT[lead]][1]:target-=12
            if final:
                goal=(key+7)%12 if bar['cadence']=='HC' else key
                note=nearest({goal},previous[lead],RANGES[ROLE_INSTRUMENT[lead]])
            elif offset==0 or duration>=1:
                note=nearest(pcs,target,RANGES[ROLE_INSTRUMENT[lead]])
            else:
                # Chordal connection; ornamental dissonance requires explicit resolution.
                target=previous[lead]+(2 if degree%2 else -2)
                note=nearest(pcs,target,RANGES[ROLE_INSTRUMENT[lead]])
            add(lead,bar,offset,duration*.94,note,vel+(2 if offset==0 else -3),
                bar['articulation'],dynamic,'cadence_goal' if final else 'motif_'+operation)
        # Coordinate chord coverage with the actual bass and melody, rather
        # than choosing each sustained voice independently.
        lead_notes=[e['midi'] for e in events if e['plan_bar']==bar['bar'] and e['instrument_id']==ROLE_INSTRUMENT[lead]]
        opening_pc=lead_notes[0]%12
        missing=pcs-{bass_note%12,opening_pc}
        inner=nearest(missing or (pcs-{bass_note%12}) or pcs,
                      previous['clarinet'],(55,min(72,min(lead_notes)-1)))
        add('clarinet',bar,0,2.7,inner,vel-21,'legato',dynamic,'coordinated_inner_chord_voice')
        # Other upper voice enters in answers and development, leaving breathing space.
        other='violin' if lead=='flute' else 'flute'
        if final or j%2==1 or operation=='development':
            missing=pcs-{bass_note%12,opening_pc,inner%12}
            note=nearest(missing or (pcs-{opening_pc}) or pcs,previous[other],RANGES[ROLE_INSTRUMENT[other]])
            add(other,bar,0 if final else 1,2.75 if final else 1.7,note,vel-19,
                'legato',dynamic,'countervoice_answer')

        # Full-orchestra realization. These are independent players/desks, not a
        # fixed list of four instruments. Players sharing an instrument share a
        # MIDI track but retain separate player_id voices in the score/event layer.
        def tone(instrument,target):
            return nearest(pcs,player_previous.get(target,target if isinstance(target,int) else 60),RANGES[instrument])
        # Strings form the continuous body.
        string_specs=[
            ('VIOLIN_I_2','violin',78),('VIOLIN_II_1','violin',70),
            ('VIOLA_1','viola',64),('VIOLA_2','viola',58),
            ('CELLO_1','cello',50),('CELLO_2','cello',45),
            ('DOUBLE_BASS_2','double_bass',36),
        ]
        for idx,(pid,iid,target_register) in enumerate(string_specs):
            n=nearest(pcs,player_previous.get(pid,target_register),RANGES[iid])
            add_player(pid,iid,bar,0.03*idx,2.72,n,vel-24-idx//2,'legato',dynamic,'orchestral_string_section')
        # Woodwinds rotate color and counterlines without forcing every player to
        # play every bar. Across the score, every desk is active.
        wood_specs=[('FLUTE_2','concert_flute',84),('OBOE_1','oboe',76),
                    ('CLARINET_2','clarinet_bb',63),('BASSOON_1','bassoon',47)]
        for idx,(pid,iid,target_register) in enumerate(wood_specs):
            if (j+idx)%2==0 or operation in ('development','contrast') or final:
                n=nearest(pcs,player_previous.get(pid,target_register),RANGES[iid])
                add_player(pid,iid,bar,.45+.28*idx,1.55,n,vel-25,'legato',dynamic,'orchestral_woodwind_color')
        # Brass grows with structural intensity; horns provide the most continuous
        # brass support while trumpet/trombone/tuba are reserved for larger moments.
        horn_specs=[('HORN_1','horn_f',60),('HORN_2','horn_f',55)]
        for idx,(pid,iid,target_register) in enumerate(horn_specs):
            if j%2==0 or operation in ('development','contrast') or final:
                n=nearest(pcs,player_previous.get(pid,target_register),RANGES[iid])
                add_player(pid,iid,bar,.08*idx,2.45,n,vel-30,'tenuto',dynamic,'orchestral_horn_support')
        if operation in ('development','contrast') or final:
            for idx,(pid,iid,target_register) in enumerate((('TRUMPET_1','trumpet_c',72),('TROMBONE_1','tenor_trombone',52),('TUBA_1','bass_tuba',36))):
                n=nearest(pcs,player_previous.get(pid,target_register),RANGES[iid])
                add_player(pid,iid,bar,.12*idx,1.95,n,vel-27-idx*2,'tenuto',dynamic,'orchestral_brass_punctuation')
        if final or j==0:
            timp_pc={(key+chord[0])%12,(key+7)%12}
            n=nearest(timp_pc,player_previous.get('TIMPANI_1',47),RANGES['timpani'])
            add_player('TIMPANI_1','timpani',bar,0,.85,n,vel-18,'tenuto',dynamic,'orchestral_timpani_structure')
    return sorted(events,key=lambda e:(e['start_beat'],e['track_id'],e.get('player_id',''),e['midi']))

def duration_seconds(plan):
    return sum(180/t['bpm'] for t in plan['tempo_map'])

def build_classical_setup(profile, mode='normal', creation_seed=0, plan=None):
    if profile.get('profile_id')!=PROFILE_ID:
        raise ValueError('CLASSICAL_PROFILE_ID_MISMATCH')
    plan=copy.deepcopy(plan) if plan is not None else make_plan(creation_seed,mode)
    events=realize(plan)
    # Keep the proven 14-section score/routing intact, but attach a researched
    # physical-population reference so balance/render stages know that one
    # section track may represent many players. Population is metadata here; it
    # must not be implemented as linear gain or identical-note cloning.
    from ensemble_architecture import get_spec, classical_section_population
    ensemble_architecture=get_spec('Classical')
    for event in events:
        pop=classical_section_population(event.get('player_id'))
        if pop is not None:
            event['ensemble_section_population']=pop
            event['population_render_policy']='SECTION_MASS_NOT_LINEAR_GAIN'
    from genre_interpreter_linkage import interpret_genre,link_genre
    interpreted=interpret_genre('Classical',profile,PARTS)
    linkage=link_genre('Classical',profile,PARTS,events,interpreted=interpreted)
    return {'genre_name':'Classical','profile_id':PROFILE_ID,'status':'PASS',
            'resolution_policy':profile['resolution_policy'],'execution_template':'classical',
            'tempo_bpm':plan['bpm'],'meter':plan['meter'],'bars':len(plan['bars']),
            'form':'aba','creation_seed':creation_seed,'palette':list(PARTS),
            'events':events,'tempo_map':plan['tempo_map'],'classical_plan':plan,
            'ensemble_architecture':ensemble_architecture,
            'orchestral_player_count':len(plan.get('orchestral_player_roster',DEFAULT_PLAYER_ROSTER)),
            'orchestral_physical_population_reference':sum((ensemble_architecture or {}).get('current_composer_section_mapping',{}).values()),
            'orchestral_player_roster':copy.deepcopy(plan.get('orchestral_player_roster')),
            'player_limit_policy':plan.get('player_limit_policy','NO_ARTIFICIAL_GLOBAL_CAP'),
            'melody_development_bars':int(plan.get('melody_development_bars',16)),
            'pre_generation_genre_plan':{'status':'PASS','source':'EXPLICIT_CLASSICAL_RULES',
                                        'harmony_family':'functional','player_limit_policy':plan.get('player_limit_policy','NO_ARTIFICIAL_GLOBAL_CAP'),
                                        'melody_development_bars':int(plan.get('melody_development_bars',16)),
                                        'plan_sha256':digest(plan)},
            'profile_required_fields_sha256':digest(profile),'theory_status':'PASS',
            'theory_request':{'form':'aba','bars':len(plan['bars']),'meter':'3/4'},
            'genre_interpreter_linkage':linkage,'beat_unit':'quarter_note',
            'duration_seconds':duration_seconds(plan),
            'musical_quality_status':'CLASSICAL_PILOT_REQUIRES_LISTENING_REVIEW'}