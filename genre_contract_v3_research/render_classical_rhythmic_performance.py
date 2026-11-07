"""Research-only Classical rhythmic/performance listening gate.

This is a response to a failed human listening review: the previous combined
grammar+melody render was harmonically valid but rhythmically mechanical.

The live Composer is not modified. Orchestration remains disabled.

This gate adds musical time before orchestral color:
- meter-aware accompaniment figures,
- beat hierarchy,
- phrase dynamic arcs,
- cadence breathing,
- deterministic tempo shaping,
- melody/accompaniment articulation contrast.

The pitch source remains the validated period grammar, SATB voice leading, and
harmony-bound melody.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import mido

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "genre_contract_v3_research"
RUNTIME = ROOT / "composer" / "runtime"
for p in (ROOT, RESEARCH, RUNTIME):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from genre_contract_v3_research import classical_melody_grammar_binding_validation as binding
from genre_contract_v3_research import classical_voice_leading_validation as voice

SCHEMA = "CLASSICAL_RHYTHMIC_PERFORMANCE_GATE_001"
TPB = 480
PIANO_PROGRAM = 0
MONITORING_GAIN_DB = 18.0
MELODY_VARIANT = "CLASSICAL_PERIOD_TOPLINE"
OUTPUT_ID = "CLASSICAL_PERIOD_RHYTHMIC"


def _load_runtime_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNTIME_MODULE_LOAD_FAILED:" + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_runtime_render = _load_runtime_module(
    "rhythmic_runtime_render_substitute",
    RUNTIME / "render_substitute_universal.py",
)
render_track = _runtime_render.render_track


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _phrase_position(bar: int) -> int:
    if bar <= 24:
        return (bar - 1) % 8
    return bar - 25


def _phrase_dynamic(bar: int) -> int:
    if bar <= 24:
        arch = (0, 2, 4, 6, 5, 3, 1, -3)
        return arch[_phrase_position(bar)]
    coda = (2, 0, -2, -5)
    return coda[_phrase_position(bar)]


def _tempo_for_bar(bar: int) -> float:
    # Phrase motion is intentional, not random jitter.
    if bar <= 8:
        curve = (74, 75, 76, 77, 77, 76, 75, 71)
        return curve[bar - 1]
    if bar <= 16:
        curve = (75, 76, 77, 78, 78, 77, 75, 71)
        return curve[bar - 9]
    if bar <= 24:
        curve = (74, 75, 76, 77, 77, 76, 74, 70)
        return curve[bar - 17]
    return (73, 72, 70, 66)[bar - 25]


def _beat_accent(offset: float) -> int:
    # Strong first beat, lighter second, mild lift into third.
    if abs(offset - 0.0) < 1e-6:
        return 6
    if abs(offset - 1.0) < 1e-6:
        return 0
    if abs(offset - 2.0) < 1e-6:
        return 2
    return -3


def _events_by_bar(realized):
    bars = defaultdict(list)
    for event in realized:
        bars[int(event["bar"])].append(event)
    for bar in bars:
        bars[bar].sort(key=lambda e: float(e["offset_qb"]))
    return bars


def _active_voicing(events, offset: float):
    for event in events:
        start = float(event["offset_qb"])
        end = start + float(event["duration_qb"])
        if start - 1e-9 <= offset < end - 1e-9:
            return event
    return events[-1]


def _classical_pattern(bar: int):
    """Return (part, offset, duration) pulses for one 3/4 bar.

    Patterns intentionally alternate instead of repeating one mechanical cell
    for all 28 bars.
    """
    pos = _phrase_position(bar)
    if bar in (8, 16, 24, 28):
        # Cadence: fewer attacks and more air.
        return (
            ("B", 0.0, 0.78),
            ("T", 1.0, 0.62),
            ("A", 1.0, 0.62),
            ("T", 2.0, 0.78),
            ("A", 2.0, 0.78),
        )
    if pos in (0, 1, 4):
        # Flowing broken-chord figure.
        return (
            ("B", 0.0, 0.42),
            ("T", 0.5, 0.34),
            ("A", 1.0, 0.38),
            ("T", 1.5, 0.34),
            ("A", 2.0, 0.38),
            ("T", 2.5, 0.30),
        )
    if pos in (2, 5):
        # Clear triple-meter support without turning every bar into oom-pah-pah.
        return (
            ("B", 0.0, 0.72),
            ("T", 1.0, 0.48),
            ("A", 1.0, 0.48),
            ("T", 2.0, 0.48),
            ("A", 2.0, 0.48),
        )
    if pos == 3:
        # Forward motion into the phrase midpoint.
        return (
            ("B", 0.0, 0.38),
            ("A", 0.5, 0.30),
            ("T", 1.0, 0.34),
            ("A", 1.5, 0.30),
            ("T", 2.0, 0.34),
            ("A", 2.5, 0.28),
        )
    # Bars 7 / pre-cadential: slightly lighter, leaving room for melody.
    return (
        ("B", 0.0, 0.66),
        ("T", 1.0, 0.42),
        ("A", 1.5, 0.34),
        ("T", 2.0, 0.44),
        ("A", 2.5, 0.28),
    )


def _build_notes(seed: int):
    bound = binding.build_bound_melody(MELODY_VARIANT, seed=seed)
    realized = voice.realize(bound["grammar_plan"])
    by_bar = _events_by_bar(realized)
    notes = []

    # Accompaniment now has an actual rhythmic function.
    for bar in range(1, 29):
        dyn = _phrase_dynamic(bar)
        for part, offset, duration in _classical_pattern(bar):
            event = _active_voicing(by_bar[bar], offset)
            base = {"B": 61, "T": 57, "A": 60}[part]
            velocity = max(35, min(96, base + dyn + _beat_accent(offset)))
            # A tiny deterministic separation between hands avoids identical attack
            # fronts without using random humanization.
            hand_delay = 0.0 if part == "B" else 0.012
            notes.append({
                "part": part,
                "bar": bar,
                "midi": int(event["voicing"][part]),
                "start_beat": (bar - 1) * 3.0 + offset + hand_delay,
                "duration_beats": duration,
                "velocity": velocity,
                "rhythmic_role": "METER_SUPPORT" if part == "B" else "INNER_MOTION",
            })

    # Melody keeps its validated pitch/rhythm identity, but gets phrase shaping.
    for event in bound["events"]:
        bar = int(event["bar"])
        offset = float(event["offset_qb"])
        dyn = _phrase_dynamic(bar)
        cadence = bool(event["cadence_melody"])
        phrase_delay = 0.045 if cadence else 0.0
        weak_note_soften = -2 if abs(offset - round(offset)) > 1e-6 else 0
        velocity = max(
            54,
            min(112, 88 + dyn + _beat_accent(offset) + weak_note_soften),
        )
        duration = float(event["duration_qb"]) * (0.90 if not cadence else 1.02)
        notes.append({
            "part": "MELODY",
            "bar": bar,
            "midi": int(event["midi"]),
            "start_beat": (bar - 1) * 3.0 + offset + phrase_delay,
            "duration_beats": max(0.12, duration),
            "velocity": velocity,
            "rhythmic_role": "FOREGROUND_PHRASE",
        })

    notes.sort(key=lambda x: (
        x["start_beat"],
        0 if x["part"] == "B" else 1 if x["part"] != "MELODY" else 2,
        x["midi"],
    ))
    return bound, realized, notes


def _build_midi(notes, out_path: Path):
    mid = mido.MidiFile(type=1, ticks_per_beat=TPB)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage(
        "track_name", name="Classical Rhythmic Performance Gate", time=0
    ))
    meta.append(mido.MetaMessage(
        "time_signature", numerator=3, denominator=4, time=0
    ))

    # Tempo is shaped bar-by-bar. This is phrase breathing, not jitter.
    tempo_events = []
    for bar in range(1, 29):
        tick = int(round((bar - 1) * 3.0 * TPB))
        tempo_events.append((
            tick,
            mido.MetaMessage(
                "set_tempo",
                tempo=mido.bpm2tempo(_tempo_for_bar(bar)),
                time=0,
            ),
        ))
    prev = 0
    for tick, msg in tempo_events:
        meta.append(msg.copy(time=max(0, tick - prev)))
        prev = tick
    mid.tracks.append(meta)

    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("track_name", name="Acoustic Grand Piano", time=0))
    tr.append(mido.Message("program_change", channel=0, program=PIANO_PROGRAM, time=0))
    tr.append(mido.Message("control_change", channel=0, control=10, value=64, time=0))
    tr.append(mido.Message("control_change", channel=0, control=11, value=108, time=0))
    tr.append(mido.Message("control_change", channel=0, control=91, value=22, time=0))

    abs_msgs = []
    for n in notes:
        start = int(round(float(n["start_beat"]) * TPB))
        end = int(round((float(n["start_beat"]) + float(n["duration_beats"])) * TPB))
        abs_msgs.append((start, 1, mido.Message(
            "note_on", channel=0, note=int(n["midi"]),
            velocity=int(n["velocity"]), time=0
        )))
        abs_msgs.append((end, 0, mido.Message(
            "note_off", channel=0, note=int(n["midi"]),
            velocity=0, time=0
        )))

    prev = 0
    for tick, order, msg in sorted(abs_msgs, key=lambda x: (x[0], x[1])):
        tr.append(msg.copy(time=max(0, tick - prev)))
        prev = tick

    mid.tracks.append(tr)
    mid.save(out_path)
    return mid


def _validate(bound, notes):
    summary = binding.summarize(bound)
    if summary["structural_chord_tone_pct"] != 100:
        raise RuntimeError("STRUCTURAL_MELODY_NOT_CHORD_LOCKED")
    if summary["cadence_chord_tone_pct"] != 100:
        raise RuntimeError("CADENCE_MELODY_NOT_CHORD_LOCKED")

    accompaniment = [n for n in notes if n["part"] != "MELODY"]
    melody = [n for n in notes if n["part"] == "MELODY"]
    by_bar = defaultdict(list)
    for n in accompaniment:
        by_bar[n["bar"]].append(n)

    if min(len(by_bar[b]) for b in range(1, 29)) < 5:
        raise RuntimeError("RHYTHMIC_ACCOMPANIMENT_TOO_SPARSE")

    strong = [n["velocity"] for n in accompaniment if abs((n["start_beat"] % 3.0) - 0.0) < 0.05]
    weak = [n["velocity"] for n in accompaniment if abs((n["start_beat"] % 3.0) - 0.5) < 0.08]
    if strong and weak and sum(strong) / len(strong) <= sum(weak) / len(weak):
        raise RuntimeError("BEAT_HIERARCHY_NOT_AUDIBLE_IN_VELOCITY")

    return {
        "status": "PASS",
        "structural_chord_tone_pct": summary["structural_chord_tone_pct"],
        "cadence_chord_tone_pct": summary["cadence_chord_tone_pct"],
        "melody_note_count": len(melody),
        "accompaniment_note_count": len(accompaniment),
        "minimum_accompaniment_attacks_per_bar": min(len(by_bar[b]) for b in range(1, 29)),
        "maximum_accompaniment_attacks_per_bar": max(len(by_bar[b]) for b in range(1, 29)),
        "mean_strong_beat_velocity": round(sum(strong) / max(1, len(strong)), 2),
        "mean_weak_halfbeat_velocity": round(sum(weak) / max(1, len(weak)), 2),
        "tempo_first_bar_bpm": _tempo_for_bar(1),
        "tempo_first_cadence_bpm": _tempo_for_bar(8),
        "tempo_final_cadence_bpm": _tempo_for_bar(28),
        "phrase_dynamic_range_velocity_units": 11,
        "random_timing_jitter_used": False,
    }


def main():
    root_out = Path(os.environ.get(
        "CLASSICAL_RHYTHMIC_OUT",
        "listening/classical_rhythmic_performance",
    ))
    root_out.mkdir(parents=True, exist_ok=True)
    seed = int(os.environ.get("CLASSICAL_RHYTHMIC_SEED", "0"))

    bound, realized, notes = _build_notes(seed)
    validation = _validate(bound, notes)

    midi_path = root_out / "Classical_Period_Rhythmic_Performance.mid"
    mid = _build_midi(notes, midi_path)

    sf = RUNTIME / "replacement_instruments" / "TimGM6mb.sf2"
    if not sf.is_file():
        raise RuntimeError("APPROVED_SOUNDFONT_MISSING:" + str(sf))

    raw_wav = root_out / "Classical_Period_Rhythmic_Performance_raw.wav"
    render_report = render_track(
        mid, 1, sf, raw_wav, "melodic",
        program=PIANO_PROGRAM, tuning_reference_hz=440,
    )

    wav_path = root_out / "Classical_Period_Rhythmic_Performance.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_wav),
        "-af", f"volume={MONITORING_GAIN_DB}dB",
        str(wav_path),
    ], check=True)

    mp3_path = root_out / "Classical_Period_Rhythmic_Performance.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(wav_path),
        "-codec:a", "libmp3lame", "-q:a", "2",
        str(mp3_path),
    ], check=True)

    note_payload = json.dumps(notes, sort_keys=True, separators=(",", ":")).encode()
    summary = {
        "status": "PASS",
        "schema": SCHEMA,
        "research_only": True,
        "live_composer_modified": False,
        "orchestration_enabled": False,
        "human_feedback_addressed": [
            "no rhythmic feel",
            "mechanical timing",
        ],
        "performance_changes": [
            "meter-aware accompaniment figures",
            "strong/weak beat hierarchy",
            "alternating accompaniment cells",
            "phrase dynamic arches",
            "cadence breathing",
            "bar-level tempo shaping",
            "melody/accompaniment articulation contrast",
        ],
        "seed": seed,
        "meter": "3/4",
        "instrumentation": "single acoustic-grand piano",
        "monitoring_gain_db": MONITORING_GAIN_DB,
        "note_plan_sha256": hashlib.sha256(note_payload).hexdigest(),
        "validation": validation,
        "render_report": render_report,
        "midi": str(midi_path),
        "wav": str(wav_path),
        "mp3": str(mp3_path),
        "mp3_sha256": _sha256(mp3_path),
        "next_gate": "HUMAN_LISTENING_BEFORE_ANY_ORCHESTRATION_BINDING",
    }
    (root_out / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
