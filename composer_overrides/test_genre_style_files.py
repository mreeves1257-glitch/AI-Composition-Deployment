"""Regression guard: finish Jazz Ballad before designing other Jazz styles.

The Jazz family catalog is shared, but only Jazz Ballad has an active
arrangement/instrument package. Rock remains an isolated style module.
"""
from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genre_styles.registry import GENRE_STYLE_MODULES, JAZZ_GENRE_PROFILES, get_style
from genre_development_patch import (
    JAZZ_GENRE_PROFILES as COMPATIBLE_PROFILES,
    build_jazz_progression,
    realize_jazz_voicings,
    apply_jazz_phrase_expression,
)
from genre_styles.Jazz.jazz_ballad import (
    chord_progression as ballad_progression,
    arrange_events,
    balance_mix,
    instrument_links,
    validate_instrument_links,
)

JAZZ_ROOT = Path(__file__).resolve().parent / "genre_styles" / "Jazz"
ROLES = {"HARMONY", "LEAD", "BASS", "KICK", "SNARE", "HAT"}


class GenreStyleFileTests(unittest.TestCase):
    def test_independent_files_and_rock(self):
        self.assertEqual(JAZZ_GENRE_PROFILES, COMPATIBLE_PROFILES)
        self.assertEqual(set(JAZZ_GENRE_PROFILES), set(GENRE_STYLE_MODULES) - {"ROCK"})
        self.assertEqual(GENRE_STYLE_MODULES["ROCK"], "Rock.rock")
        file_paths = set()
        for genre, module_name in GENRE_STYLE_MODULES.items():
            module = importlib.import_module("genre_styles." + module_name)
            self.assertEqual(module.GENRE_NAME, genre)
            self.assertTrue(Path(module.__file__).is_file())
            self.assertNotIn(module.__file__, file_paths)
            file_paths.add(module.__file__)
            if genre != "ROCK":
                self.assertTrue(module_name.startswith("Jazz."))
        self.assertEqual(len(file_paths), 9)

    def test_ballad_only_active_style(self):
        for genre, profile_id in JAZZ_GENRE_PROFILES.items():
            profile = {"resolution_policy": "AUTOMATIC_BASELINE_ALLOWED",
                       "profile_id": profile_id}
            module_name = GENRE_STYLE_MODULES[genre]
            module = importlib.import_module("genre_styles." + module_name)
            if genre == "Jazz Ballad":
                self.assertIs(get_style(genre, profile), module)
                output = build_jazz_progression(genre, profile, "major", 64, 19)
                self.assertEqual(output, ballad_progression(64, 19))
                self.assertEqual(output[-1], "I")
                self.assertTrue(all(len(set(output[i:i+4])) > 1 for i in range(61)))
                self.assertTrue(callable(arrange_events))
                self.assertTrue(callable(balance_mix))
            else:
                self.assertEqual(module.DEVELOPMENT_STATUS, "NOT_STARTED")
                self.assertFalse(hasattr(module, "chord_progression"), genre)
                self.assertFalse(hasattr(module, "instrument_links"), genre)
                self.assertFalse(hasattr(module, "arrange_events"), genre)
                self.assertIsNone(get_style(genre, profile), genre)
                mode = "natural_minor" if genre == "Jazz Fusion" else "major"
                self.assertIsNone(build_jazz_progression(genre, profile, mode, 32, 19))

    def test_one_canonical_jazz_instrument_library_and_ballad_links(self):
        from genre_styles.Jazz.instrument_packages import load_package
        with (JAZZ_ROOT / "instrument_library.json").open(encoding="utf-8") as f:
            catalog = json.load(f)
        self.assertEqual(catalog["library"], "Jazz")
        self.assertEqual(catalog["shared_root"], "sound_resources")
        self.assertEqual(len(catalog["instruments"]), 6)
        package = instrument_links()
        self.assertEqual(package, load_package("jazz_ballad"))
        self.assertEqual(package["binding_status"], "VERIFIED_RECORDED_SOURCES")
        self.assertEqual(package["source_library"], "Jazz/instrument_library.json")
        self.assertEqual(set(package["instruments"]), ROLES)
        self.assertEqual(package["instruments"]["HARMONY"]["sound_preservation"],
                         "KEEP_APPROVED_WURLITZER_PIANO")
        bindings = {
            s["registry_binding"]: {
                "resource_id": s["resource_id"],
                "preferred_mapping": s["sfz"],
                "resource_type": "SFZ_SAMPLE_LIBRARY",
            } for s in package["instruments"].values()
        }
        validate_instrument_links(bindings)
        package["instruments"]["HARMONY"]["resource_id"] = "BROKEN_COPY_ONLY"
        self.assertEqual(instrument_links()["instruments"]["HARMONY"]["resource_id"],
                         "GREG_SULLIVAN_E_PIANOS")
        bindings["clarinet_bb"]["preferred_mapping"] = "bad.sfz"
        with self.assertRaisesRegex(ValueError, "JAZZ_INSTRUMENT_LINK_MISMATCH"):
            validate_instrument_links(bindings)

    def test_other_seven_packages_preserve_original_source_ids(self):
        source = json.loads((JAZZ_ROOT / "SOURCE_RESOURCE_BINDINGS_R1.json").read_text())
        by_genre = {item["genre"]: item for item in source["genres"]}
        for genre, module_name in GENRE_STYLE_MODULES.items():
            if genre in ("ROCK", "Jazz Ballad"):
                continue
            style_id = module_name.rsplit(".", 1)[-1]
            manifest = JAZZ_ROOT / "instrument_packages" / (style_id + ".json")
            with manifest.open(encoding="utf-8") as f:
                package = json.load(f)
            self.assertEqual(package["genre"], genre)
            self.assertEqual(package["library"], "../instrument_library.json")
            self.assertFalse(package["production_enabled"])
            self.assertTrue(package["approved_3d_mixer_unchanged"])
            original = by_genre[genre]["role_bindings"]
            self.assertEqual(set(package["roles"]), set(original))
            for role, binding in original.items():
                self.assertEqual(package["roles"][role]["instrument_id"],
                                 binding["original_instrument_id"])
                if binding["lookup_policy"] != "EXACT_ID":
                    self.assertEqual(package["roles"][role]["source_binding_status"],
                                     "BLOCKED_UNVERIFIED")

    def test_undeveloped_jazz_does_not_change_existing_theory(self):
        context = {"harmony": {"chords": []}, "meter": {"numerator": 4, "denominator": 4}}
        for genre, profile_id in JAZZ_GENRE_PROFILES.items():
            if genre == "Jazz Ballad":
                continue
            profile = {"profile_id": profile_id,
                       "resolution_policy": "AUTOMATIC_BASELINE_ALLOWED"}
            self.assertIs(realize_jazz_voicings(context, genre, profile), context)
            events = [{"track_id": "HARMONY", "velocity": 77, "start_beat": 4}]
            self.assertIs(apply_jazz_phrase_expression(events, genre, profile, 4), events)

    def test_rock_balance_is_untouched(self):
        from genre_styles.Rock.rock import balance_mix
        from genre_styles.Rock.rock_balance_contract import apply_rock_balance
        original = {"genre": "Jazz Ballad", "modules": {}}
        self.assertIs(apply_rock_balance(original), original)
        self.assertIs(balance_mix(original), original)

    def test_controlled_and_unknown_no_fallback(self):
        profile = {"profile_id": "JAZZ_BALLAD_V1",
                   "resolution_policy": "REQUIRES_HUMAN_CONTROL"}
        self.assertIsNone(get_style("Jazz Ballad", profile))
        self.assertIsNone(build_jazz_progression("Jazz Ballad", profile, "major", 32, 19))
        self.assertIsNone(get_style("Unknown Genre", profile))


if __name__ == "__main__":
    unittest.main()
