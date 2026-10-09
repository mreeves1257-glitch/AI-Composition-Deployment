"""ROCK MUSICAL STORY V2 — a gated song-form-aware melodic development experiment.

Works only after the preserved opt-in Rock Melody R1 author has made musical
lead phrases. V2 is a separate, default-OFF COMPOSITION layer, not sound design.

A 127-bar Rock form gives a recognizable hook an introduction, two contrasting
verses, returns, a bridge, and a closing resolution. The lead still plays ONLY
in bars that the preserved arrangement already authorized: no new tracks,
no new notes outside those bars, no instrument/sample/mixer changes.

This is an audition candidate, not proof that generated music is good art.
"""
from __future__ import annotations
from collections import defaultdict
import math
import os

from rock_melodic_author_v1 import NOTE_PC, _get_harmony

SWITCH = "AI_COMP_ROCK_STORY_V2"
BASELINE_SWITCH = "AI_COMP_ROCK_MELODY_V1"
VERSION = "ROCK_STORY_ARC_MOTIF_AND_RETURN_V2_DEFAULT_OFF"
LOW, HIGH = 59, 76

# 4:4 phrases; times in beats within EXISTING active lead bars. Degrees carry
# musical meaning; a returning hook keeps its contour/rhythm even when chords
# are different. This is deliberate musical reuse, not 6 random notes/bar.
SHAPES = {
    "VERSE_QUESTION": ((0.25,"root"),(1.25,"scale_up"),(2.0,"third"),(3.0,"fifth")),
    "VERSE_ANSWER":   ((0.0,"fifth"),(1.20,"scale_down"),(2.5,"third"),(3.1,"root")),
    "HOOK_CALL":      ((0.0,"root"),(0.75,"third"),(1.50,"fifth"),(2.75,"root")),
    "HOOK_ANSWER":    ((0.25,"fifth"),(1.25,"scale_up"),(2.25,"third"),(3.00,"root")),
    "HOOK_RESOLVE":   ((0.0,"fifth"),(1.25,"third"),(2.75,"root")),
    "VERSE_VARIANT":  ((0.5,"third"),(1.5,"root"),(2.25,"scale_up"),(3.0,"fifth")),
    "BRIDGE_QUESTION":((0.25,"fifth"),(1.25,"third"),(2.50,"root")),
    "BRIDGE_ANSWER":  ((0.0,"third"),(1.50,"scale_down"),(2.75,"root")),
    "OUTRO":          ((0.0,"fifth"),(1.25,"third"),(2.75,"root")),
}

def _section(bar: int, total_bars: int) -> str:
    # Adapt to the preserved normal Rock length without inventing length.
    if bar < 8: return "INTRO"
    if bar < 24: return "VERSE"
    if bar < 40: return "HOOK"
    if bar < 56: return "VERSE_VARIATION"
    if bar < 72: return "HOOK_RETURN"
    if bar < 88: return "BRIDGE"
    if bar < 104: return "FINAL_HOOK"
    if bar >= max(104,total_bars-16): return "OUTRO"
    return "VERSE_VARIATION"

def _shape(section, bar):
    phrase_slot=bar%8
    answer=phrase_slot in (3,7)
    if section == "INTRO": return "VERSE_QUESTION" if not answer else "VERSE_ANSWER"
    if section == "VERSE": return "VERSE_ANSWER" if answer else "VERSE_QUESTION"
    if section == "VERSE_VARIATION": return "VERSE_ANSWER" if answer else "VERSE_VARIANT"
    if section == "BRIDGE": return "BRIDGE_ANSWER" if answer else "BRIDGE_QUESTION"
    if section == "OUTRO": return "OUTRO"
    # The HOOK_CALL and HOOK_ANSWER rhythmic signatures return in the final
    # chorus, with the same shape but harmonized to the current chord.
    if phrase_slot==7: return "HOOK_RESOLVE"
    return "HOOK_ANSWER" if answer else "HOOK_CALL"

def _closest(pcset, desired, previous, bias=0):
    # Prioritize voice-leading and playable guitar notes; avoid arbitrary
    # repeated pitches when a small step into another chord tone is possible.
    values=[note for note in range(LOW,HIGH+1) if note%12 in pcset]
    if not values: raise ValueError("NO_GUITAR_CHORD_TONE_WITHIN_RANGE")
    return min(values,key=lambda n:(abs(n-desired)+.23*abs(n-previous) if previous is not None else abs(n-desired),
                                   abs(n-(67+bias)),n))

def _neighbor(scale_pc, anchor, sign):
    values=[n for n in range(LOW,HIGH+1) if n%12 in scale_pc]
    direction=[n for n in values if 0 < (n-anchor)*sign <=4]
    if direction: return min(direction,key=lambda n:abs(n-anchor))
    return _closest(scale_pc,anchor+sign*2,anchor)

def compose_rock_story(events,ctx,creation_seed=0,*,active=None):
    """Retell melody via 8-bar theme-answer, hook recall and contrasting bridge.

    Must be explicitly enabled AND existing Melody R1 enabled; no unsafe
    backwards activation. If a chord or other context is unsupported, return
    all event data unchanged instead of silently inferring another harmony.
    """
    original=[dict(e) for e in events]
    if active is None:
        active=os.environ.get(SWITCH,"")=="1"
    if active is not True or os.environ.get(BASELINE_SWITCH,"")!="1":
        return original
    harmony=_get_harmony(ctx)
    if harmony is None: return original
    chords,scale_pc=harmony
    if len(chords)<32: return original
    bar_groups=defaultdict(list)
    for i,e in enumerate(original):
        if str(e.get("track_id","")).upper()=="LEAD" and str(e.get("instrument_id","")).lower() in ("lead_guitar","electric_guitar"):
            start=float(e.get("start_beat",-1))
            if not math.isfinite(start) or start<0: return original
            bar=int(start//4)
            if bar >= len(chords): return original
            bar_groups[bar].append(i)
    if not bar_groups: return original
    staged={}
    removed=set()
    prev_pitch=None
    for bar in sorted(bar_groups):
        chord=chords[bar]
        try:
            chord_pc={NOTE_PC[name] for name in chord["notes"]}
            root_pc=NOTE_PC[chord["root"]]
        except (KeyError,TypeError):
            return original
        if len(chord_pc)<3 or root_pc not in chord_pc: return original
        indices=sorted(bar_groups[bar],key=lambda i:float(original[i]["start_beat"]))
        family=_section(bar,len(chords))
        shape_id=_shape(family,bar)
        shape=list(SHAPES[shape_id])
        # No more notes than existing R1 in an active bar, and no new lead
        # bars: any short bar retains its original voicing if not adequate.
        if len(indices)<len(shape): continue
        base=original[indices[0]]
        register_shift=(2 if family in ("HOOK","HOOK_RETURN","FINAL_HOOK") else
                        -2 if family=="BRIDGE" else 0)
        # The old R1 source is a guardrail for where the phrase can be played;
        # new melodic destinations intentionally follow the actual harmony.
        chord_root=_closest({root_pc},67+register_shift,prev_pitch,register_shift)
        prev=prev_pitch
        for j,(position,degree) in enumerate(shape):
            if degree=="root":
                pitch=_closest({root_pc},chord_root if j==0 else (prev if prev is not None else chord_root),
                               prev,register_shift)
            elif degree=="third":
                # Use triadic third/fifth based on distance above the chord root.
                ascending=sorted(chord_pc,key=lambda x:(x-root_pc)%12)
                third_pc=ascending[1]
                pitch=_closest({third_pc},(prev if prev is not None else chord_root)+
                               (2 if family in ("HOOK","HOOK_RETURN","FINAL_HOOK") else 1),prev,register_shift)
            elif degree=="fifth":
                ascending=sorted(chord_pc,key=lambda x:(x-root_pc)%12)
                fifth_pc=ascending[2]
                pitch=_closest({fifth_pc},(prev if prev is not None else chord_root)+
                               (3 if family not in ("BRIDGE","OUTRO") else -1),prev,register_shift)
            elif degree in ("scale_up","scale_down"):
                sign=1 if degree=="scale_up" else -1
                anchor=prev if prev is not None else chord_root
                pitch=_neighbor(scale_pc,anchor,sign)
            else:
                raise AssertionError("UNKNOWN_MELODIC_DEGREE")
            # Distinct sections have perceptible density and arrival contrast,
            # not a volume effect applied later in the recorded sound/mixer.
            after=shape[j+1][0] if j+1<len(shape) else 3.9
            gap=after-position
            if gap<=0: raise AssertionError("NON_MONOTONIC_PHRASE")
            is_last=j==len(shape)-1
            duration=max(.18,min(1.65,gap*(.86 if is_last else .74)))
            strength=(1.04 if j==0 else 0.92 if j%2 else 1.00)
            lift=(1.09 if family in ("HOOK","HOOK_RETURN","FINAL_HOOK") else
                  .91 if family in ("BRIDGE","OUTRO") else 1)
            note=dict(base)
            note.update(
                start_beat=round(bar*4+position,6),
                duration_beats=round(duration,6),
                midi=int(pitch),
                velocity=int(max(45,min(112,round(float(base["velocity"])*strength*lift)))),
                articulation="genre_lead",
            )
            staged[indices[j]]=note
            prev=pitch
        removed.update(indices[len(shape):])
        prev_pitch=prev
    # For unchanged bars retain exact original R1 notes; for revised bars
    # remove surplus R1 notes and put new notes back in chronological order.
    result=[staged.get(i,e) for i,e in enumerate(original) if i not in removed]
    result.sort(key=lambda e:(float(e.get("start_beat",0)),
                              str(e.get("track_id","")),int(e.get("midi",0))))
    return result
