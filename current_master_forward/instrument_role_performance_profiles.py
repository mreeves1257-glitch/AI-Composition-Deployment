"""Reusable instrument-role performance profiles.

Purpose
-------
Keep human-approved performance behavior separate from composition generation and
from target/resource lookup. A genre/role can resolve a reusable performance
profile instead of rediscovering attack, sustain, retrigger, and articulation
behavior in each listening session.

This registry is diagnostic/research authority only on the current branch.
It does NOT promote anything to main/live runtime.

Current approved Rock profiles are evidence-backed by 2026-11-07 human
listening decisions:
- rhythm electric guitar: 2.8-beat max ring + safe note-off-preserving strum;
- lead electric guitar: treated melodic duration behavior;
- bass: held Clean body + same-onset Vicious transient at -9 dB, strong beats
  only, with no offbeat bass re-attacks.

No reasoning engine is used here.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

SCHEMA="INSTRUMENT_ROLE_PERFORMANCE_PROFILE_REGISTRY_001"
REGISTRY_STATUS="DIAGNOSTIC_APPROVED_PROFILES__NOT_LIVE_RUNTIME_AUTHORITY"


class InstrumentRolePerformanceProfileError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


ROCK_CORE_V2_PROFILES:dict[str,dict[str,Any]]={
    "HARMONY":{
        "profile_id":"ROCK_CORE_V2__HARMONY_ELECTRIC_GUITAR__APPROVED_001",
        "genre":"ROCK",
        "genre_profile_id":"ROCK_CORE_V2",
        "track_role":"HARMONY",
        "instrument_id":"electric_guitar",
        "role_state":"RHYTHM_POWER_CHORDS",
        "musical_function":"RHYTHMIC_HARMONIC_FOUNDATION",
        "human_listening_status":"APPROVED_DIAGNOSTIC",
        "performance_mode":"VERTICAL_CHORD_GESTURE",
        "duration_policy":{
            "close_attack_beats":0.105,
            "rapid_phrase_beats":0.82,
            "release_gap_beats":0.15,
            "ring_fraction":0.84,
            "max_ringing_beats":2.8,
            "bar_boundary_policy":"DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE",
        },
        "attack_policy":{
            "mode":"SAFE_NOTE_OFF_PRESERVING_STRUM",
            "note_gap_beats":0.038,
            "max_strum_span_beats":0.14,
            "alternate_direction":True,
            "absolute_note_off_preserved":True,
            "pitch_preserved":True,
            "velocity_preserved":True,
            "event_count_preserved":True,
        },
        "resource_intent":{
            "binding_key":"electric_guitar:RHYTHM_POWER_CHORDS",
            "resource_id":"KARORYFER_SHINYGUITAR",
            "mapping":"Programs/composer_electric.sfz",
            "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
        },
        "forbidden":[
            "RANDOM_STRING_TIMING",
            "KEYBOARD_BLOCK_ASSUMED_AS_FINAL_GUITAR_PERFORMANCE",
            "NEW_CHORD_NOTES_AT_PERFORMANCE_STAGE",
        ],
        "evidence":{
            "human_decision":"SAFE_STRUM_PREFERRED_WITH_2P8_RING",
            "decision_checkpoint":"ROCK_V3_STRUM_HUMAN_LISTENING_DECISION__2026-11-07",
        },
    },
    "LEAD":{
        "profile_id":"ROCK_CORE_V2__LEAD_ELECTRIC_GUITAR__APPROVED_001",
        "genre":"ROCK",
        "genre_profile_id":"ROCK_CORE_V2",
        "track_role":"LEAD",
        "instrument_id":"electric_guitar",
        "role_state":"LEAD_MELODY",
        "musical_function":"FOREGROUND_MELODIC_PHRASE",
        "human_listening_status":"APPROVED_DIAGNOSTIC",
        "performance_mode":"PICKED_MELODIC_PHRASE",
        "duration_policy":{
            "rapid_phrase_connection_fraction":0.90,
            "explicit_legato_connection_fraction":0.96,
            "preserve_explicit_short_articulation":True,
            "bar_boundary_policy":"DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE",
        },
        "timing_policy":{
            "random_jitter":False,
            "phrase_push_pull":"DISABLED_UNTIL_EXPLICIT_SHARED_GROOVE_RULE_EXISTS",
        },
        "resource_intent":{
            "binding_key":"electric_guitar:LEAD_MELODY",
            "resource_id":"KARORYFER_SHINYGUITAR",
            "mapping":"Programs/composer_electric.sfz",
            "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
        },
        "forbidden":[
            "GENERIC_OCTAVE_FLIP",
            "RANDOM_MELODY_TIMING",
            "CONTINUOUS_LEAD_FILL",
            "SUSTAIN_ACROSS_UNVERIFIED_HARMONY_CHANGE",
        ],
        "evidence":{
            "human_decision":"TREATED_LEAD_PREFERRED_IN_APPROVED_GUITAR_CONTEXT",
            "decision_checkpoint":"ROCK_V3_STRUM_HUMAN_LISTENING_DECISION__2026-11-07",
        },
    },
    "BASS":{
        "profile_id":"ROCK_CORE_V2__ELECTRIC_BASS__D_APPROVED_001",
        "genre":"ROCK",
        "genre_profile_id":"ROCK_CORE_V2",
        "track_role":"BASS",
        "instrument_id":"electric_bass_guitar",
        "role_state":"BASS",
        "musical_function":"STRONG_BEAT_FOUNDATION_WITH_HELD_BODY",
        "human_listening_status":"APPROVED_DIAGNOSTIC",
        "performance_mode":"STRONG_BEAT_HELD_BODY_PLUS_SAME_ONSET_ATTACK",
        "event_policy":{
            "strong_beat_attacks_only":True,
            "offbeat_reattacks_allowed":False,
            "offbeat_pitch_changes_allowed":False,
            "pitch_change_stage":"STRONG_BEAT_ONLY",
            "random_jitter":False,
        },
        "body_layer":{
            "resource_id":"KARORYFER_GROWLYBASS_V1_002",
            "mapping":"growlybass_clean.sfz",
            "max_hold_beats":1.50,
            "spacing_fraction":0.78,
            "release_gap_beats":0.20,
            "minimum_hold_beats":0.60,
            "note_length_responsive_required":True,
        },
        "attack_layer":{
            "resource_id":"KARORYFER_GROWLYBASS_V1_002",
            "mapping":"growlybass_vicious.sfz",
            "same_onset_as_body":True,
            "same_pitch_as_body":True,
            "same_velocity_as_body":True,
            "gate_beats":0.20,
            "mix_gain_db":-9.0,
            "creates_new_rhythmic_attack":False,
        },
        "resource_intent":{
            "binding_key":"electric_bass_guitar",
            "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
            "production_fidelity_certified":False,
        },
        "forbidden":[
            "OFFBEAT_BASS_REATTACK",
            "OFFBEAT_PITCH_CHANGE",
            "CONTINUOUS_UNBOUNDED_SUSTAIN",
            "RANDOM_BASS_TIMING",
            "SYNTHETIC_TIMBRE_SUBSTITUTION",
        ],
        "evidence":{
            "human_decision":"D_PREFERRED",
            "decision_file":"ROCK_V3_BASS_ATTACK_HYBRID_HUMAN_DECISION_2026-11-07.json",
            "held_tone_decision":"C_PREFERRED_FOR_FUNCTION_AND_SUSTAIN",
            "attack_choice":"VICIOUS_TRANSIENT_MINUS_9_DB",
        },
    },
}


REGISTRY={
    "schema":SCHEMA,
    "status":REGISTRY_STATUS,
    "profiles":{
        "ROCK":{
            "ROCK_CORE_V2":ROCK_CORE_V2_PROFILES,
        }
    },
    "reasoning_engine_used":False,
    "canonical_policy_modified":False,
    "live_runtime_authority":False,
}


def resolve(genre:str,genre_profile_id:str,track_role:str)->dict[str,Any]:
    g=str(genre).upper()
    p=str(genre_profile_id)
    r=str(track_role).upper()
    try:
        profile=REGISTRY["profiles"][g][p][r]
    except KeyError as exc:
        raise InstrumentRolePerformanceProfileError(
            f"ROLE_PROFILE_NOT_FOUND::{g}::{p}::{r}"
        ) from exc
    result=deepcopy(profile)
    result["profile_sha256"]=_sha(profile)
    return result


def registry_snapshot()->dict[str,Any]:
    result=deepcopy(REGISTRY)
    result["registry_sha256"]=_sha(REGISTRY)
    return result


if __name__=="__main__":
    print(json.dumps(registry_snapshot(),indent=2))
