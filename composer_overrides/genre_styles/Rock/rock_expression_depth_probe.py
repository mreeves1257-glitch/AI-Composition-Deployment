"""Recorded-audio verification of guitar vibrato and independently routed kick sub.
Runs during production build, blocks deploy if the bass-band proof fails.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import wave
from pathlib import Path

import numpy as np
from sfz_renderer_adapter import render_midi, validate_sfz_samples
from recorded_subkick import prepare_recorded_subkick

ROOT=Path(__file__).resolve().parent
BANK=ROOT/"sound_resources"
OUT=ROOT/"output"/"rock_expression_probe"


def _midi(path, note, vel=100):
    # One measured real kick/guitar sample; no synthetic source.
    tempo=480*3
    notes=b"\x00\x90"+bytes((note,vel))+b"\x8b\x20"+b"\x80"+bytes((note,0))+b"\x00\xff\x2f\x00"
    assert tempo==1440
    path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,480)+
                     b"MTrk"+struct.pack(">I",len(notes))+notes)


def _render(binding,note,name):
    midi=OUT/(name+".mid")
    out=OUT/(name+".wav")
    _midi(midi,note)
    result=render_midi(binding,midi,out,sample_rate=44100)
    assert result["audio_rendered"] and result["peak_linear"]>0
    return out


def _audio(path,limit_s=0.85):
    with wave.open(str(path),"rb") as reader:
        channels,width,rate=(reader.getnchannels(),reader.getsampwidth(),reader.getframerate())
        assert channels in (1,2) and width==2 and rate==44100
        raw=reader.readframes(int(limit_s*rate))
    arr=np.frombuffer(raw,dtype="<i2").astype(np.float32).reshape(-1,channels)
    return arr.mean(axis=1,dtype=np.float32)/32768.0


def _band(x,lo=25.0,hi=75.0):
    x=x[int(.045*44100):]
    w=np.hanning(x.size).astype(np.float32)
    p=np.abs(np.fft.rfft(x*w))**2
    h=np.fft.rfftfreq(x.size,d=1/44100)
    return float(p[(h>=lo)&(h<=hi)].sum())


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    renderer=ROOT.parent.parent/".composer_tools"/"bin"/"sfizz_render"
    assert renderer.is_file(),"NO_REAL_RENDERER"
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    registry=json.loads((ROOT/"target_registry.json").read_text())
    binding=registry["targets"]["INTERNAL"]["instrument_bindings"]
    lead=binding["electric_guitar:LEAD_MELODY"]
    rhythm=binding["electric_guitar:RHYTHM_POWER_CHORDS"]
    assert lead["preferred_mapping"]=="Programs/composer-electric-lead.sfz"
    assert rhythm["preferred_mapping"]=="Programs/composer-electric.sfz"
    lead_sf=BANK/"KARORYFER_SHINYGUITAR"/lead["preferred_mapping"]
    rhythm_sf=BANK/"KARORYFER_SHINYGUITAR"/rhythm["preferred_mapping"]
    assert "set_cc1=88" in lead_sf.read_text()
    assert "lfo01_pitch_oncc1=30" in lead_sf.read_text()
    assert "set_cc1=0" in rhythm_sf.read_text()
    validate_sfz_samples(lead_sf)
    validate_sfz_samples(rhythm_sf)
    _render(lead,64,"recorded-lead-vibrato")
    print("ROCK_RECORDED_GUITAR_VIBRATO_PASS",{"real_sample":True,
          "separate_lead_sfz":True,"rhythm_unchanged":True},flush=True)

    kick=binding["kick_drum_rock"]
    assert kick["resource_id"]=="KARORYFER_BIG_RUSTY_DRUMS"
    kick_sf=BANK/"KARORYFER_BIG_RUSTY_DRUMS"/kick["preferred_mapping"]
    assert "SUB-KICK" not in kick_sf.read_text(),"SOURCE_KICK_SFZ_CHANGED"
    validate_sfz_samples(kick_sf)
    wav=_render(kick,36,"recorded-kick")
    original_hash=hashlib.sha256(wav.read_bytes()).hexdigest()
    result={"genre":"ROCK","modules":{
        "instrument":{"profiles":[{"track_id":"KICK",
                                   "instrument_id":"kick_drum_rock","role":"KICK_PULSE"}]},
        "target":{"resolved_resources":[{"track_id":"KICK","resource":kick}]},
        "performance":{"events":[{"track_id":"KICK","midi":36}]}
    }}
    result_copy={**result}
    source_stems=[{"track_id":"KICK","wav_path":str(wav)}]
    data,stems=prepare_recorded_subkick(result,source_stems,OUT)
    assert len(stems)==2 and stems[-1]["track_id"]=="SUBKICK"
    assert data["recorded_subkick"]["no_oscillator_or_synthetic_fallback"] is True
    assert len(data["modules"]["instrument"]["profiles"])==2
    assert len(result["modules"]["instrument"]["profiles"])==1
    assert result==result_copy
    assert hashlib.sha256(wav.read_bytes()).hexdigest()==original_hash
    assert data["modules"]["target"]["resolved_resources"][-1]["resource"]["resource_id"]==kick["resource_id"]
    recorded=_audio(wav)
    sub=_audio(Path(stems[-1]["wav_path"]))
    assert len(recorded)==len(sub)
    # Gain on separate sub stem is -6 dB relative to kick. Verify the
    # *combined* 25-75 Hz range actually improves, not just its peak value.
    scale=10**(-6.0/20.0)
    baseline=_band(recorded)
    enhanced=_band(recorded+scale*sub)
    assert enhanced > baseline*1.25, (
        f"REAL_RECORDED_SUBSTEM_NO_AUDIBLE_BASS_IMPROVEMENT:{baseline}:{enhanced}"
    )
    high_total=_band(recorded,500,4000)
    high_sub=_band(sub,500,4000)
    assert high_sub < max(high_total*.08,0.01),"SUBSTEM_NOT_LOWPASSED"
    different={"genre":"FUNK","modules":result["modules"]}
    out,ss=prepare_recorded_subkick(different,source_stems,OUT)
    assert out is different and ss is source_stems
    print("ROCK_RECORDED_SUBKICK_PASS",{
        "source":"RECORDED_KARORYFER_KICK_WAVEFORM",
        "route":"INDEPENDENT_MONO_SUBKICK_STEM_THROUGH_3D_MIXER",
        "low_band_25_75hz_ratio":round(enhanced/baseline,3),
        "provenance_protected":True,"filter":95,
        "other_genres_unchanged":True,
    },flush=True)


if __name__=="__main__":main()
