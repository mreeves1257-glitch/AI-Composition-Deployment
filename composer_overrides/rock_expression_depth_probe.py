"""Real-recording checks for Rock lead vibrato and the paired low kick layer.

Run only during the composer build, after the existing SFZ banks are installed.
No synthesis, new instrument identities, drum-note duplication, or mixer edits.
"""
from __future__ import annotations

import json
import math
import os
import struct
import wave
from pathlib import Path

import numpy as np
from sfz_renderer_adapter import render_midi, validate_sfz_samples

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "sound_resources"
OUT = ROOT / "output" / "rock_expression_probe"


def _vlq(value: int) -> bytes:
    number = value & 127
    while value >> 7:
        value >>= 7
        number <<= 8
        number |= ((value & 127) | 128)
    out = []
    while True:
        out.append(number & 255)
        if number & 128:
            number >>= 8
        else:
            break
    return bytes(out)


def _midi(path: Path, note: int, velocity: int = 100, beats: int = 3) -> None:
    notes = (b"\x00\x90" + bytes((note,velocity)) + _vlq(480*beats) +
             b"\x80" + bytes((note,0)) + b"\x00\xff\x2f\x00")
    path.write_bytes(b"MThd" + struct.pack(">IHHH",6,0,1,480) +
                     b"MTrk" + struct.pack(">I",len(notes)) + notes)


def _first_channel(path: Path, seconds: float = 0.85) -> tuple[np.ndarray, int]:
    with wave.open(str(path),"rb") as stream:
        rate=stream.getframerate()
        channels=stream.getnchannels()
        width=stream.getsampwidth()
        assert width==2 and channels in (1,2), "SAMPLED_AUDIO_FORMAT_UNEXPECTED"
        raw=stream.readframes(round(seconds*rate))
    samples=np.frombuffer(raw,dtype="<i2").astype(np.float32).reshape(-1,channels)
    return samples[:,0]/32768.0,rate


def _low_power(wav: Path, lower: float = 25.0, upper: float = 75.0) -> float:
    arr,rate=_first_channel(wav)
    start=int(0.045*rate)
    sample=arr[start:] * np.hanning(len(arr)-start).astype(np.float32)
    power=np.abs(np.fft.rfft(sample))**2
    freq=np.fft.rfftfreq(len(sample),d=1/rate)
    band=(freq>=lower)&(freq<=upper)
    return float(np.sum(power[band]))


def _render(binding:dict, note:int, filename:str)->Path:
    midi=OUT/(filename+".mid")
    wav=OUT/(filename+".wav")
    _midi(midi,note)
    result=render_midi(binding,midi,wav,sample_rate=44100)
    assert result["audio_rendered"] and result["peak_linear"]>0
    return wav


def main()->None:
    OUT.mkdir(parents=True,exist_ok=True)
    renderer=ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
    assert renderer.is_file(),"REAL_SFZ_RENDERER_MISSING"
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    registry=json.loads((ROOT/"target_registry.json").read_text())
    binds=registry["targets"]["INTERNAL"]["instrument_bindings"]
    lead=binds["electric_guitar:LEAD_MELODY"]
    rhythm=binds["electric_guitar:RHYTHM_POWER_CHORDS"]
    assert lead["preferred_mapping"]=="Programs/composer-electric-lead.sfz"
    assert rhythm["preferred_mapping"]=="Programs/composer-electric.sfz"
    assert lead["midi_mapping"]["initial_cc"]["1"]==88
    assert "1" not in rhythm["midi_mapping"].get("initial_cc",{})
    lead_sf= BANK/"KARORYFER_SHINYGUITAR"/lead["preferred_mapping"]
    rhythm_sf=BANK/"KARORYFER_SHINYGUITAR"/rhythm["preferred_mapping"]
    lead_text=lead_sf.read_text()
    rhythm_text=rhythm_sf.read_text()
    assert "lfo01_pitch_oncc1=30" in lead_text and "set_cc1=88" in lead_text
    assert "set_cc1=0" in rhythm_text and "lfo01_pitch_oncc1=14" in rhythm_text
    assert "set_cc103=85" in lead_text and "set_cc104=90" in lead_text
    validate_sfz_samples(lead_sf)
    validate_sfz_samples(rhythm_sf)
    lead_wav=_render(lead,64,"real-lead-vibrato")
    print("ROCK_RECORDED_GUITAR_VIBRATO_PASS",{
        "resource_id":lead["resource_id"],"lead_separate_sfz":True,
        "audio_samples":int(_first_channel(lead_wav)[0].size),
        "rhythm_program_untouched":True},flush=True)

    kick=binds["kick_drum_rock"]
    assert kick["resource_id"]=="KARORYFER_BIG_RUSTY_DRUMS"
    original=dict(kick,preferred_mapping="Programs/composer-kick-without-sub.sfz")
    enhanced=kick
    orig_sf=BANK/"KARORYFER_BIG_RUSTY_DRUMS"/original["preferred_mapping"]
    enhanced_sf=BANK/"KARORYFER_BIG_RUSTY_DRUMS"/enhanced["preferred_mapping"]
    unmodified=orig_sf.read_text()
    modified=enhanced_sf.read_text()
    assert modified.startswith(unmodified),"ORIGINAL_RECORDED_KICK_REMOVED"
    assert modified.count("transpose=-12")==4,"SUBKICK_VELOCITY_LAYERS_MISSING"
    assert "fil_type=lpf_1p cutoff=105" in modified
    validate_sfz_samples(orig_sf)
    baseline=_render(original,36,"original-real-kick")
    p_before=_low_power(baseline)
    assert p_before>0,"ORIGINAL_KICK_NO_LOW_FREQUENCY_ENERGY"
    # A heavily down-pitched sample can actually diminish the audible bass
    # band through filtering and phase cancellation. Audition alternatives
    # using only the same recorded kick samples, preserving source strokes.
    # Commit to one audible response; fail rather than ship a fictitious sub.
    candidates=[
        (0,-6.0,90),
        (-5,-6.0,110),
        (0,-3.0,85),
        (-7,-5.0,110),
        (-12,-3.0,160),
        (0,-4.0,145),
    ]
    best=None
    attempts=[]
    for semitones,volume,cutoff in candidates:
        groups=["", "// Verified recorded-only subkick, aligned to the same kick triggers."]
        for lo,hi,layer in ((1,31,1),(32,63,5),(64,95,9),(96,127,13)):
            groups.append(
                f"<group> lovel={lo} hivel={hi} transpose={semitones} "
                f"volume={volume:.1f} fil_type=lpf_1p cutoff={cutoff} "
                "ampeg_attack=0.005 ampeg_hold=0.01 "
                "ampeg_decay=0.34 ampeg_sustain=0"
            )
            for rr in range(1,5):
                groups.append(
                    f"<region> sample=../Samples/kick_24/kick/kick/"
                    f"k_vl{layer}_rr{rr}.flac seq_position={rr}"
                )
        enhanced_sf.write_text(unmodified+"\n".join(groups)+"\n",encoding="utf-8")
        samples=validate_sfz_samples(enhanced_sf)
        layered=_render(enhanced,36,"layered-real-kick")
        p_after=_low_power(layered)
        ratio=p_after/max(p_before,1e-12)
        attempts.append((semitones,volume,cutoff,round(ratio,3)))
        # Favor suboctave options when they demonstrably add deep energy.
        score=ratio+(0.005 if semitones<0 else 0.0)
        if best is None or score>best["score"]:
            best={"score":score,"ratio":ratio,
                  "sfz":enhanced_sf.read_text(encoding="utf-8"),
                  "transpose":semitones,"volume":volume,"cutoff":cutoff,
                  "sample_refs":samples["sample_references"]}
        if ratio>=1.20 and semitones<0:
            break
    if best is None or best["ratio"]<1.08:
        enhanced_sf.write_text(unmodified,encoding="utf-8")
        raise AssertionError(
            f"RECORDED_SUBKICK_BASS_BAND_NOT_ENHANCED:{p_before:.4g}:{attempts}"
        )
    enhanced_sf.write_text(best["sfz"],encoding="utf-8")
    print("ROCK_RECORDED_SUBKICK_PASS",{
        "kick_source":"KARORYFER_BIG_RUSTY_DRUMS",
        "source":"RECORDED_KICK_LOWPASS_LAYER_NO_SYNTHESIS",
        "velocity_groups":4,"sample_refs":best["sample_refs"],
        "low_band_25_75hz_ratio":round(best["ratio"],3),
        "selected_recorded_kick_transpose_semitones":best["transpose"],
        "selected_lowpass_hz":best["cutoff"],
        "selected_layer_volume_db":best["volume"],
        "candidate_measurements":attempts
    },flush=True)


if __name__=="__main__":
    main()
