#!/usr/bin/env python3
"""Read-only readiness scan across the 55 preserved genre profiles.

Reports instrument routing and verified sample-bank eligibility; does NOT
pretend that a genre passed whole-song rendering. Never substitutes sounds,
removes genre profiles, or modifies the composer/3D mixer.
"""
from __future__ import annotations

import ast
import csv
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
PROFILE_PATH = ROOT / "AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json"
TARGET_PATH = ROOT / "target_registry.json"
OUTPUT_DIR = ROOT / "output" / "genre_readiness"

def source_roles():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    palette_node = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PALETTES"
                for target in node.targets)
    )
    palettes = ast.literal_eval(palette_node.value)
    family = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "family_template"
    )
    namespace = {}
    exec(compile(ast.Module(body=[family], type_ignores=[]), str(SOURCE), "exec"), namespace)
    return palettes, namespace["family_template"]

def scan():
    from production_resource_policy import (
        ProductionResourceBlocked, require_recorded_sample_resource,
    )
    palettes, family_template = source_roles()
    profiles = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["profiles"]
    bindings = json.loads(TARGET_PATH.read_text(encoding="utf-8"))["targets"]["INTERNAL"]["instrument_bindings"]
    if len(profiles) != 55:
        raise RuntimeError("GENRE_REGISTRY_COUNT_UNEXPECTED:" + str(len(profiles)))
    rows = []
    rollup = Counter()
    for genre_name in profiles:
        template = family_template(genre_name)
        if template not in palettes:
            raise RuntimeError("UNRECOGNIZED_GENRE_TEMPLATE:" + genre_name + ":" + template)
        palette = list(palettes[template])
        # Rock is the only genre with a specialized set of declared drum
        # instrument IDs in the preserved build override.
        if genre_name == "ROCK":
            palette = [
                part for role in palette
                for part in (("kick_drum_rock", "snare_drum", "hi_hat") if role == "drums" else (role,))
            ]
        mapped, unavailable, context_required = [], [], []
        for role in palette:
            resource = bindings.get(role)
            if resource is None and role == "electric_guitar":
                # Exact guitar role controls the recorded program/articulation;
                # declaring a generic guitar as ready would hide this distinction.
                context_required.append(role)
                continue
            if resource is None:
                unavailable.append(role)
                continue
            try:
                require_recorded_sample_resource(resource)
            except ProductionResourceBlocked:
                unavailable.append(role)
            else:
                mapped.append(role)
        # Musical part resources may be installed without a completed
        # track-render/full-song verification. Keep those states separate.
        status = ("RESOURCE_MAPPINGS_PRESENT_FULL_SONG_UNTESTED"
                  if not unavailable and not context_required
                  else "NEEDS_RESOURCE_OR_ROLE_ROUTING")
        rollup[status] += 1
        rows.append({
            "genre": genre_name,
            "template": template,
            "declared_instrument_roles": ",".join(palette),
            "approved_sample_mappings": ",".join(mapped),
            "missing_verified_resource": ",".join(unavailable),
            "needs_contextual_role_mapping": ",".join(context_required),
            "status": status,
            "full_music_render_verified": "NO",
        })
    report = {
        "policy": "NO_FAKE_INSTRUMENTS_NO_SILENT_SUBSTITUTION",
        "scope": "static genre declarations and active production sample bindings",
        "genre_count": len(rows),
        "template_count": len(palettes),
        "status_counts": dict(sorted(rollup.items())),
        "full_song_audio_verified_count": 0,
        "caution": ("Resource mapping is necessary but not sufficient. "
                    "Do not mark a genre production-ready until every track "
                    "and a complete song have passed audio rendering."),
        "genres": rows,
    }
    return report

def main():
    report = scan()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "genre_readiness.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_path = OUTPUT_DIR / "genre_readiness.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report["genres"][0]))
        writer.writeheader()
        writer.writerows(report["genres"])
    print("GENRE_RESOURCE_READINESS_SCAN_PASS", json.dumps({
        "genres": report["genre_count"],
        "templates": report["template_count"],
        "status_counts": report["status_counts"],
        "full_song_audio_verified_count": report["full_song_audio_verified_count"],
        "report": str(csv_path),
    }, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
