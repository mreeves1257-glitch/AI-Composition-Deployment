#!/usr/bin/env python3
"""Data-driven onboarding of *recorded* SFZ sample instruments.

A new compatible SFZ instrument is one manifest entry, not a new composer
patch. New banks can be fetched at an exact pinned Git SHA. Source SFZs and
samples are never edited; a restricted declarative note map creates a
separate derivative. Nothing is registered until a complete sample-graph
and non-silent audition of every required note passes.

The preserved 5 baseline sound libraries remain installed by the original
build script. This file adds future banks/instruments only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "verified_future_instruments.json"
BANK_ROOT = HERE / "sound_resources"
TARGET = HERE / "target_registry.json"
BANK_ID = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")
INSTRUMENT_ID = re.compile(r"^[a-z][a-z0-9_:]{1,79}$")
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
GIT_URL = re.compile(r"^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+[.]git$")
ALLOWED_LICENSES = {"CC0", "CC0-1.0", "CC-BY-3.0", "CC-BY-4.0"}
MARK = "AUTO_REAL_SAMPLE_INSTRUMENT"

def fail(reason: str):
    raise ValueError("SAMPLE_BANK_ONBOARDING_REJECTED:" + str(reason))

def clean_relative(raw: str, suffix: str = ".sfz") -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        fail("INVALID_RELATIVE_PATH")
    path = Path(raw)
    if path.is_absolute() or any(x in ("", ".", "..") for x in raw.split("/")):
        fail("PATH_TRAVERSAL")
    if path.suffix.lower() != suffix:
        fail("UNEXPECTED_FILE_TYPE:" + str(raw))
    return path

def validate_manifest(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("MANIFEST_VERSION")
    if not isinstance(data.get("new_banks"), list) or not isinstance(data.get("new_instruments"), list):
        fail("MANIFEST_SECTIONS")
    bank_ids = set()
    for bank in data["new_banks"]:
        if not isinstance(bank, dict):
            fail("BAD_BANK_ENTRY")
        rid = bank.get("resource_id")
        if not isinstance(rid, str) or not BANK_ID.fullmatch(rid) or rid in bank_ids:
            fail("INVALID_OR_DUPLICATE_BANK_ID")
        bank_ids.add(rid)
        if not isinstance(bank.get("repo"), str) or not GIT_URL.fullmatch(bank["repo"]):
            fail("UNAPPROVED_GIT_SOURCE")
        branch = bank.get("branch")
        if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", branch) or ".." in branch or branch.startswith("-"):
            fail("INVALID_GIT_REF")
        if not isinstance(bank.get("commit"), str) or not HEX_SHA.fullmatch(bank["commit"]):
            fail("BANK_SHA_NOT_PINNED")
        if not isinstance(bank.get("library"), str) or not bank["library"].strip():
            fail("BANK_PROVENANCE_REQUIRED")
        if bank.get("license") not in ALLOWED_LICENSES:
            fail("BANK_LICENSE_NOT_VERIFIED")
    instruments = set()
    for ins in data["new_instruments"]:
        if not isinstance(ins, dict):
            fail("INVALID_INSTRUMENT_ENTRY")
        instrument_id = ins.get("instrument_id")
        if not isinstance(instrument_id, str) or not INSTRUMENT_ID.fullmatch(instrument_id) or instrument_id in instruments:
            fail("INVALID_OR_DUPLICATE_INSTRUMENT_ID")
        instruments.add(instrument_id)
        rid = ins.get("resource_id")
        if not isinstance(rid, str) or not BANK_ID.fullmatch(rid):
            fail("INSTRUMENT_RESOURCE_ID_INVALID")
        clean_relative(ins.get("source_sfz"))
        derivative = ins.get("derived_sfz")
        if derivative is not None:
            clean_relative(derivative)
            if "/" in derivative or derivative == Path(ins["source_sfz"]).name:
                fail("DERIVED_SFZ_MUST_BE_DISTINCT_BASENAME")
        note_map = ins.get("note_map", {})
        if not isinstance(note_map, dict):
            fail("NOTE_MAP_MUST_BE_OBJECT")
        for source_note, dest_note in note_map.items():
            if not isinstance(source_note, str) or not re.fullmatch(r"\d{1,3}", source_note):
                fail("INVALID_SOURCE_NOTE")
            if not 0 <= int(source_note) <= 127 or type(dest_note) is not int or not 0 <= dest_note <= 127:
                fail("NOTE_OUT_OF_RANGE")
        if len(set(note_map.values())) != len(note_map):
            fail("TWO_STROKES_COLLAPSED_TO_ONE_NOTE")
        if bool(note_map) != bool(derivative):
            fail("NOTE_MAP_REQUIRES_DERIVED_SFZ")
        audition = ins.get("test_notes")
        if not isinstance(audition, list) or not audition or any(type(x) is not int or not 0 <= x <= 127 for x in audition):
            fail("AUDITION_NOTES_REQUIRED")
        if len(set(audition)) != len(audition):
            fail("DUPLICATE_AUDITION_NOTE")
        if note_map and set(audition) != set(note_map.values()):
            fail("ALL_MAPPED_STROKES_MUST_BE_AUDITIONED")
        refs = ins.get("expected_sample_references")
        if type(refs) is not int or refs < 1:
            fail("EXPECTED_SAMPLE_REFERENCE_COUNT_REQUIRED")
        if type(ins.get("gain_db", 0.0)) not in (float, int):
            fail("INVALID_GAIN")
    return data

def load_manifest() -> dict:
    return validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))

def install_new_banks(data: dict) -> None:
    for bank in data["new_banks"]:
        rid = bank["resource_id"]
        target = BANK_ROOT / rid
        if target.exists():
            fail("NEW_BANK_ALREADY_PRESENT:" + rid)
        command = ["git", "clone", "--quiet", "--depth", "1", "--branch", bank["branch"], bank["repo"], str(target)]
        subprocess.run(command, check=True, timeout=240)
        recorded = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
        if recorded != bank["commit"]:
            fail("UPSTREAM_COMMIT_CHANGED:" + rid)
        # Git LFS is optional; sample graph check below catches pointer-only files.
        try:
            subprocess.run(["git", "-C", str(target), "lfs", "pull"], check=True, timeout=180,
                           capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        print("ONBOARD_REAL_BANK_PINNED", rid, recorded, flush=True)
    print("ONBOARD_BANK_INSTALL_PASS", len(data["new_banks"]), flush=True)

def write_mapped_sfz(source: Path, destination: Path, notes: dict[str, int]) -> None:
    if source.resolve() == destination.resolve():
        fail("NEVER_OVERWRITE_ORIGINAL_INSTRUMENT")
    text = source.read_text(encoding="utf-8")
    parts = text.split("<group>")
    if len(parts) < 2:
        fail("SFZ_NO_GROUPS_FOR_REMAP")
    # Group-selecting prevents a conga sound, for instance, from being routed
    # accidentally as a bongo or vice versa. Duplicate source keys are
    # retained because they can express velocity layers.
    seen = set()
    selected = [parts[0]]
    for part in parts[1:]:
        match = re.search(r"(?m)^\s*key\s*=\s*(\d+)\s*$", part)
        if not match or match.group(1) not in notes:
            continue
        source_note = match.group(1)
        seen.add(source_note)
        rewritten = re.sub(
            r"(?m)^(\s*key\s*=\s*)\d+(\s*)$",
            lambda m: m.group(1) + str(notes[source_note]) + m.group(2),
            part, count=1)
        selected.append("<group>" + rewritten)
    if seen != set(notes):
        fail("SOURCE_STROKE_NOT_FOUND:" + ",".join(sorted(set(notes) - seen)))
    destination.write_text("\n".join(selected) + "\n", encoding="utf-8")

def make_midi(path: Path, note: int) -> None:
    events = b"\x00\x90" + bytes((note, 104)) + bytes.fromhex("83 60 80") + bytes((note, 0)) + bytes.fromhex("00 ff 2f 00")
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) +
                     b"MTrk" + struct.pack(">I", len(events)) + events)

def apply_new_instruments(data: dict) -> None:
    from production_resource_policy import APPROVED_SAMPLE_BANKS, require_recorded_sample_resource
    from sfz_renderer_adapter import validate_sfz_samples, render_midi
    registry = json.loads(TARGET.read_text(encoding="utf-8"))
    bindings = registry["targets"]["INTERNAL"]["instrument_bindings"]
    new_banks = {b["resource_id"]: b for b in data["new_banks"]}
    for bank in data["new_banks"]:
        if bank["resource_id"] in APPROVED_SAMPLE_BANKS and APPROVED_SAMPLE_BANKS[bank["resource_id"]] != {
            "library": bank["library"], "license": bank["license"]}:
            fail("RESOURCE_PROVENANCE_COLLISION")
    renderer = HERE.parent.parent / ".composer_tools" / "bin" / "sfizz_render"
    if data["new_instruments"] and not renderer.is_file():
        fail("SFIZZ_BINARY_NOT_READY")
    os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
    with tempfile.TemporaryDirectory(prefix="onboard-audio-") as tmp:
        for ins in data["new_instruments"]:
            instrument_id, rid = ins["instrument_id"], ins["resource_id"]
            if instrument_id in bindings:
                fail("PROTECTED_INSTRUMENT_ALREADY_EXISTS:" + instrument_id)
            approved = APPROVED_SAMPLE_BANKS.get(rid)
            if approved is None:
                fail("BANK_NOT_APPROVED:" + rid)
            bank_root = BANK_ROOT / rid
            src = bank_root / clean_relative(ins["source_sfz"])
            if not src.is_file():
                fail("SOURCE_SFZ_NOT_INSTALLED:" + instrument_id)
            mapping = ins["source_sfz"]
            if ins.get("note_map"):
                derived = src.with_name(ins["derived_sfz"])
                if derived.exists():
                    fail("DERIVED_MAPPING_ALREADY_EXISTS:" + str(derived))
                write_mapped_sfz(src, derived, ins["note_map"])
                mapping = str(derived.relative_to(bank_root))
            bind = {
                "resource_id": rid,
                "resource_type": "SFZ_SAMPLE_LIBRARY",
                "preferred_mapping": mapping,
                "library": approved["library"],
                "license": approved["license"],
                "renderer_requirement": "SFZ_COMPATIBLE_SAMPLE_RENDERER",
                "fallback_policy": "NO_SYNTHETIC_SUBSTITUTION",
                "target_gain_db": ins.get("gain_db", 0.0),
                "onboarded_by": MARK,
            }
            if ins.get("stroke_names"):
                bind["strike_map"] = dict(ins["stroke_names"])
            if ins.get("attribution"):
                bind["attribution"] = ins["attribution"]
            require_recorded_sample_resource(bind)
            sound_file = bank_root / mapping
            graph = validate_sfz_samples(sound_file)
            if graph["sample_references"] != ins["expected_sample_references"]:
                fail("SAMPLE_REFERENCE_COUNT_CHANGED:" + instrument_id)
            for note in ins["test_notes"]:
                midi = Path(tmp) / (instrument_id + "-" + str(note) + ".mid")
                wave = Path(tmp) / (instrument_id + "-" + str(note) + ".wav")
                make_midi(midi, note)
                result = render_midi(bind, midi, wave, sample_rate=44100)
                if not result.get("audio_rendered") or result["peak_linear"] <= 0.0:
                    fail("INSTRUMENT_RENDER_SILENT:" + instrument_id + ":" + str(note))
                print("ONBOARD_REAL_SAMPLE_NOTE_PASS", instrument_id, "midi", note,
                      "peak_dbfs", round(result["peak_dbfs"], 2), flush=True)
            bindings[instrument_id] = bind
            print("ONBOARD_VERIFIED_INSTRUMENT", instrument_id, rid,
                  "sample_references", graph["sample_references"], flush=True)
    # Do not touch persistent registry until ALL instruments in this manifest
    # have passed. Failed Render builds never replace the running service.
    if data["new_instruments"]:
        temporary = TARGET.with_suffix(".tmp")
        temporary.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        temporary.replace(TARGET)
    print("ONBOARD_VERIFIED_REAL_INSTRUMENTS_PASS", len(data["new_instruments"]), flush=True)

def self_test() -> None:
    fixture = {
        "schema_version": 1,
        "new_banks": [],
        "new_instruments": [{
            "instrument_id": "real_bongo",
            "resource_id": "FREEPATS_WORLD_PERCUSSION",
            "source_sfz": "instrument.sfz",
            "derived_sfz": "mapped.sfz",
            "note_map": {"51": 60, "52": 61},
            "test_notes": [60, 61],
            "expected_sample_references": 2
        }],
    }
    validate_manifest(fixture)
    for alter in [
        {"instrument_id": "../bad"},
        {"source_sfz": "../fake.sfz"},
        {"test_notes": [60]},
        {"note_map": {"51": 60, "52": 60}},
        {"expected_sample_references": 0},
    ]:
        changed = json.loads(json.dumps(fixture))
        changed["new_instruments"][0].update(alter)
        try:
            validate_manifest(changed)
        except ValueError:
            continue
        raise AssertionError("MANIFEST_INVALID_DATA_ACCEPTED:" + str(alter))
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "source.sfz"
        dst = Path(tmp) / "derived.sfz"
        original = ("<global>\nloop_mode=no_loop\n"
                    "<group>\nkey=51\n<region> sample=x.wav\n"
                    "<group>\nkey=52\n<region> sample=y.wav\n"
                    "<group>\nkey=52\n<region> sample=z.wav\n")
        src.write_text(original, encoding="utf-8")
        write_mapped_sfz(src, dst, {"51": 60, "52": 61})
        result = dst.read_text(encoding="utf-8")
        assert result.count("key=60") == 1 and result.count("key=61") == 2
        assert src.read_text(encoding="utf-8") == original
    print("ONBOARDING_SCHEMA_AND_NOTE_MAP_SELF_TEST PASS", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.install:
        install_new_banks(load_manifest())
    if args.apply:
        apply_new_instruments(load_manifest())
