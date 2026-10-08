"""Build-time compatibility probe for the REAL Greg Sullivan Wurlitzer EP200.

No synthesizer, GM fallback, or substitute sound may pass this test. The
Wurlitzer's original SFZ and FLAC samples are left untouched. We only create
a separate sfizz-compatible SFZ copy with original macro values expanded.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path
from sfz_renderer_adapter import render_midi, validate_sfz_samples

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "sound_resources" / "GREG_SULLIVAN_E_PIANOS"
ORIGINAL = BANK / "Wurlitzer EP200" / "Wurlitzer EP200.sfz"
COMPATIBLE = BANK / "Wurlitzer EP200" / "composer-wurlitzer.sfz"

def prepare() -> None:
    text = ORIGINAL.read_text(encoding="utf-8")
    assert "sample=" in text and "default_path=Samples/" in text, "WURLITZER_SOURCE_UNEXPECTED"
    # Original mapped instrument uses ARIA preprocessor constants. Preserve
    # their documented values, without altering note, sample, or velocity data.
    replacements = {"$RELEASE": "72", "$VELTRACK": "99", "$EXT": "flac"}
    for token, value in replacements.items():
        text = text.replace(token, value)
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#define "))
    if "$EXT" in text or "$RELEASE" in text or "$VELTRACK" in text:
        raise RuntimeError("WURLITZER_UNEXPANDED_MACRO")
    COMPATIBLE.write_text(text + "\n", encoding="utf-8")
    graph = validate_sfz_samples(COMPATIBLE)
    print("WURLITZER_REAL_SAMPLE_GRAPH_PASS", graph, flush=True)

def one_note_probe() -> None:
    work = ROOT / "output" / "resource_probe"
    work.mkdir(parents=True, exist_ok=True)
    midi = work / "wurlitzer-one-note.mid"
    wav = work / "wurlitzer-one-note.wav"
    track = bytes.fromhex("00 90 3c 64 83 60 80 3c 00 00 ff 2f 00")
    midi.write_bytes(
        b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480)
        + b"MTrk" + struct.pack(">I", len(track)) + track
    )
    source = {
        "resource_id": "GREG_SULLIVAN_E_PIANOS",
        "resource_type": "SFZ_SAMPLE_LIBRARY",
        "preferred_mapping": "Wurlitzer EP200/composer-wurlitzer.sfz",
        "library": "Greg Sullivan E-Pianos / Wurlitzer EP200",
        "license": "CC-BY-3.0",
        "fallback_policy": "NO_SYNTHETIC_SUBSTITUTION",
    }
    # The build-stage binary is not yet on PATH; target its installed path.
    renderer = ROOT.parent.parent / ".composer_tools" / "bin" / "sfizz_render"
    assert renderer.is_file(), "SFIZZ_BUILD_RENDERER_MISSING"
    os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
    rendered = render_midi(source, midi, wav, sample_rate=44100)
    assert rendered["audio_rendered"] is True
    assert rendered["measured_samples"] > 0
    assert rendered["peak_linear"] > 0
    print("WURLITZER_REAL_AUDIO_PROBE_PASS",
          {"sample_rate": rendered["sample_rate"], "peak_dbfs": rendered["peak_dbfs"],
           "rms_dbfs": rendered["rms_dbfs"], "samples": rendered["measured_samples"]}, flush=True)

if __name__ == "__main__":
    prepare()
    one_note_probe()
