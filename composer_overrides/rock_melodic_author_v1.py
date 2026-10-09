"""ROCK MELODY V1 — opt-in harmonic, motivic melody composer.

Moves musical note selection back into composition, leaving approved real
Shinyguitar samples, performance interpreter, MIDI routes, source drum/bass
parts, standalone 3D mixer and genre family structure completely unchanged.

Disabled by default. The existing 127-bar Rock recording is canonical until
this new composition is heard and approved. This is a musical candidate, not a
claim that subjective quality can be proven by numeric metrics.
"""
from __future__ import annotations

from collections import defaultdict
import math
import os
from typing import Any

FEATURE = "AI_COMP_ROCK_MELODY_V1"
VERSION = "ROCK_MELODIC_AUTHOR_V1_RESEARCH_DISABLED_DEFAULT"
NOTE_PC = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,
           "F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}
MIN_PITCH,MAX_PITCH = 59,76

# Same recurring musical motifs are transformed harmonically and by section.
# Entries are (beat position, diatonic contour step), not random MIDI notes.
MOTIFS = {
    "A_CALL":     ((0.00,0),(0.75,1),(1.50,3),(2.50,1)),
    "A_ANSWER":   ((0.00,2),(1.00,1),(1.75,0),(2.75,-1)),
    "B_LIFT":     ((0.50,0),(1.00,2),(1.75,3),(2.50,1),(3.00,0)),
    "A_REPRISE":  ((0.00,0),(0.75,1),(1.50,3),(2.25,2),(3.00,0)),
    "CADENCE":    ((0.00,2),(1.00,1),(2.25,0)),
}
# Main melody uses the older composition's silence/entry decisions; a bar
# without a lead is intentionally not populated by this composer.
def enabled() -> bool:
    return os.environ.get(FEATURE,"") == "1"

def _pitch_candidates(pcs, low=MIN_PITCH, high=MAX_PITCH):
    return [m for m in range(low,high+1) if m % 12 in pcs]

def _near(pcs, target, previous=None):
    pitches=_pitch_candidates(pcs)
    if not pitches:
        raise ValueError("EMPTY_ALLOWED_SCALE")
    return min(pitches,key=lambda p:(abs(p-target) + (0.16*abs(p-previous) if previous is not None else 0),
                                   abs(p-66),p))

def _nearest_diatonic(scale_pcs, target, reference):
    pitches=_pitch_candidates(scale_pcs)
    return min(pitches,key=lambda p:(abs(p-target),abs(p-reference),p))

def _motif_for_bar(bar, section, seed):
    local=bar%8
    if local==7:
        return "CADENCE" if (bar//8)%2 else "A_ANSWER"
    if local in (5,1):
        return "A_REPRISE" if section%3==2 else "A_CALL"
    if local==3:
        return "B_LIFT"
    return ("A_CALL","A_ANSWER","B_LIFT","A_REPRISE")[((bar//2)+seed)%4]

def _get_harmony(ctx):
    try:
        meter=ctx["meter"]
        beats=float(meter["numerator"])*4/float(meter["denominator"])
        if abs(beats-4)>1e-9:
            return None
        chords=ctx["harmony"]["chords"]
        scale=ctx["key"]["scale"]
        scale_pcs={NOTE_PC[x] for x in scale}
        if len(scale_pcs)!=7 or not chords:
            return None
        return chords,scale_pcs
    except (KeyError,TypeError,ValueError):
        return None

def compose_rock_melody(
    events:list[dict[str,Any]],ctx:dict[str,Any],creation_seed:int=0,
    *,active:bool|None=None
) -> list[dict[str,Any]]:
    """Re-author ONLY existing Rock lead bars as chord-responsive phrases.

    Disabled/missing source context -> an unchanged copy. When enabled:
    - preserve where lead already enters/rests; build motifs, not random notes
    - select chord tones on phrase anchors and resolutions
    - use scale passing tones for melodic movement, not arbitrary chromatic hits
    - vary contour / rhythmic accents between call, answer, lift and cadence
    - leave full bass, drum kit, rhythm guitar, tempo and all sample bindings as is
    - stop phrase notes before next note and within the measure
    """
    if active is None:
        active=enabled()
    original=[dict(x) for x in events]
    if active is not True:
        return original
    harmony=_get_harmony(ctx)
    if harmony is None:
        return original
    chords,scale_pcs=harmony
    groups=defaultdict(list)
    for e in original:
        if str(e.get("track_id","")).upper()!="LEAD" or \
           str(e.get("instrument_id","")).lower() not in ("lead_guitar","electric_guitar"):
            continue
        beat=float(e["start_beat"])
        if not math.isfinite(beat):
            return original
        bar=int(beat//4)
        if 0<=bar<len(chords):
            groups[bar].append(e)
    if not groups:
        return original

    # No new bars with a lead; no changes to original bars where lead is silent.
    solo=[]
    previous_pitch=None
    for bar in sorted(groups):
        chord=chords[bar]
        chord_names=chord.get("notes",[])
        chord_pcs={NOTE_PC[name] for name in chord_names if name in NOTE_PC}
        if len(chord_pcs)<3:
            return original
        root_name=chord.get("root")
        root_pc=NOTE_PC.get(root_name)
        if root_pc is None:
            return original
        section=bar//16
        motif_id=_motif_for_bar(bar,section,int(creation_seed))
        motif=MOTIFS[motif_id]
        base=sorted(groups[bar],key=lambda e:float(e["start_beat"]))[0]
        # Register is intentionally the demonstrated Shinyguitar range;
        # prefer smooth movement from the prior phrase but allow a section lift.
        midpoint=64+(2 if section%4==2 else 0)
        root=_near({root_pc},midpoint if previous_pitch is None else previous_pitch,previous_pitch)
        # Cadential final arrival is the harmonic root; nonfinal passing
        # tones can be other degrees of the current seven-note scale.
        contour_sign=-1 if section%4==3 else 1
        pitches=[]
        for j,(position,degree) in enumerate(motif):
            final=j==len(motif)-1
            if j==0:
                pitch=_near(chord_pcs,root+(2 if motif_id=="B_LIFT" else 0),previous_pitch)
            elif final:
                # A phrase destination on a real chord tone, preferably the root
                # in cadence/reprise. No fixed high octave jumps.
                target=(root if motif_id in ("CADENCE","A_REPRISE") else
                        pitches[-1]+(-1 if contour_sign>0 else 1))
                allowed={root_pc} if motif_id in ("CADENCE","A_REPRISE") else chord_pcs
                pitch=_near(allowed,target,pitches[-1])
            else:
                target=root+contour_sign*degree*2
                if pitches:
                    target=round(.65*target+.35*pitches[-1])
                pitch=_nearest_diatonic(scale_pcs,target,pitches[-1] if pitches else root)
            pitches.append(pitch)
        for j,((position,_),pitch) in enumerate(zip(motif,pitches)):
            following=motif[j+1][0] if j+1<len(motif) else 3.90
            distance=following-position
            if distance<=0:
                raise ValueError("NON_MONOTONIC_MELODY_MOTIF")
            # Leave air at phrase ends. Never force a continuous sheet of sound.
            length=min(1.45,max(.19,distance*(.89 if j==len(motif)-1 else .79)))
            accent=(1.02,.91,1.09,.96,.97)[j%5]
            role_intensity=(.96,1.00,1.08,.91)[section%4]
            clone=dict(base)
            clone["start_beat"]=round(bar*4+position,6)
            clone["duration_beats"]=round(length,6)
            clone["midi"]=pitch
            clone["velocity"]=max(50,min(115,round(float(base["velocity"])*accent*role_intensity)))
            clone["articulation"]="genre_lead"
            solo.append(clone)
        previous_pitch=pitches[-1]
    result=[e for e in original if not (str(e.get("track_id","")).upper()=="LEAD" and
                            str(e.get("instrument_id","")).lower() in ("lead_guitar","electric_guitar"))]
    result+=solo
    result.sort(key=lambda e:(float(e.get("start_beat",0)),str(e.get("track_id","")),int(e.get("midi") or 0)))
    return result
