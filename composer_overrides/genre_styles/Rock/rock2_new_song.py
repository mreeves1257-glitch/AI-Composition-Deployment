"""New, independent Rock songs — drive the arrangement from upstream Rock2 MMA.

This is a development-only Rock-specific event author, not a claim that MMA's
entire general interpreter runs. The original unmodified GPL-2.0 Rock2 style
is parsed at runtime for exact source kick/snare/hat/bass/guitar rhythmic
instructions, then mapped to the project's original REAL recorded instruments.

The old universal groove and 127-bar tune are NEVER used by this author.
Other genre scores, original SFZ recordings, direct stereo mix, and protected
checkpoints are unchanged. No fake/sample-replacement instrument is allowed.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re
from typing import Any

SOURCE=Path(__file__).resolve().with_name("EXTERNAL_MMA_ROCK2_UPSTREAM_REFERENCE.mma")
STYLE="MMA_ROCK2_HARD_DRIVING_SOURCE_DERIVED_V1"
PC={"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,
    "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}
PARTS=("Drum-KickDrum1","Drum-SnareDrum1","Drum-ClosedHiHat",
       "Bass-9","Chord-6","Chord-7")
ROLES={
    "BASS":"electric_bass_guitar",
    "HARMONY":"electric_guitar",
    "LEAD":"lead_guitar",
    "KEYS":"electric_piano",
    "KICK":"kick_drum_rock",
    "SNARE":"snare_drum",
    "HAT":"hi_hat",
    "TOMS":"tom_tom",
    "CRASH":"crash_cymbal",
    "RIDE":"ride_cymbal",
}
DRUM_PITCH={"KICK":36,"SNARE":38,"HAT":42,"TOMS":45,"CRASH":49,"RIDE":51}

def _rand(seed,*names):
    encoded=":".join([str(seed),*(str(x) for x in names)])
    return int.from_bytes(hashlib.sha256(encoded.encode()).digest()[:8],"big")

def choose_new_song_shape(seed:int)->dict:
    """Never hardwire all fresh Rock compositions to 145 BPM and 127 bars."""
    tempo=[117,124,131,139,143][_rand(seed,"tempo")%5]
    bars=[72,80,88,96,104][_rand(seed,"length")%5]
    keypart=_rand(seed,"phrases")
    return {"style":STYLE,"tempo_bpm":tempo,"bars":bars,
            "intro_bars":4,"section_bars":16,
            "signature":hashlib.sha256(str(seed).encode()).hexdigest()[:12],
            "riff_variant":keypart%4}

def read_original_rock2()->dict:
    text=SOURCE.read_text(encoding="utf-8")
    if "Rock2 (041). Hard driving rock beat." not in text or "DefGroove Rock2" not in text:
        raise ValueError("WRONG_UPSTREAM_ROCK_MUSICAL_SOURCE")
    if "SeqSize 4" not in text or "Time 4" not in text:
        raise ValueError("ROCK2_4_4_MUSICAL_STRUCTURE_MISSING")
    out={}
    for part in PARTS:
        segment=re.search(r"(?m)^Begin "+re.escape(part)+r"\s*\n(.*?)^End\s*$",text,re.S)
        if not segment:
            raise ValueError("MMA_ROCK2_REQUIRED_PART_MISSING:"+part)
        body=segment.group(1)
        seq=re.search(r"(?m)^\s*Sequence\s+(.*)$",body,re.S)
        if not seq:
            raise ValueError("MMA_ROCK2_SEQUENCE_NOT_FOUND:"+part)
        literal=seq.group(1).splitlines()
        # Rock2's main pattern is all literal brace sequences; no complex
        # MMA pseudocode, aliases, random pattern substitutions or fake notes.
        patterns=re.findall(r"\{([^{}]+)\}", " ".join(literal))
        if not patterns:
            raise ValueError("MMA_ROCK2_LITERAL_PATTERN_REQUIRED:"+part)
        parsed=[]
        for pattern in patterns:
            hits=[]
            for term in pattern.split(";"):
                bits=term.replace(chr(92), " ").strip().split()  # MMA line continuation
                if not bits:
                    continue
                if any(not re.fullmatch(r"(?:\d+\.?\d*|\.\d+)",z) for z in bits):
                    raise ValueError("ROCK2_UNSUPPORTED_PATTERN_TOKEN:"+part+":"+repr(bits))
                position=float(bits[0])-1.0
                if not 0<=position<4:
                    raise ValueError("ROCK2_INVALID_HIT_POSITION:"+part)
                duration=float(bits[1])
                if part.startswith("Drum-"):
                    if len(bits)!=3 or duration!=0:
                        raise ValueError("ROCK2_DRUM_TOKEN_WRONG:"+part)
                    duration=0.12
                    degree=0
                    velocity=int(bits[2])
                elif part=="Bass-9":
                    if len(bits)!=4 or duration<=0:
                        raise ValueError("ROCK2_BASS_TOKEN_WRONG")
                    degree=int(bits[2])
                    duration=4.0/duration
                    velocity=int(bits[3])
                else:
                    if len(bits)!=3 or duration<0:
                        raise ValueError("ROCK2_GUITAR_CHORD_TOKEN_WRONG")
                    degree=0
                    duration=4.0/duration if duration>0 else 0.09
                    velocity=int(bits[2])
                hits.append((position,duration,degree,velocity))
            if not hits:
                raise ValueError("EMPTY_MMA_ROCK2_PATTERN:"+part)
            parsed.append(tuple(hits))
        out[part]=tuple(parsed)
    if set(out)!=set(PARTS):
        raise ValueError("MMA_ROCK2_MISSING_PARTS")
    return out

def _pitch_at_pc(pitch_class, target, minimum, maximum):
    values=[i for i in range(minimum,maximum+1) if i%12==pitch_class]
    if not values:
        raise ValueError("ORIGINAL_RECORDED_INSTRUMENT_RANGE_EMPTY")
    return min(values,key=lambda p:(abs(p-target),p))

def _chord_data(chord):
    pcs=[PC[x] for x in chord["notes"] if x in PC]
    root=PC.get(chord["root"])
    if root is None or len(set(pcs))<3:
        raise ValueError("ROCK2_CHORD_CONTEXT_NOT_TRIAD")
    return root,list(dict.fromkeys(pcs))

def _event(track,beat,length,note,velocity,articulation):
    if not math.isfinite(beat) or beat<0 or length<=0 or not 1<=velocity<=127:
        raise ValueError("MMA_ROCK2_OUT_OF_RANGE_PERFORMANCE")
    return {
        "track_id":track,"instrument_id":ROLES[track],
        "start_beat":round(beat,6),"duration_beats":round(length,6),
        "midi":int(note),"velocity":int(velocity),"articulation":articulation
    }

def _choose_lead_pitch(pcs,root,target):
    return _pitch_at_pc(
        min(pcs,key=lambda pc:min(abs((target-pc)%12),abs((pc-target)%12))),
        target,59,76)

def compose_new_rock_song(ctx:dict[str,Any],creation_seed:int)->list[dict[str,Any]]:
    """Musically new SONG using Rock2 source, not altered retired melody.

    Deliberately different section sizes, harmony, pace, offbeat guitar/bass,
    expressive lead questions/answers and Wurlitzer keyboard breaks.
    Repeated same-seed score is allowed for an explicit A/B diagnostic; normal
    composition requests choose fresh seeds automatically.
    """
    source=read_original_rock2()
    shape=choose_new_song_shape(creation_seed)
    bars=shape["bars"]
    if ctx.get("meter",{}).get("numerator")!=4 or ctx["meter"]["denominator"]!=4:
        raise ValueError("ROCK2_REQUIRES_4_4")
    chords=ctx["harmony"]["chords"]
    if len(chords)!=bars:
        raise ValueError("SONG_FORM_AND_THEORY_CHORD_COUNT_MISMATCH")
    scale=[PC[x] for x in ctx["key"]["scale"] if x in PC]
    if len(set(scale))!=7:
        raise ValueError("INVALID_SEVEN_NOTE_KEY")
    result=[]
    for bar in range(bars):
        root,tones=_chord_data(chords[bar])
        start=bar*4.0
        section=bar//16
        local=bar%16
        intro=bar<4
        ending=bar>=bars-2
        section_kind=(section+shape["riff_variant"])%4
        heavy=(section_kind in (1,3) and not intro)
        turnaround=local==15 and not ending
        # Rock2 independently moves the kick OFF the alternating oompa
        # quarter-note pattern. NO overlay on top of legacy drum events.
        for pos,_,degree,vel in source["Drum-KickDrum1"][(bar+section_kind)%len(source["Drum-KickDrum1"])]:
            if intro and pos>=2.5:continue
            if ending and pos>2.5:continue
            result.append(_event("KICK",start+pos,.11,36,min(120,int(vel*(1.02 if heavy else .94))),"source_rock2_kick"))
        # Backbeat snare and distinct eighth-note hats from published Rock2.
        for pos,_,_,vel in source["Drum-SnareDrum1"][0]:
            if intro and bar<2:continue
            result.append(_event("SNARE",start+pos,.12,38,vel+(4 if heavy else 0),"source_rock2_snare"))
        for pos,_,_,vel in source["Drum-ClosedHiHat"][0]:
            if intro and bar==0 and int(pos*2)%2:continue
            if section_kind==2 and pos in (1.5,3.5):continue
            result.append(_event("HAT",start+pos,.10,42,max(48,vel+(8 if heavy else 2)),"source_rock2_hat"))
        # Source Rock2 bass phrase contains rests, offbeats, and root/fifth/
        # sixth motions, rather than repetitive hits on 1 and 3.
        for pos,duration,degree,vel in source["Bass-9"][0]:
            if intro and bar==0 and pos not in (0.0,2.0):continue
            pitch_class=(root if degree==1 else
                         tones[2] if degree==5 else
                         scale[(scale.index(root)+5)%7] if root in scale
                         else (root+9)%12)
            pitch=_pitch_at_pc(pitch_class,41+((section+shape["riff_variant"])%2)*2,35,53)
            length=min(1.15,max(.22,duration*.88))
            if ending and pos>=2:continue
            result.append(_event("BASS",start+pos,length,pitch,min(110,vel),"source_rock2_bass"))
        # Two original guitar strum patterns used as alternate SECTION gestures;
        # chord attacks form a single HARMONY role with native Shinyguitar WAV.
        rhythm=source["Chord-6"][((bar//4)+section_kind+shape["riff_variant"])%len(source["Chord-6"])]
        mute=source["Chord-7"][((bar//4)+section_kind)%len(source["Chord-7"])]
        chosen=mute if section_kind==2 else rhythm
        for j,(pos,duration,_,vel) in enumerate(chosen):
            if intro and pos>2.5 and bar<2:continue
            if ending and pos>1.5:continue
            if section_kind==0 and j%4==2:continue
            # sampled-electric-guitar chord registers; selected chord tones
            # stay in playable, compact guitar voicings.
            chord_notes=[_pitch_at_pc(t,58+(i*3)+(section_kind%2)*2,52,70)
                         for i,t in enumerate(tones[:3])]
            for i,note in enumerate(dict.fromkeys(chord_notes)):
                dur=min(1.20,max(.14,duration*.84))
                result.append(_event("HARMONY",start+pos+i*.025,dur,
                                     note,max(60,min(110,int(vel*.86))),
                                     "rock2_rhythm_guitar_strum"))
        # Genuinely different fourth *pitched* recorded instrument:
        # Greg Sullivan sampled Wurlitzer plays syncopated answers in selected
        # sections, never mimicking bass line or replacing guitar.
        if bar>=4 and not ending and (section_kind in (0,2) or bar%8 in (6,7)):
            positions=((1.5,3.5) if section_kind==0 else (2.5,))
            for pos in positions:
                for i,t in enumerate(tones[:3]):
                    note=_pitch_at_pc(t,62+i*3,58,76)
                    result.append(_event("KEYS",start+pos+i*.012,
                                         .40 if section_kind==0 else .70,note,
                                         66+(i%2)*5,"rock2_wurlitzer_answer"))
        # A new melodic conversation, NOT the old lead seed. Two-bar phrase
        # motives vary with seed, harmonies, sections, and rests.
        if bar>=4 and not ending:
            phrase=bar//4
            style_number=_rand(creation_seed,"melodic_style",phrase//2)%6
            solo_allowed=(section_kind in (1,3) or bar%8 in (2,3,6,7))
            if solo_allowed and (bar%8)!=7:
                patterns=(
                    ((.0,0),(.75,1),(1.5,2),(3.0,1)),
                    ((.5,2),(1.0,1),(2.25,0),(3.0,2)),
                    ((.0,1),(1.5,2),(2.0,0),(2.75,1)),
                    ((.5,0),(1.25,2),(2.25,1),(3.25,0)),
                    ((.0,0),(.75,1),(2.0,2),(3.25,0)),
                    ((1.0,2),(1.75,0),(2.5,1),(3.25,0)),
                )
                motif=patterns[(style_number+bar//2)%len(patterns)]
                base_pitch=65+(_rand(creation_seed,phrase,"register")%5)-2
                for j,(pos,degree) in enumerate(motif):
                    # chord anchors; stepwise diatonic movement between them.
                    target=base_pitch+(degree-1)*3
                    pcs=tones if j in (0,len(motif)-1) else scale
                    note=_pitch_at_pc(pcs[(_rand(creation_seed,"lead",phrase,j)+degree)%len(pcs)],
                                      target,59,76)
                    nxt=motif[j+1][0] if j+1<len(motif) else 3.8
                    duration=min(1.25,max(.20,(nxt-pos)*(.78 if j<len(motif)-1 else .92)))
                    result.append(_event("LEAD",start+pos,duration,note,
                                         79+(_rand(creation_seed,bar,j)%21),
                                         "rock2_melodic_answer"))
        if turnaround:
            for off,note in ((2.5,47),(3.0,45),(3.5,43)):
                result.append(_event("TOMS",start+off,.12,note,83+int(off*4),"rock2_section_fill"))
        if bar in (4,) or (bar%16==0 and bar>0) or ending:
            result.append(_event("CRASH",start,.22,49,85,"rock2_section_crash"))
        if section_kind==3 and local in (4,5,6,7):
            for pos in (0.0,1.0,2.0,3.0):
                result.append(_event("RIDE",start+pos,.12,51,65,"rock2_ride_lift"))
    result.sort(key=lambda e:(e["start_beat"],e["track_id"],e["midi"]))
    # No duplicate identical drum hits, no illegal overlaps outside song,
    # and no fallback to the retired tempo/form/groove.
    last={}
    for e in result:
        if e["start_beat"]+e["duration_beats"]>bars*4+.00001:
            raise ValueError("ROCK2_NOTE_BEYOND_END")
        if e["track_id"] in DRUM_PITCH:
            key=(e["track_id"],e["start_beat"],e["midi"])
            if key in last:
                raise ValueError("DUPLICATE_ROCK_DRUM_HIT:"+str(key))
            last[key]=True
    for required in ROLES:
        if required not in {e["track_id"] for e in result}:
            raise ValueError("NEW_ROCK_INSTRUMENT_ROLE_MISSING:"+required)
    return result
