"""Offline full Composer output handoff -> native MIDI -> real recorded WAV.

This is ONE source-aware sample test. It does not assert musical humanity or
enable any genre. It uses exactly the current target_registry's 'lead_guitar'
binding and sfizz recorded Shinyguitar SFZ program.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import os
import tempfile
import wave

from AI_Comp_Executable_Output_Core_001 import MidiAdapter
from output_handoff import build_execution_package
from sfz_renderer_adapter import render_midi
from test_instrument_gesture_handoff import engine_result


ROOT = Path(__file__).resolve().parent


def _pcm(path: Path) -> bytes:
    with wave.open(str(path), "rb") as s:
        if s.getframerate() != 44100 or s.getnframes() == 0:
            raise AssertionError("BAD_ACTUAL_SFZ_PCM")
        return s.readframes(s.getnframes())


def run():
    registry = json.loads((ROOT/"target_registry.json").read_text())
    resource = registry["targets"]["INTERNAL"]["instrument_bindings"]["lead_guitar"]
    assert resource["resource_id"] == "KARORYFER_SHINYGUITAR"
    assert resource["preferred_mapping"] == "Programs/composer-electric-lead.sfz"
    assert (ROOT/"sound_resources"/resource["resource_id"]/
            resource["preferred_mapping"]).is_file(), "REAL_RECORDED_SFZ_NOT_PRESENT"

    tagged = engine_result("sustained_vibrato")
    untagged = engine_result(None)
    for result in (tagged, untagged):
        result["modules"]["target"]["resolved_resources"][0]["resource"] = resource

    auto_package = build_execution_package(tagged)
    ordinary_package = build_execution_package(untagged)
    assert "expressive_gesture_plan" in dict(auto_package.metadata)
    assert "expressive_gesture_plan" not in dict(ordinary_package.metadata)
    # The control stream deliberately uses the *same* accepted metadata
    # but originates from an untagged note, proving that the handoff metadata
    # is the only link needed for identical expressive sample playback.
    manual_package = replace(ordinary_package, metadata=auto_package.metadata)

    with tempfile.TemporaryDirectory(prefix="resolved-instrument-",dir=str(ROOT/"output")) as tmp:
        rendered = []
        renderer = ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
        assert renderer.is_file(), "REAL_SFIZZ_RENDERER_NOT_BUILT"
        os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
        bytes_by_case={}
        for name, package in (("untagged-original",ordinary_package),
                              ("explicit-manual-plan",manual_package),
                              ("automatic-instrument-handoff",auto_package)):
            mid = Path(tmp)/(name+".mid")
            wav = Path(tmp)/(name+".wav")
            data = MidiAdapter().render(package, "identical-source-fingerprint").payload
            mid.write_bytes(data)
            bytes_by_case[name] = data
            report = render_midi(resource, mid, wav, sample_rate=44100)
            assert report["audio_rendered"], "NO_RECORDED_AUDIO:" + name
            rendered.append(_pcm(wav))
            print("INSTRUMENT_HANDOFF_AUDIO",name,{
                "source":report["resource_id"],
                "peak_dbfs":round(report["peak_dbfs"],3),
                "frames":report["frames"],
            },flush=True)
        assert bytes_by_case["explicit-manual-plan"] == bytes_by_case["automatic-instrument-handoff"], (
            "ROUTED_MIDI_DIFFERS_FROM_KNOWN_EXPRESSIVE_PROGRAM"
        )
        assert rendered[1] == rendered[2], (
            "AUTOMATIC_INSTRUMENT_ROUTE_AUDIO_DIFFERS_FROM_MANUAL_GESTURE"
        )
        assert bytes_by_case["untagged-original"] != bytes_by_case["automatic-instrument-handoff"], (
            "ARTICULATION_NOT_APPLIED_IN_OUTPUT_MIDI"
        )
        print("REAL_RECORDING_EXPLICIT_ARTICULATION_ROUTING_PASS",{
            "source":resource["resource_id"],
            "genre_used_as_performance_template":False,
            "automatic_route_matches_manual_midi":True,
            "automatic_route_matches_manual_wav":True,
            "original_note_without_tag_unchanged":True,
        },flush=True)


if __name__=="__main__":
    run()
