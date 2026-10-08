"""Isolated A/B: original Rock BASS note-offs vs conservative extended-note candidate.

No production mutation or instrument substitution. Requires already built
composer/runtime from the repository's exact preserved build script.
Outputs independent WAVs and a source-labelled JSON report.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "composer" / "runtime"
OUT = HERE / "rock_bass_ab_output"
PPQ = 480
BARS_IN_WINDOW = 8
BEATS_PER_BAR = 4

def check(condition, reason):
    if not condition:
        raise AssertionError(reason)

def vlq(n):
    check(type(n) is int and n >= 0, "INVALID_VLQ")
    data = [n & 0x7f]
    n >>= 7
    while n:
        data.insert(0, (n & 0x7f) | 0x80)
        n >>= 7
    return bytes(data)

def make_midi(notes, bpm, destination):
    check(20 <= bpm <= 300, "INVALID_TEMPO")
    us_per_quarter = round(60_000_000 / bpm)
    events = [(0, -10, b"\xff\x51\x03" + us_per_quarter.to_bytes(3, "big"))]
    for note in notes:
        onset = round(note["start_beat"] * PPQ)
        end = round((note["start_beat"] + note["duration_beats"]) * PPQ)
        check(0 <= onset < end and 0 <= note["midi"] < 128, "INVALID_BASS_NOTE")
        check(1 <= note["velocity"] <= 127, "INVALID_BASS_VELOCITY")
        events.append((onset, 1, bytes((0x90, note["midi"], note["velocity"]))))
        events.append((end, 0, bytes((0x80, note["midi"], 0))))
    events.sort(key=lambda item: (item[0], item[1]))
    cursor = 0
    chunks = []
    for tick, _, data in events:
        chunks.extend((vlq(tick - cursor), data))
        cursor = tick
    chunks.append(b"\x00\xff\x2f\x00")
    track = b"".join(chunks)
    midi = b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
    midi += b"MTrk" + struct.pack(">I", len(track)) + track
    destination.write_bytes(midi)
    return hashlib.sha256(midi).hexdigest()

def load_real_rock():
    check(ROOT.is_dir(), "ORIGINAL_COMPOSER_RUNTIME_NOT_BUILT")
    sys.path.insert(0, str(ROOT))
    src = ROOT / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
    spec = importlib.util.spec_from_file_location("rock_bass_original_adapter", src)
    check(spec is not None and spec.loader is not None, "NO_ORIGINAL_ADAPTER")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    registry = json.loads((ROOT / "AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json").read_text())
    profile = registry["profiles"]["ROCK"]
    result = adapter.build_setup("ROCK", profile, "normal", 0)
    check(result.get("status") == "PASS", "REAL_ROCK_BUILD_NOT_PASS:" + str(result.get("status")))
    events = result.get("events")
    check(isinstance(events, list), "REAL_ROCK_NOTES_NOT_FOUND")
    bass = [dict(e) for e in events if str(e.get("track_id", "")).upper() == "BASS"]
    check(len(bass) >= 8, "INSUFFICIENT_REAL_ROCK_BASS_EVENTS")
    for e in bass:
        for key in ("start_beat", "duration_beats", "midi", "velocity"):
            check(key in e, "REAL_BASS_MISSING:" + key)
        e["start_beat"] = float(e["start_beat"])
        e["duration_beats"] = float(e["duration_beats"])
        e["midi"] = int(e["midi"])
        e["velocity"] = int(e["velocity"])
    bass.sort(key=lambda e: (e["start_beat"], e["midi"]))
    return result, events, bass

def candidate_duration(note, next_onset):
    original = note["duration_beats"]
    articulation = str(note.get("articulation") or "").lower()
    if any(word in articulation for word in ("mute", "staccato", "short", "chop", "pizz", "stop")):
        return original
    if next_onset is None:
        return original
    spacing = next_onset - note["start_beat"]
    if spacing < 0.80:  # fast notes retain exactly the composed articulation
        return original
    # Never touch onset, pitch, velocity, explicit phrase gaps or sample mapping.
    # A/B heuristic only: 78% of available phrase room, with a hard 1.50-beat cap.
    desired = min(1.50, spacing * 0.78)
    if desired - original < 0.14:
        return original
    return round(desired, 6)

def choose_eight_bar_window(bass):
    for index, note in enumerate(bass[:-1]):
        next_onset = bass[index + 1]["start_beat"]
        if candidate_duration(note, next_onset) > note["duration_beats"] + 0.001:
            center_bar = int(note["start_beat"] // BEATS_PER_BAR)
            return max(0, center_bar - 2) * BEATS_PER_BAR, index
    raise AssertionError("NO_ELIGIBLE_REAL_BASS_NOTES_REPORTED_NOT_FAKED")

def audition():
    result, all_events, bass = load_real_rock()
    origin, witness_index = choose_eight_bar_window(bass)
    stop = origin + BEATS_PER_BAR * BARS_IN_WINDOW
    baseline = []
    modified = []
    revisions = []
    for i, note in enumerate(bass):
        if not origin <= note["start_beat"] < stop:
            continue
        near = copy.deepcopy(note)
        near["start_beat"] = round(note["start_beat"] - origin, 6)
        proposed = dict(near)
        next_onset = bass[i + 1]["start_beat"] if i + 1 < len(bass) else None
        new_dur = candidate_duration(note, next_onset)
        if near["start_beat"] + new_dur > BEATS_PER_BAR * BARS_IN_WINDOW:
            new_dur = min(new_dur, BEATS_PER_BAR * BARS_IN_WINDOW - near["start_beat"])
        check(new_dur > 0, "WINDOW_CROP_FAILED")
        proposed["duration_beats"] = new_dur
        baseline.append(near)
        modified.append(proposed)
        if new_dur - near["duration_beats"] >= 0.14:
            revisions.append({"midi": near["midi"], "absolute_start_beat": note["start_beat"],
                             "old_duration_beats": near["duration_beats"], "new_duration_beats": new_dur})
    check(revisions, "WINDOW_HAS_NO_CHANGES")
    check(len(baseline) == len(modified), "MISSING_NOTES")
    for a, b in zip(baseline, modified):
        check(all(a[key] == b[key] for key in ("midi", "velocity", "start_beat", "instrument_id", "track_id")),
              "UNINTENDED_MUSIC_CHANGE")
        check(b["duration_beats"] >= a["duration_beats"], "DURATION_WAS_SHORTENED")
    OUT.mkdir(parents=True, exist_ok=True)
    bpm = float(result["tempo_bpm"])
    registry = json.loads((ROOT / "target_registry.json").read_text())
    binding = registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"]
    check(binding["resource_id"] == "KARORYFER_GROWLYBASS_V1_002"
          and binding["preferred_mapping"] == "growlybass_clean.sfz"
          and binding["resource_type"] == "SFZ_SAMPLE_LIBRARY", "BASS_RESOURCE_IDENTITY_CHANGED")
    check((ROOT / "sound_resources" / binding["resource_id"] / binding["preferred_mapping"]).is_file(),
          "ORIGINAL_REAL_BASS_SOURCE_MISSING")
    from sfz_renderer_adapter import render_midi
    os.environ["AI_COMP_RESOURCE_BANK"] = str(ROOT / "sound_resources")
    renderer = HERE.parent / ".composer_tools" / "bin" / "sfizz_render"
    check(renderer.is_file(), "ORIGINAL_SFIZZ_RENDERER_NOT_BUILT")
    os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
    files = {}
    hashes = {}
    for key, notes in (("original", baseline), ("candidate", modified)):
        mid = OUT / ("rock-bass-" + key + ".mid")
        wav = OUT / ("rock-bass-" + key + ".wav")
        hashes[key] = make_midi(notes, bpm, mid)
        render = render_midi(binding, mid, wav, sample_rate=44100)
        check(render.get("audio_rendered") and render["peak_linear"] > 0, "REAL_BASS_AUDIO_NOT_RENDERED:" + key)
        with wave.open(str(wav), "rb") as stream:
            frames = stream.getnframes()
            channels = stream.getnchannels()
            check(stream.getsampwidth() == 2 and stream.getframerate() == 44100 and frames > 0,
                  "UNEXPECTED_RENDERED_AUDIO_FORMAT")
            data = np.frombuffer(stream.readframes(frames), dtype="<i2").astype(np.float32) / 32768
            files[key] = data.reshape(-1, channels).mean(axis=1)
        print("REAL_BASS_RENDER", key, "frames", frames, "rms_dbfs", render["rms_dbfs"], flush=True)
    a, b = files["original"], files["candidate"]
    common = min(a.size, b.size)
    delta = float(np.sqrt(np.mean((a[:common] - b[:common]) ** 2)))
    report = {
        "study": "EXISTING_REAL_COMPOSER_ROCK_BASS_EIGHT_BAR_AB_V1",
        "status": "SOURCE_AUDIO_AB_PROOF_NOT_PRODUCTION_APPROVAL",
        "genre": "ROCK", "composer_mode": "normal", "creation_seed": 0,
        "source": binding["resource_id"], "sfz": binding["preferred_mapping"],
        "tempo_bpm": bpm, "original_song_event_count": len(all_events),
        "original_bass_event_count": len(bass), "audition_window_start_beat": origin,
        "audition_note_count": len(baseline), "candidate_extended_notes": len(revisions),
        "revisions": revisions, "midi_sha256": hashes,
        "sample_rate": 44100, "audio_difference_rms": delta,
        "waveform_changed_measurably": delta > 1e-6,
        "loudness_improvement_proven": False,
        "natural_human_performance_proven": False,
        "deployed_or_routed": False,
    }
    (OUT / "findings.json").write_text(json.dumps(report, indent=2) + "\n")
    print("REAL_COMPOSED_ROCK_BASS_AB_REPORT", json.dumps(report, sort_keys=True), flush=True)

if __name__ == "__main__":
    audition()
