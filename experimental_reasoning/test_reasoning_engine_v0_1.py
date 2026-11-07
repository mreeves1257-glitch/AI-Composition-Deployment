"""Self-tests for Composer Musical Reasoning Engine v0.1.

Run directly:
    python experimental_reasoning/test_reasoning_engine_v0_1.py
"""
from reasoning_engine_v0_1 import (
    ComposerState,
    InstrumentMemory,
    MusicalIdeaMemory,
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
        test_hash_detects_mutation,
    ]
    for fn in tests:
        fn()
    print(f"PASS: {len(tests)} reasoning-engine v0.1 tests")
