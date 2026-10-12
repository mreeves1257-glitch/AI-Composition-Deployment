"""Classical-only, opt-in ensemble planner. No deployed wiring or audio modifications.

An interpreter chooses an ensemble size from the musical brief and available
instrument capabilities. This is a planning boundary, not a claim of audible parts.
"""
from dataclasses import dataclass
import hashlib

class EnsembleError(ValueError): pass

# IDs must be verified against the actual instrument library before use.
CLASSICAL_ROLES = (
    ("violin", "melody"), ("viola", "inner_voice"), ("cello", "countermelody"),
    ("double_bass", "bass"), ("concert_flute", "woodwind_color"),
    ("clarinet_bb", "woodwind_color"), ("oboe", "woodwind_countermelody"),
    ("bassoon", "low_woodwind"), ("horn_f", "brass_harmony"),
    ("trumpet_c", "brass_accent"), ("tenor_trombone", "brass_support"),
    ("bass_tuba", "low_brass"), ("timpani", "percussion"),
    ("harp", "arpeggio"), ("piano", "keyboard"),
    ("piccolo", "high_woodwind"), ("english_horn", "woodwind_color"),
    ("bass_clarinet", "low_woodwind"), ("glockenspiel", "pitched_percussion"),
    ("triangle", "percussion_color"),
)
@dataclass(frozen=True)
class EnsemblePlan:
    genre: str
    intent: str
    instruments: tuple
    roles: tuple
    unsupported: tuple

def plan_classical_ensemble(*, musical_intent, composition_seed, available_instruments):
    """Select instrumentation from intent, not a fixed four-instrument palette.

    This opt-in prototype accepts explicit ensemble intention from upstream.
    Unknown intention is rejected rather than guessed; no silent fallback.
    """
    if musical_intent not in ("chamber", "expanded_chamber", "small_orchestra", "orchestra"):
        raise EnsembleError("MUSICAL_INTENT_REQUIRED")
    target = {"chamber":(3,6),"expanded_chamber":(5,9),
              "small_orchestra":(9,15),"orchestra":(16,20)}[musical_intent]
    available = set(available_instruments)
    eligible = [(i,role) for i,role in CLASSICAL_ROLES if i in available]
    if len(eligible)<target[0]:
        raise EnsembleError("INSUFFICIENT_VERIFIED_INSTRUMENTS: "+str(len(eligible)))
    seed = int(hashlib.sha256(str(composition_seed).encode()).hexdigest()[:8],16)
    size = target[0] + seed % (min(target[1],len(eligible))-target[0]+1)
    # Rotate choices to avoid the same lineup for every composition; retain
    # bass and melody when possible. Ordering is a proposal for the interpreter.
    anchors = [x for x in eligible if x[0] in ("violin","double_bass")]
    others = [x for x in eligible if x not in anchors]
    offset = seed % len(others) if others else 0
    rotated = others[offset:]+others[:offset]
    chosen = (anchors+rotated)[:size]
    return EnsemblePlan("Classical",musical_intent,
       tuple(x[0] for x in chosen),tuple(x[1] for x in chosen),
       tuple(x[0] for x in CLASSICAL_ROLES if x[0] not in available))
