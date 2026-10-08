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


ROOT = Path("composer/runtime").resolve()
RESOURCE_ID = "KARORYFER_SHINYGUITAR"
PROGRAM = "Programs/composer-electric-lead.sfz"
CAPABILITY = "SHINYGUITAR_RECORDED_LEAD_CC1_V1"


def package(mode):
    if mode not in ("baseline", "manual", "note_articulation"):
        raise ValueError("UNRECOGNIZED_AUDIO_PROOF_MODE")
    routing = {"LEAD": {"initial_cc": {"1": 0}}}
    meta = [("midi_routing", json.dumps(routing))]
    selected = {
        "capability_id": CAPABILITY,
        "resource_id": RESOURCE_ID,
        "preferred_mapping": PROGRAM,
    }
    if mode in ("manual", "baseline"):
        # Equalize the complete pre-vibrato MIDI history for the true negative
        # control. Some SFZ patches react to redundant CC0 at note attack.
        selected["gestures"] = [
            {"at_beat": "0", "control": "vibrato_depth", "value": 0},
        ]
        if mode == "manual":
            selected["gestures"].extend([
                {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                {"at_beat": "7/2", "control": "vibrato_depth", "value": 0},
            ])
    else:
        selected["gesture_source"] = "note_articulation"
    meta.append(("expressive_gesture_plan", json.dumps({"LEAD": selected})))
    note_tag = "sustained_vibrato" if mode == "note_articulation" else None
    return CompositionExecutionPackage(
        "source-native-audio", "No Genre", 120.0, TimeSignature(4, 4), 480,
        (MusicalEvent("note1", "LEAD", "lead_guitar",
                      Fraction(0), Fraction(4), 60, 105,
                      articulation=note_tag),),
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
        raw_midi={}
        for name, mode in (
            ("fixed-zero-A","baseline"),
            ("fixed-zero-B","baseline"),
            ("explicit-manual-midi","manual"),
            ("note-articulation-authored-midi","note_articulation"),
        ):
            mid=directory/(name+".mid")
            wav=directory/(name+".wav")
            raw=MidiAdapter().render(package(mode),"test-fingerprint").payload
            raw_midi[name]=raw
            mid.write_bytes(raw)
            report=render_midi(resource,mid,wav,44100)
            assert report["audio_rendered"] and report["peak_linear"]>0
            recorded,rate=pcm(wav)
            rendered.append(recorded)
            print("SOURCE_NATIVE_RENDER",name,{
                "sample_rate":rate,"frames":report["frames"],
                "peak_dbfs":round(report["peak_dbfs"],2),
            },flush=True)
        assert raw_midi["explicit-manual-midi"] == raw_midi["note-articulation-authored-midi"], (
            "ARTICULATION_NOT_EQUIVALENT_TO_EXPLICIT_NATIVE_MIDI"
        )
        first,repeat,manual,gesture=rendered
        # Compare the SAME fixed-control render twice first. If the real
        # sample engine has nondeterministic selection/phase we must not
        # misattribute ordinary differences to the timed MIDI message.
        pre_repeat=window_difference(first,repeat,44100,0.03,0.14)
        pre_expression=window_difference(first,gesture,44100,0.03,0.14)
        post_repeat=window_difference(first,repeat,44100,0.7,1.2)
        post_expression=window_difference(first,gesture,44100,0.7,1.2)
        manual_to_authored=window_difference(manual,gesture,44100,0.7,1.2)
        assert manual_to_authored < 1e-8, ("MANUAL_AND_NOTE_TAG_AUDIO_DIVERGED",manual_to_authored)
        print("EXPRESSIVE_RECORDED_SOURCE_CONTROLLED_AB",{
            "pre_repeat_rms":round(pre_repeat,9),
            "pre_expression_rms":round(pre_expression,9),
            "post_repeat_rms":round(post_repeat,9),
            "post_expression_rms":round(post_expression,9),
            "manual_to_note_tag_rms":round(manual_to_authored,9),
        },flush=True)
        assert math.isfinite(post_expression) and post_expression > max(
            1e-6, post_repeat*1.25, pre_expression*0.5
        ), ("EXPRESSION_CAUSAL_AUDIO_EFFECT_NOT_YET_DEMONSTRATED",{
            "pre_repeat":pre_repeat,"pre_expression":pre_expression,
            "post_repeat":post_repeat,"post_expression":post_expression,
        })
        print("NOTE_ARTICULATION_TO_REAL_SFIZZ_WAV_PASS",{
            "baseline_variability_measured":True,
            "post_expression_difference_rms":round(post_expression,8),
            "authored_midi_equals_explicit_midi":True,
            "same_original_recorded_sample_library":True,
        },flush=True)


if __name__=="__main__":
    main()
