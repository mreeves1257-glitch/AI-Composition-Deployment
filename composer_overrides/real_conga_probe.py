"""Audio validation for real FreePats recorded congas and their genre notes.

The historical genre composer sends conga MIDI 60, 61, 62.  FreePats ships
its genuine conga strokes at 62..66.  Build a conga-only SFZ and explicitly
map groups to 60..64 WITHOUT changing sample waveforms or genre event data.
A build fails unless every sample exists AND each of the five strokes
produces non-silent audio through the actual external SFZ renderer.
"""
from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path
from sfz_renderer_adapter import render_midi, validate_sfz_samples

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "sound_resources" / "FREEPATS_WORLD_PERCUSSION"
SOURCE = BANK / "WorldPercussion 20200905.sfz"
OUTPUT = BANK / "composer-conga-five-strokes.sfz"
REGISTRY = ROOT / "target_registry.json"

# SFZ NOTE to COMPOSER NOTE, with labels based on actual sample directories.
# The FreePats README has misleading high/low labels for MIDI 63 and 64;
# use the SFZ paths, not the README order.
NOTE_MAP = {
    62: (60, "standard_conga", "Conga"),
    64: (61, "high_conga", "HighConga"),
    63: (62, "low_conga", "LowConga"),
    65: (63, "muted_conga", "MutedConga"),
    66: (64, "muted_low_conga", "MutedLowConga"),
}
EXPECTED_REFS = {62: 8, 63: 6, 64: 8, 65: 8, 66: 8}

def prepare_mappings() -> None:
    original = SOURCE.read_text(encoding="utf-8")
    chunks = original.split("<group>")
    assert len(chunks) > 20, "FREEPATS_SOURCE_SFZ_UNEXPECTED"
    groups = {}
    for chunk in chunks[1:]:
        m = re.search(r"(?m)^\s*key\s*=\s*(\d+)\s*$", chunk)
        if m is None:
            continue
        source_note = int(m.group(1))
        if source_note not in NOTE_MAP:
            continue
        assert source_note not in groups, "DUPLICATE_CONGA_NOTE_" + str(source_note)
        target_note, label, folder = NOTE_MAP[source_note]
        refs = re.findall(r"(?m)^\s*sample\s*=\s*([^\s]+)", chunk)
        assert len(refs) == EXPECTED_REFS[source_note], (
            "CONGA_REFERENCE_COUNT_MISMATCH", source_note, len(refs)
        )
        assert all(r.startswith("samples/" + folder + "/") for r in refs), (
            "CONGA_STROKE_SAMPLE_FOLDER_MISMATCH", source_note
        )
        key_changed = re.sub(
            r"(?m)^(\s*key\s*=\s*)\d+(\s*)$",
            lambda m: m.group(1) + str(target_note) + m.group(2),
            chunk,
            count=1,
        )
        assert key_changed != chunk or source_note == target_note
        groups[source_note] = "<group>" + key_changed
    assert set(groups) == set(NOTE_MAP), "CONGA_SAMPLE_GROUPS_MISSING"
    # Only FreePats' original samples are referenced; the original SFZ and
    # recordings are not edited, replaced or resynthesized.
    source_header = "<global>\n ampeg_release=100\n loop_mode=no_loop\n"
    parts = [source_header, "\n"]
    for source_note in (62, 64, 63, 65, 66):
        target_note, label, _ = NOTE_MAP[source_note]
        parts.extend((f"\n// {label}: FreePats source note {source_note} => composer note {target_note}\n",
                      groups[source_note], "\n"))
    OUTPUT.write_text("".join(parts), encoding="utf-8")
    result = validate_sfz_samples(OUTPUT)
    assert result["sample_references"] == 38, result
    assert result["unique_samples"] == 38, result
    print("REAL_CONGA_SAMPLE_GRAPH_PASS", result, flush=True)

def write_midi(path: Path, note: int) -> None:
    # One note at velocity 104, hold 0.5s at default 120BPM.
    track = (b"\x00\x90" + bytes((note, 104))
             + bytes.fromhex("83 60 80") + bytes((note, 0))
             + bytes.fromhex("00 ff 2f 00"))
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480)
                     + b"MTrk" + struct.pack(">I", len(track)) + track)

def probe() -> None:
    binding = json.loads(REGISTRY.read_text(encoding="utf-8"))[
        "targets"]["INTERNAL"]["instrument_bindings"]["conga"]
    assert binding["preferred_mapping"] == OUTPUT.name
    assert binding["resource_id"] == "FREEPATS_WORLD_PERCUSSION"
    renderer = ROOT.parent.parent / ".composer_tools" / "bin" / "sfizz_render"
    assert renderer.is_file(), "SFIZZ_BUILD_RENDERER_MISSING"
    os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
    work = ROOT / "output" / "resource_probe"
    work.mkdir(parents=True, exist_ok=True)
    for source_note in (62, 64, 63, 65, 66):
        target_note, label, folder = NOTE_MAP[source_note]
        assert binding["strike_map"][str(target_note)] == label
        midi = work / (f"conga-{label}.mid")
        wav = work / (f"conga-{label}.wav")
        write_midi(midi, target_note)
        result = render_midi(binding, midi, wav, sample_rate=44100)
        assert result["audio_rendered"] is True and result["peak_linear"] > 0.0
        print("REAL_CONGA_STROKE_AUDIO_PASS", {
            "stroke": label,
            "note": target_note,
            "source_note": source_note,
            "peak_dbfs": round(result["peak_dbfs"], 3),
            "rms_dbfs": round(result["rms_dbfs"], 3),
            "samples": result["measured_samples"],
        }, flush=True)
    print("REAL_CONGA_FIVE_STROKE_AUDIO_PASS", flush=True)

if __name__ == "__main__":
    prepare_mappings()
    probe()
