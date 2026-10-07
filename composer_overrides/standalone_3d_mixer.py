#!/usr/bin/env python3
"""Standalone final-stage 3D mixer for AI Composition.

Input is an already-rendered stem manifest plus the immutable engine result.
This process does not compose, choose instruments, or render SFZ samples.
It is deliberately the last audio stage.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

from spatial_master_handoff import finalize_real_stems


def run_job(job_path: str | Path, output_root: str | Path) -> dict:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    engine_result = job["engine_result"]
    stems = job["stems"]
    result = finalize_real_stems(engine_result, stems, Path(output_root))
    result["mixer_stage"] = "STANDALONE_3D_FINAL_STAGE"
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({
            "status": "AUDIO_3D_MIX_FAILED",
            "audio_rendered": False,
            "reason": "USAGE: standalone_3d_mixer.py JOB_JSON OUTPUT_ROOT",
        }))
        return 2
    try:
        print(json.dumps(run_job(sys.argv[1], sys.argv[2])))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "AUDIO_3D_MIX_FAILED",
            "audio_rendered": False,
            "reason": f"{type(exc).__name__}:{exc}",
            "mixer_stage": "STANDALONE_3D_FINAL_STAGE",
        }))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
