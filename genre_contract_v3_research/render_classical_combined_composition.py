"""Reproducible combined Classical grammar+melody piano listening gate.

Research only. The live Composer is not modified.

This renderer binds:
- period-specific harmonic grammar,
- validated SATB voice-leading accompaniment (A/T/B only),
- period-specific bound melody,
then renders both variants under identical piano/render/monitoring conditions.

It intentionally keeps orchestration disabled so composition behavior can be
judged before orchestral color is introduced.
"""
from __future__ import annotations

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

SCHEMA = "CLASSICAL_COMBINED_GRAMMAR_MELODY_LISTENING_001"
BPM = 76
TPB = 480
PIANO_PROGRAM = 0
MELODY_VELOCITY = 94
ACCOMP_VELOCITY = {"A": 66, "T": 62, "B": 68}
MONITORING_GAIN_DB = 18.0

VARIANTS = {
    "CLASSICAL_PERIOD_COMBINED": "CLASSICAL_PERIOD_TOPLINE",
    "ROMANTIC_TONAL_COMBINED": "ROMANTIC_TONAL_TOPLINE",
}


def _load_runtime_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNTIME_MODULE_LOAD_FAILED:" + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_runtime_render = _load_runtime_module(
    "combined_runtime_render_substitute",
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


def _note_events(melody_variant: str, seed: int):
    bound = binding.build_bound_melody(melody_variant, seed=seed)
    grammar_plan = bound["grammar_plan"]
    realized = voice.realize(grammar_plan)

    notes = []

    # Lower accompaniment: A/T/B from the validated SATB realization.
    for event in realized:
        start = (int(event["bar"]) - 1) * 3.0 + float(event["offset_qb"])
        duration = max(0.10, float(event["duration_qb"]) * 0.94)
        for part in ("A", "T", "B"):
            notes.append({
                "part": part,
                "midi": int(event["voicing"][part]),
                "start_beat": start,
                "duration_beats": duration,
                "velocity": int(ACCOMP_VELOCITY[part]),
            })

    # Foreground: the harmony-aware bound melody.
    for event in bound["events"]:
        start = (int(event["bar"]) - 1) * 3.0 + float(event["offset_qb"])
        notes.append({
            "part": "MELODY",
            "midi": int(event["midi"]),
            "start_beat": start,
            "duration_beats": max(0.10, float(event["duration_qb"])),
            "velocity": MELODY_VELOCITY,
        })

    notes.sort(key=lambda x: (x["start_beat"], 0 if x["part"] != "MELODY" else 1, x["midi"]))
    return bound, realized, notes


def _build_midi(notes, out_path: Path):
    mid = mido.MidiFile(type=1, ticks_per_beat=TPB)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name="Combined Classical Composition Gate", time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0))
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    mid.tracks.append(meta)

    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("track_name", name="Acoustic Grand Piano", time=0))
    tr.append(mido.Message("program_change", channel=0, program=PIANO_PROGRAM, time=0))
    tr.append(mido.Message("control_change", channel=0, control=10, value=64, time=0))
    tr.append(mido.Message("control_change", channel=0, control=11, value=105, time=0))
    tr.append(mido.Message("control_change", channel=0, control=91, value=24, time=0))

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


def _render_variant(output_id: str, melody_variant: str, seed: int, root_out: Path):
    out_dir = root_out / output_id
    out_dir.mkdir(parents=True, exist_ok=True)

    bound, realized, notes = _note_events(melody_variant, seed)

    midi_path = out_dir / f"{output_id}_Listening.mid"
    mid = _build_midi(notes, midi_path)

    sf = RUNTIME / "replacement_instruments" / "TimGM6mb.sf2"
    if not sf.is_file():
        raise RuntimeError("APPROVED_SOUNDFONT_MISSING:" + str(sf))

    raw_wav = out_dir / f"{output_id}_raw.wav"
    render_report = render_track(
        mid, 1, sf, raw_wav, "melodic",
        program=PIANO_PROGRAM, tuning_reference_hz=440,
    )

    listened_wav = out_dir / f"{output_id}_Listening.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_wav),
        "-af", f"volume={MONITORING_GAIN_DB}dB",
        str(listened_wav),
    ], check=True)

    mp3_path = out_dir / f"{output_id}_Listening.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(listened_wav),
        "-codec:a", "libmp3lame", "-q:a", "2",
        str(mp3_path),
    ], check=True)

    bound_summary = binding.summarize(bound)
    structural = {
        "structural_chord_tone_pct": bound_summary["structural_chord_tone_pct"],
        "cadence_chord_tone_pct": bound_summary["cadence_chord_tone_pct"],
        "nonchord_step_resolution_pct": bound_summary["nonchord_step_resolution_pct"],
        "notes_per_qb": bound_summary["notes_per_qb"],
        "mean_abs_interval": bound_summary["mean_abs_interval"],
        "step_pct": bound_summary["step_pct"],
        "leap5_pct": bound_summary["leap5_pct"],
        "max_interval_semitones": bound_summary["max_interval_semitones"],
    }
    if structural["structural_chord_tone_pct"] != 100:
        raise RuntimeError("STRUCTURAL_MELODY_NOT_CHORD_LOCKED")
    if structural["cadence_chord_tone_pct"] != 100:
        raise RuntimeError("CADENCE_MELODY_NOT_CHORD_LOCKED")

    note_payload = json.dumps(notes, sort_keys=True, separators=(",", ":")).encode()
    summary = {
        "status": "PASS",
        "schema": SCHEMA,
        "research_only": True,
        "live_composer_modified": False,
        "output_id": output_id,
        "melody_variant": melody_variant,
        "grammar_variant": bound["grammar_variant"],
        "seed": seed,
        "tempo_bpm": BPM,
        "meter": "3/4",
        "instrumentation": "single acoustic-grand piano",
        "orchestration_enabled": False,
        "melody_velocity": MELODY_VELOCITY,
        "accompaniment_velocities": ACCOMP_VELOCITY,
        "monitoring_gain_db": MONITORING_GAIN_DB,
        "note_count": len(notes),
        "note_plan_sha256": hashlib.sha256(note_payload).hexdigest(),
        "structural_summary": structural,
        "render_report": render_report,
        "midi": str(midi_path),
        "wav": str(listened_wav),
        "mp3": str(mp3_path),
        "mp3_sha256": _sha256(mp3_path),
    }
    (out_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _build_ab(root_out: Path, first: Path, second: Path):
    gap = root_out / "comparison_gap.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1.5", str(gap),
    ], check=True)

    first_wav = root_out / "ab_first.wav"
    second_wav = root_out / "ab_second.wav"
    for src, dst in ((first, first_wav), (second, second_wav)):
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src), "-ar", "44100", "-ac", "2", str(dst),
        ], check=True)

    concat_list = root_out / "ab_concat.txt"
    concat_list.write_text(
        "file '" + first_wav.name + "'\n"
        "file '" + gap.name + "'\n"
        "file '" + second_wav.name + "'\n"
    )

    out = root_out / "Classical_vs_Romantic_Combined_Grammar_Melody_AB.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-codec:a", "libmp3lame", "-q:a", "2", str(out),
    ], check=True)
    return out


def main():
    root_out = Path(os.environ.get(
        "CLASSICAL_COMBINED_OUT",
        "listening/classical_combined_composition",
    ))
    root_out.mkdir(parents=True, exist_ok=True)
    seed = int(os.environ.get("CLASSICAL_COMBINED_SEED", "0"))

    summaries = {}
    for output_id, melody_variant in VARIANTS.items():
        summaries[output_id] = _render_variant(
            output_id, melody_variant, seed, root_out
        )

    first = Path(summaries["CLASSICAL_PERIOD_COMBINED"]["mp3"])
    second = Path(summaries["ROMANTIC_TONAL_COMBINED"]["mp3"])
    ab_path = _build_ab(root_out, first, second)

    pair = {
        "status": "PASS",
        "schema": SCHEMA,
        "research_only": True,
        "live_composer_modified": False,
        "seed": seed,
        "render_conditions_held_constant": [
            "piano_program",
            "tempo",
            "meter",
            "seed",
            "renderer",
            "monitoring_gain",
        ],
        "orchestration_enabled": False,
        "audition_order": [
            "CLASSICAL_PERIOD_COMBINED",
            "1.5_SECOND_GAP",
            "ROMANTIC_TONAL_COMBINED",
        ],
        "variants": summaries,
        "ab_comparison_mp3": str(ab_path),
        "ab_comparison_sha256": _sha256(ab_path),
        "listening_question": (
            "Before orchestration is added, does the first half read as a tighter "
            "Classical-period composition and the second as a broader, more chromatic "
            "Romantic composition rather than merely the same piano texture?"
        ),
        "next_gate": "HUMAN_LISTENING_THEN_PERIOD_PACKAGE_ORCHESTRATION_BINDING",
    }
    (root_out / "pair_validation_summary.json").write_text(
        json.dumps(pair, indent=2)
    )
    print(json.dumps(pair, indent=2))


if __name__ == "__main__":
    main()
