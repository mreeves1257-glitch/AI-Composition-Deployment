"""Classical V3 canonical orchestration binder.

Research/diagnostic only. Binds the validated abstract Classical score to
canonical V3 orchestral sections. It does not resolve sample resources, MIDI
programs, soundfonts, mix levels, or audio.

The first supported package is Classical-period orchestral. It deliberately
uses a conservative period formation subset and does not activate trombone,
generic percussion, or tuba merely because those roles exist in the broad
Classical family roster.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy

SCHEMA = "CLASSICAL_V3_CANONICAL_ORCHESTRATION_001"

PERIOD_CORE = (
    "VIOLIN_I",
    "VIOLIN_II",
    "VIOLA",
    "CELLO",
    "DOUBLE_BASS",
    "FLUTE_SECTION",
    "OBOE_SECTION",
    "CLARINET_SECTION",
    "BASSOON_SECTION",
    "FRENCH_HORN",
    "TRUMPET",
    "TIMPANI",
)

INTENTIONALLY_INACTIVE = (
    "TROMBONE_FAMILY",
    "PERCUSSION",
    "TUBA_VARIANT_DEPENDENT",
)

SECTION_RANGES = {
    "VIOLIN_I": (55, 96),
    "VIOLIN_II": (55, 93),
    "VIOLA": (48, 84),
    "CELLO": (36, 76),
    "DOUBLE_BASS": (28, 67),
    "FLUTE_SECTION": (60, 96),
    "OBOE_SECTION": (58, 91),
    "CLARINET_SECTION": (50, 94),
    "BASSOON_SECTION": (34, 75),
    "FRENCH_HORN": (35, 77),
    "TRUMPET": (55, 82),
    "TIMPANI": (40, 55),
}

MELODY_OWNER_BY_PHRASE = {
    "A_STATEMENT": "VIOLIN_I",
    "A_ANSWER": "OBOE_SECTION",
    "B_CONTRAST": "FLUTE_SECTION",
    "DEVELOPMENT": "CLARINET_SECTION",
    "A_RETURN": "VIOLIN_I",
    "CODA": "VIOLIN_I",
    "TRANSITION": "OBOE_SECTION",
    "DEVELOPMENT_1": "CLARINET_SECTION",
    "DEVELOPMENT_2": "VIOLIN_I",
    "RETRANSITION": "BASSOON_SECTION",
    "CLOSING": "OBOE_SECTION",
}

SUPPORT_OWNER = {
    "SUPPORT_ALTO": "VIOLIN_II",
    "SUPPORT_TENOR": "VIOLA",
    "SUPPORT_BASS": "CELLO",
}


def _check_range(section, midi):
    lo, hi = SECTION_RANGES[section]
    return lo <= int(midi) <= hi


def bind(note_plan, structural_plan, package):
    if note_plan.get("schema") != "CLASSICAL_V3_ABSTRACT_NOTE_PLAN_001":
        raise ValueError("CLASSICAL_V3_ABSTRACT_NOTE_PLAN_REQUIRED")
    if structural_plan.get("schema") != "CLASSICAL_V3_STRUCTURAL_PLAN_001":
        raise ValueError("CLASSICAL_V3_STRUCTURAL_PLAN_REQUIRED")
    if package.get("variant_id") != "CLASSICAL_PERIOD_ORCHESTRAL":
        raise ValueError("CLASSICAL_V3_ORCHESTRATION_VARIANT_UNSUPPORTED")

    family_roster = set(package.get("ensemble_roster") or [])
    missing_core = [s for s in PERIOD_CORE if s not in family_roster]
    if missing_core:
        raise ValueError(
            "CLASSICAL_V3_PERIOD_CORE_NOT_IN_FAMILY_ROSTER::" +
            ",".join(missing_core)
        )

    phrase_map = {
        p["phrase_id"]: p for p in structural_plan["phrases"]
    }
    assignments = []
    foreground_windows = []

    for phrase in structural_plan["phrases"]:
        phrase_id = phrase["phrase_id"]
        owner = MELODY_OWNER_BY_PHRASE.get(phrase_id, "VIOLIN_I")
        if owner not in PERIOD_CORE:
            raise ValueError("CLASSICAL_V3_FOREGROUND_OWNER_NOT_PERIOD_CORE")
        foreground_windows.append({
            "phrase_id": phrase_id,
            "section_id": owner,
            "start_bar": phrase["start_bar"],
            "length_bars": phrase["length_bars"],
            "role": "FOREGROUND_MELODY",
        })

    for index, note in enumerate(note_plan["notes"]):
        role = note["role"]
        if role == "MELODY":
            phrase_id = note["phrase_id"]
            section = MELODY_OWNER_BY_PHRASE.get(phrase_id, "VIOLIN_I")
            orchestral_role = "FOREGROUND_MELODY"
        else:
            section = SUPPORT_OWNER[role]
            orchestral_role = "HARMONIC_SUPPORT"

        if not _check_range(section, note["midi"]):
            # A foreground handoff may choose another V3-approved section only
            # when the preferred section cannot play the abstract pitch.
            if role == "MELODY":
                candidates = (
                    "VIOLIN_I", "FLUTE_SECTION", "OBOE_SECTION",
                    "CLARINET_SECTION", "BASSOON_SECTION",
                )
                playable = [s for s in candidates if _check_range(s, note["midi"])]
                if not playable:
                    raise ValueError("CLASSICAL_V3_MELODY_NO_PLAYABLE_SECTION")
                section = playable[0]
            else:
                raise ValueError(
                    "CLASSICAL_V3_SUPPORT_RANGE_FAIL::" + section
                )

        assignments.append({
            "assignment_id": f"A{index:04d}",
            "source_role": role,
            "section_id": section,
            "orchestral_role": orchestral_role,
            "midi": int(note["midi"]),
            "start_beat": float(note["start_beat"]),
            "duration_beats": float(note["duration_beats"]),
            "velocity_intent": int(note["velocity"]),
            "articulation_intent": note["articulation"],
            "harmony_id": note["harmony_id"],
            "phrase_id": note.get("phrase_id"),
            "bar": note.get("bar"),
            "structural": bool(note["structural"]),
            "cadence": bool(note["cadence"]),
        })

    # Time-bounded reinforcement instructions are metadata only at this stage.
    # They do not duplicate notes or create extra voices yet.
    reinforcement = []
    for bar in structural_plan["bars"]:
        if bar.get("cadence"):
            reinforcement.append({
                "bar": bar["bar"],
                "cadence": bar["cadence"],
                "allowed_support_sections": [
                    "DOUBLE_BASS",
                    "BASSOON_SECTION",
                    "FRENCH_HORN",
                    "TRUMPET",
                    "TIMPANI",
                ],
                "rule": (
                    "CADENTIAL_REINFORCEMENT_ONLY__NO_FOREGROUND_PROMOTION__"
                    "NO_IDENTICAL_SECTION_CLONING_WITHOUT_REGISTER_PLAN"
                ),
            })

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "research_only": True,
        "audio_approved": False,
        "resource_mapping_bound": False,
        "variant_id": package["variant_id"],
        "family_roster": sorted(family_roster),
        "active_period_core": list(PERIOD_CORE),
        "intentionally_inactive_family_roles": list(INTENTIONALLY_INACTIVE),
        "foreground_windows": foreground_windows,
        "primary_assignments": assignments,
        "cadential_reinforcement_intent": reinforcement,
        "role_state_authority": deepcopy(package["role_state"]),
        "orchestration_rules": [
            "Strings provide continuous mass without permanent foreground ownership.",
            "Woodwind foreground handoffs are explicit and time-bounded.",
            "Brass is support/reinforcement by default, not melodic foreground.",
            "Timpani is structurally motivated, not continuously active.",
            "Outgoing foreground sections yield role rather than compete as a second lead.",
            "No broad-family roster role becomes active merely because a patch exists.",
        ],
    }
    return result


def validate(orchestration, note_plan, structural_plan):
    if orchestration.get("schema") != SCHEMA:
        raise ValueError("CLASSICAL_V3_ORCHESTRATION_SCHEMA_INVALID")

    assignments = orchestration["primary_assignments"]
    source_notes = note_plan["notes"]
    if len(assignments) != len(source_notes):
        raise ValueError("CLASSICAL_V3_ORCHESTRATION_NOTE_LOSS")

    active_core = set(orchestration["active_period_core"])
    inactive = set(orchestration["intentionally_inactive_family_roles"])
    sections = {a["section_id"] for a in assignments}
    if not sections.issubset(active_core):
        raise ValueError("CLASSICAL_V3_ORCHESTRATION_NONCORE_SECTION_USED")
    if sections & inactive:
        raise ValueError("CLASSICAL_V3_INACTIVE_SECTION_USED")

    for source, assignment in zip(source_notes, assignments):
        identity = (
            int(source["midi"]) == assignment["midi"]
            and abs(float(source["start_beat"]) - assignment["start_beat"]) < 1e-9
            and abs(float(source["duration_beats"]) - assignment["duration_beats"]) < 1e-9
            and source["harmony_id"] == assignment["harmony_id"]
        )
        if not identity:
            raise ValueError("CLASSICAL_V3_ORCHESTRATION_SOURCE_NOTE_MUTATION")
        if not _check_range(assignment["section_id"], assignment["midi"]):
            raise ValueError("CLASSICAL_V3_ORCHESTRATION_RANGE_FAIL")

    melody = [a for a in assignments if a["source_role"] == "MELODY"]
    support = [a for a in assignments if a["source_role"] != "MELODY"]
    phrase_windows = orchestration["foreground_windows"]

    owners_by_phrase = {
        w["phrase_id"]: w["section_id"] for w in phrase_windows
    }
    if len(owners_by_phrase) != len(structural_plan["phrases"]):
        raise ValueError("CLASSICAL_V3_FOREGROUND_WINDOW_LOSS")

    melody_sections_by_phrase = defaultdict(set)
    for a in melody:
        melody_sections_by_phrase[a["phrase_id"]].add(a["section_id"])

    # Range fallback is allowed, but the preferred owner must remain the
    # dominant melody owner in each phrase.
    dominant_owner_pass = 0
    for phrase_id, preferred in owners_by_phrase.items():
        counts = Counter(
            a["section_id"] for a in melody if a["phrase_id"] == phrase_id
        )
        if counts and counts.most_common(1)[0][0] == preferred:
            dominant_owner_pass += 1

    unique_foreground = set(a["section_id"] for a in melody)
    brass_foreground = unique_foreground & {"FRENCH_HORN", "TRUMPET"}
    percussion_foreground = unique_foreground & {"TIMPANI"}
    if brass_foreground or percussion_foreground:
        raise ValueError("CLASSICAL_V3_BRASS_OR_PERCUSSION_FOREGROUND_DEFAULT")
    if len(unique_foreground) < 3:
        raise ValueError("CLASSICAL_V3_FOREGROUND_HANDOFFS_TOO_FEW")

    support_sections = set(a["section_id"] for a in support)
    if not {"VIOLIN_II", "VIOLA", "CELLO"}.issubset(support_sections):
        raise ValueError("CLASSICAL_V3_CORE_SUPPORT_SECTION_MISSING")

    return {
        "status": "PASS",
        "source_note_assignment_pct": 100.0,
        "range_valid_pct": 100.0,
        "foreground_phrase_window_count": len(phrase_windows),
        "foreground_unique_section_count": len(unique_foreground),
        "foreground_sections": sorted(unique_foreground),
        "preferred_foreground_owner_phrase_pct": round(
            100 * dominant_owner_pass / max(1, len(phrase_windows)), 2
        ),
        "support_sections": sorted(support_sections),
        "inactive_family_roles_used": [],
        "brass_foreground_default": False,
        "percussion_foreground_default": False,
        "resource_mapping_bound": False,
        "audio_generated": False,
    }
