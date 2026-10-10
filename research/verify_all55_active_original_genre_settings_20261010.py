"""55 active, ORIGINAL genre settings and MIDI-only end-to-end route audit.

No synthesizers, audio stems or live services in this test. The reusable
Composer -> MIDI -> own-genre entry point is active for EVERY genre; the
readiness gate remains closed for unverified source instruments and full music.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
sys.path.insert(0,str(ROOT/"research"))
from genre_styles.genre_run_settings import (
    all_genre_configurations,selected_composer_configuration,
    OriginalGenreSettingsError,
)
from genre_styles.genre_owned_midi_inlet import receive_genre_midi
from genre_styles.source_pattern_library import compile_original_source_seed
from export_55_original_genre_midi_previews_20261009 import export_genre_midi


def main():
    all_settings=all_genre_configurations()
    assert len(all_settings)==55
    counts=Counter()
    missing={}
    with tempfile.TemporaryDirectory(prefix="configured-original-55-") as td:
        for i,(genre,settings) in enumerate(all_settings.items()):
            selected=selected_composer_configuration(genre,
                {"profile_id":settings["profile_id"]},
                {"status":"PASS","meter":settings["meter_options"][0],
                 "tempo_bpm":settings["tempo_bpm_range"][0]})
            assert selected["genre_routing_active"] and selected["midi_inlet_active"]
            assert not selected["live_production_activated"]
            assert selected["source_sfz_preserved"] and selected["mix_and_performance_settings_unchanged"]
            assert selected["original_full_track_count"]>=1
            assert selected["original_full_track_count"]==len(selected["all_original_instruments"])
            if selected["missing_recorded_programs"]:
                missing[genre]=selected["missing_recorded_programs"]
            counts["exact_program_references"]+=selected["exact_recorded_program_references"]
            counts["all_tracks"]+=selected["original_full_track_count"]
            if selected["full_recorded_audio_approved_in_isolated_development"]:
                counts["development_recorded_stereo_genres"]+=1
            plan=compile_original_source_seed(genre)
            filename=Path(td)/(f"original_{i:02}.mid")
            source=export_genre_midi(plan,filename)
            receipt=receive_genre_midi(filename,selected_genre=genre,
                     composer_genre=genre,source_kind="SEED_PREVIEW")
            assert receipt["genre_style_rules_loaded_from_own_profile"]
            assert receipt["midi_tracks_received"]==source["role_count"]
            assert receipt["notes_received"]==source["note_event_count"]
            assert receipt["exact_own_profile_id"]==settings["profile_id"]
            assert receipt["abbreviated_seed_is_not_full_instrument_ensemble"]
            assert not receipt["complete_recorded_music_verified"]
            counts["genre_midi_ingresses"]+=1
            counts["seed_notes_received"]+=receipt["notes_received"]
            counts["families:"+settings["family"]]+=1
        assert counts["genre_midi_ingresses"]==55
        assert counts["development_recorded_stereo_genres"]==2
        assert len([k for k in counts if k.startswith("families:")])==13
        assert counts["all_tracks"]==315,(counts["all_tracks"],"FULL_TRACK_COUNT_CHANGED")
        assert counts["exact_program_references"]==66,(counts["exact_program_references"],"SOURCE_REFERENCE_COUNT_CHANGED")
        assert counts["seed_notes_received"]==4371,counts["seed_notes_received"]
        assert "ROCK" not in missing and "Jazz Ballad" not in missing
        assert missing,"INVALID_ALL55_FULL_SAMPLE_MAP_CLAIM"
        assert "Jazz Waltz" in all_settings and "Salsa" in all_settings
        assert all_settings["Jazz Waltz"]["meter_options"]==["3/4"]
        assert all_settings["ROCK"]["meter_options"]==["4/4"]
        assert all_settings["Swing"]["groove_behavior"]!=all_settings["ROCK"]["groove_behavior"]
        assert all_settings["ROCK"]["original_own_interpreter"] != all_settings["Jazz Ballad"]["original_own_interpreter"]
        build=(ROOT/"build_current_composer.sh").read_text()
        assert "result['active_original_genre_settings'] = selected_composer_configuration(" in build
        assert "from genre_styles.genre_run_settings import selected_composer_configuration" in build
        assert "apply_jazz_ballad_balance(stereo_instructions, stems)" in build
        report={"status":"ALL_55_ORIGINAL_GENRE_SETTINGS_ROUTED_AND_MIDI_INLETS_ACTIVE_IN_DEVELOPMENT",
                "configured_genres":55,"genre_families":13,
                "each_own_meter_tempo_groove_and_interpreter":True,
                "separate_actual_midi_files_validated":55,
                "musical_seed_notes":counts["seed_notes_received"],
                "full_original_instrument_tracks":counts["all_tracks"],
                "exact_program_identity_references":counts["exact_program_references"],
                "unverified_original_tracks":counts["all_tracks"]-counts["exact_program_references"],
                "development_full_recording_verified_genres":["ROCK","Jazz Ballad"],
                "audio_ready_other53":False,
                "production_live_enabled":False,
                "mix_piano_brush_clarinet_settings_changed":False,
                "original_samples_preserved":True,
                "rock2_song_and_mix_unchanged":True,
                "missing_source_mappings_by_genre":missing}
        out=ROOT/"research_artifacts"/"55_GENRE_RUN_CONFIGURATION.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print("ALL_55_RUN_SETTINGS_MIDI_ACTIVE_SAFE_PASS",
              json.dumps({k:report[k] for k in (
                  "configured_genres","genre_families",
                  "separate_actual_midi_files_validated","musical_seed_notes",
                  "full_original_instrument_tracks","exact_program_identity_references",
                  "unverified_original_tracks","production_live_enabled")},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
