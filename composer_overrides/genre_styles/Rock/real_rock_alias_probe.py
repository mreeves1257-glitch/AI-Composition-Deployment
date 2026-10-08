"""One-note sampled-audio proof for legacy genre names.

These aliases must address actual Karoryfer SFZ recordings. If either is
silent, missing, or substituted, the Render build MUST fail safely.
"""
from __future__ import annotations
import json
import os
import struct
from pathlib import Path
from sfz_renderer_adapter import render_midi

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "target_registry.json"
OUT = ROOT / "output" / "resource_probe"

def write_midi(path: Path, note: int) -> None:
    track = (b"\x00\x90" + bytes((note, 100))
             + bytes.fromhex("83 60 80") + bytes((note, 0))
             + bytes.fromhex("00 ff 2f 00"))
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480)
                     + b"MTrk" + struct.pack(">I", len(track)) + track)

def main() -> None:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    bindings = reg["targets"]["INTERNAL"]["instrument_bindings"]
    renderer = ROOT.parent.parent / ".composer_tools" / "bin" / "sfizz_render"
    assert renderer.is_file(), "SFIZZ_BUILD_RENDERER_MISSING"
    os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
    OUT.mkdir(parents=True, exist_ok=True)
    cases = (
        ("electric_bass", "electric_bass_guitar", "KARORYFER_GROWLYBASS_V1_002", 48),
        ("lead_guitar", "electric_guitar:LEAD_MELODY", "KARORYFER_SHINYGUITAR", 60),
    )
    for instrument_id, original_id, resource_id, note in cases:
        binding = bindings[instrument_id]
        original = bindings[original_id]
        assert binding["resource_id"] == resource_id
        assert binding["preferred_mapping"] == original["preferred_mapping"]
        assert binding["license"] == original["license"]
        assert binding["fallback_policy"] == "NO_SYNTHETIC_SUBSTITUTION"
        assert binding["alias_of"] == original_id
        midi = OUT / (instrument_id + "-test.mid")
        wav = OUT / (instrument_id + "-test.wav")
        write_midi(midi, note)
        result = render_midi(binding, midi, wav, sample_rate=44100)
        assert result["audio_rendered"] and result["peak_linear"] > 0.0
        print("REAL_GENRE_INSTRUMENT_ALIAS_AUDIO_PASS",
              {"instrument_id": instrument_id, "source_instrument": original_id,
               "sample_bank": resource_id,
               "peak_dbfs": round(result["peak_dbfs"], 3),
               "rms_dbfs": round(result["rms_dbfs"], 3),
               "samples": result["measured_samples"]}, flush=True)

if __name__ == "__main__":
    main()
