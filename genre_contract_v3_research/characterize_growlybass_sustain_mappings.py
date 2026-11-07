"""Compare sustain-capable Growlybass v1.002 mappings in isolation.

Research-only characterization. The Composer target registry remains unchanged.

Mappings tested:
- growlybass_clean.sfz
- growlybass_dirty.sfz

Each mapping receives identical short/long MIDI notes through the exact pinned
sfizz renderer. The test records sample-graph completeness and whether audible
note duration materially follows MIDI note-off timing.

No musical composition judgment, no registry mutation, no live promotion.
"""
from __future__ import annotations

from pathlib import Path
import json
import math
import os
import struct
import sys
import tempfile
import wave

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from sfz_renderer_adapter import render_midi, validate_sfz_samples

SCHEMA="GROWLYBASS_SUSTAIN_MAPPING_CHARACTERIZATION_001"
RESOURCE_ID="KARORYFER_GROWLYBASS_V1_002"
MAPPINGS=("growlybass_clean.sfz","growlybass_dirty.sfz")
PITCH=40
VELOCITY=88
TPQ=480
TEMPO_US_PER_QUARTER=500000
SHORT_TICKS=240
LONG_TICKS=1920
TOTAL_TICKS=3840
SAMPLE_RATE=44100


class MappingCharacterizationError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    out=[value&0x7F]
    value >>= 7
    while value:
        out.append((value&0x7F)|0x80)
        value >>= 7
    return bytes(reversed(out))


def _midi(note_ticks:int)->bytes:
    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(TEMPO_US_PER_QUARTER.to_bytes(3,"big"))
    track.extend(bytes((0x00,0x90,PITCH,VELOCITY)))
    track.extend(_vlq(note_ticks))
    track.extend(bytes((0x80,PITCH,0x00)))
    track.extend(_vlq(TOTAL_TICKS-note_ticks))
    track.extend(b"\xFF\x2F\x00")
    return (
        b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+
        b"MTrk"+struct.pack(">I",len(track))+bytes(track)
    )


def _pcm_mono(path:Path)->tuple[list[float],int]:
    with wave.open(str(path),"rb") as w:
        rate=w.getframerate()
        channels=w.getnchannels()
        width=w.getsampwidth()
        raw=w.readframes(w.getnframes())
    if rate!=SAMPLE_RATE or channels not in (1,2) or width not in (1,2,4):
        raise MappingCharacterizationError(
            f"UNEXPECTED_WAV_FORMAT::{rate}::{channels}::{width}"
        )
    if width==1:
        vals=[(x-128)/128.0 for x in raw]
    elif width==2:
        vals=[x[0]/32768.0 for x in struct.iter_unpack("<h",raw)]
    else:
        vals=[x[0]/2147483648.0 for x in struct.iter_unpack("<i",raw)]
    mono=vals if channels==1 else [
        sum(vals[i:i+channels])/channels for i in range(0,len(vals),channels)
    ]
    if not mono or max(abs(x) for x in mono)<=0:
        raise MappingCharacterizationError("SILENT_RENDER")
    return mono,rate


def _rms(samples:list[float],rate:int,start:float,end:float)->float:
    left=max(0,round(start*rate))
    right=min(len(samples),round(end*rate))
    if right<=left:
        return 0.0
    return math.sqrt(sum(x*x for x in samples[left:right])/(right-left))


def _active_end(samples:list[float],rate:int)->float:
    early=_rms(samples,rate,0.05,0.18)
    threshold=max(1e-5,early*0.025)
    width=max(1,round(rate*0.020))
    last=0
    for left in range(0,len(samples),width):
        right=min(len(samples),left+width)
        if right<=left:
            break
        rms=math.sqrt(sum(x*x for x in samples[left:right])/(right-left))
        if rms>=threshold:
            last=right
    return last/rate


def _characterize(binding:dict,mapping_name:str,renderer:str)->dict:
    bank=FORWARD/"sound_resources"/RESOURCE_ID
    mapping_path=bank/mapping_name
    if not mapping_path.is_file():
        raise MappingCharacterizationError("MAPPING_MISSING::"+mapping_name)

    sample_graph=validate_sfz_samples(mapping_path,allowed_root=bank)
    resource=dict(binding)
    resource["preferred_mapping"]=mapping_name

    with tempfile.TemporaryDirectory(prefix="growlybass-map-char-") as tmp:
        folder=Path(tmp)
        audio={}
        render_reports={}
        for name,ticks in (("short",SHORT_TICKS),("long",LONG_TICKS)):
            midi_path=folder/f"{mapping_name}.{name}.mid"
            wav_path=folder/f"{mapping_name}.{name}.wav"
            midi_path.write_bytes(_midi(ticks))
            render_reports[name]=render_midi(resource,midi_path,wav_path,SAMPLE_RATE)
            audio[name]=_pcm_mono(wav_path)

        short,rate=audio["short"]
        long,_=audio["long"]

        short_early=_rms(short,rate,0.05,0.18)
        long_early=_rms(long,rate,0.05,0.18)
        short_mid=_rms(short,rate,0.80,1.20)
        long_mid=_rms(long,rate,0.80,1.20)
        long_after=_rms(long,rate,2.55,2.95)
        short_end=_active_end(short,rate)
        long_end=_active_end(long,rate)
        short_seconds=len(short)/rate
        long_seconds=len(long)/rate

        if min(short_early,long_early)<=1e-5:
            raise MappingCharacterizationError("EARLY_BODY_TOO_QUIET::"+mapping_name)

        active_delta=long_end-short_end
        render_delta=long_seconds-short_seconds
        mid_ratio=long_mid/max(short_mid,1e-12)

        responsive=(
            long_mid>max(1e-5,short_mid*3.0)
            and active_delta>0.50
            and render_delta>0.50
        )

        releases_after_long_note=(
            long_after < max(1e-5,long_mid*0.60)
        )

        return {
            "mapping":mapping_name,
            "sample_graph":sample_graph,
            "short_early_rms":short_early,
            "long_early_rms":long_early,
            "short_mid_rms":short_mid,
            "long_mid_rms":long_mid,
            "long_after_release_rms":long_after,
            "held_vs_short_mid_ratio":mid_ratio,
            "short_active_end_seconds":short_end,
            "long_active_end_seconds":long_end,
            "active_end_delta_seconds":active_delta,
            "short_render_seconds":short_seconds,
            "long_render_seconds":long_seconds,
            "render_duration_delta_seconds":render_delta,
            "note_length_responsive":responsive,
            "releases_after_long_note":releases_after_long_note,
            "classification":(
                "SUSTAIN_CAPABLE_NOTE_LENGTH_RESPONSIVE"
                if responsive
                else "NOT_SUITABLE_FOR_NOTE_LENGTH_SUSTAIN"
            ),
            "render_reports":{
                key:{
                    "frames":value["frames"],
                    "channels":value["channels"],
                    "sample_rate":value["sample_rate"],
                    "audio_rendered":value["audio_rendered"],
                }
                for key,value in render_reports.items()
            }
        }


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise MappingCharacterizationError("PINNED_RENDERER_NOT_SET")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    binding=registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"]
    if binding.get("resource_id")!=RESOURCE_ID:
        raise MappingCharacterizationError("WRONG_RESOURCE_ID")
    if binding.get("version")!="1.002":
        raise MappingCharacterizationError("WRONG_VERSION")
    if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise MappingCharacterizationError("FALLBACK_CHANGED")

    results=[
        _characterize(binding,mapping,renderer)
        for mapping in MAPPINGS
    ]

    responsive=[x["mapping"] for x in results if x["note_length_responsive"]]

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "resource_id":RESOURCE_ID,
        "version":"1.002",
        "official_release_archive_sha256":"b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc",
        "renderer_pin":os.environ.get("AI_COMP_SFIZZ_PIN"),
        "registry_current_mapping":binding.get("preferred_mapping"),
        "registry_production_preferred_mapping":binding.get("production_preferred_mapping"),
        "registry_modified":False,
        "results":results,
        "responsive_mappings":responsive,
        "production_fidelity_certified":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "reasoning_engine_used":False,
        "next_gate":(
            "CHOOSE_NARROW_RESEARCH_MAPPING_FOR_BASS_SUSTAIN_A_B"
            if responsive
            else "STOP_BASS_SUSTAIN_AUDIO_PATH__NO_TESTED_SUSTAIN_CAPABLE_MAPPING"
        )
    }

    out=ROOT/"genre_contract_v3_research"/"GROWLYBASS_SUSTAIN_MAPPING_CHARACTERIZATION.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
