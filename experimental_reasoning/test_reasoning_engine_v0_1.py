"""Self-tests for Composer Musical Reasoning Engine v0.1.

Run directly:
    python experimental_reasoning/test_reasoning_engine_v0_1.py
"""
from reasoning_engine_v0_1 import ComposerState, MusicalGoal, reason, validate


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


def test_bridge_requires_contrast_but_not_more_volume():
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
    assert d["instrument_balance"]["mode"] == "COMPLETE_EQUAL_BALANCE"


def test_complete_equal_instrument_balance_is_default():
    state = ComposerState(
        genre="Funk",
        profile_id="FUNK_PROFILE",
        section="Chorus",
    )
    packet = reason(state=state)
    validate(packet)
    b = packet["decisions"]["instrument_balance"]
    assert b["target_0_to_1"] == 1.0
    assert b["relative_prominence"] == "EQUAL"
    assert b["persistent_instrument_dominance_allowed"] is False
    assert b["identical_note_density_required"] is False
    assert b["solo_or_feature_exception"] == "REQUIRES_EXPLICIT_OVERRIDE"


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
        test_bridge_requires_contrast_but_not_more_volume,
        test_complete_equal_instrument_balance_is_default,
        test_hash_detects_mutation,
    ]
    for fn in tests:
        fn()
    print(f"PASS: {len(tests)} reasoning-engine v0.1 tests")
