"""Non-mutating verification for family-based genre ratios and separate kits."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
KIT_PATH = ROOT.parent.parent / "drum_kits" / "drum_kit_catalog.json"
kits = json.loads(KIT_PATH.read_text(encoding="utf-8"))
assert index["schema_version"] == 2 and index["profile_count"] == 55
assert index["family_count"] == 13
assert len(index["genre_to_family_file"]) == 55
assert len(set(index["genre_to_family_file"].values())) == 13
assert kits["id"] == "UNIVERSAL_DRUM_KIT_CATALOG"
assert kits["original_files_copied"] is False
assert kits["genre_balance_owned_by_each_genre"] is True
assert index["automatic_application_enabled"] is False
assert index["original_instrument_sources_immutable"] is True

all_genres = set()
for filename in set(index["genre_to_family_file"].values()):
    file = ROOT / filename
    family = json.loads(file.read_text(encoding="utf-8"))
    assert family["schema_version"] == 2
    assert family["reference_only"] is True
    assert family["source_assets_immutable"] is True
    assert family["original_drum_library_is_separate"] is True
    assert family["genre_count"] == len(family["profiles"])
    assert family["genre_count"] == sum(
        target == filename for target in index["genre_to_family_file"].values())
    for genre, p in family["profiles"].items():
        assert genre not in all_genres, "DUPLICATE_GENRE:" + genre
        all_genres.add(genre)
        assert p["genre"] == genre
        assert p["family_name"] == family["musical_family"]
        assert index["genre_to_family_file"][genre] == filename
        assert p["drum_kit_catalog_path"] == index["shared_drum_kit_catalog"]
        assert p["drum_kit_not_a_single_rendered_stem"] is True
        assert p["original_instrument_sources_off_limits"] is True
        assert p["actual_source_wav_sfz_files_must_remain_unchanged"] is True
        assert p["auto_apply"] is False
        assert family["family_contains_original_music_definitions"] is True
        assert family["original_routing_protected"] is True
        assert family["development_mode"] == "MUSICAL_PROFILE_DATA_POPULATED_NOT_AUTO_ACTIVATED"
        definition = p.get("musical_definition")
        assert isinstance(definition, dict) and definition["profile_id"]
        assert len(definition.get("tempo_bpm_range", [])) == 2
        assert definition.get("meter_options")
        assert definition.get("resolution_policy") == "AUTOMATIC_BASELINE_ALLOWED"
        assert p.get("musical_definition_source") == "PRESERVED_2026_10_02_COMPOSER_PERFORMANCE_REGISTRY_EXACT_COPY"
        assert p["runtime_musical_connections"]["original_family_template"] == p["genre_template"]
        assert p["runtime_musical_connections"]["runtime_integration"] == "FAMILY_DATA_REFERENCE_ONLY_RUNTIME_STILL_READS_ORIGINAL_PROFILE"
        assert p["runtime_musical_connections"]["selected_universal_drum_kit"] == p["selected_shared_drum_kit_id"]
        tracks = p["individual_instrument_tracks"]
        track_ids = [r["track_id"] for r in tracks]
        assert track_ids and len(track_ids) == len(set(track_ids))
        assert all(row["source_is_read_only"] is True for row in tracks)
        kit = p["selected_shared_drum_kit_id"]
        if kit is not None:
            assert kit in kits["kits"], "UNKNOWN_KIT:" + genre
            assert kits["kits"][kit]["original_palette_descriptor"] in p["original_composer_instrument_palette"]
            assert {"KICK", "SNARE", "HAT"} <= set(track_ids)
        if genre == "ROCK":
            assert kit == "rock_recorded" and len(tracks) == 9
            assert all("existing_gain_trim_db" in x for x in tracks)
            assert p["profile_status"] == "WORKING_ROCK_PROTECTED_UNCHANGED"
        elif genre == "Jazz Ballad":
            assert kit == "jazz_ballad_brush_recorded" and len(tracks) == 6
            ratio = {r["track_id"]: r["proposed_relative_active_level_db"]
                     for r in tracks}
            assert ratio == {
                "HARMONY": 0, "LEAD": 0, "BASS": -3,
                "KICK": 8, "SNARE": -22, "HAT": -7}
        else:
            assert p["profile_status"] == "DRAFT_SUGGESTED_RATIOS_NOT_DEPLOYED"
            assert all(isinstance(x["proposed_relative_active_level_db"], (int, float))
                       for x in tracks)
            if kit:
                assert kit.startswith("unverified_")
                for role in ("KICK", "SNARE", "HAT"):
                    row = next(x for x in tracks if x["track_id"] == role)
                    assert row["instrument_id"] is None

assert all_genres == set(index["genre_to_family_file"]), "MISSING_STYLE"
assert sum(len(members) for members in index["family_memberships"].values()) == 55
for name, members in index["family_memberships"].items():
    assert all(index["genre_to_family_file"][genre] == name + ".json"
               for genre in members)
assert len(list(ROOT.glob("*.json"))) == 14, "OLD_FLAT_GENRE_FILES_STILL_PRESENT"
print("PASS: 55 independent styles in 13 family files; 1 separate immutable drum catalog")
