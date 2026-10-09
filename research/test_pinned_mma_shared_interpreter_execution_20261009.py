"""Exact original MMA -> shared interpreter -> per-part note data proof."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path("composer_overrides").resolve()))
from genre_styles.shared_interpreter_router import (
    compile_selected_musical_interpreter,
    route_to_shared_interpreter,
    InterpreterConnectionError,
)
from genre_styles.Rock.rock_pinned_mma_interpreter import (
    split_external_midi, compile_transition_intents,
    PINNED_USER_LIKED_MMA_SHA256,
)

midi=Path("research/pinned_input/MMA_Rock_16Bar_Two_Sections.mid")
assert midi.exists(),"ORIGINAL_HARD_STOP_MIDI_NOT_RECOVERED"
assert hashlib.sha256(midi.read_bytes()).hexdigest()==PINNED_USER_LIKED_MMA_SHA256
stage3={"status":"PASS","palette":["electric_guitar","electric_bass","drums"],"meter":"4/4","tempo_bpm":145}
sc=compile_selected_musical_interpreter("ROCK",original_mma_midi_path=midi,original_stage3_result=stage3)
assert sc["status"]=="PINNED_MMA_ROCK_SCORE_INTERPRETED"
assert sc["note_count"]==420
assert sc["tempo_bpm"]==145 and sc["bars"]==16
assert len(sc["intent_trace"])==7
assert sorted(set(e["track_id"] for e in sc["notes"]))==["BASS","CRASH","HARMONY","HAT","KICK","SNARE","TOMS"]
assert len([e for e in sc["notes"] if e["track_id"]=="HARMONY"])==225
assert len([e for e in sc["notes"] if e["track_id"]=="BASS"])==56
assert len([e for e in sc["notes"] if e["track_id"]=="KICK"])==32
assert len([e for e in sc["notes"] if e["track_id"]=="SNARE"])==38
assert len([e for e in sc["notes"] if e["track_id"]=="HAT"])==64
assert len([e for e in sc["notes"] if e["track_id"]=="TOMS"])==4
assert len([e for e in sc["notes"] if e["track_id"]=="CRASH"])==1

# Reconcile independently against the previous 2026-10-08 reference bridge:
original, mapping, ignored, extras=split_external_midi(midi)
reference,trace=compile_transition_intents(original)
refnotes=[dict(e) for role,events in reference.items() for e in events]
refnotes.sort(key=lambda e:(e["start_beat"],list(("HARMONY","BASS","KICK","SNARE","HAT","TOMS","CRASH")).index(e["track_id"]),e["midi"]))
assert sc["notes"]==refnotes, "USER_LIKED_SCORE_ORIGINAL_EVENTS_DRIFTED"
assert sc["intent_trace"]==trace, "ORIGINAL_TYPED_ROCK_FILLS_CHANGED"
assert sc["midi_translation_evidence"]==mapping, "ORIGINAL_MIDI_MAPPING_CHANGED"
assert sc["unsupported_mma_drum_notes"]==ignored
assert sc["unselected_extra_mma_tracks"]==extras

# Compile the exact originally approved musical data; no automatic Jazz
# as Rock, no altered original MIDI, no fabricated instrument resources.
bad=Path("research/pinned_input/corrupt_demo.mid")
bad.write_bytes(b"x")
try: compile_selected_musical_interpreter("ROCK",original_mma_midi_path=bad,original_stage3_result=stage3)
except AssertionError as e: assert "PINNED_USER_LIKED_INPUT_MISMATCH" in str(e)
else:raise AssertionError("CORRUPT_MIDI_WAS_ACCEPTED")
try: compile_selected_musical_interpreter("Jazz Waltz",original_mma_midi_path=midi)
except InterpreterConnectionError as e: assert "NO_VERIFIED_SCORE_BACKEND_FOR_GENRE" in str(e)
else:raise AssertionError("NON_ROCK_BACKEND_SILENTLY_ACTIVATED")
try:compile_selected_musical_interpreter("ROCK",original_mma_midi_path=midi,original_stage3_result={"status":"PASS","meter":"3/4"})
except InterpreterConnectionError:pass
else:raise AssertionError("ROCK_WALTZ_BAD_METER_ACCEPTED")

out=Path("research/pinned_shared_interpreter_rock_output");out.mkdir(parents=True,exist_ok=True)
p=out/"ROCK_16BAR_420_SOURCE_BACKED_INTERPRETED_NOTES.json"
p.write_text(json.dumps(sc,indent=2)+"\n")
info={"source_sha256":PINNED_USER_LIKED_MMA_SHA256,"backend":"ONE_SHARED_INTERPRETER_WITH_ROCK_SPECIFIC_NOTE_COMPILER","original_note_count":420,"original_7_roles_preserved":True,"source_midi_unchanged":True,"note_events_exact_original_match":True,"genre_profiles_original":True,"live_not_deployed":True,"format":"PROJECT_TYPED_SCORE_EVENTS_NOT_RECORDING"}
(out/"CHECKSUM_AND_STATUS.json").write_text(json.dumps(info,indent=2)+"\n")
print("SHARED_INTERPRETER_PINNED_ROCK_420_NOTE_EXECUTION_PASS",json.dumps(info,sort_keys=True))
