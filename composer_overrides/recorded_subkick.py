"""Bounded, recorded-source sub-kick for Rock; never an oscillator.

Derive a separate low-frequency STEM from the *actual rendered Karoryfer kick*.
The 3D mixer, genre scores, source library, instrument identity and samples
remain unchanged. A provenance-bound accompaniment layer, not a fake bass.
"""
from __future__ import annotations

from pathlib import Path
import math
import wave

import numpy as np

VERSION="RECORDED_KICK_SUBSTEM_R1"
TRACK="SUBKICK"
FIR_TAPS=1025
CUTOFF_HZ=95.0
BLOCK_FRAMES=65536


def _make_kernel(rate:int)->np.ndarray:
    if not 8000 <= rate <= 192000:
        raise ValueError("SUBKICK_SAMPLE_RATE_INVALID")
    indices=np.arange(FIR_TAPS,dtype=np.float64)-(FIR_TAPS-1)/2
    freq=CUTOFF_HZ/rate
    kernel=(2*freq*np.sinc(2*freq*indices))*np.hamming(FIR_TAPS)
    kernel/=np.sum(kernel)
    return kernel.astype(np.float32)


def _decode(raw:bytes,channels:int,width:int)->np.ndarray:
    if width==2:
        a=np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768
    elif width==4:
        a=np.frombuffer(raw,dtype="<i4").astype(np.float32)/2147483648
    else:
        raise ValueError("SUBKICK_UNSUPPORTED_SAMPLE_WIDTH")
    if a.size%channels:
        raise ValueError("SUBKICK_MALFORMED_STEM")
    return a.reshape(-1,channels).mean(axis=1,dtype=np.float32)


def make_recorded_substem(source:Path,destination:Path)->dict:
    source=Path(source)
    destination=Path(destination)
    if not source.is_file():
        raise ValueError("ORIGINAL_RECORDED_KICK_STEM_MISSING")
    if source.resolve()==destination.resolve():
        raise ValueError("SUBKICK_CANNOT_OVERWRITE_RECORDED_STEM")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(source),"rb") as r:
        channels,width,rate,count=(r.getnchannels(),r.getsampwidth(),r.getframerate(),r.getnframes())
        if channels not in (1,2) or width not in (2,4) or count<=0:
            raise ValueError("SUBKICK_SOURCE_AUDIO_INVALID")
        kernel=_make_kernel(rate)
        nfft=2**int(math.ceil(math.log2(BLOCK_FRAMES+FIR_TAPS-1)))
        freq_response=np.fft.rfft(kernel,n=nfft)
        overlap=np.zeros(FIR_TAPS-1,dtype=np.float32)
        compensate=(FIR_TAPS-1)//2
        produced=0
        with wave.open(str(destination),"wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            while True:
                raw=r.readframes(BLOCK_FRAMES)
                if not raw:
                    break
                mono=_decode(raw,channels,width)
                n=len(mono)
                signal=np.zeros(BLOCK_FRAMES,dtype=np.float32)
                signal[:n]=mono
                transformed=np.fft.irfft(
                    np.fft.rfft(signal,n=nfft)*freq_response,n=nfft
                ).astype(np.float32)
                chunk=transformed[:BLOCK_FRAMES]
                chunk[:len(overlap)]+=overlap
                overlap=transformed[BLOCK_FRAMES:BLOCK_FRAMES+FIR_TAPS-1].copy()
                result=chunk[:n]
                # Symmetric FIR delays audio by 512 samples. Undo that delay
                # so each sub-kick remains aligned to its recorded kick hit.
                if compensate:
                    skip=min(compensate,n)
                    result=result[skip:]
                    compensate-=skip
                if len(result):
                    pcm=(np.clip(result,-.9999,.9999)*32767).astype("<i2")
                    w.writeframes(pcm.tobytes())
                    produced+=len(result)
            if produced<count:
                w.writeframes(np.zeros(count-produced,dtype="<i2").tobytes())
                produced=count
    with wave.open(str(destination),"rb") as check:
        if (check.getnframes()!=count or check.getframerate()!=rate or
            check.getnchannels()!=1):
            raise ValueError("SUBKICK_RENDERED_WAVEFORM_INVALID")
    return {
        "source":"RECORDED_KICK_AUDIO","derivation":"FIR_LOWPASS_FILTERED",
        "source_path":str(source),"wav_path":str(destination),
        "frequency_cutoff_hz":CUTOFF_HZ,"phase_alignment":"GROUP_DELAY_COMPENSATED",
        "frames":count,"sample_rate":rate
    }


def prepare_recorded_subkick(engine_result:dict, stems:list, job_dir:Path)->tuple[dict,list]:
    if str(engine_result.get("genre","")).upper()!="ROCK":
        return engine_result,stems
    if any(str(s.get("track_id","")).upper()==TRACK for s in stems):
        raise ValueError("SUBKICK_DUPLICATE_TRACK")
    kicked=[s for s in stems if str(s.get("track_id","")).upper()=="KICK"]
    if len(kicked)!=1:
        raise ValueError("SUBKICK_NEEDS_EXACTLY_ONE_REAL_KICK_STEM")
    instrument=engine_result["modules"]["instrument"]
    target=engine_result["modules"]["target"]
    profiles=instrument["profiles"]
    bindings=target["resolved_resources"]
    kp=next((p for p in profiles if str(p.get("track_id","")).upper()=="KICK"),None)
    kr=next((r for r in bindings if str(r.get("track_id","")).upper()=="KICK"),None)
    if not kp or not kr or kp.get("instrument_id")!="kick_drum_rock":
        raise ValueError("SUBKICK_REAL_KICK_PROVENANCE_MISSING")
    binding=kr.get("resource",{})
    if (binding.get("resource_id")!="KARORYFER_BIG_RUSTY_DRUMS" or
        binding.get("resource_type")!="SFZ_SAMPLE_LIBRARY" or
        binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION"):
        raise ValueError("SUBKICK_SOURCE_IS_NOT_APPROVED_RECORDED_DRUM")
    if not isinstance(binding.get("target_gain_db"),(int,float)):
        raise ValueError("SUBKICK_INVALID_GAIN")
    recorded=Path(kicked[0]["wav_path"]).resolve()
    rendered=Path(job_dir).resolve()/"recorded-subkick.wav"
    proof=make_recorded_substem(recorded,rendered)
    profile={**kp,"track_id":TRACK,"role":"SUB_KICK_RECORDED_KICK_ATTACHED"}
    resource={
        **binding,"target_gain_db":float(binding["target_gain_db"])-6.0,
        "source_kick_track":"KICK","derived_audio":VERSION,
        "derivation_proof":proof,
    }
    rr={**kr,"track_id":TRACK,"resource":resource}
    out={
        **engine_result,
        "modules":{
            **engine_result["modules"],
            "instrument":{**instrument,"profiles":[*profiles,profile]},
            "target":{**target,"resolved_resources":[*bindings,rr]},
        },
        "recorded_subkick":{
            "version":VERSION,"source_track":"KICK","track_id":TRACK,
            "same_kick_onsets":True,"source_is_recorded":True,
            "no_oscillator_or_synthetic_fallback":True,
            "filter_cutoff_hz":CUTOFF_HZ,
        }
    }
    return out,[*stems,{
        "track_id":TRACK,"instrument_id":"kick_drum_rock",
        "wav_path":str(rendered),
        "derivation":"LOWPASS_PROCESSED_REAL_KICK_STEM"
    }]
