"""Research-only Rock backbeat collision resolver. OFF by default.

The existing Rock score combines legacy kick/snare hits with generated
"rock_kick"/"rock_backbeat" at identical onset and MIDI pitch. Each pair
can retrigger the same recorded sample twice. This opt-in stage removes the
legacy hit only when a KNOWN exact two-event pair exists. It retains the
existing stronger backbeat event with unchanged velocity, pitch, timing, and
instrument. All unmatched drum hits, all other parts and all source SFZ files
stay byte-equivalent at the score field level.

No inferred quantization and no instrument gain adjustments.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
import math
import os

SWITCH = "AI_COMP_ROCK_DRUM_COLLISION_V1"
VERSION = "ROCK_KICK_SNARE_COLLISION_RESEARCH_V1_DEFAULT_OFF"
COLLISIONS = {
    ("KICK", "kick_drum_rock"): ("kick", "rock_kick"),
    ("SNARE", "snare_drum"): ("snare", "rock_backbeat"),
}

def _onset(x):
    beat=float(Fraction(str(x)))
    if not math.isfinite(beat):
        raise ValueError("INVALID_DRUM_BEAT")
    return round(beat, 9)

def resolve_rock_drum_collisions(events, genre, *, enabled=None):
    """Return independent events; remove only approved simultaneous pairs.

    If ambiguous (e.g. triple triggers, new articulation, mismatched pitch),
    keep original events rather than guessing the musician's intention.
    """
    out=[dict(e) for e in events]
    if enabled is None:
        enabled=os.environ.get(SWITCH, "") == "1"
    if enabled is not True or str(genre).upper() != "ROCK":
        return out
    groups=defaultdict(list)
    for idx,event in enumerate(out):
        identity=(str(event.get("track_id","")).upper(),
                  str(event.get("instrument_id","")))
        if identity not in COLLISIONS:
            continue
        key=(identity,_onset(event["start_beat"]),int(event["midi"]))
        groups[key].append(idx)
    remove=set()
    for (identity,_,_),indices in groups.items():
        if len(indices)!=2:
            continue
        legacy,reinforcement=COLLISIONS[identity]
        old=[i for i in indices if str(out[i].get("articulation","")).lower()==legacy]
        strong=[i for i in indices if str(out[i].get("articulation","")).lower()==reinforcement]
        if len(old)==1 and len(strong)==1:
            # Keep the already authored stronger backbeat exactly as it was;
            # don't layer a second note-on to the SAME sample at the same tick.
            remove.add(old[0])
    return [event for i,event in enumerate(out) if i not in remove]
