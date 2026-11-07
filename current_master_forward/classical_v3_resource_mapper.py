"""Classical V3 canonical-section to Composer resource mapper.

Research/diagnostic only. Converts V3 canonical orchestral assignments into the
existing Composer event/instrument vocabulary, then allows the normal
InstrumentProgram to resolve those IDs. It generates no audio.

This is the first point where the V3 Classical genre path is permitted to name
actual Composer instrument resources.
"""
from __future__ import annotations

from copy import deepcopy

SCHEMA = "CLASSICAL_V3_RESOURCE_MAPPING_001"

SECTION_RESOURCE = {
    "VIOLIN_I": "violin",
    "VIOLIN_II": "violin",
    "VIOLA": "viola",
    "CELLO": "cello",
    "DOUBLE_BASS": "double_bass",
    "FLUTE_SECTION": "concert_flute",
    "OBOE_SECTION": "oboe",
    "CLARINET_SECTION": "clarinet_bb",
    "BASSOON_SECTION": "bassoon",
    "FRENCH_HORN": "horn_f",
    "TRUMPET": "trumpet_c",
    "TIMPANI": "timpani",
}

SECTION_PLAYER = {
    "VIOLIN_I": "VIOLIN_I_1",
    "VIOLIN_II": "VIOLIN_II_1",
    "VIOLA": "VIOLA_1",
    "CELLO": "CELLO_1",
    "DOUBLE_BASS": "DOUBLE_BASS_1",
    "FLUTE_SECTION": "FLUTE_1",
    "OBOE_SECTION": "OBOE_1",
    "CLARINET_SECTION": "CLARINET_1",
    "BASSOON_SECTION": "BASSOON_1",
    "FRENCH_HORN": "HORN_1",
    "TRUMPET": "TRUMPET_1",
    "TIMPANI": "TIMPANI_1",
}


def map_resources(orchestration):
    if orchestration.get("schema") != "CLASSICAL_V3_CANONICAL_ORCHESTRATION_001":
        raise ValueError("CLASSICAL_V3_CANONICAL_ORCHESTRATION_REQUIRED")
    if orchestration.get("resource_mapping_bound"):
        raise ValueError("CLASSICAL_V3_RESOURCE_MAPPING_ALREADY_BOUND")

    events = []
    mappings = []
    used_sections = set()

    for assignment in orchestration["primary_assignments"]:
        section = assignment["section_id"]
        instrument_id = SECTION_RESOURCE.get(section)
        player_id = SECTION_PLAYER.get(section)
        if not instrument_id or not player_id:
            raise ValueError(
                "CLASSICAL_V3_SECTION_RESOURCE_MAPPING_MISSING::" + section
            )

        used_sections.add(section)
        event = {
            "track_id": section,
            "instrument_id": instrument_id,
            "player_id": player_id,
            "midi": int(assignment["midi"]),
            "start_beat": float(assignment["start_beat"]),
            "duration_beats": float(assignment["duration_beats"]),
            "velocity": int(assignment["velocity_intent"]),
            "dynamic": None,
            "articulation": assignment["articulation_intent"],
            "section": section,
            "phrase_id": assignment.get("phrase_id"),
            "plan_bar": assignment.get("bar"),
            "harmony_id": assignment["harmony_id"],
            "source_role": assignment["source_role"],
            "orchestral_role": assignment["orchestral_role"],
            "source_rule": "CLASSICAL_V3_CANONICAL_ORCHESTRATION",
            "genre_contract_authority": "GENRE_CONTRACT_V3",
            "classical_variant_id": orchestration["variant_id"],
        }
        events.append(event)
        mappings.append({
            "section_id": section,
            "instrument_id": instrument_id,
            "player_id": player_id,
        })

    unique_mappings = []
    seen = set()
    for item in mappings:
        key = (item["section_id"], item["instrument_id"], item["player_id"])
        if key not in seen:
            seen.add(key)
            unique_mappings.append(item)

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "research_only": True,
        "audio_approved": False,
        "variant_id": orchestration["variant_id"],
        "source_orchestration_schema": orchestration["schema"],
        "section_resource_mappings": unique_mappings,
        "used_sections": sorted(used_sections),
        "events": events,
        "instrument_resolver_ready": True,
        "audio_generated": False,
    }


def validate(mapping, orchestration, instrument_library_ids):
    if mapping.get("schema") != SCHEMA:
        raise ValueError("CLASSICAL_V3_RESOURCE_MAPPING_SCHEMA_INVALID")

    source = orchestration["primary_assignments"]
    events = mapping["events"]
    if len(events) != len(source):
        raise ValueError("CLASSICAL_V3_RESOURCE_EVENT_LOSS")

    library_ids = set(instrument_library_ids)
    missing_resources = sorted({
        e["instrument_id"] for e in events
        if e["instrument_id"] not in library_ids
    })
    if missing_resources:
        raise ValueError(
            "CLASSICAL_V3_RESOURCE_NOT_IN_LIBRARY::" +
            ",".join(missing_resources)
        )

    for assignment, event in zip(source, events):
        if assignment["section_id"] != event["section"]:
            raise ValueError("CLASSICAL_V3_SECTION_IDENTITY_MUTATION")
        if (
            assignment["midi"] != event["midi"]
            or abs(assignment["start_beat"] - event["start_beat"]) > 1e-9
            or abs(assignment["duration_beats"] - event["duration_beats"]) > 1e-9
            or assignment["harmony_id"] != event["harmony_id"]
        ):
            raise ValueError("CLASSICAL_V3_RESOURCE_MAPPING_NOTE_MUTATION")
        if event["genre_contract_authority"] != "GENRE_CONTRACT_V3":
            raise ValueError("CLASSICAL_V3_RESOURCE_AUTHORITY_LOST")

    used = set(mapping["used_sections"])
    mapped = {m["section_id"] for m in mapping["section_resource_mappings"]}
    if used != mapped:
        raise ValueError("CLASSICAL_V3_RESOURCE_SECTION_MAPPING_INCOMPLETE")

    return {
        "status": "PASS",
        "source_assignment_preservation_pct": 100.0,
        "resource_library_presence_pct": 100.0,
        "section_mapping_completion_pct": 100.0,
        "used_section_count": len(used),
        "used_sections": sorted(used),
        "resource_instrument_ids": sorted({
            e["instrument_id"] for e in events
        }),
        "instrument_resolver_ready": True,
        "audio_generated": False,
    }
