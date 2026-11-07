"""Render paired Classical-variant auditions from one identical musical plan.

Research only. The live Composer is not modified.

Both variants use:
- the same seed,
- the same form/harmony/theme plan,
- the same approved Classical section programs and rendering/mixing path.

Only the research sidecar's orchestration role/activity behavior differs.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "genre_contract_v3_research"
EXPERIMENTAL = ROOT / "experimental_reasoning"
MASTER = ROOT / "current_master_forward"
RUNTIME = ROOT / "composer" / "runtime"
for p in (RESEARCH, EXPERIMENTAL, MASTER, RUNTIME):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from classical_composition import digest, make_plan
from classical_variant_validation import (
    VARIANT_SCHEDULES,
    orchestrate_variant,
    summarize_variant,
)
import render_classical_reasoning_real_harmony_v0_1 as approved_render


VARIANT_FILENAMES = {
    "CLASSICAL_PERIOD_BASELINE": "Classical_Period_Baseline",
    "LATE_ROMANTIC_EXPANDED": "Late_Romantic_Expanded",
}


def _event_signature(events):
    payload = [
        {
            "player_id": e.get("player_id"),
            "instrument_id": e.get("instrument_id"),
            "midi": int(e["midi"]),
            "start_beat": round(float(e["start_beat"]), 5),
            "duration_beats": round(float(e["duration_beats"]), 5),
            "velocity": int(e["velocity"]),
            "role_state": e.get("role_state"),
            "foreground_family": e.get("foreground_family"),
        }
        for e in events
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _role_timeline(events):
    bars = {}
    for e in events:
        bar = int(e["plan_bar"])
        item = bars.setdefault(bar, {
            "foreground_family": e.get("foreground_family"),
            "foreground_players": set(),
            "active_families": set(),
            "role_states": {},
        })
        fam = approved_render.section_for_player(e["player_id"])
        if e.get("role_state") == "FOREGROUND":
            item["foreground_players"].add(e["player_id"])
        item["active_families"].add(
            "STRINGS" if fam in {"VIOLIN_I","VIOLIN_II","VIOLA","CELLO","DOUBLE_BASS"}
            else "WOODWINDS" if fam in {"FLUTE","OBOE","CLARINET","BASSOON"}
            else "BRASS" if fam in {"HORN","TRUMPET","TROMBONE","TUBA"}
            else "PERCUSSION"
        )
        state = str(e.get("role_state") or "UNSET")
        item["role_states"][state] = item["role_states"].get(state, 0) + 1

    out = {}
    for bar, item in sorted(bars.items()):
        out[str(bar)] = {
            "foreground_family": item["foreground_family"],
            "foreground_players": sorted(item["foreground_players"]),
            "active_families": sorted(item["active_families"]),
            "role_states": dict(sorted(item["role_states"].items())),
        }
    return out


def render_variant(plan, variant_id, root_out):
    events = orchestrate_variant(plan, variant_id)
    approved_render.validate_original_harmony(events, plan)

    name = VARIANT_FILENAMES[variant_id]
    out_dir = root_out / name
    out_dir.mkdir(parents=True, exist_ok=True)

    midi_path = out_dir / f"{name}.mid"
    mid, by_section = approved_render.build_midi(plan, events, midi_path)
    mix_result, wav_path = approved_render.render(mid, out_dir)

    mp3_path = out_dir / f"{name}.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)
    ], check=True)

    event_path = out_dir / f"{name}_events.json"
    event_path.write_text(json.dumps(events, indent=2))

    role_path = out_dir / f"{name}_role_timeline.json"
    role_path.write_text(json.dumps(_role_timeline(events), indent=2))

    structural = summarize_variant(plan, variant_id, events)
    summary = {
        "status": "PASS",
        "research_only": True,
        "live_composer_modified": False,
        "variant_id": variant_id,
        "plan_sha256": digest(plan),
        "event_sha256": _event_signature(events),
        "structural_summary": structural,
        "harmony_validation": "PASS",
        "same_renderer_as_existing_classical_reasoning_audition": True,
        "section_event_counts": {k: len(v) for k, v in by_section.items()},
        "mixer_status": mix_result.get("status"),
        "midi": str(midi_path),
        "wav": str(wav_path),
        "mp3": str(mp3_path),
        "events": str(event_path),
        "role_timeline": str(role_path),
    }
    (out_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _build_ab_file(root_out, first_mp3, second_mp3):
    gap = root_out / "comparison_gap.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1.5", str(gap)
    ], check=True)

    # Normalize container/codec before concatenation; no loudness normalization
    # is applied, because relative orchestral dynamics are part of the audition.
    first_wav = root_out / "ab_first.wav"
    second_wav = root_out / "ab_second.wav"
    for src, dst in ((first_mp3, first_wav), (second_mp3, second_wav)):
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src), "-ar", "44100", "-ac", "2", str(dst)
        ], check=True)

    concat_list = root_out / "ab_concat.txt"
    concat_list.write_text(
        "file '" + first_wav.name + "'\n"
        "file '" + gap.name + "'\n"
        "file '" + second_wav.name + "'\n"
    )
    out = root_out / "Classical_Variant_AB_Comparison.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-codec:a", "libmp3lame", "-q:a", "2", str(out)
    ], check=True)
    return out


def main():
    root_out = Path(os.environ.get(
        "CLASSICAL_VARIANT_OUT",
        "listening/classical_variant_comparison",
    ))
    root_out.mkdir(parents=True, exist_ok=True)

    seed = int(os.environ.get("CLASSICAL_VARIANT_SEED", "0"))
    plan = make_plan(seed=seed, mode="quick", bpm=76)
    plan_path = root_out / "shared_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2))

    summaries = {}
    for variant_id in VARIANT_SCHEDULES:
        summaries[variant_id] = render_variant(plan, variant_id, root_out)

    first = Path(summaries["CLASSICAL_PERIOD_BASELINE"]["mp3"])
    second = Path(summaries["LATE_ROMANTIC_EXPANDED"]["mp3"])
    ab_path = _build_ab_file(root_out, first, second)

    if summaries["CLASSICAL_PERIOD_BASELINE"]["plan_sha256"] != summaries["LATE_ROMANTIC_EXPANDED"]["plan_sha256"]:
        raise RuntimeError("PAIR_DOES_NOT_SHARE_IDENTICAL_PLAN")

    pair_summary = {
        "status": "PASS",
        "research_only": True,
        "live_composer_modified": False,
        "seed": seed,
        "shared_plan_sha256": digest(plan),
        "audition_order": [
            "CLASSICAL_PERIOD_BASELINE",
            "1.5_SECOND_GAP",
            "LATE_ROMANTIC_EXPANDED",
        ],
        "variants": summaries,
        "ab_comparison_mp3": str(ab_path),
        "listening_question": (
            "With melody/harmony/form held constant, do the variants sound like "
            "meaningfully different orchestration behaviors rather than the same "
            "arrangement with different loudness?"
        ),
    }
    (root_out / "pair_validation_summary.json").write_text(json.dumps(pair_summary, indent=2))
    print(json.dumps(pair_summary, indent=2))


if __name__ == "__main__":
    main()
