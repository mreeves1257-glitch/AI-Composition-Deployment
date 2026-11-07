"""Rock Core V3 performance-realization plan.

Non-rendering plan for applying instrument-specific performance to the validated
40-bar Rock Core symbolic composition candidate.

This module separates:
1) current V3 performance authority,
2) existing project-authored Rock guitar duration behavior,
3) prior isolated research candidates that remain NOT listening-approved.

No performance mutation is executed here.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for
from instrument_role_performance_profiles import resolve as resolve_role_profile
from rock_v3_core_development_executor import execute as build_symbolic_piece

SCHEMA="ROCK_V3_CORE_PERFORMANCE_PLAN_001"


class RockV3CorePerformancePlanError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def build()->dict[str,Any]:
    contract=contract_for("ROCK")
    piece=build_symbolic_piece()
    perf=contract.get("performance") or {}
    snapshot=contract.get("current_profile_snapshot") or {}

    approved_harmony_profile=resolve_role_profile("ROCK","ROCK_CORE_V2","HARMONY")
    approved_lead_profile=resolve_role_profile("ROCK","ROCK_CORE_V2","LEAD")
    approved_bass_profile=resolve_role_profile("ROCK","ROCK_CORE_V2","BASS")

    required=(
        "articulation_behavior","dynamic_behavior",
        "timing_humanization_behavior","continuous_performance_control",
        "interaction_rules",
    )
    missing=[key for key in required if not perf.get(key)]
    if missing:
        raise RockV3CorePerformancePlanError(
            "ROCK_V3_PERFORMANCE_AUTHORITY_MISSING::"+",".join(missing)
        )

    if "no independent random jitter" not in str(perf["timing_humanization_behavior"]):
        raise RockV3CorePerformancePlanError(
            "ROCK_V3_NO_RANDOM_JITTER_GUARD_MISSING"
        )

    plan={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "symbolic_execution_sha256":piece["execution_sha256"],
        "bar_count":piece["bar_count"],
        "tempo_bpm":piece["tempo_bpm"],
        "v3_performance_authority":deepcopy(perf),
        "v3_snapshot_performance_fields":{
            key:deepcopy(snapshot.get(key))
            for key in (
                "articulation_behavior","dynamic_behavior",
                "timing_humanization_behavior","continuous_performance_control",
                "instrument_role_behavior","ensemble_player_behavior",
                "bass_behavior","percussion_behavior_if_applicable",
            )
        },
        "role_plans":{
            "HARMONY":{
                "instrument_id":"electric_guitar",
                "role_state":"RHYTHM_POWER_CHORDS",
                "performance_mode":"VERTICAL_CHORD_GESTURE",
                "duration_policy":{
                    "source":"PROJECT_EXISTING_INSTRUMENT_PERFORMANCE_V1",
                    "close_attack_beats":0.105,
                    "rapid_phrase_beats":0.82,
                    "release_gap_beats":0.15,
                    "ring_fraction":0.84,
                    "max_ringing_beats":2.8,
                    "status":"PROJECT_AUTHORED_POLICY__REVALIDATE_ON_NEW_40_BAR_SCORE",
                    "v3_harmony_safety_cap":"DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE",
                },
                "attack_strum_candidate":{
                    "source":"ROCK_SHINYGUITAR_STRUM_ATTACK_TIMING_V1",
                    "max_cluster_gap_beats":0.047,
                    "note_gap_beats":0.038,
                    "max_strum_span_beats":0.14,
                    "alternate_direction":True,
                    "preserve_pitch_velocity_count":True,
                    "listening_approved":True,
                    "default_enabled":False,
                    "status":"HUMAN_APPROVED_DIAGNOSTIC__USED_BY_APPROVED_ROLE_PACKAGE__NOT_ENABLED_IN_MODE_A",
                },
                "forbidden":[
                    "KEYBOARD_BLOCK_ASSUMED_AS_FINAL_GUITAR_PERFORMANCE",
                    "RANDOM_STRING_TIMING",
                    "NEW_CHORD_NOTES_AT_STAGE5",
                ],
            },
            "LEAD":{
                "instrument_id":"electric_guitar",
                "role_state":"LEAD_MELODY",
                "performance_mode":"PICKED_MELODIC_PHRASE",
                "duration_policy":{
                    "source":"PROJECT_EXISTING_INSTRUMENT_PERFORMANCE_V1",
                    "rapid_phrase_connection_fraction":0.90,
                    "explicit_legato_connection_fraction":0.96,
                    "preserve_explicit_short_articulation":True,
                    "preserve_pitch_onset_velocity":True,
                    "status":"PROJECT_AUTHORED_POLICY__REVALIDATE_ON_NEW_40_BAR_SCORE",
                    "v3_harmony_safety_cap":"DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE",
                },
                "timing_policy":{
                    "random_jitter":False,
                    "phrase_push_pull":"NOT_EXECUTED_UNTIL_EXPLICIT_SHARED_GROOVE_RULE_EXISTS",
                    "status":"NO_UNGROUNDED_TIMING_MUTATION",
                },
                "forbidden":[
                    "GENERIC_OCTAVE_FLIP",
                    "RANDOM_MELODY_TIMING",
                    "CONTINUOUS_LEAD_FILL",
                    "SUSTAIN_ACROSS_UNVERIFIED_HARMONY_CHANGE",
                ],
            },
            "BASS":{
                "instrument_id":"electric_bass_guitar",
                "role_state":"BASS",
                "performance_mode":"LOCK_WITH_KICK__INDEPENDENT_LINE",
                "base_policy":"PRESERVE_SYMBOLIC_ONSETS_PITCHES_VELOCITIES",
                "sustain_candidate":{
                    "source":"ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT",
                    "next_attack_min_beats":0.80,
                    "next_attack_max_beats":2.50,
                    "spacing_fraction":0.78,
                    "max_sustain_beats":1.50,
                    "minimum_extension_beats":0.14,
                    "listening_approved":False,
                    "default_enabled":False,
                    "status":"REJECTED_AND_SUPERSEDED_BY_APPROVED_HELD_TONE_BASS_D_PROFILE",
                },
                "forbidden":[
                    "FORCE_CONTINUOUS_BASS_SUSTAIN",
                    "REMOVE_PHRASE_GAPS",
                    "CHANGE_PITCH_AT_PERFORMANCE_STAGE",
                ],
            },
            "KICK":{
                "instrument_id":"kick_drum_rock",
                "role_state":"KICK",
                "performance_mode":"SOURCE_PATTERN_ONE_SHOT",
                "timing_policy":"PRESERVE_AUTHORED_ONSETS",
                "random_jitter":False,
                "new_hits_allowed":False,
            },
            "SNARE":{
                "instrument_id":"snare_drum",
                "role_state":"SNARE",
                "performance_mode":"SOURCE_PATTERN_ONE_SHOT",
                "timing_policy":"PRESERVE_AUTHORED_ONSETS",
                "random_jitter":False,
                "new_hits_allowed":False,
            },
            "HAT":{
                "instrument_id":"hi_hat",
                "role_state":"HAT",
                "performance_mode":"SOURCE_PATTERN_TIMEKEEPING",
                "timing_policy":"PRESERVE_AUTHORED_ONSETS",
                "random_jitter":False,
                "new_hits_allowed":False,
            },
        },
        "approved_role_profile_refs":{
            "HARMONY":{
                "profile_id":approved_harmony_profile["profile_id"],
                "profile_sha256":approved_harmony_profile["profile_sha256"],
                "status":"HUMAN_APPROVED_DIAGNOSTIC",
            },
            "LEAD":{
                "profile_id":approved_lead_profile["profile_id"],
                "profile_sha256":approved_lead_profile["profile_sha256"],
                "status":"HUMAN_APPROVED_DIAGNOSTIC",
            },
            "BASS":{
                "profile_id":approved_bass_profile["profile_id"],
                "profile_sha256":approved_bass_profile["profile_sha256"],
                "status":"HUMAN_APPROVED_DIAGNOSTIC",
                "treatment":"HELD_CLEAN_BODY_PLUS_VICIOUS_TRANSIENT_MINUS_9_DB",
                "old_sustain_candidate_superseded":True,
            },
        },
        "approved_package_status":"AVAILABLE_VIA_ROCK_V3_APPROVED_PERFORMANCE_PACKAGE__NOT_LIVE_RUNTIME_AUTHORITY",
        "shared_groove_policy":{
            "status":"STRUCTURED_BUT_NOT_YET_MUTATING_TIMING",
            "authority":perf["timing_humanization_behavior"],
            "random_independent_offsets_allowed":False,
            "current_candidate_action":"KEEP_COMPOSITION_ONSETS_EXACT",
            "future_requirement":"Any phrase push/pull must move interacting roles relationally, not independently.",
        },
        "dynamic_policy":{
            "authority":perf["dynamic_behavior"],
            "current_candidate_action":"PRESERVE_COMPOSITION_VELOCITIES",
            "reason":"Section energy is already encoded upstream; Stage5 should not double-apply a generic chorus boost.",
        },
        "drum_policy":{
            "authority":snapshot.get("percussion_behavior_if_applicable"),
            "current_candidate_action":"PRESERVE_KICK_SNARE_HAT_EVENT_TIMING_AND_COUNT",
            "fill_rule":"Use only composition-authorized source-pattern fill states at this stage.",
            "random_jitter":False,
        },
        "candidate_modes":{
            "A_GUITAR_DURATION_ONLY":{
                "apply_guitar_duration_policy":True,
                "apply_rhythm_guitar_strum_candidate":False,
                "apply_bass_sustain_candidate":False,
                "status":"FIRST_STRUCTURAL_PERFORMANCE_CANDIDATE",
            },
            "B_GUITAR_DURATION_PLUS_STRUM":{
                "apply_guitar_duration_policy":True,
                "apply_rhythm_guitar_strum_candidate":True,
                "apply_bass_sustain_candidate":False,
                "status":"PRIOR_STRUM_RESEARCH_REQUIRES_LISTENING",
            },
            "C_GUITAR_PLUS_STRUM_PLUS_BASS_SUSTAIN":{
                "apply_guitar_duration_policy":True,
                "apply_rhythm_guitar_strum_candidate":True,
                "apply_bass_sustain_candidate":True,
                "status":"MULTI_VARIABLE__DO_NOT_USE_FOR_FIRST_LISTENING_COMPARISON",
            },
        },
        "recommended_first_symbolic_performance_mode":"A_GUITAR_DURATION_ONLY",
        "reasoning_engine_used":False,
        "notes_added":False,
        "pitches_changed":False,
        "velocities_changed":False,
        "drum_onsets_changed":False,
        "audio_generated":False,
        "audio_authority":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "listening_approval":False,
        "next_gate":"EXECUTE_AND_AUDIT_MODE_A_GUITAR_DURATION_ONLY",
    }
    plan["performance_plan_sha256"]=_sha(plan)
    return plan
