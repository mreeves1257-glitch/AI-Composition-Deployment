"""Swing-only original recorded trumpet note-range crosswalk.

NOT a new genre, arranger style, tone setting, envelope, source replacement
or mix adjustment. Preserve the original Swing Composer MIDI rhythm, dynamics,
chord-tone pitch class, section, and all accompaniment notes; only transpose
physically unplayable sampled-trumpet melody notes by octaves. This makes
original VSCO recorded-trumpet notes available without transposing WAVs.
"""
from __future__ import annotations

GENRE_NAME="Swing"
GENRE_PROFILE_ID="JAZZ_SWING_V1"
VERSION="SWING_ACTUAL_RECORDED_TRUMPET_REGISTER_CROSSWALK_R1"
MIN_TRUMPET=60
MAX_TRUMPET=83

def fit_original_trumpet_register(events:list[dict])->list[dict]:
    """Musical Stage-4 note range guard; all other original notes untouched."""
    if not isinstance(events,list) or not events:
        raise ValueError("SWING_ORIGINAL_SCORE_EMPTY")
    output=[]
    modified=0
    for ev in events:
        if not isinstance(ev,dict) or "instrument_id" not in ev:
            raise ValueError("SWING_NOT_ORIGINAL_EVENT")
        if ev["instrument_id"]!="trumpet":
            output.append(ev)
            continue
        old=ev.get("midi")
        if not isinstance(old,int) or isinstance(old,bool) or not 0<=old<=127:
            raise ValueError("SWING_TRUMPET_BAD_MIDI")
        now=old
        while now<MIN_TRUMPET:
            now+=12
        while now>MAX_TRUMPET:
            now-=12
        if not MIN_TRUMPET<=now<=MAX_TRUMPET or (old-now)%12!=0:
            raise ValueError("SWING_TRUMPET_NOTE_NOT_IN_RECORDED_RANGE")
        if old!=now:
            new=dict(ev)
            new["midi"]=now
            output.append(new)
            modified+=1
        else:
            output.append(ev)
    if not any(x.get("instrument_id")=="trumpet" for x in output):
        raise ValueError("SWING_ORIGINAL_TRUMPET_MISSING")
    # No velocity, beat, note-length, other instrument or original source edits.
    if len(output)!=len(events):
        raise ValueError("SWING_COMP_EVENT_LOSS")
    return output
