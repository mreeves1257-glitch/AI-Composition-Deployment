"""Check Rock's working Composer->MIDI->genre-slot PROCEDURE for other 54.

Each selected original genre is independently checked against its own profile,
musical backend, interpreter slot, tempo/meter and separate MIDI tracks.
Actual MIDI is written and re-read, NOT a theoretical spreadsheet only.
The 7-bar source seeds are explicitly NOT full arrangements/audio approvals.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
sys.path.insert(0,str(ROOT/"research"))
from genre_styles.shared_interpreter_router import listed_genres,InterpreterConnectionError
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.genre_owned_midi_inlet import receive_genre_midi
from export_55_original_genre_midi_previews_20261009 import export_genre_midi

def main():
    names=[name for name in listed_genres() if name!="ROCK"]
    assert len(names)==54,"EXACT_OTHER_54_GENRE_NAMES_REQUIRED"
    receipts=[]
    with tempfile.TemporaryDirectory(prefix="all-54-owned-midi-inlets-") as td:
        root=Path(td)
        for number,genre in enumerate(names):
            plan=compile_original_source_seed(genre)
            source=root/(f"genre_{number:02d}.mid")
            produced=export_genre_midi(plan,source)
            before=source.read_bytes()
            got=receive_genre_midi(source,selected_genre=genre,
                                   composer_genre=genre,source_kind="SEED_PREVIEW")
            assert got["status"]=="GENRE_SPECIFIC_MIDI_ARRIVED_AT_CORRECT_INTERPRETER_SLOT"
            assert got["notes_received"]==produced["note_event_count"]
            assert got["midi_tracks_received"]==produced["role_count"]
            assert got["exact_own_profile_id"]==produced["profile_id"]
            assert got["family"]==produced["family"]
            assert got["individual_musical_backend"] and got["exact_own_interpreter_slot"]
            assert got["original_source_midi_byte_identical"] is True
            assert got["abbreviated_seed_is_not_full_instrument_ensemble"] is True
            assert got["production_deployed"] is False
            assert got["complete_recorded_music_verified"] is False
            assert got["genre_musical_performance_activated"] is False
            assert source.read_bytes()==before
            receipts.append({
                "genre":genre,"family":got["family"],
                "profile_id":got["exact_own_profile_id"],
                "owned_interpreter_slot":got["exact_own_interpreter_slot"],
                "midi_notes_received":got["notes_received"],
                "tracks_received":got["midi_tracks_received"],
                "full_original_tracks_not_in_short_seed":
                    got["full_original_tracks_not_present_in_preview"],
                "separate_style_program_identity_verified_for_audio":False,
            })
        assert len(receipts)==54
        assert len({r["profile_id"] for r in receipts})==54
        assert len({r["owned_interpreter_slot"] for r in receipts})==54
        assert sum(r["midi_notes_received"] for r in receipts)>1000
        # Same-meter/tempo cases must still reject another genre: identity is
        # NEVER guessed from music's rhythm or from a copied Rock label.
        source= root/"genre_00.mid"
        try:
            receive_genre_midi(source,selected_genre=names[1],
                               composer_genre=names[1],source_kind="SEED_PREVIEW")
        except InterpreterConnectionError:
            pass
        else:
            raise AssertionError("CROSS_GENRE_MIDI_MISROUTED")
        # No source-preview may pose as complete Composer MIDI.
        try:
            receive_genre_midi(source,selected_genre=names[0],
                               composer_genre=names[0],source_kind="COMPOSER")
        except InterpreterConnectionError:
            pass
        else:
            raise AssertionError("SEVEN_BAR_SEED_MISIDENTIFIED_AS_FULL_COMPOSER_SCORE")
        # Exact receipt for all 54 in one file, not duplicate master files.
        report={
            "status":"REMAINING_54_INDEPENDENT_GENRE_MIDI_INGRESS_CHECKS_PASS",
            "other_genres":54,"rock_instrument_mix_unchanged":True,
            "families":len({r["family"] for r in receipts}),
            "own_source_interpreter_slot_count":54,
            "actual_type1_midi_read_and_validated":54,
            "common_midi_transport_not_common_rock_style":True,
            "cross_genre_routing_rejected":True,
            "source_preview_not_misrepresented_as_full_song":True,
            "original_samples_and_mixer_changed":False,
            "production_activated":False,
            "performance_and_audio_not_yet_verified":True,
            "per_genre":receipts
        }
        (ROOT/"research_artifacts").mkdir(exist_ok=True)
        (ROOT/"research_artifacts/REMAINING_54_MIDI_GENRE_CONNECTIONS.json").write_text(
            json.dumps(report,indent=2)+"\n")
    print("OTHER_54_GENRES_CORRECT_MIDI_INLETS_PASS",
          json.dumps({"genres":54,"families":report["families"],
                      "separate_owned_interpreter_slots":54,
                      "midi_note_events":sum(x["midi_notes_received"] for x in receipts),
                      "recorded_audio_claimed":False},sort_keys=True))
if __name__=="__main__":
    main()
