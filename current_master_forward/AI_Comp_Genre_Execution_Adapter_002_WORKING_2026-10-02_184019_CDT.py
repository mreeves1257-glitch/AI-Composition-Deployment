from __future__ import annotations
import json, math, hashlib, importlib.util, wave
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent
PROFILE_PATH=ROOT/'AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json'
THEORY_PATH=ROOT/'executable_theory_engine_SOURCE_PRESERVED.py'
OUT=ROOT/'output'
OUT.mkdir(parents=True, exist_ok=True)
STAMP='2026-10-02_184019_CDT'

spec=importlib.util.spec_from_file_location('theory_engine',THEORY_PATH)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
TheoryEngine=mod.TheoryEngine
engine=TheoryEngine()
profiles=json.loads(PROFILE_PATH.read_text())['profiles']

NOTE_PC={'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
def midi(note:str,octave:int)->int: return 12*(octave+1)+NOTE_PC[note]

def h(obj:Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def family_template(name:str)->str:
    n=name.lower()
    if name=='ROCK': return 'rock'
    if name=='Jazz Waltz': return 'jazz_waltz'
    if name=='Two-Step': return 'two_step'
    if any(x in n for x in ['swing','jazz ballad','bebop','cool jazz','dixieland','jazz fusion','big band']):
        if 'ballad' in n: return 'jazz_ballad'
        if 'bebop' in n: return 'bebop'
        if 'big band' in n: return 'big_band'
        if 'dixieland' in n: return 'dixieland'
        if 'fusion' in n: return 'fusion'
        if 'cool' in n: return 'cool_jazz'
        if 'waltz' in n: return 'jazz_waltz'
        return 'swing'
    if any(x in n for x in ['rhythm and blues','soul','funk','r&b','neo-soul']):
        if 'funk' in n: return 'funk'
        if 'neo' in n: return 'neo_soul'
        if 'contemporary' in n: return 'contemporary_rnb'
        if n=='soul': return 'soul'
        return 'rnb'
    if any(x in n for x in ['country','bluegrass']):
        if 'bluegrass' in n: return 'bluegrass'
        if 'rock' in n: return 'country_rock'
        if 'waltz' in n: return 'country_waltz'
        if 'shuffle' in n: return 'country_shuffle'
        if 'two-step' in n: return 'two_step'
        if 'ballad' in n: return 'country_ballad'
        return 'country'
    if any(x in n for x in ['bossa','samba','salsa','mambo','rumba','cha-cha','bolero']):
        if 'bossa' in n: return 'bossa'
        if 'samba' in n: return 'samba'
        if 'salsa' in n: return 'salsa'
        if 'mambo' in n: return 'mambo'
        if 'rumba' in n: return 'rumba'
        if 'cha-cha' in n: return 'cha_cha'
        return 'bolero'
    if any(x in n for x in ['house','techno','trance','ambient electronic','downtempo','breakbeat','garage','experimental electronic']):
        if 'afro house' in n: return 'afro_house'
        if n=='house': return 'house'
        if 'techno' in n: return 'techno'
        if 'trance' in n: return 'trance'
        if 'ambient' in n: return 'ambient_electronic'
        if 'downtempo' in n: return 'downtempo'
        if 'breakbeat' in n: return 'breakbeat'
        if 'garage' in n: return 'garage'
        return 'experimental_electronic'
    if name=='New Age': return 'new_age'
    if name=='Classical': return 'classical'
    if name=='DISCO': return 'disco'
    if name=='WALTZ': return 'waltz'
    if name=='PIANIST': return 'pianist'
    if name=='Spiritual': return 'spiritual'
    if 'afrobeats' in n and 'fusion' not in n: return 'afrobeats'
    if 'afro house' in n: return 'afro_house'
    if 'contemporary trip-hop' in n or 'trip-hop revival' in n: return 'contemporary_trip_hop'
    if 'trip-hop' in n: return 'trip_hop'
    if 'mexican reggaeton' in n: return 'reggaeton'
    if 'chugg' in n: return 'chugg'
    if 'eclectic new indie' in n: return 'indie'
    return 'hybrid'

# Machine-readable baselines. They deliberately stay within the existing TheoryEngine's supported vocabulary.
BASE={
 'rock':('E','natural_minor','4/4',112,'verse_chorus','roots_fifths'),
 'swing':('Bb','major','4/4',132,'verse_chorus','walking'),
 'jazz_ballad':('Eb','major','4/4',72,'aba','walking'),
 'big_band':('Bb','major','4/4',148,'verse_chorus','walking'),
 'bebop':('F','major','4/4',176,'through_composed','walking'),
 'cool_jazz':('C','major','4/4',104,'aba','walking'),
 'dixieland':('Bb','major','4/4',152,'through_composed','walking'),
 'fusion':('D','natural_minor','4/4',118,'verse_chorus','roots_fifths'),
 'jazz_waltz':('F','major','3/4',108,'aba','walking'),
 'rnb':('C','natural_minor','4/4',92,'verse_chorus','roots_fifths'),
 'soul':('F','major','4/4',88,'verse_chorus','roots_fifths'),
 'funk':('E','natural_minor','4/4',108,'verse_chorus','roots_fifths'),
 'contemporary_rnb':('F','natural_minor','4/4',82,'verse_chorus','roots_fifths'),
 'neo_soul':('Eb','major','4/4',86,'aba','walking'),
 'country':('G','major','4/4',104,'verse_chorus','roots_fifths'),
 'country_rock':('A','major','4/4',122,'verse_chorus','roots_fifths'),
 'country_ballad':('G','major','4/4',72,'verse_chorus','root_primary_beats'),
 'country_shuffle':('E','major','4/4',116,'verse_chorus','roots_fifths'),
 'two_step':('D','major','4/4',126,'verse_chorus','roots_fifths'),
 'country_waltz':('G','major','3/4',92,'aba','root_primary_beats'),
 'bluegrass':('G','major','4/4',148,'through_composed','roots_fifths'),
 'bossa':('D','minor','4/4',126,'aba','roots_fifths'),
 'samba':('C','major','4/4',104,'through_composed','roots_fifths'),
 'salsa':('C','minor','4/4',104,'verse_chorus','roots_fifths'),
 'mambo':('F','minor','4/4',112,'through_composed','roots_fifths'),
 'rumba':('D','minor','4/4',96,'aba','root_primary_beats'),
 'cha_cha':('C','minor','4/4',120,'verse_chorus','roots_fifths'),
 'bolero':('G','minor','4/4',76,'aba','root_primary_beats'),
 'house':('C','minor','4/4',124,'verse_chorus','roots_fifths'),
 'techno':('D','minor','4/4',132,'through_composed','pedal'),
 'trance':('A','minor','4/4',136,'verse_chorus','pedal'),
 'ambient_electronic':('C','major','4/4',70,'through_composed','pedal'),
 'downtempo':('D','minor','4/4',88,'aba','roots_fifths'),
 'breakbeat':('E','minor','4/4',132,'verse_chorus','roots_fifths'),
 'garage':('F','minor','4/4',132,'verse_chorus','roots_fifths'),
 'experimental_electronic':('C','minor','4/4',96,'through_composed','pedal'),
 'new_age':('E','major','4/4',76,'aba','pedal'),
 'classical':('G','natural_minor','3/4',92,'aba','root_primary_beats'),
 'disco':('A','minor','4/4',118,'verse_chorus','roots_fifths'),
 'waltz':('D','major','3/4',96,'aba','root_primary_beats'),
 'pianist':('C','major','4/4',84,'aba','broken_octave'),
 'spiritual':('G','major','4/4',74,'through_composed','pedal'),
 'afrobeats':('A','minor','4/4',108,'verse_chorus','roots_fifths'),
 'afro_house':('D','minor','4/4',120,'verse_chorus','roots_fifths'),
 'trip_hop':('C','minor','4/4',82,'aba','roots_fifths'),
 'contemporary_trip_hop':('D','minor','4/4',88,'verse_chorus','roots_fifths'),
 'reggaeton':('F','minor','4/4',96,'verse_chorus','roots_fifths'),
 'chugg':('C','minor','4/4',144,'through_composed','roots_fifths'),
 'indie':('G','major','4/4',116,'verse_chorus','roots_fifths'),
 'hybrid':('C','minor','4/4',100,'through_composed','roots_fifths'),
}

# Diagnostic resource roles. These are not claims of production-fidelity instrument bindings.
PALETTES={
 'rock':['electric_bass','electric_guitar','lead_guitar','drums'],
 'swing':['double_bass','electric_piano','trumpet','drums_ride'], 'jazz_ballad':['double_bass','electric_piano','clarinet','brush_drums'],
 'big_band':['double_bass','piano','electric_guitar','alto_sax','tenor_sax','baritone_sax','trumpet','trombone','drums_ride'], 'bebop':['double_bass','piano','trumpet','drums_ride'],
 'cool_jazz':['double_bass','piano','flute','brush_drums'], 'dixieland':['double_bass','banjo','clarinet','trumpet','trombone','drums_ride'],
 'fusion':['electric_bass','electric_piano','electric_guitar','synth_lead','drums'], 'jazz_waltz':['double_bass','electric_piano','flute','brush_drums'],
 'rnb':['electric_bass','electric_piano','electric_guitar','drums'], 'soul':['electric_bass','electric_piano','trumpet','drums'],
 'funk':['electric_bass','electric_guitar','clav','drums'], 'contemporary_rnb':['synth_bass','electric_piano','synth_pad','drums_soft'],
 'neo_soul':['electric_bass','electric_piano','electric_guitar','drums_soft'],
 'country':['electric_bass','acoustic_guitar','violin','pedal_steel_guitar','drums'], 'country_rock':['electric_bass','electric_guitar','acoustic_guitar','drums'],
 'country_ballad':['electric_bass','acoustic_guitar','violin','pedal_steel_guitar','drums_soft'], 'country_shuffle':['electric_bass','acoustic_guitar','electric_guitar','pedal_steel_guitar','drums_shuffle'],
 'two_step':['electric_bass','acoustic_guitar','violin','pedal_steel_guitar','drums'], 'country_waltz':['double_bass','acoustic_guitar','violin','pedal_steel_guitar','drums_soft'],
 'bluegrass':['double_bass','acoustic_guitar','violin','banjo','mandolin'],
 'bossa':['double_bass','acoustic_guitar','electric_piano','conga'], 'samba':['electric_bass','electric_piano','surdo','caixa','repinique','tamborim','agogo_bells','shaker'],
 'salsa':['electric_bass','piano','flute','tenor_sax','trumpet','trombone','conga','bongo_family','claves','cowbell','timbales'], 'mambo':['double_bass','piano','alto_sax','tenor_sax','baritone_sax','trumpet','shaker','bongo_family','conga','timbales','drums'],
 'rumba':['double_bass','acoustic_guitar','conga','claves','flute'], 'cha_cha':['electric_bass','piano','trumpet','conga','bongo_family','claves','cowbell','timbales'],
 'bolero':['double_bass','acoustic_guitar','flute','conga'],
 'house':['synth_bass','synth_chord','synth_lead','drums_electronic'], 'techno':['synth_bass','synth_pulse','noise_fx','drums_electronic'],
 'trance':['synth_bass','synth_pad','synth_arp','drums_electronic'], 'ambient_electronic':['synth_pad','synth_arp','flute','noise_fx'],
 'downtempo':['synth_bass','electric_piano','synth_pad','break_drums'], 'breakbeat':['synth_bass','synth_chord','break_drums','noise_fx'],
 'garage':['synth_bass','synth_chord','synth_lead','break_drums'], 'experimental_electronic':['synth_bass','synth_pad','noise_fx','break_drums'],
 'new_age':['electric_piano','flute','strings','synth_pad'], 'classical':['double_bass','violin','flute','clarinet'],
 'disco':['electric_bass','electric_guitar','strings','drums_four'], 'waltz':['double_bass','acoustic_guitar','violin','flute'],
 'pianist':['piano'], 'spiritual':['piano','strings','flute','choir'],
 'afrobeats':['electric_bass','electric_piano','electric_guitar','conga','shaker','drums_afro'], 'afro_house':['synth_bass','synth_chord','conga','shaker','drums_four'],
 'trip_hop':['synth_bass','electric_piano','synth_pad','break_drums'], 'contemporary_trip_hop':['synth_bass','synth_chord','synth_pad','break_drums'], 'reggaeton':['synth_bass','synth_chord','drums_dembow','noise_fx'],
 'chugg':['synth_bass','synth_lead','break_drums','noise_fx'], 'indie':['electric_bass','electric_guitar','synth_pad','drums'],
 'hybrid':['synth_bass','electric_piano','synth_pad','drums_electronic'],
}

# Per-genre instrument authority: each selected genre profile may extend its baseline
# with supported roles explicitly named in its own musical instructions. The
# switch does not interpret the genre; it only routes to its own profile.
PROFILE_ROLE_ALIASES = (
    ('double bass', 'double_bass'), ('electric bass', 'electric_bass'),
    ('synth bass', 'synth_bass'), ('acoustic guitar', 'acoustic_guitar'),
    ('electric guitar', 'electric_guitar'), ('lead guitar', 'lead_guitar'),
    ('electric piano', 'electric_piano'), ('piano', 'piano'),
    ('trumpet', 'trumpet'), ('trombone', 'trombone'),
    ('clarinet', 'clarinet'), ('flute', 'flute'), ('violin', 'violin'),
    ('strings', 'strings'), ('choir', 'choir'), ('conga', 'conga'),
    ('marimba', 'marimba'), ('synth pad', 'synth_pad'),
    ('synth lead', 'synth_lead'), ('synth arp', 'synth_arp'),
)
SUPPORTED_EVENT_ROLES = set(role for parts in PALETTES.values() for role in parts)

def resolve_genre_parts(name, tmpl, profile):
    # Executable instrumentation is explicit, never inferred by blindly scanning
    # prose.  The old keyword extension treated alternatives such as
    # 'piano/electric piano' and 'acoustic/electric bass' as simultaneous required
    # players, which created avoidable masking and muddiness.  PALETTES is now the
    # controlled executable role map; profile prose remains recognition/context.
    baseline = list(PALETTES.get(tmpl, PALETTES['hybrid']))
    if tmpl == 'classical':
        baseline = [role for role in baseline if role not in ('strings', 'choir')]
    return baseline

# stable per-template variants so closely related genres don't collapse into identical grooves
VARIANT={name:i for i,name in enumerate(BASE)}

def build_setup(name:str, profile:dict[str,Any], mode='quick', creation_seed:int=0):
    if name == 'Classical':
        from classical_composition import build_classical_setup
        return build_classical_setup(profile, mode, creation_seed)
    policy=profile['resolution_policy']
    if policy!='AUTOMATIC_BASELINE_ALLOWED':
        return {'genre_name':name,'profile_id':profile['profile_id'],'status':'CONTROLLED_INPUT_REQUIRED','resolution_policy':policy,'events':[]}
    tmpl=family_template(name)
    baseline=BASE.get(tmpl,BASE['hybrid'])
    tonic,quality,_,_,_,_=baseline
    parts=resolve_genre_parts(name,tmpl,profile)

    # The genre interpreter now runs BEFORE theory and before any notes are generated.
    from genre_interpreter_linkage import interpret_genre, link_genre
    interpreted=interpret_genre(name,profile,parts)
    from genre_pre_generation_compiler import compile_generation_plan
    generation_plan=compile_generation_plan(profile,baseline,creation_seed)
    from genre_communication_blueprint import build as build_communication_blueprint
    communication_blueprint=build_communication_blueprint(
        name,profile,parts,interpreted,generation_plan)
    meter=generation_plan['meter']; bpm=generation_plan['tempo_bpm']; form=generation_plan['form']
    semantic_seed=int(generation_plan['variation_seed'])
    major_keys=['C','D','Eb','E','F','G','A','Bb']; minor_keys=['A','C','D','E','F','G']
    key_pool=major_keys if quality in ('major','ionian') else minor_keys
    tonic=key_pool[(semantic_seed//13)%len(key_pool)]
    # quick test bars intentionally shorter; normal target ~3:30.
    numerator, denominator = map(int, meter.split('/'))
    beats_per_bar = numerator * 4 / denominator
    if mode=='normal':
        target_s=210
        bars=max(24, round(target_s*bpm/(60*beats_per_bar)))
        bars=max(24,min(320,bars))
    else:
        bars=12 if meter.startswith('3/') else 16
    req={'tonic':tonic,'mode':quality,'meter':meter,'bars':bars,'form':form,
         'phrase_bars':generation_plan['phrase_bars'],'bass_behavior':generation_plan['bass_behavior'],
         'roman_progression':list(generation_plan['roman_progression'])}
    ctx=engine.build_composition_context(req)
    if ctx.get('status') not in ('PASS','REVIEW_REQUIRED'):
        return {'genre_name':name,'profile_id':profile['profile_id'],'status':'THEORY_BLOCK','theory':ctx,'events':[],
                'pre_generation_genre_plan':generation_plan}
    events=generate_events(name,tmpl,profile,ctx,bpm,creation_seed,parts=parts,generation_plan=generation_plan,communication_blueprint=communication_blueprint)
    # Large ensembles are expanded only where a researched formation is present.
    # Small/flexible genres keep their existing palette unchanged.
    from ensemble_architecture import expand_events
    ensemble_expansion=expand_events(name,events,ctx)
    events=ensemble_expansion['events']
    linkage=link_genre(name,profile,parts,events,interpreted=interpreted)
    return {
        'genre_name':name,'profile_id':profile['profile_id'],'status':'PASS','resolution_policy':policy,
        'execution_template':tmpl,'tempo_bpm':bpm,'meter':meter,'bars':bars,'form':form,'creation_seed':creation_seed,
        'profile_required_fields_sha256':h({k:profile[k] for k in profiles_meta_required}),
        'pre_generation_genre_plan':generation_plan,
        'communication_blueprint':communication_blueprint,
        'theory_request':req,'theory_status':ctx['status'],'palette':parts,
        'ensemble_architecture':ensemble_expansion.get('spec'),
        'ensemble_expansion_manifest':{k:v for k,v in ensemble_expansion.items() if k not in ('events','spec')},
        'events':events, 'genre_interpreter_linkage':linkage, 'beat_unit':'quarter_note',
        'duration_seconds':bars * beats_per_bar * 60 / bpm,
    }

profiles_meta_required=json.loads(PROFILE_PATH.read_text())['universal_required_fields']

def chord_midis(ch, base_oct=3):
    out=[]
    for note in ch['notes']:
        out.append(midi(note,base_oct))
    return sorted(out)

def _melody_cells(name:str, creation_seed:int, window:int, steps:int, energetic:bool=False):
    """Build a deterministic development window with no literal cell reuse.

    Short motifs may recur *inside* a cell, but the bar-level melody cell is unique
    across the first window bars. After the window, reuse is allowed.
    """
    window=max(16,int(window)); steps=max(2,int(steps))
    base=[0,2,4,6,5,3,1,2] if energetic else [0,2,4,5,3,1,2,0]
    cells=[]; used=set()
    for bar in range(window):
        nonce=0
        while True:
            raw=hashlib.sha256(f"{name}:{creation_seed}:{bar}:{nonce}".encode()).digest()
            rot=raw[0] % len(base); shift=raw[1] % 7
            invert=bool(raw[2] & 1); drift=(raw[3] % 3)-1
            seq=[]
            for j in range(steps):
                degree=base[(j+rot)%len(base)]
                if invert: degree=(-degree) % 7
                degree=(degree+shift+drift*j+(bar//4)) % 7
                seq.append(degree)
            cell=tuple(seq)
            if cell not in used:
                used.add(cell); cells.append(cell); break
            nonce+=1
    return cells


def _bb_nearest_pc(pc:int,target:int,lo:int=36,hi:int=84)->int:
    choices=[n for n in range(lo,hi+1) if n%12==pc%12]
    return min(choices,key=lambda n:(abs(n-target),n))


def _bb_extended_pcs(chord):
    """Compact swing-era/jazz color set for section and comping voicings.

    This is intentionally functional rather than a universal jazz-harmony claim:
    tonic/subdominant major harmony gets 6/9 color; dominant-function harmony gets
    b7/9; minor harmony gets m7/9.  The TheoryEngine chord remains authoritative
    for the root/function and this layer only supplies idiomatic arranged color.
    """
    root_pc=NOTE_PC[chord['root']]
    quality=str(chord.get('quality','major')).lower()
    roman=str(chord.get('roman',''))
    if 'minor' in quality or quality.startswith('m'):
        intervals=(0,3,7,10,2)
    elif roman.startswith('V'):
        intervals=(0,4,7,10,2)
    else:
        intervals=(0,4,7,9,2)
    return {(root_pc+i)%12 for i in intervals}


def _bb_voicing(chord, low=50, high=74, rootless=True):
    root_pc=NOTE_PC[chord['root']]
    pcs=_bb_extended_pcs(chord)
    if rootless and root_pc in pcs:
        pcs=set(pcs);pcs.remove(root_pc)
    targets=(52,57,62,67,72)
    out=[]
    for pc,target in zip(sorted(pcs),targets):
        n=_bb_nearest_pc(pc,target,low,high)
        if n not in out: out.append(n)
    return sorted(out)[:4]


def _bb_walking_line(chord,next_chord):
    root_pc=NOTE_PC[chord['root']]; next_pc=NOTE_PC[next_chord['root']]
    root=_bb_nearest_pc(root_pc,40,34,52)
    pcs=_bb_extended_pcs(chord)
    third_pc=(root_pc+(3 if 'minor' in str(chord.get('quality','')).lower() else 4))%12
    fifth_pc=(root_pc+7)%12
    beat2=_bb_nearest_pc(third_pc,root+4,34,55)
    beat3=_bb_nearest_pc(fifth_pc,root+7,34,55)
    next_root=_bb_nearest_pc(next_pc,root,34,55)
    approach=next_root-1 if next_root>=beat3 else next_root+1
    approach=max(34,min(55,approach))
    return (root,beat2,beat3,approach)


def _generate_big_band_events(name,profile,ctx,bpm,creation_seed,palette,generation_plan):
    """Dedicated Big Band arranger with explicit chair-level leadership hierarchy.

    Big Band V3 separates *who owns the musical foreground* from which section is
    currently sounding.  A section may harmonize its lead chair or answer the lead,
    but only one foreground owner is declared at a time.  The shout chorus is the
    full-ensemble exception, while Lead Trumpet remains the top perceptual line.
    """
    ev=[]; chords=ctx['harmony']['chords']; meter=int(ctx['meter']['numerator'])
    if meter!=4:
        raise ValueError('BIG_BAND_V1_REQUIRES_4_4')

    def add(track,iid,bar,pos,dur,note,vel,art,**extra):
        x={'track_id':track,'instrument_id':iid,'start_beat':bar*4+pos,
           'duration_beats':dur,'midi':int(note),'velocity':int(max(1,min(127,vel))),
           'articulation':art,'big_band_arranger_v3':True}
        x.update(extra);ev.append(x)

    # Four distinct assignments inside a 16-bar behavior window:
    #   0-3   Lead Alto owns the head; brass only answers in the holes.
    #   4-7   Lead Trumpet owns the foreground; saxes answer, bones support.
    #   8-11  Tenor 1 is a true single-chair solo feature; horn figures stay behind it.
    #   12-15 Full shout; Lead Trumpet remains the top line while sections couple below.
    sax_patterns=(
        ((0.0,.42,0),(1.667,.28,4),(2.0,.48,7),(3.667,.26,9)),
        ((.667,.28,4),(1.0,.42,7),(2.667,.30,9),(3.0,.48,7)),
        ((0.0,.30,7),(.667,.24,9),(1.667,.34,4),(3.0,.50,2)),
        ((.667,.26,4),(1.667,.26,7),(2.667,.26,9),(3.333,.48,0)),
    )
    trumpet_patterns=(
        ((0.0,.30,0),(.667,.22,4),(1.667,.30,7),(3.0,.34,9)),
        ((.667,.24,2),(1.0,.32,4),(2.667,.24,7),(3.667,.30,4)),
        ((0.0,.28,7),(1.667,.26,9),(2.0,.34,7),(3.333,.26,4)),
        ((.667,.22,4),(1.667,.22,7),(2.667,.26,9),(3.0,.38,0)),
    )
    tenor_solo_patterns=(
        ((0,.42,0),(.667,.28,2),(1.667,.36,4),(2.0,.48,7),(3.333,.34,9)),
        ((.333,.26,2),(1.0,.44,4),(2.333,.30,7),(3.0,.54,4)),
        ((0,.32,7),(.667,.24,9),(1.333,.30,11),(2.0,.46,9),(3.0,.38,7)),
        ((.667,.28,4),(1.333,.32,7),(2.333,.28,9),(3.333,.44,2)),
    )
    background_hits=((1.667,.20),(3.667,.22))
    shout_hits=((0.0,.26),(.667,.22),(1.667,.24),(2.0,.34),(3.667,.28))

    for b,ch in enumerate(chords):
        nxt=chords[(b+1)%len(chords)]
        root4=midi(ch['root'],4)
        cycle=b%16
        if cycle<4:
            epoch='HEAD_LEAD_ALTO'; global_owner='ALTO_SAX_1'
        elif cycle<8:
            epoch='FEATURE_LEAD_TRUMPET'; global_owner='TRUMPET_1'
        elif cycle<12:
            epoch='TENOR_SOLO_FEATURE'; global_owner='TENOR_SAX_1'
        else:
            epoch='SHOUT_LEAD_TRUMPET'; global_owner='TRUMPET_1'

        # Rhythm section is always a foundation, never the declared foreground.
        gvo=_bb_voicing(ch,48,69,rootless=True)
        for beat in (0,1,2,3):
            for n in gvo[:3]:
                add('GUITAR','electric_guitar',b,beat,.17,n,40+(beat%2)*2,'freddie_green_quarter',
                    foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)
        pvo=_bb_voicing(ch,50,76,rootless=True)
        # Piano deliberately leaves more air under featured horn lines.
        comp=(1.667,3.333) if cycle<12 else (.667,2.667)
        for k,pos in enumerate(comp):
            for n in pvo:
                add('PIANO','piano',b,pos,.28,n,46+(k%2)*4,'swing_comp',
                    foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)

        for j,n in enumerate(_bb_walking_line(ch,nxt)):
            add('BASS','double_bass',b,float(j),.76,n,70+(j%2)*3,'walking_quarter',
                foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)

        for j,pos in enumerate((0,1,1.667,2,3,3.667)):
            add('RIDE','drums_ride',b,pos,.08,51,55+(6 if j in (2,5) else 0),'swing_ride',drum='ride',
                foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)
        for pos in (1,3):
            add('HIHAT_FOOT','drums_ride',b,pos,.07,44,51,'two_four_hihat',drum='hat',
                foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)
        for pos in (0,2):
            add('KICK','drums_ride',b,pos,.09,36,47,'feathered_kick',drum='kick',
                foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)
        snpos=1.667 if b%2==0 else 3.667
        add('SNARE_COMP','drums_ride',b,snpos,.08,38,49,'snare_comp',drum='snare',
            foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)

        if cycle<4:
            # Lead Alto is the audible top voice of a harmonized sax section.
            for pos,dur,off in sax_patterns[cycle%4]:
                add('SAX_SECTION','alto_sax',b,pos,dur,root4+off,72,'head_melody',
                    foreground_owner='ALTO_SAX_1',arrangement_role='FOREGROUND_LEAD',
                    lead_chair='ALTO_SAX_1',section_harmonized=True,assignment_epoch=epoch)
            # Brass only answers in spaces; it never becomes a second lead block.
            if cycle in (2,3):
                for pos,dur in background_hits:
                    add('TRUMPET_SECTION','trumpet',b,pos,dur,root4+12,60,'brass_background_answer',
                        foreground_owner='ALTO_SAX_1',arrangement_role='BACKGROUND',
                        lead_chair='TRUMPET_1',section_harmonized=True,assignment_epoch=epoch)
                    add('TROMBONE_SECTION','trombone',b,pos,dur,root4,54,'brass_background_answer',
                        foreground_owner='ALTO_SAX_1',arrangement_role='BACKGROUND',
                        lead_chair='TROMBONE_1',section_harmonized=True,assignment_epoch=epoch)

        elif cycle<8:
            # Trumpet 1 owns the feature. The rest of the trumpet section harmonizes it.
            for pos,dur,off in trumpet_patterns[cycle%4]:
                add('TRUMPET_SECTION','trumpet',b,pos,dur,root4+12+off,76,'lead_trumpet_feature',
                    foreground_owner='TRUMPET_1',arrangement_role='FOREGROUND_LEAD',
                    lead_chair='TRUMPET_1',section_harmonized=True,assignment_epoch=epoch)
            # Trombones are a lower background layer, not co-owners.
            for pos,dur in background_hits:
                add('TROMBONE_SECTION','trombone',b,pos,dur,root4,53,'trombone_background',
                    foreground_owner='TRUMPET_1',arrangement_role='BACKGROUND',
                    lead_chair='TROMBONE_1',section_harmonized=True,assignment_epoch=epoch)
            # One short sax answer near the end of the bar, still subordinate to Tpt 1.
            for pos,dur,off in ((2.667,.22,4),(3.333,.26,7)):
                add('SAX_SECTION','alto_sax',b,pos,dur,root4+off,57,'sax_background_response',
                    foreground_owner='TRUMPET_1',arrangement_role='SECONDARY_RESPONSE',
                    lead_chair='ALTO_SAX_1',section_harmonized=True,assignment_epoch=epoch)

        elif cycle<12:
            # A true single-chair solo feature.  This is intentionally NOT expanded
            # into all five saxes; the band backs Tenor 1 instead of becoming Tenor 1.
            for pos,dur,off in tenor_solo_patterns[cycle%4]:
                add('TENOR_SOLO','tenor_sax',b,pos,dur,root4+off,75,'tenor_solo_feature',
                    foreground_owner='TENOR_SAX_1',arrangement_role='FOREGROUND_LEAD',
                    lead_chair='TENOR_SAX_1',single_chair=True,assignment_epoch=epoch)
            # Compact horn backgrounds enter only in holes and are deliberately lower.
            if cycle%2:
                for pos,dur in background_hits:
                    add('TRUMPET_SECTION','trumpet',b,pos,dur,root4+12,57,'solo_background',
                        foreground_owner='TENOR_SAX_1',arrangement_role='BACKGROUND',
                        lead_chair='TRUMPET_1',section_harmonized=True,assignment_epoch=epoch)
                    add('TROMBONE_SECTION','trombone',b,pos,dur,root4,50,'solo_background',
                        foreground_owner='TENOR_SAX_1',arrangement_role='BACKGROUND',
                        lead_chair='TROMBONE_1',section_harmonized=True,assignment_epoch=epoch)

        else:
            # Shout chorus: whole band participates, but Lead Trumpet still owns the
            # top perceptual line.  Saxes/trombones are linked supporting sections,
            # not independent competing melodies.
            for pos,dur in shout_hits:
                lift=2 if (cycle in (14,15) and pos>=2) else 0
                add('TRUMPET_SECTION','trumpet',b,pos,dur,root4+14+lift,82+(cycle-12), 'shout_lead',
                    foreground_owner='TRUMPET_1',arrangement_role='FOREGROUND_LEAD',
                    lead_chair='TRUMPET_1',section_harmonized=True,assignment_epoch=epoch)
                add('SAX_SECTION','alto_sax',b,pos,dur,root4+7+lift,67+(cycle-12), 'shout_coupled_saxes',
                    foreground_owner='TRUMPET_1',arrangement_role='SUPPORTING_SECTION',
                    lead_chair='ALTO_SAX_1',section_harmonized=True,assignment_epoch=epoch)
                add('TROMBONE_SECTION','trombone',b,pos,dur,root4+2+lift,62+(cycle-12), 'shout_coupled_trombones',
                    foreground_owner='TRUMPET_1',arrangement_role='SUPPORTING_SECTION',
                    lead_chair='TROMBONE_1',section_harmonized=True,assignment_epoch=epoch)
                add('SNARE_SETUP','drums_ride',b,pos,.07,38,68+(cycle-12)*2,'ensemble_hit',drum='snare',
                    foreground_owner='TRUMPET_1',arrangement_role='FOUNDATION',assignment_epoch=epoch)
            if cycle in (12,15):
                add('CRASH','drums_ride',b,0,.18,49,78,'shout_crash',drum='crash',
                    foreground_owner='TRUMPET_1',arrangement_role='FOUNDATION',assignment_epoch=epoch)

        if b%4==3:
            for j,pos in enumerate((3.0,3.333,3.667)):
                add('SNARE_SETUP','drums_ride',b,pos,.07,38,58+j*4,'section_setup',drum='snare',
                    foreground_owner=global_owner,arrangement_role='FOUNDATION',assignment_epoch=epoch)

    ev=[e for e in ev if e['start_beat'] < len(chords)*4 and e['duration_beats']>0]
    ev.sort(key=lambda x:(x['start_beat'],x['track_id'],x.get('midi',0)))
    return ev

def generate_events(name,tmpl,profile,ctx,bpm,creation_seed=0,parts=None,generation_plan=None,communication_blueprint=None):
    ev=[]; chords=ctx['harmony']['chords']; meter=ctx['meter']['numerator']; palette=list(parts) if parts is not None else resolve_genre_parts(name,tmpl,profile); v=VARIANT.get(tmpl,0)+creation_seed*3
    from genre_communication_blueprint import validate as validate_communication_blueprint
    validate_communication_blueprint(communication_blueprint,genre=name,profile_id=profile.get('profile_id'),requested_parts=palette,generation_plan=generation_plan or {})
    semantic_tags=set((generation_plan or {}).get('semantic_tags', []))
    if tmpl=='big_band':
        return _generate_big_band_events(name,profile,ctx,bpm,creation_seed,palette,generation_plan or {})
    # section-aware density
    sections=ctx['form'].get('sections',[])
    def sec_mult(bar):
        for si,s in enumerate(sections):
            if s['start_bar']-1 <= bar < s['start_bar']-1+s['length_bars']:
                return 1.0 + 0.08*si
        return 1.0
    for b,ch in enumerate(chords):
        root=ch['root']; cm=chord_midis(ch,3); density=sec_mult(b)
        # HARMONY: one of piano/guitar/synth/strings roles, rhythm depends on genre
        harmony_role=next((x for x in palette if x in ('electric_piano','piano','electric_guitar','acoustic_guitar','synth_chord','synth_pad','strings','clav','synth_pulse','synth_arp')),None)
        if harmony_role:
            if 'static_harmony' in semantic_tags or ('space' in semantic_tags and 'legato' in semantic_tags):
                positions=[0]; dur=max(1,meter-.15)
            elif 'montuno' in semantic_tags or 'clave' in semantic_tags:
                positions=[0,0.75,1.5,2.5,3.25] if meter==4 else [0,1,2]; dur=.42
            elif 'four_floor' in semantic_tags and 'offbeat' in semantic_tags:
                positions=[0.5,1.5,2.5,3.5] if meter==4 else [0,1,2]; dur=.34
            elif 'sixteenth' in semantic_tags or 'riff_vamp' in semantic_tags:
                positions=[0,.5,1.5,2,3] if meter==4 else [0,.75,1.5,2.25]; dur=.30
            elif tmpl in ('house','techno','trance','afro_house','disco'):
                positions=[0.5,1.5,2.5,3.5] if meter==4 else [0,1,2]
                dur=.34
            elif tmpl in ('bossa','salsa','mambo','cha_cha','samba','afrobeats','reggaeton'):
                positions=[0,0.75,1.5,2.5,3.25] if meter==4 else [0,1,2]
                dur=.42
            elif tmpl in ('funk',):
                positions=[0,0.5,1.25,2,2.75,3.5]; dur=.28
            elif tmpl in ('new_age','ambient_electronic','spiritual'):
                positions=[0]; dur=max(1,meter-.15)
            elif tmpl in ('swing','bebop','big_band','cool_jazz','jazz_ballad','jazz_waltz','dixieland'):
                positions=[1,3] if meter==4 else [0,2]; dur=.55
            else:
                positions=[0,2] if meter==4 else [0,1.5]; dur=.72
            for p in positions:
                for m in cm:
                    ev.append({'track_id':'HARMONY','instrument_id':harmony_role,'start_beat':b*meter+p,'duration_beats':dur,'midi':m+12,'velocity':int(60*density)+(v%7),'articulation':'genre_harmony'})
        # BASS
        bass_role=next((x for x in palette if x in ('electric_bass','double_bass','synth_bass')),None)
        if bass_role:
            root_m=midi(root,2 if bass_role!='synth_bass' else 1)
            if 'tumbao' in semantic_tags:
                poss=[.5,1.5,2.75,3.5] if meter==4 else [0,1,2]
            elif 'walking3' in semantic_tags:
                poss=list(range(meter))
            elif 'four_floor' in semantic_tags:
                poss=[0,1,2,3] if meter==4 else list(range(meter))
            elif tmpl in ('funk','afrobeats','salsa','samba','reggaeton'):
                poss=[0,.75,1.5,2.25,3.25] if meter==4 else [0,1,2]
            elif tmpl in ('swing','bebop','big_band','cool_jazz','dixieland','jazz_waltz'):
                poss=list(range(meter))
            elif tmpl in ('house','techno','trance','afro_house','disco'):
                poss=[0,1,2,3] if meter==4 else list(range(meter))
            elif tmpl in ('new_age','ambient_electronic','spiritual'):
                poss=[0]
            else:
                poss=[0,2] if meter==4 else [0,1.5]
            for j,p in enumerate(poss):
                note=root_m + ([0,7,12,7,3,5][j%6] if tmpl in ('funk','afrobeats') else (7 if j%2 else 0))
                ev.append({'track_id':'BASS','instrument_id':bass_role,'start_beat':b*meter+p,'duration_beats':.62 if len(poss)<3 else .42,'midi':note,'velocity':78+(j%2)*7,'articulation':'genre_bass'})
        # DRUMS / PERCUSSION
        if any('drums' in x for x in palette):
            d_role=next(x for x in palette if 'drums' in x)
            if 'half_time' in semantic_tags and meter==4:
                kicks=[0,2.5]; snares=[2]; hats=[0,.5,1,1.5,2,2.5,3,3.5]
            elif 'broken_beat' in semantic_tags and meter==4:
                kicks=[0,1.75,3]; snares=[1,2.5]; hats=[.5,1.5,2,3.5]
            elif 'four_floor' in semantic_tags and meter==4:
                kicks=[0,1,2,3]; snares=[1,3]; hats=[.5,1.5,2.5,3.5]
            elif tmpl in ('house','techno','trance','afro_house','disco'):
                kicks=[0,1,2,3]; snares=[1,3]; hats=[.5,1.5,2.5,3.5]
            elif tmpl=='reggaeton':
                kicks=[0,2.5]; snares=[1.5,3]; hats=[.5,1,2,3.5]
            elif tmpl in ('swing','bebop','big_band','dixieland','cool_jazz'):
                kicks=[0,2]; snares=[1.5,3]; hats=[0,1,2,3]
            elif tmpl in ('country_shuffle',):
                kicks=[0,2]; snares=[1,3]; hats=[0,0.67,1.33,2,2.67,3.33]
            elif tmpl in ('afrobeats','salsa','samba','mambo','cha_cha'):
                kicks=[0,2.25]; snares=[1,3]; hats=[.5,1.5,2.5,3.5]
            elif meter==3:
                kicks=[0]; snares=[1.5]; hats=[0,1,2]
            else:
                kicks=[0,2]; snares=[1,3]; hats=[0,.5,1,1.5,2,2.5,3,3.5]
            kicks=[p*meter/4 if meter<4 else p for p in kicks]
            snares=[p*meter/4 if meter<4 else p for p in snares]
            hats=[p*meter/4 if meter<4 else p for p in hats]
            for p in kicks: ev.append({'track_id':'KICK','instrument_id':d_role,'drum':'kick','start_beat':b*meter+p,'duration_beats':.12,'midi':36,'velocity':100,'articulation':'kick'})
            for p in snares: ev.append({'track_id':'SNARE','instrument_id':d_role,'drum':'snare','start_beat':b*meter+p,'duration_beats':.10,'midi':38,'velocity':66 if d_role=='brush_drums' else 92,'articulation':'brush_snare' if d_role=='brush_drums' else 'snare'})
            timekeeping_drum = 'ride' if d_role in ('drums_ride','brush_drums') else 'hat'
            timekeeping_midi = 51 if timekeeping_drum == 'ride' else 42
            for p in hats: ev.append({'track_id':'RIDE' if timekeeping_drum=='ride' else 'HAT','instrument_id':d_role,'drum':timekeeping_drum,'start_beat':b*meter+p,'duration_beats':.08 if timekeeping_drum=='ride' else .06,'midi':timekeeping_midi,'velocity':58+(b%2)*4 if d_role=='brush_drums' else (68+(b%2)*5 if timekeeping_drum=='ride' else 62+(b%2)*5),'articulation':'brush_ride' if d_role=='brush_drums' else timekeeping_drum})
            # Honor existing acoustic-kit profile intent at phrase boundaries without changing genre grammar.
            # Big Rusty full-kit keys: toms 41/43/45/47, crash 49, ride 51.
            if d_role in ('drums','drums_four','drums_shuffle') and meter == 4:
                if b > 0 and b % 8 == 7:
                    for j,(p,note) in enumerate(((3.0,47),(3.25,45),(3.5,43),(3.75,41))):
                        ev.append({'track_id':'TOMS','instrument_id':d_role,'drum':'tom','start_beat':b*meter+p,'duration_beats':.10,'midi':note,'velocity':78+j*4,'articulation':'tom_fill'})
                if b % 8 == 0:
                    ev.append({'track_id':'CRASH','instrument_id':d_role,'drum':'crash','start_beat':b*meter,'duration_beats':.18,'midi':49,'velocity':96,'articulation':'crash'})
        if 'conga' in palette:
            poss=[.25,1.0,1.75,2.5,3.25] if meter==4 else [.25,1.25,2.25]
            for j,p in enumerate(poss):
                ev.append({'track_id':'PERC','instrument_id':'conga','start_beat':b*meter+p,'duration_beats':.10,'midi':60+(j%3),'velocity':66+8*(j%2),'articulation':'hand_percussion'})
        # NATIVE FOLK ROLES. Keep banjo/mandolin independent rather than
        # substituting a generic mallet or guitar voice.
        if 'banjo' in palette:
            notes=[m+12 for m in cm[:3]]
            if tmpl=='bluegrass':
                # Rolling eighth-note texture; the high drone/roll identity stays
                # independent from guitar and fiddle.
                positions=[0,.5,1,1.5,2,2.5,3,3.5] if meter==4 else [i*meter/8 for i in range(8)]
                for j,p in enumerate(positions):
                    ev.append({'track_id':'BANJO','instrument_id':'banjo','start_beat':b*meter+p,'duration_beats':.28,'midi':notes[j%len(notes)]+(12 if j in (2,6) else 0),'velocity':58+(j%3)*5,'articulation':'banjo_roll'})
            else:
                for p in range(meter):
                    for note in notes:
                        ev.append({'track_id':'BANJO','instrument_id':'banjo','start_beat':b*meter+p,'duration_beats':.24,'midi':note,'velocity':54,'articulation':'banjo_strum'})
        if 'mandolin' in palette:
            notes=[m+12 for m in cm[:3]]
            positions=[1,3] if meter==4 else [1,2]
            for p in positions:
                for note in notes:
                    ev.append({'track_id':'MANDOLIN','instrument_id':'mandolin','start_beat':b*meter+p,'duration_beats':.14,'midi':note,'velocity':62,'articulation':'mandolin_chop'})

        # LATIN / WORLD AUXILIARY PERCUSSION. These identities remain separate so
        # the mixer can balance them independently instead of collapsing them into
        # one generic 'Latin kit'. MIDI note numbers follow common GM percussion
        # locations as transport hints; the target resource remains authoritative.
        if 'claves' in palette:
            positions=[0,1.5,3] if b%2==0 else [1,2]
            for p0 in positions:
                ev.append({'track_id':'CLAVES','instrument_id':'claves','start_beat':b*meter+p0,'duration_beats':.06,'midi':75,'velocity':74 if p0==0 else 66,'articulation':'clave_strike'})
        if 'bongo_family' in palette:
            positions=[0,.5,1,1.5,2,2.5,3,3.5] if meter==4 else [i*meter/6 for i in range(6)]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'BONGOS','instrument_id':'bongo_family','start_beat':b*meter+p0,'duration_beats':.07,'midi':60+(j%2),'velocity':54+(j%4)*6,'articulation':'bongo_martillo'})
        if 'cowbell' in palette:
            positions=[0,1,2,3] if meter==4 else list(range(meter))
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'COWBELL','instrument_id':'cowbell','start_beat':b*meter+p0,'duration_beats':.07,'midi':56,'velocity':60+(12 if j in (0,2) else 0),'articulation':'cowbell_pulse'})
        if 'shaker' in palette:
            positions=[i*.5 for i in range(int(meter*2))]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'SHAKER','instrument_id':'shaker','start_beat':b*meter+p0,'duration_beats':.05,'midi':82,'velocity':44+(j%2)*8,'articulation':'shaker_subdivision'})
        if 'timbales' in palette:
            # Cascara-like shell pulse with a short phrase-ending fill.
            positions=[0,.75,1.5,2.5,3.25] if meter==4 else [0,1,2]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'TIMBALES','instrument_id':'timbales','start_beat':b*meter+p0,'duration_beats':.07,'midi':65+(j%2),'velocity':58+(j%3)*6,'articulation':'timbale_cascara'})
            if meter==4 and b%8==7:
                for j,p0 in enumerate((3,3.25,3.5,3.75)):
                    ev.append({'track_id':'TIMBALES','instrument_id':'timbales','start_beat':b*meter+p0,'duration_beats':.07,'midi':65+(j%2),'velocity':72+j*4,'articulation':'timbale_fill'})

        # COUNTRY PEDAL STEEL. Preserve the steel as its own performer instead of
        # hiding it inside guitar/strings. V1 emits overlapping sustained voice-leading
        # gestures and explicit glide intent; actual pedal/knee-lever pitch transitions
        # remain the responsibility of a capable target resource.
        if 'pedal_steel_guitar' in palette:
            steel_notes=[m+12 for m in cm[:3]]
            positions=[0, meter/2] if meter>=3 else [0]
            for j,p0 in enumerate(positions):
                note=steel_notes[(b+j)%len(steel_notes)]
                ev.append({'track_id':'PEDAL_STEEL','instrument_id':'pedal_steel_guitar',
                           'start_beat':b*meter+p0,'duration_beats':max(.6,meter/2+.15),
                           'midi':note,'velocity':52+(b%3)*4,'articulation':'pedal_steel_glide_intent'})

        # SAMBA BATERIA ROLES. Keep the low surdo pulse, caixa subdivision,
        # repinique calls, tamborim timeline and agogo bell pattern independent.
        if 'surdo' in palette:
            positions=[0,1,2,3] if meter==4 else list(range(int(meter)))
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'SURDO','instrument_id':'surdo','start_beat':b*meter+p0,
                           'duration_beats':.16,'midi':36,'velocity':72+(10 if j%2 else 0),
                           'articulation':'surdo_open' if j%2 else 'surdo_muted'})
        if 'caixa' in palette:
            positions=[i*.5 for i in range(int(meter*2))]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'CAIXA','instrument_id':'caixa','start_beat':b*meter+p0,
                           'duration_beats':.06,'midi':38,'velocity':48+(j%4)*4,'articulation':'caixa_samba'})
        if 'repinique' in palette:
            if b%4==3:
                for j,p0 in enumerate((2.5,3.0,3.25,3.5,3.75) if meter==4 else (meter-1,meter-.5)):
                    ev.append({'track_id':'REPINIQUE','instrument_id':'repinique','start_beat':b*meter+p0,
                               'duration_beats':.07,'midi':64,'velocity':64+j*4,'articulation':'repinique_call'})
            else:
                for p0 in ([1,3] if meter==4 else [0,meter-1]):
                    ev.append({'track_id':'REPINIQUE','instrument_id':'repinique','start_beat':b*meter+p0,
                               'duration_beats':.07,'midi':64,'velocity':58,'articulation':'repinique_support'})
        if 'tamborim' in palette:
            positions=[0,.75,1.5,2.0,2.75,3.5] if meter==4 else [i*meter/6 for i in range(6)]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'TAMBORIM','instrument_id':'tamborim','start_beat':b*meter+p0,
                           'duration_beats':.045,'midi':65,'velocity':50+(j%3)*5,'articulation':'tamborim_teleco_teco'})
        if 'agogo_bells' in palette:
            positions=[0,1.5,2,3.25] if meter==4 else [0,meter/2,meter-.5]
            for j,p0 in enumerate(positions):
                ev.append({'track_id':'AGOGO','instrument_id':'agogo_bells','start_beat':b*meter+p0,
                           'duration_beats':.07,'midi':67+(j%2),'velocity':54+(j%2)*8,'articulation':'agogo_high_low'})

        # LEAD/MELODY: develop for at least sixteen bars before literal reuse.
        # A genre may still use short motifs; those motifs are transformed into distinct
        # bar cells so a four-bar idea cannot become a three-minute literal loop.
        lead_role=next((x for x in palette if x in ('lead_guitar','alto_sax','tenor_sax','baritone_sax','trumpet','trombone','clarinet','flute','violin','synth_lead','synth_arp')),None)
        if lead_role and (b%2==1 or tmpl in ('bebop','bluegrass','trance')):
            scale=ctx['key']['scale']
            steps=4 if (tmpl!='rock' and ('lyrical' in semantic_tags or 'space' in semantic_tags or tmpl in ('new_age','jazz_ballad','spiritual'))) else 6
            development_window=max(16,int((generation_plan or {}).get('melody_development_bars',16)))
            cells=_melody_cells(name,creation_seed,development_window,steps,energetic=tmpl in ('bebop','bluegrass','trance','rock','funk'))
            cell=cells[b % development_window]
            for j,degree in enumerate(cell):
                nn=scale[degree % len(scale)]
                octv=4 if lead_role in ('alto_sax','tenor_sax','baritone_sax','trumpet','clarinet','violin','lead_guitar') else 5
                p=(j*(meter/max(steps,1)))
                dur=.7 if (tmpl!='rock' and ('lyrical' in semantic_tags or 'legato' in semantic_tags or tmpl in ('new_age','jazz_ballad','spiritual'))) else .34
                ev.append({'track_id':'LEAD','instrument_id':lead_role,'start_beat':b*meter+p,'duration_beats':dur,'midi':midi(nn,octv),'velocity':72+(j%3)*5,'articulation':'genre_lead','melody_development_bar':b % development_window})
        # strings/choir pads if present and not already harmony role
        for r in ('strings','choir'):
            if r in palette and r!=harmony_role:
                for m in cm[:3]:
                    ev.append({'track_id':r.upper(),'instrument_id':r,'start_beat':b*meter+.02,'duration_beats':meter-.08,'midi':m+12,'velocity':42,'articulation':'sustain'})
    ev.sort(key=lambda x:(x['start_beat'],x['track_id'],x.get('midi',0)))
    # Every declared palette part is emitted by Theory, with its own track.
    # Previously only the first harmony and lead roles were selected.
    used = {event['instrument_id'] for event in ev}
    for role in palette:
        if role in used:
            continue
        for b, chord in enumerate(chords):
            notes = chord_midis(chord, 4)
            if role in ('synth_pad', 'strings', 'choir'):
                hits = [(0.02, meter - 0.08, note, 42, 'sustain') for note in notes]
            elif role in ('electric_piano', 'piano', 'electric_guitar', 'acoustic_guitar', 'clav', 'synth_chord'):
                hits = [(offset, min(0.45, meter-offset), note, 54, 'genre_harmony')
                        for offset in (0, meter/2) for note in notes]
            elif role in ('alto_sax','tenor_sax','baritone_sax','trumpet', 'trombone', 'clarinet', 'flute', 'violin', 'synth_lead', 'synth_arp', 'marimba', 'pedal_steel_guitar'):
                # Supplemental instruments answer the primary lead, without dropping their identities.
                if b % 2: continue
                hits = [(j*meter/3, min(0.5, meter/3), notes[j % len(notes)], 58, 'counterline') for j in range(3)]
            elif role in ('electric_bass', 'double_bass', 'synth_bass'):
                hits = [(0, min(0.9, meter), notes[0]-12, 76, 'support_bass')]
            elif role == 'noise_fx':
                if b % 4: continue
                hits = [(0, min(1.0, meter), 60, 35, 'noise_texture')]
            else:
                raise ValueError('UNIMPLEMENTED_PALETTE_PART::' + role)
            for offset, duration, note, velocity, articulation in hits:
                ev.append({'track_id':'SUPPORT_' + role.upper(), 'instrument_id':role,
                           'start_beat':b*meter+offset, 'duration_beats':duration,
                           'midi':note, 'velocity':velocity, 'articulation':articulation})
    # Legacy generator positions use denominator-note units. Normalize once here.
    # Scale 4-beat drum patterns into meters shorter than four denominator notes.
    normalized=[]
    factor=4/ctx['meter']['denominator']
    total=len(chords)*meter
    for event in ev:
        event=dict(event)
        if event['start_beat'] >= total:
            continue
        event['duration_beats']=min(event['duration_beats'], total-event['start_beat']) * factor
        event['start_beat'] *= factor
        if event['duration_beats'] > 0:
            normalized.append(event)
    normalized.sort(key=lambda x:(x['start_beat'],x['track_id'],x.get('midi',0)))
    return normalized



class GenreExecutionAdapter:
    def __init__(self, profile_registry_path=PROFILE_PATH, history_path=None):
        global profiles, profiles_meta_required
        data=json.loads(Path(profile_registry_path).read_text())
        profiles=data["profiles"]
        profiles_meta_required=data["universal_required_fields"]
        self.history_path = Path(history_path) if history_path is not None else OUT / 'composition_history.json'

    def _history(self):
        if not self.history_path.exists():
            return set()
        data = json.loads(self.history_path.read_text())
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            raise ValueError('INVALID_COMPOSITION_HISTORY')
        return set(data)

    def _remember(self, fingerprint):
        import os, tempfile
        history = self._history() | {fingerprint}
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.composition-history-', dir=self.history_path.parent)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(sorted(history), stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.history_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def resolve(self, genre_name:str, mode:str="normal", creation_seed:int=0):
        if genre_name not in profiles:
            raise KeyError(f"GENRE_NOT_REGISTERED::{genre_name}")
        return build_setup(genre_name, profiles[genre_name], mode, creation_seed)
    def create_new(self, genre_name:str, prior_fingerprints:set[str]|None=None, mode:str="normal", start_seed:int|None=None, max_attempts:int=64, remember:bool=True):
        prior=self._history() | set(prior_fingerprints or set())
        if start_seed is None: start_seed = len(prior)
        for seed in range(start_seed,start_seed+max_attempts):
            s=self.resolve(genre_name,mode,seed)
            if s.get("status") != "PASS": return s
            sig=[(e['track_id'],e['instrument_id'],round(e['start_beat'],4),round(e['duration_beats'],4),e.get('midi'),e.get('drum')) for e in s['events']]
            legacy_fp=h(sig)
            fp=h({'tempo_bpm':s['tempo_bpm'],'meter':s['meter'],'events':s['events']})
            s['composition_fingerprint']=fp
            s['fingerprint_schema']='AUDIBLE_PERFORMANCE_V2'
            if fp not in prior and legacy_fp not in prior:
                if remember:
                    self._remember(fp)
                s['duplicate_guard']='PASS_UNIQUE'
                return s
        return {'genre_name':genre_name,'status':'DUPLICATION_GUARD_BLOCK','attempts':max_attempts}