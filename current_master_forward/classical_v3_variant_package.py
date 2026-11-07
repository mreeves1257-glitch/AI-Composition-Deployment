"""Resolve evidence-backed Classical V3 packages for structural compilation.

Diagnostic branch only. This module does not generate notes or audio and does
not invoke the experimental reasoning engine.

The generic genre label "Classical" is not itself an executable formation.
A concrete period/ensemble package must be resolved first.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

PACKAGE_ID = "CLASSICAL_V3_VARIANT_PACKAGE_001"

SUPPORTED = {
    "CLASSICAL_PERIOD_ORCHESTRAL": {
        "candidate_variant_label": "Classical-period orchestral",
        "composition_grammar_key": "CLASSICAL_PERIOD_TONAL",
        "melody_behavior_key": "CLASSICAL_PERIOD_TONAL",
        "role_state_key": "CLASSICAL_SYMPHONIC_BASELINE",
    },
}


class ClassicalV3VariantError(RuntimeError):
    pass


def resolve(profile: dict[str, Any], variant_id: str) -> dict[str, Any]:
    if variant_id not in SUPPORTED:
        raise ClassicalV3VariantError("CLASSICAL_V3_VARIANT_NOT_SUPPORTED")

    source = profile.get("_genre_contract_v3_source") or {}
    if source.get("genre_name") != "Classical":
        raise ClassicalV3VariantError("CLASSICAL_V3_PROFILE_SOURCE_MISMATCH")

    v3 = profile.get("_genre_contract_v3") or {}
    variant_resolution = v3.get("variant_resolution") or {}
    spec = SUPPORTED[variant_id]

    if spec["candidate_variant_label"] not in variant_resolution.get("candidate_variants", []):
        raise ClassicalV3VariantError("CLASSICAL_V3_CANDIDATE_VARIANT_MISSING")

    composition = (
        variant_resolution.get("candidate_composition_grammar", {})
        .get(spec["composition_grammar_key"])
    )
    melody = (
        variant_resolution.get("candidate_melody_behavior", {})
        .get(spec["melody_behavior_key"])
    )
    role_state = (
        variant_resolution.get("candidate_role_state_priors", {})
        .get("variants", {})
        .get(spec["role_state_key"])
    )
    if not composition or not melody or not role_state:
        raise ClassicalV3VariantError("CLASSICAL_V3_PACKAGE_COMPONENT_MISSING")

    # Empirical references are carried as validation evidence, never copied as
    # literal generation quotas.
    from genre_contract_v3_execution_bridge import contract_for
    contract = contract_for("Classical")
    grammar_ref = (
        contract.get("composition_grammar_empirical_reference", {})
        .get("sources", {})
        .get("classical_period_mozart", {})
    )
    melody_ref = (
        contract.get("melody_empirical_reference", {})
        .get("classical_period_mozart", {})
    )
    ensemble = contract.get("ensemble") or {}
    performance = contract.get("performance") or {}
    musical_grammar = contract.get("musical_grammar") or {}

    package = {
        "package_id": PACKAGE_ID,
        "status": "RESEARCH_PACKAGE_READY_FOR_STRUCTURAL_COMPILER__NOT_AUDIO_APPROVED",
        "genre": "Classical",
        "variant_id": variant_id,
        "candidate_variant_label": spec["candidate_variant_label"],
        "source_contract_sha256": source.get("contract_sha256"),
        "evidence_level": {
            "composition": composition.get("evidence_level"),
            "orchestration_role_state": role_state.get("evidence_level"),
            "melody_reference_status": (
                contract.get("melody_empirical_reference", {}).get("status")
            ),
        },
        "composition_grammar": deepcopy(composition),
        "melody_behavior": deepcopy(melody),
        "role_state": deepcopy(role_state),
        "ensemble_roster": deepcopy(ensemble.get("instrument_roster") or []),
        "performance": deepcopy(performance),
        "family_grammar": deepcopy(musical_grammar),
        "empirical_validation_reference": {
            "harmony": {
                "mean_harmony_duration_quarterbeats": grammar_ref.get(
                    "mean_harmony_duration_quarterbeats"
                ),
                "harmonic_event_duration_bins_percent": deepcopy(
                    grammar_ref.get("harmonic_event_duration_bins_percent")
                ),
                "cadence_distribution_percent": deepcopy(
                    grammar_ref.get("cadence_distribution_percent")
                ),
                "tonicized_or_localkey_not_global_tonic_duration_percent":
                    grammar_ref.get(
                        "tonicized_or_localkey_not_global_tonic_duration_percent"
                    ),
                "applied_harmony_event_percent":
                    grammar_ref.get("applied_harmony_event_percent"),
                "diminished_chord_type_percent":
                    grammar_ref.get("diminished_chord_type_percent"),
                "seventh_or_extended_chord_type_percent":
                    grammar_ref.get("seventh_or_extended_chord_type_percent"),
            },
            "melody": {
                "notes_per_quarterbeat":
                    melody_ref.get("notes_per_quarterbeat"),
                "mean_absolute_interval_semitones":
                    melody_ref.get("mean_absolute_interval_semitones"),
                "interval_distribution_percent": deepcopy(
                    melody_ref.get("interval_distribution_percent")
                ),
                "selected_note_duration_percent": deepcopy(
                    melody_ref.get("selected_note_duration_percent")
                ),
                "direction_change_percent":
                    melody_ref.get("direction_change_percent"),
            },
        },
        "execution_requirements": {
            "variant_must_be_resolved_before_note_generation": True,
            "fixed_one_chord_per_bar_default_forbidden": True,
            "fixed_eight_bar_only_phrase_default_forbidden": True,
            "harmonic_rhythm_must_vary_within_phrase": True,
            "vertical_harmony_validation_required": True,
            "simultaneous_harmonic_support_required": True,
            "monophonic_single_note_texture_cannot_be_default": True,
            "audible_foreground_melody_required": True,
            "melody_requires_active_small_values_with_phrase_breathing": True,
            "mechanically_even_attack_grid_forbidden": True,
            "whole_note_like_staccato_pacing_forbidden": True,
            "tempo_must_be_resolved_from_piece_character_not_test_harness_constant": True,
            "cadence_choice_must_follow_formal_function": True,
            "inner_voice_and_bass_voice_leading_required": True,
            "orchestration_cannot_mask_composition_failure": True,
        },
        "human_listening_failures_to_prevent": [
            "no convincing melody",
            "harmony sounded off",
            "single-note-at-a-time texture",
            "mechanically even attacks",
            "staccato whole-note-like pacing",
            "extremely slow perceived tempo",
        ],
        "promotion_gate": (
            "STRUCTURAL_COMPILER_PASS__THEN_PIANO_COMPOSITION_LISTENING__"
            "THEN_ORCHESTRATION__NO_LIVE_MERGE_BEFORE_HUMAN_APPROVAL"
        ),
    }
    return package
