"""Real recorded snare velocity-layer proof for the new source-aware interpreter.

Source sample program is the existing Big Rusty recorded SFZ. Only note-on
MIDI velocity is changed. No new sound assets, no synthetic substitution,
no sample edits, no genre wiring or production Composer update.
"""
from __future__ import annotations

import json
import os
import struct
import tempfile
import wave
from pathlib import Path
from fractions import Fraction

from AI_Comp_Executable_Output_Core_001 import MusicalEvent
from recorded_percussion_strike_interpreter import interpret_recorded_percussion
from sfz_renderer_adapter import render_midi

ROOT = Path(__file__).resolve().parent
RESOURCE = "KARORYFER_BIG_RUSTY_DRUMS"
PROGRAM = "Programs/composer-snare-lite.sfz"


def make_midi(note: int, velocity: int) -> bytes:
    assert 1 <= velocity <= 127
    track = (
        b"\x00\x90" + bytes((note,velocity)) +
        bytes.fromhex("83 60 80") + bytes((note,0)) +
        bytes.fromhex("00 ff 2f 00")
    )
    return (
        b"MThd" + struct.pack(">IHHH",6,0,1,480) +
        b"MTrk" + struct.pack(">I",len(track)) + track
    )


def main():
    target=json.loads((ROOT/"target_registry.json").read_text())
    resource=target["targets"]["INTERNAL"]["instrument_bindings"]["snare_drum"]
    assert resource["resource_type"]=="SFZ_SAMPLE_LIBRARY"
    assert resource["resource_id"]==RESOURCE
    assert resource["preferred_mapping"]==PROGRAM
    assert (ROOT/"sound_resources"/RESOURCE/PROGRAM).is_file()
    sfizz=ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
    assert sfizz.is_file()
    os.environ["AI_COMP_SFZ_RENDERER"]=str(sfizz)

    selected=[{"track_id":"SNARE","instrument_id":"snare_drum","resource":resource}]
    reports={}
    audio={}
    with tempfile.TemporaryDirectory(prefix="recorded-stroke-",dir=str(ROOT/"output")) as temporary:
        for label,articulation in (("ghost","ghost_note"),("strong","strong_hit")):
            original=MusicalEvent(
                label,"SNARE","snare_drum",
                Fraction(0),Fraction(1,8),38,90,articulation=articulation,
            )
            translated=interpret_recorded_percussion(
                [original],selected,enabled=True,
            )[0]
            assert original.velocity==90, "COMPOSED_NOTE_WAS_MUTATED"
            if label=="ghost":
                assert 1 <= translated.velocity <= 31
            else:
                assert 96 <= translated.velocity <= 127
            mid=Path(temporary)/(label+".mid")
            wav=Path(temporary)/(label+".wav")
            mid.write_bytes(make_midi(38,translated.velocity))
            rendered=render_midi(resource,mid,wav,sample_rate=44100)
            assert rendered["audio_rendered"] and rendered["peak_linear"]>0
            with wave.open(str(wav),"rb") as w:
                assert w.getframerate()==44100
                sample=w.readframes(w.getnframes())
                assert sample
                audio[label]=sample
            reports[label]={
                "sample_bank":rendered["resource_id"],
                "velocity":translated.velocity,
                "peak_dbfs":round(rendered["peak_dbfs"],3),
                "rms_dbfs":round(rendered["rms_dbfs"],3),
            }
            print("RECORDED_STRIKE_SFZ_RENDER",label,reports[label],flush=True)
        assert audio["ghost"] != audio["strong"],(
            "RECORDED_SOFT_AND_STRONG_STRIKE_AUDIO_NOT_DISTINGUISHED"
        )
        print("RECORDED_PERCUSSION_VELOCITY_LAYER_AUDIO_PASS",{
            "library":RESOURCE,"program":PROGRAM,
            "recordings_replaced":False,
            "genre_routes_activated":False,
            "control_panel_changed":False,
            "audible_layer_response_verified":True,
        },flush=True)


if __name__=="__main__":
    main()
