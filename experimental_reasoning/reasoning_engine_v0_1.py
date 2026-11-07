"""Experimental Composer Musical Reasoning Engine v0.1.

REASONING ONLY.
This module does not render audio, generate MIDI, select samples, replace a
genre interpreter, or mutate the live Composer pipeline.

Intended future insertion point:
    genre selection/profile/interpreter
      -> pre-generation genre plan
      -> THIS REASONING LAYER
      -> existing note/event generation
      -> existing performance/render chain

The selected genre profile remains authoritative for genre identity.  This
engine reasons about musical state: section function, energy movement,
density, repetition, contrast, and transition intent.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping, Optional, Sequence

ENGINE_ID = "COMPOSER_MUSICAL_REASONING_ENGINE_V0_1"
AUTHORITY = "REASONING_ONLY_NOT_RENDER_AUTHORITY"

_SECTION_BASE_ENERGY = {
    "intro": 0.24,
    "verse": 0.46,
    "prechorus": 0.64,
    "pre_chorus": 0.64,
    "chorus": 0.82,
    "bridge": 0.60,
    "breakdown": 0.34,
    "solo": 0.76,
    "outro": 0.30,
}

_SECTION_BASE_DENSITY = {
    "intro": 2,
    "verse": 3,
    "prechorus": 4,
    "pre_chorus": 4,
    "chorus": 5,
    "bridge": 3,
    "breakdown": 2,
    "solo": 4,
    "outro": 2,
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _norm_section(value: Optional[str]) -> str:
    return str(value or "unknown").strip().lower().replace("-", "_").replace(" ", "_")


def _norm_tags(tags: Iterable[str]) -> set[str]:
    return {str(tag).strip().lower() for tag in tags if str(tag).strip()}


@dataclass(frozen=True)
class SectionMemory:
    section: str
    occurrence: int = 1
    energy: float = 0.5
    density: int = 3


@dataclass(frozen=True)
class ComposerState:
    genre: str
    profile_id: str
    section: str
    section_occurrence: int = 1
    previous_section: Optional[str] = None
    next_section: Optional[str] = None
    bars_elapsed: int = 0
    bars_in_section: int = 0
    section_bars_total: Optional[int] = None
    current_energy: Optional[float] = None
    previous_energy: Optional[float] = None
    current_density: Optional[int] = None
    chord_context: Sequence[str] = field(default_factory=tuple)
    recent_sections: Sequence[SectionMemory] = field(default_factory=tuple)


@dataclass(frozen=True)
class MusicalGoal:
    target_energy: Optional[float] = None
    emotional_direction: str = "preserve"
    requested_contrast: Optional[str] = None
    force_transition: Optional[str] = None


def _section_target_energy(state: ComposerState, goal: MusicalGoal) -> float:
    section = _norm_section(state.section)
    previous = _norm_section(state.previous_section)
    target = _SECTION_BASE_ENERGY.get(section, 0.50)

    if state.section_occurrence > 1:
        if section == "verse":
            target += min(0.08, 0.03 * (state.section_occurrence - 1))
        elif section == "chorus":
            target += min(0.06, 0.02 * (state.section_occurrence - 1))
        elif section == "bridge":
            target -= 0.03

    if section == "verse" and previous == "chorus":
        target = min(target, 0.48)

    direction = str(goal.emotional_direction or "preserve").strip().lower()
    if direction in {"build", "rise", "lift", "intensify"}:
        target += 0.10
    elif direction in {"release", "fall", "soften", "pull_back", "pullback"}:
        target -= 0.10
    elif direction in {"peak", "maximum"}:
        target = max(target, 0.90)

    if goal.target_energy is not None:
        target = (target * 0.45) + (_clamp(float(goal.target_energy), 0.0, 1.0) * 0.55)

    return round(_clamp(target, 0.05, 1.0), 3)


def _density_target(state: ComposerState, energy: float) -> int:
    section = _norm_section(state.section)
    base = _SECTION_BASE_DENSITY.get(section, 3)

    if section == "verse" and _norm_section(state.previous_section) == "chorus":
        base = min(base, 3)

    if energy >= 0.88:
        base = max(base, 5)
    elif energy >= 0.70:
        base = max(base, 4)
    elif energy <= 0.35:
        base = min(base, 2)

    return int(_clamp(base, 1, 5))


def _energy_motion(state: ComposerState, target: float) -> str:
    reference = state.current_energy
    if reference is None:
        reference = state.previous_energy
    if reference is None:
        reference = _SECTION_BASE_ENERGY.get(_norm_section(state.previous_section), 0.5)

    delta = target - float(reference)
    if delta >= 0.12:
        return "BUILD"
    if delta <= -0.12:
        return "PULL_BACK"
    return "HOLD_OR_GENTLY_SHAPE"


def _role_intent(state: ComposerState, energy_motion: str, density: int) -> dict[str, Any]:
    section = _norm_section(state.section)

    intent: dict[str, Any] = {
        "preserve_foundation_roles": ["bass", "primary_groove"],
        "foreground_policy": "ONE_CLEAR_PRIMARY_FOCUS",
        "supporting_role_density": density,
        "do_not_choose_specific_instruments_here": True,
    }

    if energy_motion == "PULL_BACK":
        intent.update({
            "reduce": ["secondary_accompaniment", "fills", "doublings"],
            "drop_when_genre_allows": ["ornamental_layers"],
            "add": [],
        })
    elif energy_motion == "BUILD":
        intent.update({
            "reduce": [],
            "drop_when_genre_allows": [],
            "add": ["supporting_motion", "transition_activity"],
        })
    else:
        intent.update({
            "reduce": [],
            "drop_when_genre_allows": [],
            "add": ["subtle_variation"],
        })

    if section == "chorus":
        intent["foreground_policy"] = "STRONG_PRIMARY_FOCUS_WITH_SUPPORT"
        intent["add"] = list(dict.fromkeys(intent["add"] + ["width_or_counter_support"]))
    elif section == "bridge":
        intent["foreground_policy"] = "CONTRASTING_PRIMARY_FOCUS"
    elif section == "breakdown":
        intent["foreground_policy"] = "MINIMAL_FOCUS"

    return intent


def _rhythm_intent(tags: set[str], energy_motion: str, section: str) -> dict[str, Any]:
    behavior = "PRESERVE_GENRE_GROOVE"
    detail: list[str] = []

    if energy_motion == "PULL_BACK":
        detail.append("REDUCE_FILL_FREQUENCY")
        detail.append("CREATE_MORE_SPACE")
    elif energy_motion == "BUILD":
        detail.append("INCREASE_FORWARD_MOTION_WITHIN_GENRE_RULES")
        detail.append("PREPARE_SECTION_BOUNDARY")
    else:
        detail.append("VARY_MICRO_PATTERN_WITHOUT_LOSING_GROOVE_IDENTITY")

    for tag, instruction in (
        ("syncopated", "PRESERVE_SYNCOPATION"),
        ("offbeat", "PRESERVE_OFFBEAT_IDENTITY"),
        ("clave", "DO_NOT_BREAK_CLAVE"),
        ("dembow", "PRESERVE_DEMBOW_IDENTITY"),
        ("four_floor", "PRESERVE_FOUR_ON_FLOOR_IDENTITY"),
        ("triple", "PRESERVE_TRIPLE_METER_FEEL"),
        ("laidback", "PRESERVE_LAID_BACK_PLACEMENT"),
        ("breaks", "ALLOW_STRUCTURAL_BREAKS"),
    ):
        if tag in tags:
            detail.append(instruction)

    if section == "breakdown":
        detail.append("SIMPLIFY_TO_ESSENTIAL_PULSE")

    return {"behavior": behavior, "instructions": list(dict.fromkeys(detail))}


def _harmony_intent(tags: set[str], state: ComposerState) -> dict[str, Any]:
    family = "FOLLOW_PRE_GENERATION_HARMONY_FAMILY"
    detail = ["DO_NOT_REPLACE_GENRE_HARMONY_RULES"]

    if "static_harmony" in tags:
        detail.append("USE_TEXTURE_OR_RHYTHM_FOR_DEVELOPMENT_BEFORE_ADDING_CHORD_MOTION")
    if "extended" in tags:
        detail.append("ALLOW_PROFILE_AUTHORIZED_EXTENSIONS_AND_VOICE_LEADING")
    if "riff_vamp" in tags:
        detail.append("DEVELOP_RIFF_OR_VAMP_WITHOUT_FORCING_FUNCTIONAL_CADENCE")
    if "modal" in tags:
        detail.append("PRESERVE_MODAL_CENTER")
    if "functional" in tags:
        detail.append("PRESERVE_FUNCTIONAL_DIRECTION")

    if state.next_section and _norm_section(state.next_section) in {"chorus", "prechorus", "pre_chorus"}:
        detail.append("CREATE_END_OF_SECTION_TENSION_IF_GENRE_ALLOWS")
    elif _norm_section(state.section) == "outro":
        detail.append("FAVOR_RESOLUTION_OR_DELIBERATE_OPEN_ENDING_PER_PROFILE")

    return {"behavior": family, "instructions": list(dict.fromkeys(detail))}


def _melody_intent(state: ComposerState, generation_plan: Mapping[str, Any]) -> dict[str, Any]:
    reuse_after = max(16, int(generation_plan.get("literal_melody_reuse_after_bars", 16) or 16))
    developed = max(16, int(generation_plan.get("melody_development_bars", 16) or 16))
    repeated_section = state.section_occurrence > 1

    instructions = ["PRESERVE_SECTION_IDENTITY_WITHOUT_DEFAULTING_TO_LITERAL_COPY"]

    if repeated_section:
        instructions.extend([
            "VARY_CONTOUR_OR_RHYTHM_OR_REGISTER",
            "RETAIN_RECOGNIZABLE_MOTIVIC_RELATIONSHIP",
        ])
    if state.bars_elapsed < reuse_after:
        instructions.append("BLOCK_LITERAL_MELODY_REUSE")
    else:
        instructions.append("LITERAL_RECALL_ALLOWED_ONLY_WHEN_MUSICALLY_JUSTIFIED")

    return {
        "behavior": "DEVELOP_NOT_CLONE",
        "section_is_repeat": repeated_section,
        "minimum_development_window_bars": developed,
        "literal_reuse_after_bars": reuse_after,
        "instructions": instructions,
    }


def _transition_intent(state: ComposerState, energy_motion: str, goal: MusicalGoal) -> dict[str, Any]:
    if goal.force_transition:
        mode = str(goal.force_transition).strip().upper()
    else:
        nxt = _norm_section(state.next_section)
        cur = _norm_section(state.section)
        if nxt in {"chorus", "prechorus", "pre_chorus", "solo"}:
            mode = "BUILD_TOWARD_NEXT_SECTION"
        elif cur == "outro" or nxt in {"outro", "end", "ending"}:
            mode = "RESOLVE_OR_THIN"
        elif energy_motion == "PULL_BACK":
            mode = "CLEAN_RESET"
        else:
            mode = "CONTINUITY_WITH_CLEAR_BOUNDARY"

    return {
        "mode": mode,
        "fill_policy": "GENRE_AUTHORIZED_ONLY",
        "boundary_strength": "CLEAR_NOT_MECHANICAL",
    }


def _contrast_intent(state: ComposerState, goal: MusicalGoal) -> dict[str, Any]:
    requested = (goal.requested_contrast or "").strip().lower()
    if requested:
        return {"required": True, "basis": requested.upper()}

    if _norm_section(state.section) == "bridge":
        return {"required": True, "basis": "TEXTURE_OR_REGISTER_OR_RHYTHMIC_CONTRAST"}

    if state.section_occurrence > 1:
        return {"required": True, "basis": "DEVELOPMENT_WITHIN_SECTION_IDENTITY"}

    return {"required": False, "basis": "NO_FORCED_CONTRAST"}


def reason(
    *,
    state: ComposerState,
    semantic_tags: Sequence[str] = (),
    generation_plan: Optional[Mapping[str, Any]] = None,
    goal: Optional[MusicalGoal] = None,
) -> dict[str, Any]:
    """Return a deterministic musical decision packet.

    The packet is advisory.  It is safe to inspect, test, log, and compare.
    It is deliberately not wired to event generation in v0.1.
    """
    if not state.genre:
        raise ValueError("REASONING_STATE_GENRE_REQUIRED")
    if not state.profile_id:
        raise ValueError("REASONING_STATE_PROFILE_ID_REQUIRED")
    if state.section_occurrence < 1:
        raise ValueError("REASONING_SECTION_OCCURRENCE_INVALID")

    generation_plan = dict(generation_plan or {})
    goal = goal or MusicalGoal()
    tags = _norm_tags(semantic_tags)
    section = _norm_section(state.section)

    target_energy = _section_target_energy(state, goal)
    energy_motion = _energy_motion(state, target_energy)
    density = _density_target(state, target_energy)

    decisions = {
        "section_function": section.upper(),
        "energy": {
            "target": target_energy,
            "motion": energy_motion,
        },
        "density": {
            "target_level_1_to_5": density,
            "principle": "DENSITY_FOLLOWS_SECTION_FUNCTION_AND_ENERGY_NOT_FIXED_TRACK_COUNT",
        },
        "roles": _role_intent(state, energy_motion, density),
        "rhythm": _rhythm_intent(tags, energy_motion, section),
        "harmony": _harmony_intent(tags, state),
        "melody": _melody_intent(state, generation_plan),
        "transition": _transition_intent(state, energy_motion, goal),
        "contrast": _contrast_intent(state, goal),
        "guardrails": [
            "GENRE_PROFILE_AND_GENRE_INTERPRETER_REMAIN_AUTHORITATIVE",
            "DO_NOT_SELECT_SAMPLES_OR_RENDER_AUDIO",
            "DO_NOT_EMIT_MIDI_OR_NOTE_EVENTS_IN_V0_1",
            "DO_NOT_CHANGE_INSTRUMENT_IDENTITY",
            "DO_NOT_ACTIVATE_LIVE_PIPELINE",
        ],
    }

    packet = {
        "status": "PASS",
        "engine_id": ENGINE_ID,
        "authority": AUTHORITY,
        "integration_active": False,
        "genre": state.genre,
        "profile_id": state.profile_id,
        "state": asdict(state),
        "semantic_tags": sorted(tags),
        "goal": asdict(goal),
        "decisions": decisions,
    }
    packet["decision_sha256"] = _hash(packet)
    return packet


def validate(packet: Mapping[str, Any]) -> dict[str, Any]:
    packet = dict(packet)
    expected_hash = packet.pop("decision_sha256", None)
    if packet.get("engine_id") != ENGINE_ID:
        raise ValueError("REASONING_ENGINE_ID_INVALID")
    if packet.get("authority") != AUTHORITY:
        raise ValueError("REASONING_AUTHORITY_INVALID")
    if packet.get("integration_active") is not False:
        raise ValueError("REASONING_V0_1_MUST_REMAIN_ISOLATED")
    if _hash(packet) != expected_hash:
        raise ValueError("REASONING_DECISION_HASH_MISMATCH")
    if not packet.get("genre") or not packet.get("profile_id"):
        raise ValueError("REASONING_PACKET_IDENTITY_MISSING")
    return packet
