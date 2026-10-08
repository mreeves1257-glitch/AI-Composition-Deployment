"""Offline evidence: a timed source-native MIDI control must change actual WAV.

Run ONLY after build_current_composer.sh has installed the recorded Shinyguitar
sample bank and real sfizz_render executable. No live service, user test,
artificial instrument, 3D mix, or genre handoff is involved.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import wave
from fractions import Fraction
from pathlib import Path

import numpy as np

from AI_Comp_Executable_Output_Core_001 import (
    CompositionExecutionPackage, MidiAdapter, MusicalEvent, TimeSignature,
)
from sfz_renderer_adapter import render_midi


ROOT = Path(__file__).resolve().parent
RESOURCE_ID = "KARORYFER_SHINYGUITAR"
PROGRAM = "Programs/composer-electric-lead.sfz"
CAPABILITY = "SHINYGUITAR_RECORDED_LEAD_CC1_V1"


def package(with_timed_vibrato):
    routing = {"LEAD": {"initial_cc": {"1": 0}}}
    meta = [("midi_routing", json.dumps(routing))]
    if with_timed_vibrato:
        meta.append(("expressive_gesture_plan", json.dumps({
            "LEAD": {
                "capability_id": CAPABILITY,
                "resource_id": RESOURCE_ID,
                "preferred_mapping": PROGRAM,
                "gestures": [
                    {"at_beat": "0", "control": "vibrato_depth", "value": 0},
                    {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                    {"at_beat": "7/2", "control": "vibrato_depth", "value": 0},
                ],
            },
        })))
    return CompositionExecutionPackage(
        "source-native-audio", "No Genre", 120.0, TimeSignature(4, 4), 480,
        (MusicalEvent("note1", "LEAD", "lead_guitar",
                      Fraction(0), Fraction(4), 60, 105),),
        tuple(meta),
    )


def pcm(path):
    with wave.open(str(path), "rb") as w:
        rate=w.getframerate()
        frames=w.getnframes()
        width=w.getsampwidth()
        if width not in (1, 2, 4):
            raise AssertionError("UNSUPPORTED_PCM_WIDTH")
        raw=w.readframes(frames)
        channels=w.getnchannels()
    if width==1:
        decoded=(np.frombuffer(raw,dtype=np.uint8).astype(np.float64)-128.0)/128.0
    elif width==2:
        decoded=np.frombuffer(raw,dtype="<i2").astype(np.float64)/32768.0
    else:
        decoded=np.frombuffer(raw,dtype="<i4").astype(np.float64)/2147483648.0
    return decoded.reshape(-1,channels).mean(axis=1),rate


def window_difference(a,b,rate,start_sec,end_sec):
    start=round(start_sec*rate)
    end=min(len(a),len(b),round(end_sec*rate))
    if end <= start:
        raise AssertionError("SFIZZ_RENDER_TOO_SHORT_FOR_EXPRESSION")
    x=a[start:end]
    y=b[start:end]
    return float(np.sqrt(np.mean((x-y)**2)))


def main():
    renderer=ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
    assert renderer.is_file(),"SFIZZ_RENDERER_NOT_BUILT"
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    bindings=json.loads((ROOT/"target_registry.json").read_text(encoding="utf-8"))[
        "targets"]["INTERNAL"]["instrument_bindings"]
    resource=bindings["lead_guitar"]
    assert resource["resource_id"]==RESOURCE_ID
    assert resource["preferred_mapping"]==PROGRAM
    assert (ROOT/"sound_resources"/RESOURCE_ID/PROGRAM).is_file()
    with tempfile.TemporaryDirectory(prefix="sfizz-expression-",dir=str(ROOT/"output")) as temp:
        directory=Path(temp)
        rendered=[]
        for expressive in (False,True):
            name="timed-vibrato" if expressive else "fixed-zero"
            mid=directory/(name+".mid")
            wav=directory/(name+".wav")
            mid.write_bytes(MidiAdapter().render(package(expressive),"test-fingerprint").payload)
            report=render_midi(resource,mid,wav,44100)
            assert report["audio_rendered"] and report["peak_linear"]>0
            recorded,rate=pcm(wav)
            rendered.append(recorded)
            print("SOURCE_NATIVE_RENDER",name,{
                "sample_rate":rate,"frames":report["frames"],
                "peak_dbfs":round(report["peak_dbfs"],2),
            },flush=True)
        base,gesture=rendered
        pre=window_difference(base,gesture,44100,0.08,0.35)
        mid=window_difference(base,gesture,44100,0.9,1.45)
        assert math.isfinite(mid) and mid > max(1e-6,pre*2),(
            "TIMED_CC1_DID_NOT_CHANGE_ACTUAL_RECORDED_INSTRUMENT",
            {"pre_difference_rms":pre,"mid_difference_rms":mid},
        )
        print("TIMED_NATIVE_CC1_SFIZZ_WAV_RESPONSE_PASS",{
            "pre_difference_rms":round(pre,8),
            "mid_difference_rms":round(mid,8),
            "different_waveform_from_same_recorded_source":True,
        },flush=True)


if __name__=="__main__":
    main()
