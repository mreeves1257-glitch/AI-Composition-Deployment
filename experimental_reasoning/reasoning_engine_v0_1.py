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
class InstrumentMemory:
    instrument_id: str
    meaningful_windows: int = 0
    total_windows: int = 0
    featured_windows: int = 0
    last_role: Optional[str] = None


@dataclass(frozen=True)
class MusicalIdeaMemory:
    idea_id: str
    origin_section: str
    origin_instrument: Optional[str] = None
    contour_signature: str = ""
    rhythm_signature: str = ""
    harmonic_relation: str = ""
    expressive_character: str = ""
    introduced_bar: int = 0
    last_seen_bar: int = 0
    appearances: int = 1
    transformations: int = 0
    last_carrier: Optional[str] = None


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
    active_instruments: Sequence[str] = field(default_factory=tuple)
    instrument_history: Sequence[InstrumentMemory] = field(default_factory=tuple)
    musical_idea_history: Sequence[MusicalIdeaMemory] = field(default_factory=tuple)


@dataclass(frozen=True)
class MusicalGoal:
    target_energy: Optional[float] = None
    emotional_direction: str = "preserve"
    requested_contrast: Optional[str] = None
    force_transition: Optional[str] = None
    # 1.0 means complete equal compositional importance among all active instruments.
    # This does NOT require equal note counts, equal loudness, or equal foreground time.
    instrument_balance: float = 1.0
    # 1.0 requests maximum bass richness/depth while preserving clarity and genre fit.
    bass_richness: float = 1.0
    # 1.0 requests a deeply pronounced, physically felt kick without raising its compositional importance.
    kick_impact: float = 1.0


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
        "foreground_policy": "NO_PERSISTENT_INSTRUMENT_DOMINANCE",
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
        intent["add"] = list(dict.fromkeys(intent["add"] + ["width_or_counter_support"]))
    elif section == "bridge":
        intent["add"] = list(dict.fromkeys(intent["add"] + ["contrasting_role_behavior"]))
    elif section == "breakdown":
        intent["add"] = list(dict.fromkeys(intent["add"] + ["shared_sparse_space"]))

    return intent


def _kick_character_intent(goal: MusicalGoal, tags: set[str]) -> dict[str, Any]:
    """Describe a pronounced kick character without turning kick into a hierarchy override."""
    impact = _clamp(float(goal.kick_impact), 0.0, 1.0)
    maximum = impact >= 0.999
    instructions = [
        "PRESERVE_DEEP_LOW_FREQUENCY_IMPACT",
        "PRESERVE_CLEAR_PHYSICAL_PUNCH",
        "KEEP_TRANSIENT_DEFINED_WITHOUT_THIN_CLICK",
        "KEEP_KICK_BODY_FULL_AND_ROUND",
        "MAKE_THE_KICK_EASY_TO_FEEL_AND_EASY_TO_LOCATE",
        "COORDINATE_WITH_BASS_SO_BOTH_REMAIN_POWERFUL_AND_DISTINCT",
        "AVOID_BOOMY_UNCONTROLLED_LOW_END",
        "AVOID_OVERCOMPRESSION_THAT_FLATTENS_IMPACT",
    ]
    if "four_floor" in tags:
        instructions.append("PRESERVE_REPEATED_KICK_IMPACT_WITHOUT FATIGUE_OR LOW_END_BUILDUP")
    if "sidechain" in tags:
        instructions.append("USE_DUCKING_OR_SPACE_RELATIONSHIP_TO_CLARIFY_KICK_BASS_HANDOFF_WITHOUT WEAKENING_EITHER")

    return {
        "parameter": "kick_impact",
        "target_0_to_1": round(impact, 3),
        "mode": "MAXIMUM_PRONOUNCED_IMPACT" if maximum else "SCALED_PRONOUNCED_IMPACT",
        "compositional_importance_change": False,
        "importance_rule": "KICK_REMAINS_EQUAL_IN_COMPOSITIONAL_IMPORTANCE_WITH_OTHER_ACTIVE_INSTRUMENTS",
        "sound_character": {
            "depth": "DEEP",
            "impact": "VERY_PRONOUNCED",
            "punch": "STRONG",
            "body": "FULL_AND_ROUND",
            "transient": "DEFINED_NOT_THIN",
            "physical_feel": "HIGH",
        },
        "clarity_policy": "KICK_MUST_BE_PRONOUNCED_WITHOUT MASKING_BASS_OR OTHER_EQUAL_IMPORTANCE_INSTRUMENTS",
        "bass_relationship": "KICK_PROVIDES_IMPACT_WHILE_BASS_PROVIDES_SUSTAINED_DEPTH_AND_BODY_WITH_CLEAR LOW_END_SEPARATION",
        "future_realization_requirements": instructions,
        "v0_1_audio_processing_applied": False,
    }


def _bass_character_intent(goal: MusicalGoal, tags: set[str]) -> dict[str, Any]:
    """Describe the required bass sound character without changing bass importance.

    This is a future realization contract only.  It does not alter notes, select
    samples, apply EQ, or render audio in v0.1.
    """
    richness = _clamp(float(goal.bass_richness), 0.0, 1.0)
    maximum = richness >= 0.999
    instructions = [
        "PRESERVE_STRONG_LOW_FUNDAMENTAL",
        "PRESERVE_FULL_LOW_MID_BODY",
        "ADD_ENOUGH_UPPER_HARMONIC_INFORMATION_FOR_NOTE_DEFINITION",
        "CONTROL_ATTACK_SO_DEPTH_IS_NOT_REPLACED_BY_CLICK_OR_THIN_TRANSIENT",
        "AVOID_HOLLOW_OR_WEAK_BASS_TIMBRE",
        "AVOID_LOW_END_MUD_BY_COORDINATING_WITH_KICK_AND_OTHER_LOW_REGISTER_PARTS",
        "KEEP_BASS_AUDIBLE_AS_MUSICAL_TONE_NOT_ONLY_SUB_ENERGY",
    ]
    if "walking" in tags or "walking3" in tags:
        instructions.append("PRESERVE_NOTE_DEFINITION_AND_WARM_BODY_FOR_MOVING_BASS_LINES")
    if "sidechain" in tags:
        instructions.append("PRESERVE_DEPTH_DURING_DUCKING_OR_SIDECHAIN_MOVEMENT")
    if "pedal" in tags:
        instructions.append("SUSTAIN_LOW_FUNDAMENTAL_WITHOUT_BUILDING_UNCONTROLLED_MUD")

    return {
        "parameter": "bass_richness",
        "target_0_to_1": round(richness, 3),
        "mode": "MAXIMUM_RICH_DEPTH" if maximum else "SCALED_RICH_DEPTH",
        "compositional_importance_change": False,
        "importance_rule": "BASS_REMAINS_EQUAL_IN_COMPOSITIONAL_IMPORTANCE_WITH_OTHER_ACTIVE_INSTRUMENTS",
        "sound_character": {
            "depth": "VERY_DEEP",
            "weight": "POWERFUL",
            "body": "FULL_AND_RICH",
            "warmth": "HIGH",
            "fundamental_authority": "STRONG",
            "harmonic_definition": "PRESENT",
            "transient_character": "CONTROLLED_NOT_THIN",
        },
        "register_policy": "USE_A_NATURAL_DEEP_BASS_REGISTER_SUPPORTED_BY_THE_INSTRUMENT_AND_GENRE_WITHOUT_FORCING_UNMUSICAL_EXTREMES",
        "clarity_policy": "DEPTH_AND_RICHNESS_MUST_NOT_BECOME_MUD_OR_MASK_OTHER_EQUAL_IMPORTANCE_INSTRUMENTS",
        "kick_relationship": "COORDINATE_LOW_END_SPACE_SO_KICK_AND_BASS_CAN_BOTH_REMAIN POWERFUL_AND_DISTINCT",
        "small_speaker_policy": "RETAIN_HARMONIC_DEFINITION_SO_THE_BASS_LINE_REMAINS PERCEPTIBLE_WHEN THE DEEPEST FUNDAMENTAL_IS NOT REPRODUCED",
        "future_realization_requirements": instructions,
        "v0_1_audio_processing_applied": False,
    }


def _spatial_3d_intent(state: ComposerState, goal: MusicalGoal, importance_plan: Mapping[str, Any]) -> dict[str, Any]:
    """Plan spatial relationships early while leaving actual 3D processing downstream.

    This stage emits compositional spatial intent only. The preserved 3D mixer remains
    the realization stage after stems exist.
    """
    active=[str(x) for x in state.active_instruments if str(x).strip()]
    section=_norm_section(state.section)
    bass_ids=[x for x in active if "bass" in x.lower()]
    kick_ids=[x for x in active if "kick" in x.lower()]
    return {
        "status": "PASS" if active else "WAITING_FOR_ACTIVE_INSTRUMENT_LIST",
        "architecture": "SPATIAL_INTENT_EARLY__PHYSICAL_3D_MIX_LATE",
        "planning_stage": "PRE_GENERATION_REASONING",
        "realization_stage": "POST_STEM_EXISTING_3D_MIXER",
        "move_existing_mixer_now": False,
        "dimensions": {
            "left_right": "PLANNED_FOR_SEPARATION_AND_CONVERSATION",
            "front_back": "PLANNED_FOR_DEPTH_WITHOUT_IMPORTANCE_HIERARCHY",
            "vertical_or_spectral_space": "PLANNED_AS_REGISTER_AND_FREQUENCY_OCCUPANCY_NOT_LITERAL_HEIGHT",
            "distance": "PLANNED_FOR_INTIMACY_OR_DEPTH_BY_ROLE_AND_SECTION",
        },
        "equal_importance_rule": "SPATIAL_DEPTH_MUST_NOT_BE_USED_TO MAKE_ANY ACTIVE_INSTRUMENT LESS IMPORTANT",
        "clarity_rule": "CREATE_DISTINCT SPATIAL HOMES SO RICHNESS DOES NOT COLLAPSE INTO MASKING",
        "interaction_rule": "POSITIONING SHOULD SUPPORT CALL_RESPONSE_HANDOFF_AND_COUNTER_MOTION",
        "section_rule": (
            "ALLOW_WIDER_DEEPER_FIELD_WITH_CLEAR_CENTER_OF_GRAVITY"
            if section in {"chorus","solo"} else
            "PRESERVE_SPACE_AND_DEPTH_WITHOUT OVERCROWDING"
        ),
        "kick_spatial_rule": {
            "kick_instruments": kick_ids,
            "center_of_gravity": "FIRM_LOW_CENTER_ANCHOR",
            "depth": "FORWARD_PHYSICAL_IMPACT_WITH_LOW_END_DEPTH",
            "width": "TIGHT_CONTROLLED_LOW_FREQUENCY_IMAGE",
            "impact_target": round(float(goal.kick_impact),3),
            "importance_change": False,
            "masking_guardrail": "MAKE_KICK_PRONOUNCED_WITHOUT PUSHING_BASS_OR OTHER INSTRUMENTS OUT_OF THEIR OWN SPACE",
        },
        "bass_spatial_rule": {
            "bass_instruments": bass_ids,
            "center_of_gravity": "STABLE_LOW_FREQUENCY_ANCHOR",
            "depth": "DEEP_AND_PHYSICALLY_GROUNDED",
            "width": "CONTROLLED_LOW_END_WIDTH",
            "richness_target": round(float(goal.bass_richness),3),
            "importance_change": False,
            "masking_guardrail": "PRESERVE_LOW_END_AUTHORITY_WHILE LEAVING DISTINCT SPACE_FOR KICK_AND OTHER INSTRUMENTS",
        },
        "importance_priority_context": list(importance_plan.get("priority_for_next_window",[])),
        "future_handoff_required": True,
        "audio_processing_applied_here": False,
    }


def _instrument_balance_intent(goal: MusicalGoal) -> dict[str, Any]:
    strength = _clamp(float(goal.instrument_balance), 0.0, 1.0)
    complete = strength >= 0.999
    return {
        "parameter": "instrument_balance",
        "target_0_to_1": round(strength, 3),
        "mode": "COMPLETE_EQUAL_IMPORTANCE" if complete else "PARTIAL_IMPORTANCE_BALANCE",
        "applies_to": "ALL_ACTIVE_INSTRUMENTS",
        "compositional_importance": "EQUAL" if complete else "BALANCE_WEIGHTED",
        "persistent_structural_subordination_allowed": not complete,
        "role_differences_allowed": True,
        "identical_note_density_required": False,
        "identical_loudness_required": False,
        "identical_foreground_time_required": False,
        "arrangement_instruction": "EVERY_ACTIVE_INSTRUMENT_MUST HAVE A MEANINGFUL MUSICAL FUNCTION",
        "interaction_instruction": "INSTRUMENTS_MAY_LEAD_SUPPORT_ANSWER_OR_REST_BUT REMAIN EQUALLY IMPORTANT TO THE WHOLE",
        "future_mix_instruction": "KEEP_EACH INSTRUMENT CLEAR AND INTENTIONAL WITHOUT FORCING EQUAL VOLUME",
        "solo_or_feature_exception": "TEMPORARY_FOCUS_ALLOWED_WITHOUT_REDUCING_OTHER_INSTRUMENTS_OVERALL_IMPORTANCE",
    }


def _instrument_importance_plan(state: ComposerState, goal: MusicalGoal) -> dict[str, Any]:
    """Track equal importance across the composition without equating importance to activity.

    Meaningful musical function is the unit of fairness.  Note count, velocity,
    loudness, and foreground time are explicitly not used as importance scores.
    """
    active = [str(x) for x in state.active_instruments if str(x).strip()]
    seen = set()
    active = [x for x in active if not (x in seen or seen.add(x))]
    memory = {m.instrument_id: m for m in state.instrument_history if m.instrument_id}

    if not active:
        return {
            "status": "WAITING_FOR_ACTIVE_INSTRUMENT_LIST",
            "target": "EQUAL_COMPOSITIONAL_IMPORTANCE",
            "importance_unit": "MEANINGFUL_MUSICAL_FUNCTION",
            "note_quantity_is_importance": False,
            "loudness_is_importance": False,
            "foreground_time_is_importance": False,
            "rule": "WHEN_INSTRUMENTS_ARE_KNOWN_GIVE_EACH_EQUAL_STRUCTURAL_VALUE_OVER_THE_WHOLE_COMPOSITION",
        }

    rows = []
    rates = []
    for instrument_id in active:
        hist = memory.get(instrument_id)
        meaningful = int(hist.meaningful_windows) if hist else 0
        total = int(hist.total_windows) if hist else 0
        featured = int(hist.featured_windows) if hist else 0
        rate = (meaningful / total) if total > 0 else 1.0
        rates.append(rate)
        rows.append({
            "instrument_id": instrument_id,
            "equal_importance_weight": 1.0,
            "meaningful_windows": meaningful,
            "observed_windows": total,
            "featured_windows": featured,
            "meaningful_function_rate": round(rate, 3),
            "last_role": hist.last_role if hist else None,
        })

    min_rate = min(rates) if rates else 1.0
    max_rate = max(rates) if rates else 1.0
    gap = round(max_rate - min_rate, 3)
    underserved = sorted(
        row["instrument_id"] for row in rows
        if row["meaningful_function_rate"] < max_rate - 0.001
    )

    complete = float(goal.instrument_balance) >= 0.999
    return {
        "status": "PASS",
        "target": "EQUAL_COMPOSITIONAL_IMPORTANCE" if complete else "WEIGHTED_COMPOSITIONAL_IMPORTANCE",
        "scope": "WHOLE_COMPOSITION_NOT_EVERY_INSTANT",
        "importance_unit": "MEANINGFUL_MUSICAL_FUNCTION",
        "note_quantity_is_importance": False,
        "loudness_is_importance": False,
        "foreground_time_is_importance": False,
        "active_instrument_count": len(active),
        "ledger": rows,
        "meaningful_function_gap": gap,
        "priority_for_next_window": underserved if underserved else list(active),
        "priority_rule": (
            "RESTORE_UNDERSERVED_INSTRUMENTS_TO_MEANINGFUL_FUNCTION"
            if underserved else
            "ROTATE_MEANINGFUL_FUNCTIONS_WITHOUT_HIERARCHY"
        ),
        "rest_rule": "AN_INSTRUMENT_MAY_REST_WHEN_THE_REST_IS_MUSICALLY_PURPOSEFUL_BUT_MAY_NOT_BE_CHRONICALLY_NEGLECTED",
        "role_rule": "DIFFERENT_ROLES_ARE_ALLOWED_EQUAL_IMPORTANCE_DOES_NOT_MEAN_IDENTICAL_BEHAVIOR",
        "feature_rule": "TEMPORARY_FEATURES_ARE_ALLOWED_BUT_MUST_NOT_CREATE_PERMANENT_STRUCTURAL_SUPERIORITY",
    }


def _instrument_interaction_plan(state: ComposerState, density: int, importance_plan: Mapping[str, Any]) -> dict[str, Any]:
    """Describe how equally-important instruments should share musical space.

    V0.1 intentionally produces abstract role slots rather than assigning a
    specific instrument to a role it may not be capable of performing.  The
    existing genre/interpreter/capability layers remain responsible for that
    compatibility decision.
    """
    section = _norm_section(state.section)
    active = [str(x) for x in state.active_instruments if str(x).strip()]
    priority = list(importance_plan.get("priority_for_next_window", []))

    role_pool = [
        "FOUNDATION_OR_ANCHOR",
        "PRIMARY_GROOVE_OR_PULSE",
        "HARMONIC_MOTION_OR_COLOR",
        "ANSWER_OR_COUNTER_MOTION",
        "TEXTURE_OR_SPACE_SHAPING",
        "TRANSITION_OR_SECTION_LINK",
    ]

    if section == "bridge":
        role_pool = [
            "CONTRASTING_FUNCTION",
            "ANSWER_OR_COUNTER_MOTION",
            "HARMONIC_MOTION_OR_COLOR",
            "FOUNDATION_OR_ANCHOR",
            "TEXTURE_OR_SPACE_SHAPING",
            "TRANSITION_OR_SECTION_LINK",
        ]
    elif section == "breakdown":
        role_pool = [
            "FOUNDATION_OR_ANCHOR",
            "SPACE_SHAPING_OR_INTENTIONAL_REST",
            "SPARSE_RESPONSE",
            "TRANSITION_OR_SECTION_LINK",
        ]
    elif section == "chorus":
        role_pool = [
            "FOUNDATION_OR_ANCHOR",
            "PRIMARY_GROOVE_OR_PULSE",
            "SHARED_LIFT_OR_WIDTH",
            "ANSWER_OR_COUNTER_MOTION",
            "HARMONIC_MOTION_OR_COLOR",
            "TRANSITION_OR_SECTION_LINK",
        ]

    slot_count = max(1, min(len(role_pool), int(density)))
    slots = role_pool[:slot_count]

    return {
        "status": "PASS" if active else "WAITING_FOR_ACTIVE_INSTRUMENT_LIST",
        "principle": "INSTRUMENTS_CONVERSE_AND_HAND_OFF_FUNCTIONS_INSTEAD_OF_STACKING_INTO_A_PERMANENT_HIERARCHY",
        "active_instruments": active,
        "meaningful_role_slots": slots,
        "assignment_policy": "MATCH_ROLES_TO_INSTRUMENT_CAPABILITY_WITHOUT_RANKING_INSTRUMENT_IMPORTANCE",
        "assignment_priority": priority,
        "handoff_rule": "ROTATE_MEANINGFUL_FOCUS_AND_RESPONSE_WHILE_PRESERVING_GENRE_APPROPRIATE_FOUNDATION",
        "collision_rule": "WHEN_PARTS_COMPETE_FOR_THE_SAME_REGISTER_RHYTHM_OR_ATTENTION_REDESIGN_THE_PARTS_RATHER_THAN_MAKING_ONE_DISPOSABLE",
        "space_rule": "NOT_ALL_INSTRUMENTS_MUST_PLAY_SIMULTANEOUSLY",
        "rest_rule": "REST_MAY_BE_AN_EQUAL_IMPORTANCE_MUSICAL_CHOICE_WHEN_IT_CREATES_SPACE_OR_EXPECTATION",
        "hierarchy_rule": "NO_INSTRUMENT_IS_PERMANENTLY_CLASSIFIED_AS_LESS_IMPORTANT_BACKGROUND_MATERIAL",
        "compatibility_guardrail": "DO_NOT_ASSIGN_A_ROLE_UNLESS_THE_EXISTING_GENRE_AND_INSTRUMENT_CAPABILITY_LAYERS_ALLOW_IT",
    }


def _musical_memory_plan(
    state: ComposerState,
    generation_plan: Mapping[str, Any],
    importance_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Plan recall and development of prior musical ideas without literal copying.

    Musical memory stores identity descriptors, not executable notes.  The
    existing generator may later realize a selected transformation, but v0.1
    only decides whether an idea should be recalled, answered, transformed,
    left dormant, or retired.
    """
    ideas = [x for x in state.musical_idea_history if x.idea_id]
    if not ideas:
        return {
            "status": "NO_PRIOR_IDEAS",
            "policy": "INTRODUCE_A_CLEAR_IDEA_THAT_CAN_BE_REMEMBERED_LATER",
            "memory_unit": "ABSTRACT_MUSICAL_IDENTITY_NOT_EXACT_NOTE_SEQUENCE",
            "literal_copy_requested": False,
            "new_idea_allowed": True,
        }

    reuse_after = max(16, int(generation_plan.get("literal_melody_reuse_after_bars", 16) or 16))
    section = _norm_section(state.section)
    priority_instruments = list(importance_plan.get("priority_for_next_window", []))

    candidates = []
    for idea in ideas:
        age = max(0, int(state.bars_elapsed) - int(idea.last_seen_bar))
        same_section_family = _norm_section(idea.origin_section) == section
        exact_recall_eligible = age >= reuse_after
        development_need = max(0, 3 - int(idea.transformations))
        score = (age * 2) + (development_need * 5) + (3 if same_section_family else 0)
        candidates.append({
            "idea_id": idea.idea_id,
            "origin_section": idea.origin_section,
            "origin_instrument": idea.origin_instrument,
            "last_carrier": idea.last_carrier,
            "age_bars": age,
            "appearances": int(idea.appearances),
            "transformations": int(idea.transformations),
            "same_section_family": same_section_family,
            "exact_recall_eligible": exact_recall_eligible,
            "development_priority_score": score,
            "identity": {
                "contour_signature": idea.contour_signature,
                "rhythm_signature": idea.rhythm_signature,
                "harmonic_relation": idea.harmonic_relation,
                "expressive_character": idea.expressive_character,
            },
        })

    candidates.sort(key=lambda x: (-x["development_priority_score"], x["idea_id"]))
    chosen = candidates[0]

    if state.section_occurrence > 1 and chosen["same_section_family"]:
        action = "TRANSFORM_AND_RECALL"
    elif chosen["age_bars"] >= 8:
        action = "RECALL_AS_RESPONSE_OR_COUNTER_IDEA"
    elif chosen["transformations"] == 0:
        action = "DEVELOP_BEFORE_INTRODUCING_ANOTHER_MAJOR_IDEA"
    else:
        action = "LEAVE_DORMANT_AND_CREATE_SPACE"

    preferred_carrier = None
    for instrument_id in priority_instruments:
        if instrument_id != chosen.get("last_carrier"):
            preferred_carrier = instrument_id
            break
    if preferred_carrier is None and priority_instruments:
        preferred_carrier = priority_instruments[0]

    transformation_choices = [
        "RHYTHMIC_RESHAPING",
        "CONTOUR_VARIATION",
        "REGISTER_SHIFT",
        "CALL_AND_RESPONSE",
        "FRAGMENTATION_OR_EXTENSION",
        "HARMONIC_RECONTEXTUALIZATION_IF_GENRE_ALLOWS",
        "TRANSFER_TO_ANOTHER_COMPATIBLE_INSTRUMENT",
    ]

    return {
        "status": "PASS",
        "memory_unit": "ABSTRACT_MUSICAL_IDENTITY_NOT_EXACT_NOTE_SEQUENCE",
        "selected_idea_id": chosen["idea_id"],
        "selected_idea": chosen,
        "action": action,
        "preferred_next_carrier": preferred_carrier,
        "carrier_rule": "WHEN_MUSICALLY_COMPATIBLE_PASS_IDEAS_BETWEEN_INSTRUMENTS_TO_CREATE_CONVERSATION_WITHOUT_CREATING_HIERARCHY",
        "transformation_choices": transformation_choices,
        "literal_copy_requested": False,
        "exact_recall_eligible": bool(chosen["exact_recall_eligible"]),
        "development_rule": "RECALL_SHOULD_PRESERVE_RECOGNIZABLE_IDENTITY_WHILE CHANGING_AT_LEAST_ONE_MUSICAL_DIMENSION",
        "dormancy_rule": "NOT_EVERY_IDEA_MUST_RETURN_IMMEDIATELY_MEMORY_GAINS_MEANING_FROM_ABSENCE_AS_WELL_AS_RECALL",
        "new_idea_rule": "INTRODUCE_NEW_MAJOR_IDEAS_ONLY_WHEN_EXISTING_MATERIAL_HAS_ROOM_TO_BREATHE_OR_DEVELOP",
        "all_candidates": candidates,
    }


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
    if not 0.0 <= float(goal.instrument_balance) <= 1.0:
        raise ValueError("REASONING_INSTRUMENT_BALANCE_OUT_OF_RANGE")
    if not 0.0 <= float(goal.bass_richness) <= 1.0:
        raise ValueError("REASONING_BASS_RICHNESS_OUT_OF_RANGE")
    if not 0.0 <= float(goal.kick_impact) <= 1.0:
        raise ValueError("REASONING_KICK_IMPACT_OUT_OF_RANGE")
    tags = _norm_tags(semantic_tags)
    section = _norm_section(state.section)

    target_energy = _section_target_energy(state, goal)
    energy_motion = _energy_motion(state, target_energy)
    density = _density_target(state, target_energy)
    importance_plan = _instrument_importance_plan(state, goal)

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
        "kick_character": _kick_character_intent(goal, tags),
        "bass_character": _bass_character_intent(goal, tags),
        "instrument_balance": _instrument_balance_intent(goal),
        "spatial_3d_intent": _spatial_3d_intent(state, goal, importance_plan),
        "instrument_importance_plan": importance_plan,
        "instrument_interaction_plan": _instrument_interaction_plan(state, density, importance_plan),
        "musical_memory": _musical_memory_plan(state, generation_plan, importance_plan),
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
            "DO_NOT_TREAT_ANY_ACTIVE_INSTRUMENT_AS_DISPOSABLE_OR_STRUCTURALLY_INFERIOR_WHEN_BALANCE_IS_1_0",
            "DO_NOT_USE_NOTE_COUNT_LOUDNESS_OR_FOREGROUND_TIME_AS_A_PROXY_FOR_INSTRUMENT_IMPORTANCE",
            "DO_NOT_ALLOW_CHRONIC_INSTRUMENT_NEGLECT_ACROSS_THE_COMPOSITION",
            "DO_NOT_SOLVE_INSTRUMENT_COLLISIONS_BY_DECLARING_ONE_PART_UNIMPORTANT",
            "DO_NOT_EQUATE_KICK_IMPACT_WITH_GREATER_COMPOSITIONAL_IMPORTANCE",
            "DO_NOT_LET_PRONOUNCED_KICK_MASK_THE_RICH_BASS_OR_OTHER_INSTRUMENTS",
            "DO_NOT_EQUATE_BASS_DEPTH_WITH_GREATER_COMPOSITIONAL_IMPORTANCE",
            "DO_NOT_ALLOW_RICH_BASS_TO_MASK_OTHER_EQUAL_IMPORTANCE_INSTRUMENTS",
            "DO_NOT_APPLY_PHYSICAL_3D_AUDIO_PROCESSING_INSIDE_REASONING",
            "DO_NOT_POSTPONE_ALL_SPATIAL_DECISIONS_UNTIL_AFTER_RENDERING",
            "DO_NOT_EQUATE_MUSICAL_MEMORY_WITH_LITERAL_NOTE_COPYING",
            "DO_NOT_REINTRODUCE_EVERY_REMEMBERED_IDEA_IMMEDIATELY",
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
