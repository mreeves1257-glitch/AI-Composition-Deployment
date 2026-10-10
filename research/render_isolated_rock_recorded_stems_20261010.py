#!/usr/bin/env python3
"""Render the isolated Rock source-pattern candidate with original recorded SFZs.

Diagnostic only: never inserts candidate events into the live Composer or mixer.
"""
import json
import math
import os
from pathlib import Path

from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from sfz_renderer_adapter import render_midi

OUT = Path(os.environ.get("ROCK_DIAGNOSTIC_OUT", "rock-diagnostic-audio")).resolve()
TICKS = 480

def variable_length(value):
    if value < 0:
        raise ValueError("Negative MIDI delta")
    result = [value & 127]
    value >>= 7
    while value:
        result.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(result)

def midi_track(events, bpm):
    tempo = round(60_000_000 / bpm)
    commands = [(0, 0, b"\xff\x51\x03" + tempo.to_bytes(3, "big"))]
    for e in events:
        note, velocity = int(e["midi"]), int(e["velocity"])
        start = round(float(e["start_beat"]) * TICKS)
        end = round((float(e["start_beat"]) + float(e["duration_beats"])) * TICKS)
        if not (0 <= note <= 127 and 1 <= velocity <= 127 and end > start):
            raise ValueError("Invalid candidate MIDI note")
        commands.append((start, 1, bytes([0x90, note, velocity])))
        commands.append((end, 0, bytes([0x80, note, 0])))
    commands.sort(key=lambda row: (row[0], row[1]))
    track = bytearray()
    last = 0
    for tick, _, message in commands:
        track.extend(variable_length(tick - last))
        track.extend(message)
        last = tick
    track.extend(b"\x00\xff\x2f\x00")
    return (b"MThd" + (6).to_bytes(4, "big") +
            b"\x00\x00\x00\x01\x01\xe0" +
            b"MTrk" + len(track).to_bytes(4, "big") + bytes(track))

def main():
    registry = json.loads(Path("composer/runtime/target_registry.json").read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    proposal = prepare_source_pattern_composer_handoff(compile_original_source_seed("ROCK"), target_bindings=registry)
    if not proposal["candidate_is_not_live_events"] or proposal["audio_render_authorized"]:
        raise RuntimeError("Candidate isolation violated")
    roles = proposal["routing"]["roles"]
    if len(roles) != 5 or any(r["status"] != "EXACT_PROGRAM_REFERENCE_ONLY" for r in roles):
        raise RuntimeError("Exact original source mappings incomplete")
    events = proposal["candidate_stage4_events"]
    if not events:
        raise RuntimeError("No Rock candidate events")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"genre": "ROCK", "diagnostic_only": True, "live_composer_unchanged": True,
                "mixer_unchanged": True, "tempo_bpm": 123, "stems": []}
    for role in roles:
        name = role["role"]
        selected = [e for e in events if e["track_id"] == name]
        if not selected:
            raise RuntimeError("Empty original-source part: " + name)
        midi = OUT / (name.lower() + ".mid")
        wav = OUT / (name.lower() + ".wav")
        midi.write_bytes(midi_track(selected, 123))
        result = render_midi(registry[role["binding_id"]], midi, wav, sample_rate=22050)
        if not result["audio_rendered"] or not math.isfinite(result["peak_linear"]) or result["peak_linear"] <= 0:
            raise RuntimeError("Silent original-source part: " + name)
        manifest["stems"].append({"role": name, "events": len(selected),
                                  "source": role["binding_id"], "peak_dbfs": result["peak_dbfs"],
                                  "wav": wav.name, "midi": midi.name})
        print("ORIGINAL_ROCK_STEM_RENDERED", name, len(selected), flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("FIVE_ORIGINAL_RECORDED_ROCK_STEMS_READY_FOR_ISOLATED_LISTENING")

if __name__ == "__main__":
    main()
