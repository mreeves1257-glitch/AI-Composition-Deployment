"""ROCK GROOVE MOTION — opt-in composition, not an instrument/SFZ change.

The verified Rock score (127 bars / 145 BPM) plays the same quarter-note HAT
on every beat and kick/snare backbeat nearly everywhere. Pure meter is not an
authored groove. This RESEARCH layer gives hats patterned eighths and restrained
sixteenth turnarounds, and moves a 2.5-beat kick to an actual bass syncopation
on 2.25 only when the source bass is there.

The existing deduplicated drum score is REQUIRED. Never activate on the
legacy doubled-sample score. No samples, track mappings, mixer parameters,
global BPM, bass notes, lead, or chord guitar changed. OFF unless both
AI_COMP_ROCK_DRUM_COLLISION_V1=1 and AI_COMP_ROCK_GROOVE_MOTION_V1=1.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
import math
import os

SWITCH = "AI_COMP_ROCK_GROOVE_MOTION_V1"
REQUIRED_GATE = "AI_COMP_ROCK_DRUM_COLLISION_V1"
VERSION = "ROCK_GROOVE_EIGHTH_SIXTEENTH_BASS_SYNC_RESEARCH_V1"
HAT = ("HAT","hi_hat")
KICK = ("KICK","kick_drum_rock")
BASS_IDS = frozenset(("electric_bass_guitar","electric_bass"))
# 8-bar motives: chorus-like sections have extra offbeats; bars 3/7 add
# a short sixteenth turnaround. There are intentional gaps: not a constant
# unswerving roll of eighths or sixteenths.
HAT_OFFBEATS = (
    (.5,1.5,3.5),
    (.5,1.5,2.5,3.5),
    (.5,1.5,2.5,3.5),
    (.5,1.5,2.5,3.25,3.5,3.75),
    (.5,2.5,3.5),
    (.5,1.5,2.5,3.5),
    (.5,1.5,2.5,3.5),
    (.5,1.5,2.5,3.25,3.5,3.75),
)

def _beat(x):
    val = float(Fraction(str(x)))
    if not math.isfinite(val):
        raise ValueError("INVALID_BEAT")
    return round(val,6)

def apply_rock_groove(events, genre, *, enabled=None):
    """An explicit authored drum-score copy; fail closed for unknown geometry."""
    copied=[dict(e) for e in events]
    if enabled is None:
        enabled=os.environ.get(SWITCH,"")=="1"
    if (enabled is not True or str(genre).upper()!="ROCK"
            or os.environ.get(REQUIRED_GATE,"")!="1"):
        return copied
    hats=defaultdict(list)
    kicks=defaultdict(list)
    bass=defaultdict(list)
    for i, e in enumerate(copied):
        track=str(e.get("track_id","")).upper()
        inst=str(e.get("instrument_id","")).lower()
        if track not in ("HAT","KICK","BASS"):
            continue
        start=_beat(e["start_beat"])
        bar=int(start//4)
        local=round(start-bar*4,6)
        if track=="HAT" and inst==HAT[1]:
            hats[bar].append((i,local))
        elif track=="KICK" and inst==KICK[1]:
            kicks[bar].append((i,local))
        elif track=="BASS" and inst in BASS_IDS:
            bass[bar].append(local)
    existing=set()
    for bar, current in hats.items():
        existing.update((bar,loc) for _,loc in current)
    additions=[]
    for bar,current in sorted(hats.items()):
        if not current:
            continue
        # Reuse authorized 42-key HAT (recorded Big Rusty sound). Choose a
        # real source hat of that bar and keep all its SFZ/drum routing fields.
        anchors=[(idx,loc) for idx,loc in current if copied[idx].get("midi")==42]
        if not anchors:
            continue
        for offset in HAT_OFFBEATS[bar%8]:
            if (bar,offset) in existing:
                continue
            # Strictly within the same bar and before the next phrase boundary.
            idx,_=min(anchors,key=lambda pair:abs(pair[1]-offset))
            source=copied[idx]
            velocity=int(source.get("velocity",0))
            if velocity<1 or velocity>127:
                continue
            new=dict(source)
            new["start_beat"]=round(bar*4+offset,6)
            new["duration_beats"]=min(float(source.get("duration_beats",.1)),.15)
            # Offbeat hats lightly carry subdivision instead of masking vocals
            # or adding an equally heavy downbeat on every eighth/sixteenth.
            new["velocity"]=max(25,min(62,round(velocity*(.68 if offset%0.5==0 else .56))))
            # Keep the ORIGINAL recorded program's articulation contract.
            # The note's onset is the rhythmic instruction; the sample bank
            # never needs to understand a new articulation tag.
            new["articulation"]=source.get("articulation","hat")
            additions.append(new)
            existing.add((bar,offset))
    # Bass-locked pickup: at bars where existing bass hits 2.25 and there is
    # a programmed extra kick at 2.5, shift ONLY that extra kick to the bass
    # onset, retaining all other fields. Do not move anchors 1 and 3.
    moved=set()
    for bar,notes in kicks.items():
        if 2.25 not in set(bass.get(bar,())):
            continue
        if any(abs(pos-2.25)<1e-5 for _,pos in notes):
            continue
        choices=[idx for idx,local in notes if local==2.5]
        if len(choices)==1:
            idx=choices[0]
            if str(copied[idx].get("articulation","")).lower() in ("rock_kick","kick"):
                copied[idx]["start_beat"]=round(bar*4+2.25,6)
                moved.add(idx)
    out=copied+additions
    out.sort(key=lambda e:(float(e.get("start_beat",0)),
                           str(e.get("track_id","")),int(e.get("midi",0))))
    return out
