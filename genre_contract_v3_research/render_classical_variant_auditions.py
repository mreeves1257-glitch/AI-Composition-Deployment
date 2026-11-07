"""Render paired research-only Classical variant auditions from one fixed plan.

Both variants use the same theme, harmony, form, tempo map, instrument resources,
stem renderer and final mixer. Only the variant orchestration event layer differs.

This file is isolated under genre_contract_v3_research and does not modify live
Composer runtime authority.
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
MASTER = ROOT / "current_master_forward"
RUNTIME = ROOT / "composer" / "runtime"
RESEARCH = ROOT / "genre_contract_v3_research"
for p in (MASTER, RUNTIME, RESEARCH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import classical_composition as cc
import classical_variant_validation as cvv
from approved_audio_pipeline import (
    CLASSICAL_GOLDEN_SECTION_CONTROLS,
    CLASSICAL_GOLDEN_SECTION_PROGRAMS,
)


def _load_runtime_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNTIME_MODULE_LOAD_FAILED:" + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_runtime_render = _load_runtime_module(
    "variant_runtime_render", RUNTIME / "render_substitute_universal.py"
)
_runtime_mixer = _load_runtime_module(
    "variant_runtime_mixer", RUNTIME / "original_mixer_adapter.py"
)
render_track = _runtime_render.render_track
mix = _runtime_mixer.mix

SECTIONS = [
    ("VIOLIN_I", "violin"),
    ("VIOLIN_II", "violin"),
    ("VIOLA", "viola"),
    ("CELLO", "cello"),
    ("DOUBLE_BASS", "double_bass"),
    ("FLUTE", "concert_flute"),
    ("OBOE", "oboe"),
    ("CLARINET", "clarinet_bb"),
    ("BASSOON", "bassoon"),
    ("HORN", "horn_f"),
    ("TRUMPET", "trumpet_c"),
    ("TROMBONE", "tenor_trombone"),
    ("TUBA", "bass_tuba"),
    ("TIMPANI", "timpani"),
]
CHANNELS = [0,1,2,3,4,5,6,7,8,10,11,12,13,14]


def section_for_player(player_id):
    p = str(player_id or "").upper()
    if p.startswith("VIOLIN_I_"): return "VIOLIN_I"
    if p.startswith("VIOLIN_II_"): return "VIOLIN_II"
    if p.startswith("VIOLA_"): return "VIOLA"
    if p.startswith("CELLO_"): return "CELLO"
    if p.startswith("DOUBLE_BASS_"): return "DOUBLE_BASS"
    if p.startswith("FLUTE_"): return "FLUTE"
    if p.startswith("OBOE_"): return "OBOE"
    if p.startswith("CLARINET_"): return "CLARINET"
    if p.startswith("BASSOON_"): return "BASSOON"
    if p.startswith("HORN_"): return "HORN"
    if p.startswith("TRUMPET_"): return "TRUMPET"
    if p.startswith("TROMBONE_"): return "TROMBONE"
    if p.startswith("TUBA_"): return "TUBA"
    if p.startswith("TIMPANI_"): return "TIMPANI"
    raise ValueError("CLASSICAL_SECTION_UNRESOLVED:" + p)


def validate_harmony(events, plan):
    bars = {int(b["bar"]): b for b in plan["bars"]}
    bad = []
    for e in events:
        if e["instrument_id"] == "timpani":
            continue
        b = bars[int(e["plan_bar"])]
        chord = cc.CHORDS[b["quality"]][b["roman"]]
        pcs = {(int(b["tonic_pc"]) + int(x)) % 12 for x in chord}
        if int(e["midi"]) % 12 not in pcs:
            bad.append((e["plan_bar"], e["player_id"], e["midi"], sorted(pcs)))
    if bad:
        raise RuntimeError("VARIANT_HARMONY_VALIDATION_FAILED:" + repr(bad[:12]))


def build_midi(plan, events, out_path, title):
    tpb = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name=title, time=0))
    prev = 0
    tempo_events = []
    for item in plan["tempo_map"]:
        tick = int(round(float(item["start_beat"]) * tpb))
        tempo_events.append(
            (tick, mido.MetaMessage(
                "set_tempo", tempo=mido.bpm2tempo(float(item["bpm"])), time=0
            ))
        )
    for tick, msg in sorted(tempo_events, key=lambda x: x[0]):
        meta.append(msg.copy(time=tick - prev))
        prev = tick
    mid.tracks.append(meta)

    dedupe = {}
    for e in events:
        sec = section_for_player(e["player_id"])
        key = (
            sec,
            round(float(e["start_beat"]), 5),
            round(float(e["duration_beats"]), 5),
            int(e["midi"]),
        )
        old = dedupe.get(key)
        if old is None or int(e["velocity"]) > int(old["velocity"]):
            dedupe[key] = e

    by_section = defaultdict(list)
    for e in dedupe.values():
        by_section[section_for_player(e["player_id"])].append(e)

    for channel, (sec, iid) in zip(CHANNELS, SECTIONS):
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=sec, time=0))
        program = int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec])
        ctl = CLASSICAL_GOLDEN_SECTION_CONTROLS[sec]
        tr.append(mido.Message(
            "program_change", channel=channel, program=program, time=0
        ))
        tr.append(mido.Message(
            "control_change", channel=channel, control=10,
            value=int(ctl["pan"]), time=0
        ))
        tr.append(mido.Message(
            "control_change", channel=channel, control=11,
            value=int(ctl["expression"]), time=0
        ))
        tr.append(mido.Message(
            "control_change", channel=channel, control=91,
            value=int(ctl["reverb"]), time=0
        ))
        abs_msgs = []
        for e in by_section.get(sec, []):
            start = int(round(float(e["start_beat"]) * tpb))
            end = int(round(
                (float(e["start_beat"]) + float(e["duration_beats"])) * tpb
            ))
            note = int(e["midi"])
            vel = int(e["velocity"])
            abs_msgs.append((
                start, 1,
                mido.Message(
                    "note_on", channel=channel, note=note,
                    velocity=vel, time=0
                ),
            ))
            abs_msgs.append((
                end, 0,
                mido.Message(
                    "note_off", channel=channel, note=note,
                    velocity=0, time=0
                ),
            ))
        prev = 0
        for tick, order, msg in sorted(abs_msgs, key=lambda x: (x[0], x[1])):
            tr.append(msg.copy(time=max(0, tick - prev)))
            prev = tick
        mid.tracks.append(tr)

    mid.save(out_path)
    return mid, by_section


def render_variant(mid, out_dir, variant_id):
    stems = out_dir / "stems"
    mixed = out_dir / "mixed"
    stems.mkdir(parents=True, exist_ok=True)
    mixed.mkdir(parents=True, exist_ok=True)

    sf = RUNTIME / "replacement_instruments" / "TimGM6mb.sf2"
    if not sf.is_file():
        raise RuntimeError("APPROVED_SOUNDFONT_MISSING:" + str(sf))

    rendered = []
    for idx, (sec, iid) in enumerate(SECTIONS, 1):
        wav = stems / f"{idx:02d}_{sec}.wav"
        program = int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec])
        rep = render_track(
            mid, idx, sf, wav, "melodic",
            program=program, tuning_reference_hz=440
        )
        rep.update(
            track_id=sec, instrument_id=iid, program=program, wav_path=str(wav)
        )
        rendered.append(rep)

    perf = []
    profiles = []
    bindings = []
    for idx, (sec, iid) in enumerate(SECTIONS, 1):
        profiles.append({"track_id": sec, "instrument_id": iid, "role": sec})
        bindings.append({
            "track_id": sec,
            "resource": {
                "renderer": "TIMGM6MB_APPROVED_SUBSTITUTE",
                "soundfont": str(sf),
                "program": int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec]),
                "target_gain_db": 0.0,
                "substitute": True,
            },
        })
        for msg in mid.tracks[idx]:
            if msg.type == "note_on" and msg.velocity > 0:
                perf.append({
                    "track_id": sec,
                    "instrument_id": iid,
                    "pitch": msg.note,
                    "velocity": msg.velocity,
                })

    fingerprint = hashlib.sha256(
        json.dumps(perf, sort_keys=True).encode()
    ).hexdigest()
    engine_result = {
        "genre": "Classical",
        "modules": {
            "instrument": {"profiles": profiles},
            "target": {"resolved_resources": bindings},
            "performance": {"events": perf},
            "theory": {"composition_fingerprint": fingerprint},
        },
        "research_variant_id": variant_id,
    }
    stem_manifest = {
        "tracks": [
            {
                "track_id": r["track_id"],
                "instrument_id": r["instrument_id"],
                "wav_path": r["wav_path"],
            }
            for r in rendered
        ]
    }
    manifest_path = out_dir / "stem_manifest.json"
    manifest_path.write_text(json.dumps(stem_manifest, indent=2))
    result = mix(
        manifest_path, mixed, genre="Classical", engine_result=engine_result
    )
    wav_path = (
        Path(result["wav_path"])
        if result.get("wav_path")
        else next(mixed.rglob("stereo_derivative.wav"))
    )
    return result, wav_path


def main():
    out = Path(os.environ.get(
        "CLASSICAL_VARIANT_OUT", "listening/research_classical_variants"
    ))
    out.mkdir(parents=True, exist_ok=True)

    plan = cc.make_plan(seed=0, mode="quick", bpm=76)
    common_plan_hash = cc.digest(plan)
    structural = cvv.build_validation(seed=0, mode="quick")
    summaries = {}

    for variant_id in (
        "CLASSICAL_PERIOD_BASELINE",
        "LATE_ROMANTIC_EXPANDED",
    ):
        variant_dir = out / variant_id
        variant_dir.mkdir(parents=True, exist_ok=True)
        events = cvv.orchestrate_variant(plan, variant_id)
        validate_harmony(events, plan)

        midi_path = variant_dir / f"{variant_id}.mid"
        mid, by_section = build_midi(
            plan, events, midi_path, f"Research {variant_id}"
        )
        mix_result, wav_path = render_variant(mid, variant_dir, variant_id)

        mp3_path = variant_dir / f"{variant_id}.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)
        ], check=True)

        summaries[variant_id] = {
            "status": "PASS",
            "plan_sha256": common_plan_hash,
            "event_count": len(events),
            "section_event_counts": {
                k: len(v) for k, v in by_section.items()
            },
            "structural_summary": structural["variants"][variant_id],
            "mixer_status": mix_result.get("status"),
            "midi": str(midi_path),
            "wav": str(wav_path),
            "mp3": str(mp3_path),
        }

    if (
        summaries["CLASSICAL_PERIOD_BASELINE"]["plan_sha256"]
        != summaries["LATE_ROMANTIC_EXPANDED"]["plan_sha256"]
    ):
        raise RuntimeError("PAIRED_VARIANTS_DID_NOT_SHARE_PLAN")

    result = {
        "status": "PASS",
        "research_only": True,
        "live_runtime_modified": False,
        "same_theme_harmony_form_and_tempo": True,
        "plan_sha256": common_plan_hash,
        "variants": summaries,
    }
    (out / "validation_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
