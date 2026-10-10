"""Run the ORIGINAL documented MMA Swing groove with its REAL Python engine.

This is not a replacement for Composer musical theory or recorded instrument
rendering. It is a proof that the published style's exact Groove/DefGroove
implementation can execute; genre label alone is never enough.

GPL source: infojunkie/mma @ c52943c31aa1e64fa9b5313620d5065f91c22773
Archived byte-identical original: research/genre_reference_sources/mma/lib/stdlib/swing.mma.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import mido

ROOT=Path(__file__).resolve().parents[1]
PIN="c52943c31aa1e64fa9b5313620d5065f91c22773"
ARCHIVED=ROOT/"research/genre_reference_sources/mma/lib/stdlib/swing.mma"
OUT=ROOT/"research_artifacts/swing_mma_original_engine"
STRUCTURE=[
  ("SwingIntro", ["C6","F6","Dm7","G7"]),
  ("SwingWalk", ["C6","Am7","Dm7","G7","Cmaj7","F6","Dm7","G7"]),
  ("Swing1Walk",["Fmaj7","Em7","Am7","D7","Dm7","G7","C6","C7"]),
  ("SwingFill",["F6","G7"]),
  ("Swing2",["Cmaj7","A7","Dm7","G7"]),
  ("SwingEnd",["Cmaj7","C6"]),
]
EXPECTED_GROOVES=[label for label,_ in STRUCTURE]
EXPECTED_BARS=sum(len(chords) for _,chords in STRUCTURE)

def fail(why):
    raise AssertionError("ORIGINAL_MMA_SWING_ENGINE:"+why)

def original_git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def main():
    if len(sys.argv)!=2:
        fail("PASS_PATH_TO_EXACT_UPSTREAM_MMA_CHECKOUT")
    checkout=Path(sys.argv[1]).resolve()
    source=checkout/"lib/stdlib/swing.mma"
    engine=checkout/"mma.py"
    if not source.is_file() or not engine.is_file():
        fail("ORIGINAL_MMA_ENGINE_AND_STYLE_NOT_PRESENT")
    source_data=source.read_bytes()
    archived_data=ARCHIVED.read_bytes()
    if source_data!=archived_data:
        fail("ARCHIVED_STYLE_NOT_BYTE_IDENTICAL_TO_UPSTREAM")
    original_sha=original_git_blob(source_data)
    if original_sha!="5902928a9a13ffcd8ca660d7dd2a58033982a14f":
        fail("MMA_SWING_SOURCE_GIT_BLOB_CHANGED")
    cmd=["Tempo 132","Time 4","TimeSig 4 4",
         "// Original upstream Swing defgrooves, NOT self-authored new patterns",
         "// Source selected from standard MMA library: swing.mma"]
    b=1
    for groove,chords in STRUCTURE:
        cmd.append("Groove "+groove)
        for chord in chords:
            cmd.append(str(b)+" "+chord)
            b+=1
        cmd.append("")
    if b-1!=EXPECTED_BARS:fail("SONG_FORM_IS_NOT_28_BARS")
    OUT.mkdir(parents=True,exist_ok=True)
    song=OUT/"swing_original_mma_28bar_score.mma"
    midi=OUT/"swing_original_mma_28bar_accompaniment.mid"
    song.write_text("\n".join(cmd)+"\n",encoding="utf-8")
    # ORIGINAL GPL MMA program reads chord chart and switches groove.
    # Do NOT import/copy a tiny imitation renderer.
    argv=[sys.executable,str(engine),"-f",str(midi),str(song)]
    done=subprocess.run(argv,cwd=checkout,encoding="utf-8",
                        capture_output=True,timeout=75)
    if done.returncode or not midi.is_file():
        fail("MMA_SWING_EXECUTION_FAILED rc="+str(done.returncode)+
             " STDOUT:"+done.stdout[-2600:]+" STDERR:"+done.stderr[-2600:])
    parsed=mido.MidiFile(str(midi))
    counts={}
    names=[]
    channels={}
    tempos=[]
    meters=[]
    for i,track in enumerate(parsed.tracks):
        label=next((x.name for x in track if x.type=="track_name"),f"Track {i}")
        names.append(label)
        notes=[x for x in track if x.type=="note_on" and x.velocity>0]
        if notes:counts[label]=len(notes)
        for msg in track:
            if msg.type=="set_tempo":tempos.append(round(mido.tempo2bpm(msg.tempo),3))
            if msg.type=="time_signature":meters.append(f"{msg.numerator}/{msg.denominator}")
            if msg.type=="note_on" and msg.velocity>0:
                channels.setdefault(label,set()).add(msg.channel)
    if not counts or sum(counts.values())<100:
        fail("ORIGINAL_SWING_ENGINE_NO_ACTUAL_ACC_MIDI")
    if len(counts)<3:
        fail("ORIGINAL_SWING_ENGINE_DID_NOT_GENERATE_SEPARATE_INSTRUMENT_TRACKS")
    if "4/4" not in meters and meters:
        fail("GENERATED_SWING_UNEXPECTED_METER:"+repr(meters))
    if not any(abs(t-132)<.1 for t in tempos):
        fail("MMA_GENERATED_SWING_TEMPO_NOT_132:"+repr(tempos))
    report={
       "status":"ORIGINAL_PUBLISHED_MMA_SWING_ENGINE_GENERATED_MULTITRACK_MIDI_PASS",
       "upstream_repo":"infojunkie/mma","upstream_commit":PIN,
       "original_style":"lib/stdlib/swing.mma",
       "original_upstream_git_blob_sha":original_sha,
       "matched_archive_bytes":True,
       "used_exact_published_grooves":EXPECTED_GROOVES,
       "actual_original_engine_executed":True,
       "bars":EXPECTED_BARS,
       "tempo_bpm":132,
       "time_signature":"4/4",
       "generated_midi_type":parsed.type,
       "midi_ticks_per_beat":parsed.ticks_per_beat,
       "separate_midi_tracks_with_notes":counts,
       "total_note_on_events":sum(counts.values()),
       "output_midi":midi.name,
       "generated_midi_sha256":hashlib.sha256(midi.read_bytes()).hexdigest(),
       "original_recorded_instruments_connected":False,
       "composer_chord_and_lead_merge_not_yet_verified":True,
       "production_ready":False,"original_rock2_and_jazz_ballad_untouched":True,
       "source_mixer_and_instrument_settings_changed":False,
    }
    (OUT/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_ORIGINAL_MMA_SWING_ENGINE_MIDI_PASS",
          json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
