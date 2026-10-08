"""Full recorded-source A/B for automatic musical phrase decisions.

Build sfizz and the original recorded SFZ bank before running. Test compares:
- CONTROL: no automatic decisions, one initial reset CC1=0 at note start
- MANUAL: same onset control, precisely scheduled vibrato at beat 1
- AUTO: NO note articulation tagged; phrase interpreter chooses the timing
Every track routes through actual output_handoff.build_execution_package.
"""
from __future__ import annotations

import json
import os
import tempfile
import wave
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

from AI_Comp_Executable_Output_Core_001 import MidiAdapter
from output_handoff import build_execution_package
from sfz_renderer_adapter import render_midi
from test_instrument_gesture_handoff import engine_result, independently_authored_midi_plan

ROOT = Path(__file__).resolve().parent


def pcm_mono(wav: Path):
    with wave.open(str(wav),"rb") as w:
        assert w.getframerate()==44100 and w.getsampwidth()==2
        channels=w.getnchannels()
        s=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float64)/32768.
        return s.reshape(-1,channels).mean(axis=1)


def difference(a,b,left,right):
    start=round(left*44100)
    end=min(len(a),len(b),round(right*44100))
    assert start<end
    return float(np.sqrt(np.mean((a[start:end]-b[start:end])**2)))


def run():
    target=json.loads((ROOT/"target_registry.json").read_text())
    resource=target["targets"]["INTERNAL"]["instrument_bindings"]["lead_guitar"]
    assert resource["resource_id"]=="KARORYFER_SHINYGUITAR"
    assert resource["preferred_mapping"]=="Programs/composer-electric-lead.sfz"
    assert (ROOT/"sound_resources"/resource["resource_id"]/
            resource["preferred_mapping"]).is_file()

    source=engine_result(None)
    source["modules"]["target"]["resolved_resources"][0]["resource"]=resource

    with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"0"}):
        base=build_execution_package(source)
    with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
        auto=build_execution_package(source)

    assert all(n.articulation is None for n in auto.events)
    assert "expressive_gesture_plan" not in dict(base.metadata)
    assert "expressive_gesture_plan" in dict(auto.metadata)
    assert json.loads(dict(auto.metadata)["expressive_gesture_plan"])=={
        "SOLO":independently_authored_midi_plan()["SOLO"]
    }, "AUTOMATIC_PHRASE_TIMING_NOT_EQUAL_TO_MANUAL_REFERENCE"

    native=independently_authored_midi_plan()
    neutral={"SOLO":dict(native["SOLO"],gestures=[native["SOLO"]["gestures"][0]])}
    def with_plan(src,plan):
        return replace(src,metadata=src.metadata+((
            "expressive_gesture_plan",json.dumps(plan)
        ),))
    baseline=with_plan(base,neutral)
    manual=with_plan(base,native)
    assert os.environ.get("AI_COMP_AUTO_PHRASING_V1") != "1"

    renderer=ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
    assert renderer.is_file(),"REAL_SFIZZ_RENDERER_MISSING"
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    recorded={}
    midi={}
    with tempfile.TemporaryDirectory(prefix="automatic-phrase-audio-",dir=str(ROOT/"output")) as folder:
        for label,pkg in (
            ("neutral-control",baseline),
            ("independently-manual",manual),
            ("automatic-phrase-decision",auto),
        ):
            mid=Path(folder)/(label+".mid")
            wav=Path(folder)/(label+".wav")
            data=MidiAdapter().render(pkg,"same-composition-fingerprint").payload
            midi[label]=data
            mid.write_bytes(data)
            result=render_midi(resource,mid,wav,sample_rate=44100)
            assert result["audio_rendered"] and result["peak_linear"]>0
            recorded[label]=pcm_mono(wav)
            print("AUTO_PHRASE_SFZ_RENDER",label,{
                "resource_id":result["resource_id"],
                "frames":result["frames"],
                "peak_dbfs":round(result["peak_dbfs"],3)
            },flush=True)
    assert midi["independently-manual"]==midi["automatic-phrase-decision"], (
        "AUTOMATED_PHRASE_MIDI_DIFFERS_FROM_NATIVE_MANUAL_REFERENCE"
    )
    assert np.array_equal(recorded["independently-manual"],
                          recorded["automatic-phrase-decision"]), (
        "AUTOMATED_PHRASE_WAV_DIFFERS_FROM_MANUAL_REFERENCE"
    )
    before=difference(recorded["neutral-control"],
                      recorded["automatic-phrase-decision"],0.05,0.35)
    after=difference(recorded["neutral-control"],
                     recorded["automatic-phrase-decision"],0.7,1.2)
    assert before<1e-8,("UNCONTROLLED_AUDIO_DIFFERENCE_BEFORE_AUTO_VIBRATO",before)
    assert after>max(1e-6,before*10), (
        "AUTOMATIC_PHRASE_VIBRATO_DID_NOT_AFFECT_REAL_AUDIO",after
    )
    print("AUTOMATIC_PHRASE_TO_ORIGINAL_SFZ_WAV_PASS",{
        "pre_vibrato_difference_rms":before,
        "post_vibrato_difference_rms":round(after,7),
        "manual_and_auto_wavs_identical":True,
        "composer_note_annotation_required":False,
        "ordinary_production_auto_gate_enabled":False,
        "genre_family_paths_activated":False,
    },flush=True)


if __name__=="__main__":
    run()
