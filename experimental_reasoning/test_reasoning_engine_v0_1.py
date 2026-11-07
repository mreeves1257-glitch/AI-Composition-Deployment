"""Self-tests for Composer Musical Reasoning Engine v0.1.

Run directly:
    python experimental_reasoning/test_reasoning_engine_v0_1.py
"""
from reasoning_engine_v0_1 import (
    ComposerState,
    InstrumentMemory,
    MusicalIdeaMemory,
    SpatialSceneMemory,
    MusicalGoal,
    reason,
    validate,
)


def test_verse_two_after_chorus_pulls_back_and_develops():
    state = ComposerState(
        genre="Rock",
        profile_id="ROCK_PROFILE",
        section="Verse",
        section_occurrence=2,
        previous_section="Chorus",
        next_section="Chorus",
        bars_elapsed=24,
        bars_in_section=0,
        previous_energy=0.88,
        current_energy=0.84,
    )
    packet = reason(
        state=state,
        semantic_tags=["riff_vamp", "syncopated"],
        generation_plan={
            "melody_development_bars": 16,
            "literal_melody_reuse_after_bars": 16,
        },
    )
    validate(packet)
    d = packet["decisions"]
    assert d["energy"]["motion"] == "PULL_BACK"
    assert d["density"]["target_level_1_to_5"] <= 3
    assert d["melody"]["section_is_repeat"] is True
    assert "VARY_CONTOUR_OR_RHYTHM_OR_REGISTER" in d["melody"]["instructions"]
    assert d["transition"]["mode"] == "BUILD_TOWARD_NEXT_SECTION"


def test_chorus_builds_without_choosing_instruments():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Chorus",
        previous_section="Pre-Chorus",
        next_section="Verse",
        bars_elapsed=16,
        current_energy=0.62,
    )
    packet = reason(
        state=state,
        semantic_tags=["gospel", "syncopated", "call_response"],
        goal=MusicalGoal(emotional_direction="build"),
    )
    validate(packet)
    d = packet["decisions"]
    assert d["energy"]["motion"] == "BUILD"
    assert d["density"]["target_level_1_to_5"] >= 4
    assert d["roles"]["do_not_choose_specific_instruments_here"] is True


def test_bridge_requires_contrast_without_creating_instrument_hierarchy():
    state = ComposerState(
        genre="Jazz Ballad",
        profile_id="JAZZ_BALLAD_PROFILE",
        section="Bridge",
        section_occurrence=1,
        previous_section="Chorus",
        next_section="Chorus",
        bars_elapsed=32,
        current_energy=0.78,
    )
    packet = reason(
        state=state,
        semantic_tags=["extended", "laidback"],
    )
    validate(packet)
    d = packet["decisions"]
    assert d["contrast"]["required"] is True
    assert d["roles"]["foreground_policy"] == "NO_PERSISTENT_INSTRUMENT_DOMINANCE"
    assert d["instrument_balance"]["mode"] == "COMPLETE_EQUAL_IMPORTANCE"


def test_equal_importance_is_not_equal_notes_or_equal_volume():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Chorus",
        active_instruments=("drums", "bass", "guitar", "keys"),
    )
    packet = reason(state=state)
    validate(packet)
    b = packet["decisions"]["instrument_balance"]
    assert b["target_0_to_1"] == 1.0
    assert b["compositional_importance"] == "EQUAL"
    assert b["persistent_structural_subordination_allowed"] is False
    assert b["identical_note_density_required"] is False
    assert b["identical_loudness_required"] is False
    assert b["identical_foreground_time_required"] is False


def test_importance_ledger_prioritizes_instrument_that_has_been_neglected():
    state = ComposerState(
        genre="Country",
        profile_id="COUNTRY_PROFILE",
        section="Verse",
        active_instruments=("drums", "bass", "guitar", "fiddle"),
        instrument_history=(
            InstrumentMemory("drums", meaningful_windows=4, total_windows=4, last_role="groove"),
            InstrumentMemory("bass", meaningful_windows=4, total_windows=4, last_role="foundation"),
            InstrumentMemory("guitar", meaningful_windows=4, total_windows=4, last_role="harmony"),
            InstrumentMemory("fiddle", meaningful_windows=1, total_windows=4, last_role="rest"),
        ),
    )
    packet = reason(state=state)
    validate(packet)
    p = packet["decisions"]["instrument_importance_plan"]
    assert p["target"] == "EQUAL_COMPOSITIONAL_IMPORTANCE"
    assert p["importance_unit"] == "MEANINGFUL_MUSICAL_FUNCTION"
    assert p["note_quantity_is_importance"] is False
    assert p["priority_for_next_window"] == ["fiddle"]
    assert p["priority_rule"] == "RESTORE_UNDERSERVED_INSTRUMENTS_TO_MEANINGFUL_FUNCTION"


def test_equal_importance_creates_conversation_not_permanent_background():
    state = ComposerState(
        genre="Rock",
        profile_id="ROCK_PROFILE",
        section="Chorus",
        active_instruments=("drums", "bass", "guitar", "keys"),
        instrument_history=(
            InstrumentMemory("drums", meaningful_windows=3, total_windows=3, last_role="groove"),
            InstrumentMemory("bass", meaningful_windows=3, total_windows=3, last_role="foundation"),
            InstrumentMemory("guitar", meaningful_windows=3, total_windows=3, last_role="riff"),
            InstrumentMemory("keys", meaningful_windows=2, total_windows=3, last_role="texture"),
        ),
    )
    packet = reason(state=state)
    validate(packet)
    p = packet["decisions"]["instrument_interaction_plan"]
    assert p["status"] == "PASS"
    assert p["assignment_priority"] == ["keys"]
    assert "PERMANENT_HIERARCHY" in p["principle"]
    assert "NO_INSTRUMENT_IS_PERMANENTLY_CLASSIFIED_AS_LESS_IMPORTANT" in p["hierarchy_rule"]
    assert p["space_rule"] == "NOT_ALL_INSTRUMENTS_MUST_PLAY_SIMULTANEOUSLY"


def test_musical_memory_recalls_idea_as_transformed_conversation():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Verse",
        section_occurrence=2,
        bars_elapsed=32,
        active_instruments=("drums", "bass", "guitar", "keys"),
        instrument_history=(
            InstrumentMemory("drums", meaningful_windows=4, total_windows=4, last_role="groove"),
            InstrumentMemory("bass", meaningful_windows=4, total_windows=4, last_role="foundation"),
            InstrumentMemory("guitar", meaningful_windows=4, total_windows=4, last_role="answer"),
            InstrumentMemory("keys", meaningful_windows=2, total_windows=4, last_role="texture"),
        ),
        musical_idea_history=(
            MusicalIdeaMemory(
                idea_id="IDEA_A",
                origin_section="Verse",
                origin_instrument="guitar",
                contour_signature="RISE_FALL",
                rhythm_signature="SHORT_SHORT_LONG",
                harmonic_relation="CHORD_TONE_TO_EXTENSION",
                expressive_character="QUESTIONING",
                introduced_bar=4,
                last_seen_bar=12,
                appearances=2,
                transformations=1,
                last_carrier="guitar",
            ),
        ),
    )
    packet = reason(
        state=state,
        generation_plan={"literal_melody_reuse_after_bars": 16},
    )
    validate(packet)
    m = packet["decisions"]["musical_memory"]
    assert m["status"] == "PASS"
    assert m["selected_idea_id"] == "IDEA_A"
    assert m["action"] == "TRANSFORM_AND_RECALL"
    assert m["preferred_next_carrier"] == "keys"
    assert m["literal_copy_requested"] is False
    assert m["exact_recall_eligible"] is True
    assert "TRANSFER_TO_ANOTHER_COMPATIBLE_INSTRUMENT" in m["transformation_choices"]


def test_musical_memory_allows_dormancy_and_does_not_force_every_idea_back():
    state = ComposerState(
        genre="Ambient",
        profile_id="AMBIENT_PROFILE",
        section="Intro",
        bars_elapsed=6,
        musical_idea_history=(
            MusicalIdeaMemory(
                idea_id="IDEA_SPACE",
                origin_section="Intro",
                contour_signature="STATIC",
                rhythm_signature="LONG_SUSTAIN",
                expressive_character="OPEN",
                introduced_bar=2,
                last_seen_bar=5,
                appearances=2,
                transformations=1,
            ),
        ),
    )
    packet = reason(state=state)
    validate(packet)
    m = packet["decisions"]["musical_memory"]
    assert m["literal_copy_requested"] is False
    assert "NOT_EVERY_IDEA_MUST_RETURN_IMMEDIATELY" in m["dormancy_rule"]


def test_bass_defaults_to_maximum_rich_depth_without_higher_importance():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Chorus",
        active_instruments=("drums", "bass", "guitar", "keys"),
    )
    packet = reason(state=state)
    validate(packet)
    b = packet["decisions"]["bass_character"]
    assert b["target_0_to_1"] == 1.0
    assert b["mode"] == "MAXIMUM_RICH_DEPTH"
    assert b["sound_character"]["depth"] == "VERY_DEEP"
    assert b["sound_character"]["weight"] == "POWERFUL"
    assert b["sound_character"]["body"] == "FULL_AND_RICH"
    assert b["compositional_importance_change"] is False
    assert "EQUAL_IN_COMPOSITIONAL_IMPORTANCE" in b["importance_rule"]


def test_rich_bass_preserves_clarity_and_low_end_separation():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Verse",
        active_instruments=("kick", "bass", "guitar", "clav"),
    )
    packet = reason(state=state, semantic_tags=("syncopated",))
    validate(packet)
    b = packet["decisions"]["bass_character"]
    assert "MUD" in b["clarity_policy"]
    assert "KICK_AND_BASS" in b["kick_relationship"]
    assert b["sound_character"]["harmonic_definition"] == "PRESENT"
    assert b["v0_1_audio_processing_applied"] is False


def test_3d_spatial_intent_is_planned_early_but_processed_late():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Chorus",
        active_instruments=("drums", "bass", "guitar", "keys"),
    )
    packet = reason(state=state)
    validate(packet)
    s = packet["decisions"]["spatial_3d_intent"]
    assert s["architecture"] == "SPATIAL_INTENT_EARLY__PHYSICAL_3D_MIX_LATE"
    assert s["planning_stage"] == "PRE_GENERATION_REASONING"
    assert s["realization_stage"] == "POST_STEM_EXISTING_3D_MIXER"
    assert s["move_existing_mixer_now"] is False
    assert s["audio_processing_applied_here"] is False


def test_3d_bass_position_preserves_depth_without_more_importance():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Verse",
        active_instruments=("kick", "bass", "guitar", "clav"),
    )
    packet = reason(state=state)
    validate(packet)
    b = packet["decisions"]["spatial_3d_intent"]["bass_spatial_rule"]
    assert b["depth"] == "DEEP_AND_PHYSICALLY_GROUNDED"
    assert b["importance_change"] is False
    assert "KICK" in b["masking_guardrail"]


def test_kick_defaults_to_maximum_pronounced_impact_without_higher_importance():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Chorus",
        active_instruments=("kick", "bass", "guitar", "clav"),
    )
    packet = reason(state=state)
    validate(packet)
    k = packet["decisions"]["kick_character"]
    assert k["target_0_to_1"] == 1.0
    assert k["mode"] == "MAXIMUM_PRONOUNCED_IMPACT"
    assert k["sound_character"]["impact"] == "VERY_PRONOUNCED"
    assert k["sound_character"]["punch"] == "STRONG"
    assert k["sound_character"]["physical_feel"] == "HIGH"
    assert k["compositional_importance_change"] is False


def test_kick_and_bass_have_distinct_low_end_jobs():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Verse",
        active_instruments=("kick", "bass", "keys", "guitar"),
    )
    packet = reason(state=state)
    validate(packet)
    k = packet["decisions"]["kick_character"]
    s = packet["decisions"]["spatial_3d_intent"]
    assert "KICK_PROVIDES_IMPACT" in k["bass_relationship"]
    assert s["kick_spatial_rule"]["impact_target"] == 1.0
    assert s["kick_spatial_rule"]["importance_change"] is False
    assert s["bass_spatial_rule"]["importance_change"] is False
    assert "TIGHT_CONTROLLED" in s["kick_spatial_rule"]["width"]


def test_chorus_spatial_scene_expands_from_verse_without_random_motion():
    state = ComposerState(
        genre="Soul",
        profile_id="SOUL_PROFILE",
        section="Chorus",
        previous_section="Verse",
        active_instruments=("kick", "bass", "guitar", "keys"),
        spatial_history=(
            SpatialSceneMemory(section="Verse", width="MEDIUM", depth="MEDIUM_DEEP", intimacy="CLOSE"),
        ),
    )
    packet = reason(state=state)
    validate(packet)
    s = packet["decisions"]["spatial_choreography"]
    assert s["target_scene"]["width"] == "WIDE"
    assert "EXPAND_WIDTH_AND_DEPTH" in s["transition"]
    assert "RANDOM_PANNING" in s["continuity_rule"]
    assert "KICK_AND_BASS_REMAIN_SPATIALLY_STABLE" in s["low_end_anchor_rule"]


def test_spatial_choreography_uses_clarity_before_loudness_for_underserved_instrument():
    state = ComposerState(
        genre="Country",
        profile_id="COUNTRY_PROFILE",
        section="Verse",
        active_instruments=("kick", "bass", "guitar", "fiddle"),
        instrument_history=(
            InstrumentMemory("kick", meaningful_windows=4, total_windows=4, last_role="groove"),
            InstrumentMemory("bass", meaningful_windows=4, total_windows=4, last_role="foundation"),
            InstrumentMemory("guitar", meaningful_windows=4, total_windows=4, last_role="harmony"),
            InstrumentMemory("fiddle", meaningful_windows=1, total_windows=4, last_role="rest"),
        ),
    )
    packet = reason(state=state)
    validate(packet)
    s = packet["decisions"]["spatial_choreography"]
    assert s["underserved_instruments"] == ["fiddle"]
    assert "CLEARER SPACE" in s["underserved_instrument_rule"]
    assert "BEFORE GAIN" in s["clarity_over_loudness_rule"]


def test_low_end_interaction_keeps_kick_and_bass_distinct_but_coherent():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Chorus",
        active_instruments=("kick", "bass", "guitar", "clav"),
    )
    packet = reason(state=state, semantic_tags=("syncopated",))
    validate(packet)
    p = packet["decisions"]["low_end_interaction"]
    assert p["relationship"] == "INTERLOCK_AND_ANSWER"
    assert p["kick_job"] == "PHYSICAL_IMPACT_AND_PULSE_DEFINITION"
    assert p["bass_job"] == "SUSTAINED_DEPTH_TONAL_BODY_AND_MOTION"
    assert "TWO_DISTINCT_VOICES" in p["shared_job"]
    assert "SIMPLY MAKING EITHER PART WEAKER" in p["density_rule"]


def test_walking_bass_is_not_forced_to_duplicate_every_kick():
    state = ComposerState(
        genre="Swing",
        profile_id="SWING_PROFILE",
        section="Verse",
        active_instruments=("kick", "double_bass", "ride", "piano"),
    )
    packet = reason(state=state, semantic_tags=("walking",))
    validate(packet)
    p = packet["decisions"]["low_end_interaction"]
    assert p["relationship"] == "KICK_PUNCTUATES_WHILE_BASS_CARRIES_CONTINUOUS_MOTION"
    assert any("DO_NOT_FORCE_WALKING_BASS_TO DUPLICATE_EVERY_KICK" in x for x in p["instructions"])


def test_hash_detects_mutation():
    state = ComposerState(
        genre="Country",
        profile_id="COUNTRY_PROFILE",
        section="Verse",
    )
    packet = reason(state=state)
    packet["decisions"]["density"]["target_level_1_to_5"] = 5
    try:
        validate(packet)
    except ValueError as exc:
        assert str(exc) == "REASONING_DECISION_HASH_MISMATCH"
    else:
        raise AssertionError("mutation was not detected")


if __name__ == "__main__":
    tests = [
        test_verse_two_after_chorus_pulls_back_and_develops,
        test_chorus_builds_without_choosing_instruments,
        test_bridge_requires_contrast_without_creating_instrument_hierarchy,
        test_equal_importance_is_not_equal_notes_or_equal_volume,
        test_importance_ledger_prioritizes_instrument_that_has_been_neglected,
        test_equal_importance_creates_conversation_not_permanent_background,
        test_musical_memory_recalls_idea_as_transformed_conversation,
        test_musical_memory_allows_dormancy_and_does_not_force_every_idea_back,
        test_bass_defaults_to_maximum_rich_depth_without_higher_importance,
        test_rich_bass_preserves_clarity_and_low_end_separation,
        test_3d_spatial_intent_is_planned_early_but_processed_late,
        test_3d_bass_position_preserves_depth_without_more_importance,
        test_kick_defaults_to_maximum_pronounced_impact_without_higher_importance,
        test_kick_and_bass_have_distinct_low_end_jobs,
        test_chorus_spatial_scene_expands_from_verse_without_random_motion,
        test_spatial_choreography_uses_clarity_before_loudness_for_underserved_instrument,
        test_low_end_interaction_keeps_kick_and_bass_distinct_but_coherent,
        test_walking_bass_is_not_forced_to_duplicate_every_kick,
        test_hash_detects_mutation,
    ]
    for fn in tests:
        fn()
    print(f"PASS: {len(tests)} reasoning-engine v0.1 tests")
