"""Isolated 55-genre real component execution regression: NO deployment/audio."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import copy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "composer_overrides"))
from genre_styles.genre_owned_interpreter_dispatch import (
    connect_selected_genre_components, connect_all_55_component_checkpoints,
)
from genre_styles.shared_interpreter_router import (
    InterpreterConnectionError, ORIGINAL_STAGE_ORDER,
)
from genre_styles.source_pattern_library import read_pack
from genre_styles.source_pattern_resource_handoff import ORIGINAL_SOURCE_PROVENANCE


def recorded_original_rock_fixture():
    # Fixture is only registry metadata: *not* installed source audio.
    pinned = (
        ("electric_bass_guitar", "KARORYFER_GROWLYBASS_V1_002",
         "growlybass_clean.sfz"),
        ("electric_guitar:RHYTHM_POWER_CHORDS", "KARORYFER_SHINYGUITAR",
         "Programs/composer-electric.sfz"),
        ("kick_drum_rock", "KARORYFER_BIG_RUSTY_DRUMS",
         "Programs/composer-kick-lite.sfz"),
        ("snare_drum", "KARORYFER_BIG_RUSTY_DRUMS",
         "Programs/composer-snare-lite.sfz"),
        ("hi_hat", "KARORYFER_BIG_RUSTY_DRUMS",
         "Programs/composer-hihat-lite.sfz"),
    )
    return {identity: dict(
        resource_id=bank, preferred_mapping=sfz,
        resource_type="SFZ_SAMPLE_LIBRARY",
        fallback_policy="NO_SYNTHETIC_SUBSTITUTION",
        library=ORIGINAL_SOURCE_PROVENANCE[bank][0],
        license=ORIGINAL_SOURCE_PROVENANCE[bank][1],
    ) for identity, bank, sfz in pinned}


class All55ComponentHandoffs(unittest.TestCase):
    def test_all_55_complete_non_live_component_connections_and_original_maps(self):
        outputs = connect_all_55_component_checkpoints(target_bindings={})
        self.assertEqual(len(outputs), 55)
        self.assertEqual(len({p["family"] for p in outputs.values()}), 13)
        tally = Counter()
        for genre, response in outputs.items():
            with self.subTest(genre=genre):
                self.assertEqual(genre, response["genre"])
                self.assertEqual(response["original_seven_stage_order"],
                                 list(ORIGINAL_STAGE_ORDER))
                self.assertEqual(response["interpreter_inserted_between"],
                  ["CHOOSE_INSTRUMENTS_AND_DRUM_KIT", "COMPOSE_SEPARATE_PARTS"])
                self.assertTrue(response["stage3_to_interpreter"]["genre_exclusive"])
                self.assertTrue(response["stage4_to_stage5_performance"]
                                ["shared_22_capability_handlers_connected"])
                self.assertEqual(response["stage4_to_stage5_performance"]["handler_count"], 22)
                self.assertTrue(response["interpreter_to_original_stage4"]
                                ["candidate_only_not_active_composer_events"])
                self.assertEqual(response["interpreter_to_original_stage4"]
                                 ["candidate_event_count"], 0)
                self.assertEqual(response["stage5_to_stage6_recorded_stems"]
                                 ["stem_wav_count"], 0)
                self.assertFalse(response["stage5_to_stage6_recorded_stems"]["renderer_executed"])
                self.assertFalse(response["stage6_to_stage7_independent_3d_mixer"]["mixer_executed"])
                self.assertFalse(response["audio_render_authorized"])
                self.assertFalse(response["live_deployment_authorized"])
                self.assertFalse(response["live_composer_events_replaced"])
                self.assertTrue(response["original_event_list_unchanged"])
                self.assertTrue(response["connection_blockers"])
                self.assertEqual(response["status"],
                    "COMPONENTS_LINKED_IN_REHEARSAL_NOT_END_TO_END_AUDIO_COMPLETE")
                tally["source_roles"] += (
                    response["stage3_to_sound_mapping"]["mapped_symbolic_role_references"] +
                    len(response["stage3_to_sound_mapping"]["missing_or_rejected_symbolic_roles"]))
                tally["full_tracks"] += len(
                    response["stage5_to_stage6_recorded_stems"]["required_original_separate_tracks"])
                tally["full_pins"] += len(
                    response["stage5_to_stage6_recorded_stems"]["exact_recorded_program_reference_tracks"])
                tally["full_blocked"] += len(
                    response["stage5_to_stage6_recorded_stems"]["blocked_exact_program_tracks"])
                tally["interpreter_notes"] += response["stage3_to_interpreter"]["musical_event_count"]
                tally["executable_seed_genres"] += int(genre not in ("Jazz Waltz", "Salsa"))
                tally["external_waiting_genres"] += int(genre in ("Jazz Waltz", "Salsa"))
        # No original source file or recorded sample is modified to create this report.
        self.assertEqual(tally["full_tracks"], 315)
        self.assertEqual(tally["full_pins"], 66)
        self.assertEqual(tally["full_blocked"], 249)
        self.assertEqual(tally["source_roles"], 234)
        self.assertEqual(tally["executable_seed_genres"], 53)
        self.assertEqual(tally["external_waiting_genres"], 2)
        self.assertGreater(tally["interpreter_notes"], 1000)
        print("ALL_55_COMPONENT_CONNECTIONS_NO_AUDIO_PASS", dict(tally))

    def test_reset_rock_uses_new_own_pattern_not_old_pinned_mma(self):
        seed, _ = read_pack("ROCK")
        selected = {"status": "PASS", "palette":
            list(dict.fromkeys(x["instrument_id"] for x in seed["roles"])),
            "meter": seed["meter"], "tempo_bpm": seed["tempo_bpm"]}
        originals = [{"track_id": "ORIGINAL_LEAD", "instrument_id": "electric_guitar",
                      "start_beat": 0, "midi": 64, "velocity": 91}]
        copy_of_originals = copy.deepcopy(originals)
        result = connect_selected_genre_components(
            "ROCK", original_stage3_result=selected,
            original_composer_events=originals,
            target_bindings=recorded_original_rock_fixture(),
        )
        self.assertEqual(originals, copy_of_originals)
        self.assertTrue(result["original_event_list_unchanged"])
        self.assertGreater(result["stage3_to_interpreter"]["musical_event_count"], 30)
        self.assertEqual(result["stage3_to_sound_mapping"]
                         ["mapped_symbolic_role_references"], 5)
        self.assertEqual(result["interpreter_to_original_stage4"]["candidate_event_count"],
                         result["stage3_to_interpreter"]["musical_event_count"])
        self.assertEqual(result["interpreter_to_original_stage4"]["status"],
                         "CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING")
        self.assertEqual(len(result["stage5_to_stage6_recorded_stems"]
                             ["exact_recorded_program_reference_tracks"]), 9)
        self.assertIn("SEVEN_BAR_SOURCE_SEED_DOES_NOT_COVER_ALL_FULL_SONG_TRACKS",
                      result["connection_blockers"])
        self.assertFalse(result["audio_render_authorized"])
        self.assertFalse(result["live_composer_events_replaced"])

    def test_salsa_jazz_waltz_do_not_fake_missing_external_mma(self):
        for genre in ("Salsa", "Jazz Waltz"):
            seed, _ = read_pack(genre)
            stage3 = {"status": "PASS", "palette":
                      list(dict.fromkeys(x["instrument_id"] for x in seed["roles"])),
                      "meter": seed["meter"], "tempo_bpm": seed["tempo_bpm"]}
            result = connect_selected_genre_components(
                genre, original_stage3_result=stage3, target_bindings={})
            self.assertEqual(result["stage3_to_interpreter"]["musical_event_count"], 0)
            self.assertEqual(result["interpreter_to_original_stage4"]["candidate_event_count"], 0)
            self.assertIn("EXTERNAL_STYLE_NOT_YET_TRANSLATED_INTO_ORIGINAL_COMPOSER_EVENT_DIALECT",
                          result["connection_blockers"])
            self.assertFalse(result["audio_render_authorized"])

    def test_invalid_role_source_and_stage3_cross_genre_are_not_accepted(self):
        seed, _ = read_pack("ROCK")
        originals = [{"track_id": "UNTOUCHED", "midi": 60}]
        with self.assertRaises(InterpreterConnectionError):
            connect_selected_genre_components(
                "ROCK", original_stage3_result=dict(
                    status="PASS", palette=["piano"], meter="3/4",
                    tempo_bpm=seed["tempo_bpm"]),
                original_composer_events=originals, target_bindings={})
        with self.assertRaises(InterpreterConnectionError):
            connect_selected_genre_components(
                "NONEXISTENT_GENRE",
                original_stage3_result={"status": "PASS",
                                        "palette": ["piano"], "meter": "4/4",
                                        "tempo_bpm": 120})
        self.assertEqual(originals, [{"track_id": "UNTOUCHED", "midi": 60}])

if __name__ == "__main__":
    unittest.main(verbosity=2)
