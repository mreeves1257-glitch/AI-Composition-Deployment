#!/usr/bin/env python3
"""Read-only proof for separate public backing-track arrangers: does NOT run inside our Composer."""
import json
from pathlib import Path
import mido

root=Path("research/EXTERNAL_KEYBOARD_RESEARCH_20261009")
files={"ROCK":"ROCK_example.mid","JAZZ":"JAZZ_example.mid","FOLK":"FOLK_example.mid"}
report={}
for genre,filename in files.items():
    path=root/"02_BACKING_TRACKS_MIT"/"ISOLATED_SAMPLE_MIDI"/filename
    assert path.is_file() and path.stat().st_size>300, f"MIDI_NOT_RENDERED:{genre}"
    midi=mido.MidiFile(str(path))
    assert midi.ticks_per_beat>0 and midi.type in (0,1), f"MIDI_MALFORMED:{genre}"
    events=[]
    for index,track in enumerate(midi.tracks):
        ticks=0
        for msg in track:
            ticks+=msg.time
            if msg.type=="note_on" and msg.velocity>0:
                events.append((index,ticks,msg.channel,msg.note,msg.velocity))
    assert len(events)>=12, f"NOT_ENOUGH_REAL_NOTES:{genre}"
    assert all(0<=n[3]<=127 and 0<n[4]<=127 for n in events)
    report[genre]=dict(notes=len(events),channels=sorted(set(n[2] for n in events)),
                       distinct_pitches=len(set(n[3] for n in events)),tracks=len(midi.tracks),
                       tempo_ticks=midi.ticks_per_beat)
assert set(report)==set(files)
assert report["ROCK"]["notes"]!=report["JAZZ"]["notes"] or report["ROCK"]["distinct_pitches"]!=report["JAZZ"]["distinct_pitches"],"GENRES_INDISTINGUISHABLE"
(root/"ISOLATED_MIDI_PROOF_2026-10-09.json").write_text(json.dumps({"status":"THREE_ORIGINAL_MIT_MIDI_EXPORTS_VERIFIED","unmodified_composer":True,"genre_55_activation":False,"source":"ako/backing-tracks@534b7be0d07595121a9e782c8793244604a1cd41","genres":report},indent=2)+"\n")
print("ISOLATED_PUBLIC_ARRANGER_ROCK_JAZZ_FOLK_MIDI_EXPORT_PASS",json.dumps(report,sort_keys=True))
