"""Independent genre-file routing regression tests.

Keeps the existing Composer and its protected Rock path unchanged.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genre_styles.registry import (
    GENRE_STYLE_MODULES, JAZZ_GENRE_PROFILES, get_style
)
from genre_development_patch import (
    JAZZ_GENRE_PROFILES as COMPATIBLE_PROFILES,
    build_jazz_progression, realize_jazz_voicings,
    apply_jazz_phrase_expression,
)
from genre_styles.jazz_ballad import (
    chord_progression as ballad_progression,
    arrange_events, balance_mix
)


class GenreStyleFileTests(unittest.TestCase):
    def test_each_genre_is_an_independent_python_file(self):
        self.assertEqual(set(JAZZ_GENRE_PROFILES), set(GENRE_STYLE_MODULES) - {"ROCK"})
        paths = set()
        for name, filename in GENRE_STYLE_MODULES.items():
            module = importlib.import_module("genre_styles." + filename)
            self.assertEqual(module.GENRE_NAME, name)
            self.assertTrue(Path(module.__file__).is_file())
            self.assertNotIn(module.__file__, paths)
            paths.add(module.__file__)
        self.assertEqual(len(paths), 9)

    def test_all_jazz_styles_route_through_own_file(self):
        self.assertEqual(JAZZ_GENRE_PROFILES, COMPATIBLE_PROFILES)
        for name, profile_id in JAZZ_GENRE_PROFILES.items():
            profile = {
                "resolution_policy": "AUTOMATIC_BASELINE_ALLOWED",
                "profile_id": profile_id,
            }
            module = get_style(name, profile)
            self.assertIsNotNone(module, name)
            mode = "natural_minor" if name == "Jazz Fusion" else "major"
            output = build_jazz_progression(name, profile, mode, 32, 19)
            self.assertEqual(output, module.chord_progression(32, 19), name)
            self.assertEqual(len(output), 32, name)
            self.assertEqual(output[-1], "i" if name == "Jazz Fusion" else "I")
            self.assertEqual(build_jazz_progression(
                name, {**profile, "profile_id": "WRONG"}, mode, 32, 19
            ), None)

    def test_ballad_still_uses_own_arrangement_and_mix(self):
        profile = {"profile_id": "JAZZ_BALLAD_V1",
                   "resolution_policy": "AUTOMATIC_BASELINE_ALLOWED"}
        progression = build_jazz_progression("Jazz Ballad", profile, "major", 40, 23)
        self.assertEqual(progression, ballad_progression(40, 23))
        self.assertTrue(callable(arrange_events))
        self.assertTrue(callable(balance_mix))
        self.assertTrue(all(len(set(progression[b:b + 4])) >= 2
                            for b in range(len(progression) - 3)))

    def test_jazz_ballad_has_six_linked_real_instruments(self):
        from genre_styles.jazz_ballad import instrument_links, validate_instrument_links
        package = instrument_links()
        self.assertEqual(package["link_mode"], "SHARED_SAMPLE_LIBRARY_REFERENCE")
        self.assertEqual(package["shared_root"], "sound_resources")
        roles = package["instruments"]
        self.assertEqual(set(roles), {"HARMONY", "LEAD", "BASS", "KICK", "SNARE", "HAT"})
        self.assertEqual(roles["HARMONY"]["sound_preservation"],
                         "KEEP_APPROVED_WURLITZER_PIANO")
        bindings = {
            entry["registry_binding"]: {
                "resource_id": entry["resource_id"],
                "preferred_mapping": entry["sfz"],
                "resource_type": package["resource_type"],
            }
            for entry in roles.values()
        }
        validate_instrument_links(bindings)
        roles["HARMONY"]["resource_id"] = "ALTERED_IN_COPY"
        self.assertEqual(instrument_links()["instruments"]["HARMONY"]["resource_id"],
                         "GREG_SULLIVAN_E_PIANOS")
        bindings["clarinet_bb"]["preferred_mapping"] = "bad.sfz"
        with self.assertRaisesRegex(ValueError, "JAZZ_INSTRUMENT_LINK_MISMATCH"):
            validate_instrument_links(bindings)

    def test_unknown_or_controlled_style_no_automatic_fallback(self):
        profile = {"profile_id": "JAZZ_BALLAD_V1",
                   "resolution_policy": "REQUIRES_HUMAN_CONTROL"}
        self.assertIsNone(get_style("Jazz Ballad", profile))
        self.assertIsNone(build_jazz_progression("Jazz Ballad", profile, "major", 32, 19))
        self.assertIsNone(get_style("Psychedelic Space Polka", profile))

    def test_rock_mix_untouched(self):
        from genre_styles.rock import balance_mix
        from rock_balance_contract import apply_rock_balance
        self.assertIsNotNone(balance_mix)
        unchanged = {"genre": "Jazz Ballad", "modules": {}}
        self.assertIs(apply_rock_balance(unchanged), unchanged)
        self.assertIs(balance_mix(unchanged), unchanged)


if __name__ == "__main__":
    unittest.main()
