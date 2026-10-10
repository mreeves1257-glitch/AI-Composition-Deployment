"""Exercise the ORIGINAL, unmodified MMA Swing style with its REAL interpreter.

Purpose: no new musical interpreter, no fake chord_progression() replacement.
The upstream published Swing groove defines accompaniment; each input song
supplies a DIFFERENT independent chord sequence/section progression. The test
creates MIDI but does NOT claim original SFZ/audio wiring or user approval.
This is an isolated research harness; Rock2/Jazz Ballad samples and mix untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import mido

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM_REV="c52943c31aa1e64fa9b5313620d5065f91c22773"
ARCHIVED=ROOT/"research/genre_reference_sources/mma/lib/stdlib/swing.mma"
PROOF=ROOT/"research_artifacts/original_mma_swing_executable_20261010"
# These are the AUTHOR'S exact available named published Swing groove names,
# as printed in the original source, not newly invented styles.
GROOVES=("SwingIntro","SwingWalk","Swing1Walk","SwingTriple",
         "SwingFill","SwingEnd")
# Explicit test chords, not extracted from the user's actual composer yet.
# Real Composer chord-timeline-to-groove handoff is a later connection gate.
CHORDS={
  "A":(
    ("SwingIntro",("Cmaj7","Am7","Dm7","G7")),
    ("SwingWalk",("Cmaj7","Am7","Dm7","G7","Em7","A7","Dm7","G7")),
    ("Swing1Walk",("Fmaj7","Fm6","Em7","A7","Dm7","G7","Cmaj7","G7")),
    ("SwingTriple",("Dm7","G7","Cmaj7","A7")),
    ("SwingFill",("Dm7","G7")),
    ("SwingEnd",("G7","Cmaj7")),
  ),
  "B":(
    ("SwingIntro",("Fmaj7","D7","Gm7","C7")),
    ("Swing1Walk",("Fmaj7","Bbmaj7","Am7","D7","Gm7","C7","Fmaj7","C7")),
    ("SwingWalk",("Bbmaj7","Bdim","Am7","D7","Gm7","C7","Fmaj7","D7")),
    ("SwingTriple",("Gm7","C7","Am7","D7")),
    ("SwingFill",("Gm7","C7")),
    ("SwingEnd",("C7","Fmaj7")),
  ),
}
TEMPOS={"A":136,"B":148}

def require(ok,reason):
    if not ok:raise AssertionError("REAL_UPSTREAM_SWING:"+reason)

def git_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()

def write_song(name:str)->Path:
    require(name in CHORDS,"WRONG_TEST_SONG")
    tempo=TEMPOS[name]
    lines=[
        "// Independent new chord progression for published MMA Swing groove.",
        "// NO new pattern instructions; GROOVE names come from original Swing style.",
        "// Instrument samples/recordings cannot be inferred from this MIDI.",
        "Tempo "+str(tempo),
        "Time 4",
        "TimeSig 4 4",
        "MIDIFile SMF=1",
        # The original MMA interpreter requires its named groove library to be
        # loaded before GROOVE; do not fake a missing global groove database.
        "Use swing",
    ]
    for groove,chords in CHORDS[name]:
        require(groove in GROOVES,"INVALID_GROOVE_NAME")
        lines.extend(["Groove "+groove,*chords])
    target=PROOF/("Original_MMA_Swing_"+name+".mma")
    target.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return target

def original_mma_render(name:str,mma_root:Path)->dict:
    script=mma_root/"mma.py"
    require(script.is_file(),"ORIGINAL_MMA_EXECUTABLE_MISSING")
    source=write_song(name)
    target=PROOF/("Original_MMA_Swing_"+name+".mid")
    argv=[sys.executable,str(script),"-M","1","-f",str(target),str(source)]
    proc=subprocess.run(argv,cwd=str(mma_root),capture_output=True,
                        text=True,timeout=120)
    if proc.returncode!=0:
        raise AssertionError("ORIGINAL_MMA_EXEC_FAILED:"+name+
                             "\nSTDOUT "+proc.stdout[-3500:]+
                             "\nSTDERR "+proc.stderr[-3500:])
    require(target.is_file() and target.stat().st_size>1000,
            "ORIGINAL_MMA_NO_MIDI:"+name)
    midi=mido.MidiFile(target)
    require(midi.type==1,"NOT_TYPE1_MIDI")
    timing=midi.ticks_per_beat
    require(timing>0,"NO_PULSES_PER_BEAT")
    counter={}
    for tr in midi.tracks:
        notes=[msg for msg in tr
               if msg.type=="note_on" and msg.velocity>0]
        if not notes:continue
        names=[x.name for x in tr if x.type=="track_name"]
        label=names[0] if names else "unnamed_"+str(len(counter))
        counter[label]=len(notes)
    count=sum(counter.values())
    require(len(counter)>=4 and count>100,
            "NO_FULL_SEPARATE_SWING_ACCOMPANIMENT")
    used=set(g for g,_ in CHORDS[name])
    require(set(GROOVES)==used,"INTRO_MAIN_FILL_END_ARE_NOT_ALL_EXERCISED")
    return {"name":name,"tempo":TEMPOS[name],
            "length_bars":sum(len(b) for _,b in CHORDS[name]),
            "published_grooves_in_order":[g for g,_ in CHORDS[name]],
            "midi_type":midi.type,"actual_ppq":timing,
            "note_count":count,"separate_midi_tracks":counter,
            "midi_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
            "source_score_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "original_mma_engine_executed":True,
            "recorded_audio_rendered":False,
            "original_user_instrument_sound_settings_changed":False}

def main():
    require(len(sys.argv)==2,"USAGE: script path-to-cloned-upstream-MMA")
    upstream=Path(sys.argv[1]).resolve()
    need_rev=subprocess.run(["git","-C",str(upstream),"rev-parse","HEAD"],
                            check=True,capture_output=True,text=True).stdout.strip()
    require(need_rev==UPSTREAM_REV,"UPSTREAM_COMMIT_NOT_FROZEN")
    first=ARCHIVED.read_bytes()
    original=(upstream/"lib/stdlib/swing.mma").read_bytes()
    require(first==original and
            git_sha(first)=="5902928a9a13ffcd8ca660d7dd2a58033982a14f",
            "SAVED_SWING_STYLE_DIFFERS_FROM_UPSTREAM")
    for name in GROOVES:
        require(("DefGroove "+name) in first.decode(),
                "MISSING_PUBLISHED_GROOVE:"+name)
    PROOF.mkdir(parents=True,exist_ok=True)
    reports=[original_mma_render(name,upstream) for name in ("A","B")]
    require(reports[0]["midi_sha256"]!=reports[1]["midi_sha256"],
            "TWO_SONGS_SAME_MIDI")
    require(reports[0]["source_score_sha256"]!=reports[1]["source_score_sha256"],
            "TWO_SONGS_SAME_HARMONY")
    report={
        "status":"ORIGINAL_PUBLISHED_MMA_SWING_ENGINE_AND_TWO_DIFFERENT_MIDI_SONGS_PASS",
        "official_upstream_repo":"infojunkie/mma",
        "official_upstream_commit":UPSTREAM_REV,
        "verbatim_source":"lib/stdlib/swing.mma",
        "source_style_unmodified":True,
        "external_engine_is_original_mma":True,
        "actual_stereo_audio_verified":False,
        "original_sfz_instrument_mapping_verified":False,
        "song_chords_from_actual_composer":False,
        "production_activated":False,
        "genre_label_alone_not_accepted":True,
        "songs":reports,
        "next":"Connect actual new Composer chord timeline to this original MMA input "
               "and verify sampled-instrument mappings before any finished audio",
    }
    (PROOF/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ORIGINAL_MMA_SWING_REAL_GROOVE_EXECUTION_PASS",
          json.dumps({"song_count":2,
            "tracks_per_song":[len(x["separate_midi_tracks"]) for x in reports],
            "notes_per_song":[x["note_count"] for x in reports],
            "source_still_original":True,
            "audio_proof_not_claimed":True},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
