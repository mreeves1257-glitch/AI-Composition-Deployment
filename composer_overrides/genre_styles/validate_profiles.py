"""Non-mutating verification for family-based genre ratios and separate kits."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
KIT_PATH = ROOT.parent / "drum_kits" / "drum_kit_catalog.json"
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

UNVERIFIED = "STRUCTURE_FILED_FULL_MUSIC_UNVERIFIED"
NOT_READY = "NOT_READY_UNTIL_INSTRUMENTS_PERFORMANCE_AND_FINAL_AUDIO_VERIFIED"
EXECUTION_UNKNOWN = "GENRE_SPECIFIC_END_TO_END_EXECUTION_UNVERIFIED"
assert index["operational_readiness_policy"] == UNVERIFIED
assert index["verified_full_music_genre_count"] == 0
assert set(index["genre_to_family_file"].values()) == {
    family + "/profile.json" for family in index["family_memberships"]
}
all_genres = set()
profile_keys = None
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
        keys = set(p)
        if profile_keys is None:
            profile_keys = keys
        assert keys == profile_keys, ("INCONSISTENT_GENRE_FIELDS", genre)
        assert p["profile_status"] == UNVERIFIED, ("GENRE_NOT_VERIFIED", genre)
        assert p["ready_for_composition"] == NOT_READY, ("NO_COMPLETED_SONG", genre)
        assert p["runtime_musical_connections"]["musical_implementation_state"] == EXECUTION_UNKNOWN
        assert p["family_name"] == family["musical_family"]
        assert index["genre_to_family_file"][genre] == filename
        assert p["drum_kit_catalog_path"] == index["shared_drum_kit_catalog"]
        assert p["drum_kit_not_a_single_rendered_stem"] is True
        assert p["original_instrument_sources_off_limits"] is True
        assert p["actual_source_wav_sfz_files_must_remain_unchanged"] is True
        assert p["auto_apply"] is False
        assert family["seven_stage_sequence_filed_for_every_genre"] is True
        assert family["stage_wiring_activated"] is False
        plan=p["seven_stage_plan"]
        assert plan["genre_identity"] == "GENRE_"+p["musical_definition"]["profile_id"].replace("-", "_")
        assert plan["stage_count"] == 7
        assert plan["enable_runtime_connections"] is False
        assert plan["auto_apply"] is False
        assert plan["do_not_change_universal_recordings"] is True
        assert plan["do_not_reconfigure_current_composer_or_plug"] is True
        expected_order=[
            "SELECT_GENRE",
            "DEFINE_MUSICAL_STRUCTURE",
            "CHOOSE_INSTRUMENTS_AND_DRUM_KIT",
            "COMPOSE_SEPARATE_PARTS",
            "PERFORM_MUSICALLY",
            "RENDER_SEPARATE_AUDIO_STEMS",
            "GENRE_MIX_THEN_STANDALONE_3D_MIX",
        ]
        assert plan["stage_order"] == expected_order
        steps=plan["stages"]
        assert len(steps) == 7
        assert [s["order"] for s in steps] == list(range(1,8))
        assert [s["name"] for s in steps] == expected_order
        assert all(s["connection_activated"] is False for s in steps)
        assert len({s["planned_stage_id"] for s in steps}) == 7
        handoffs=plan["proposed_handoffs"]
        assert len(handoffs) == 6
        assert all(x["status"] == "RESERVED_NOT_CONNECTED" for x in handoffs)
        assert all(x["from"] == steps[i]["planned_stage_id"] and
                   x["to"] == steps[i+1]["planned_stage_id"]
                   for i,x in enumerate(handoffs))
        assert steps[2]["drum_kit_id"] == p["selected_shared_drum_kit_id"]
        assert steps[2]["independent_track_roles"] == [x["track_id"] for x in p["individual_instrument_tracks"]]
        assert steps[5]["required_track_roles"] == [x["track_id"] for x in p["individual_instrument_tracks"]]
        assert steps[6]["operation_order"] == ["GENRE_OWNS_INDIVIDUAL_STEM_RATIOS","STANDALONE_3D_MIXER_LAST"]
        def exists_field(ref):
            v=p
            for section in ref.split("."):
                if not isinstance(v,dict) or section not in v:
                    return False
                v=v[section]
            return True
        for step in steps:
            assert all(exists_field(f) for f in step.get("source_fields",[])), (genre,step["name"])
        source_map=p["existing_file_cross_references"]
        assert source_map["shared_drum_catalog"] == index["shared_drum_kit_catalog"]
        repo_root=ROOT.parents[1]
        for source_group,sources in source_map.items():
            if isinstance(sources,list):
                assert all((repo_root/source).is_file() for source in sources), (genre,source_group)
            elif source_group=="original_runtime_bundle":
                assert (repo_root/sources).is_file()
            elif source_group=="shared_drum_catalog":
                assert (repo_root/sources).is_file()
        assert family["family_contains_original_music_definitions"] is True
        assert family["original_routing_protected"] is True
        assert family["development_mode"] == "MUSICAL_PROFILE_DATA_POPULATED_NOT_AUTO_ACTIVATED"
        definition = p.get("musical_definition")
        assert isinstance(definition, dict) and definition["profile_id"]
        assert len(definition.get("tempo_bpm_range", [])) == 2
        assert definition.get("meter_options")
        assert definition.get("resolution_policy") in {"AUTOMATIC_BASELINE_ALLOWED", "CONTROLLED_RESOLVER", "USER_COMPONENTS_REQUIRED", "SAVED_PROFILE_REQUIRED"}
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
            assert family["family_operational_status"] == "DYSFUNCTIONAL_FULL_SONG_OUTPUT_USER_REPORTED"
        elif genre == "Jazz Ballad":
            assert kit == "jazz_ballad_brush_recorded" and len(tracks) == 6
            ratio = {r["track_id"]: r["proposed_relative_active_level_db"]
                     for r in tracks}
            assert ratio == {
                "HARMONY": 0, "LEAD": 0, "BASS": -3,
                "KICK": 8, "SNARE": -22, "HAT": -7}
        else:
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
    assert all(index["genre_to_family_file"][genre] == name + "/profile.json"
               for genre in members)
assert len(list(ROOT.glob("*.json"))) == 1, "OLD_FLAT_GENRE_FILES_STILL_PRESENT"
assert len(list(ROOT.glob("*/profile.json"))) == 13, "MISSING_FAMILY_FOLDER"
for name in index["family_memberships"]:
    p = ROOT / name / "profile.json"
    family = json.loads(p.read_text(encoding="utf-8"))
    if name in ("Rock", "Jazz"):
        assert family["family_operational_status"] == "DYSFUNCTIONAL_FULL_SONG_OUTPUT_USER_REPORTED"
    else:
        assert family["family_operational_status"] == "NOT_END_TO_END_VERIFIED"
print("PASS: 55 independent genres in 13 family folders; Rock and Jazz dysfunctional; all stage links inactive")
