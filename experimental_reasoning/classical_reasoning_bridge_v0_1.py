"""Classical bridge for Composer Musical Reasoning Engine v0.1.

The existing Classical score generator remains authoritative. This bridge maps
its formal plan into the isolated reasoning engine without changing any notes,
players, articulations, orchestration, rendering, or the live Composer.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from typing import Any, Mapping, Optional

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent / "current_master_forward"
if str(MASTER) not in sys.path:
    sys.path.insert(0, str(MASTER))

from classical_composition import PROFILE_ID, make_plan, validate_plan
from genre_pre_generation_compiler import compile_semantic_contract
from reasoning_engine_v0_1 import (
    ComposerState,
    MusicalGoal,
    MusicalIdeaMemory,
    reason,
    validate,
)

BRIDGE_ID = "CLASSICAL_REASONING_BRIDGE_V0_1"

FORMAL_FUNCTION = {
    "A": "statement",
    "B": "contrast",
    "A_RETURN": "return",
    "CODA": "coda",
}


def _active_instruments(plan: Mapping[str, Any]) -> tuple[str, ...]:
    roster = list(plan.get("orchestral_player_roster") or [])
    out = []
    seen = set()
    for item in roster:
        iid = str(item.get("instrument_id") or "").strip()
        if iid and iid not in seen:
            seen.add(iid)
            out.append(iid)
    return tuple(out)


def _goal_for_formal_function(base: MusicalGoal, formal_function: str) -> MusicalGoal:
    if formal_function == "contrast":
        return replace(
            base,
            requested_contrast="ORCHESTRAL_REGISTER_TEXTURE_HARMONIC_REFRAME",
            emotional_direction="preserve",
        )
    if formal_function == "return":
        return replace(
            base,
            requested_contrast=None,
            emotional_direction="build",
        )
    if formal_function == "coda":
        return replace(
            base,
            requested_contrast=None,
            emotional_direction="release",
        )
    return replace(
        base,
        requested_contrast=None,
        emotional_direction="preserve",
    )


def _idea_history(formal_function: str, bars_elapsed: int) -> tuple[MusicalIdeaMemory, ...]:
    if formal_function == "statement":
        return ()
    main_theme = MusicalIdeaMemory(
        idea_id="CLASSICAL_MAIN_THEME",
        origin_section="statement",
        origin_instrument="violin",
        contour_signature="PRIMARY_MOTIVIC_CONTOUR",
        rhythm_signature="PRIMARY_MOTIVIC_RHYTHM",
        harmonic_relation="TONAL_FUNCTIONAL_THEME",
        expressive_character="PRIMARY_THEME_IDENTITY",
        introduced_bar=0,
        last_seen_bar=max(0, bars_elapsed - 8),
        appearances=1 if formal_function == "contrast" else 2,
        transformations=0 if formal_function == "contrast" else 1,
        last_carrier="violin",
    )
    if formal_function != "coda":
        return (main_theme,)
    contrast_idea = MusicalIdeaMemory(
        idea_id="CLASSICAL_CONTRAST_IDEA",
        origin_section="contrast",
        origin_instrument="concert_flute",
        contour_signature="CONTRASTING_MOTIVIC_CONTOUR",
        rhythm_signature="CONTRASTING_PHRASE_RHYTHM",
        harmonic_relation="RELATIVE_MAJOR_CONTRAST",
        expressive_character="CONTRAST_SECTION_IDENTITY",
        introduced_bar=max(0, bars_elapsed - 24),
        last_seen_bar=max(0, bars_elapsed - 16),
        appearances=1,
        transformations=1,
        last_carrier="concert_flute",
    )
    return (main_theme, contrast_idea)


def build_classical_reasoning_report(
    *,
    profile: Mapping[str, Any],
    plan: Optional[Mapping[str, Any]] = None,
    creation_seed: int = 0,
    mode: str = "normal",
    goal: Optional[MusicalGoal] = None,
) -> dict[str, Any]:
    """Build section-level reasoning packets for the existing Classical plan."""
    if profile.get("profile_id") != PROFILE_ID:
        raise ValueError("CLASSICAL_REASONING_PROFILE_ID_MISMATCH")

    working_plan = dict(plan) if plan is not None else make_plan(creation_seed, mode)
    validate_plan(working_plan)

    contract = compile_semantic_contract(dict(profile))
    active = _active_instruments(working_plan)
    base_goal = goal or MusicalGoal()
    sections = list(working_plan["sections"])
    packets = []
    previous_energy = None

    generation_plan = {
        "melody_development_bars": working_plan.get("melody_development_bars", 16),
        "literal_melody_reuse_after_bars": working_plan.get("literal_melody_reuse_after_bars", 16),
    }

    for index, section in enumerate(sections):
        name = str(section["name"])
        formal = FORMAL_FUNCTION.get(name)
        if formal is None:
            raise ValueError("CLASSICAL_REASONING_UNKNOWN_FORMAL_SECTION:" + name)

        previous_formal = FORMAL_FUNCTION.get(str(sections[index - 1]["name"])) if index > 0 else None
        next_formal = FORMAL_FUNCTION.get(str(sections[index + 1]["name"])) if index + 1 < len(sections) else None
        bars_elapsed = int(section["start_bar"]) - 1

        state = ComposerState(
            genre="Classical",
            profile_id=PROFILE_ID,
            section=formal,
            section_occurrence=1,
            previous_section=previous_formal,
            next_section=next_formal,
            bars_elapsed=bars_elapsed,
            bars_in_section=0,
            section_bars_total=int(section["length_bars"]),
            previous_energy=previous_energy,
            current_energy=previous_energy,
            active_instruments=active,
            musical_idea_history=_idea_history(formal, bars_elapsed),
        )

        packet = reason(
            state=state,
            semantic_tags=contract["tags"],
            generation_plan=generation_plan,
            goal=_goal_for_formal_function(base_goal, formal),
        )
        validate(packet)
        previous_energy = packet["decisions"]["energy"]["target"]

        packets.append({
            "classical_section": name,
            "formal_function": formal,
            "start_bar": int(section["start_bar"]),
            "length_bars": int(section["length_bars"]),
            "reasoning_packet": packet,
        })

    return {
        "status": "PASS",
        "bridge_id": BRIDGE_ID,
        "profile_id": PROFILE_ID,
        "plan_schema": working_plan["schema"],
        "source_classical_plan_preserved": True,
        "live_composer_modified": False,
        "orchestral_player_count": len(working_plan.get("orchestral_player_roster") or []),
        "distinct_instruments": list(active),
        "kick_present": any("kick" in x.lower() for x in active),
        "section_count": len(packets),
        "sections": packets,
    }
