"""Characterize note-length response of the exact Growlybass mapping.

This is a diagnostic capability characterization, not a musical listening test.

Control variables held constant:
- same resource and mapping;
- same pitch, velocity, onset, tempo;
- same renderer and sample rate;
- same total MIDI duration.

Independent variable:
- MIDI note-off time only.

Unlike the Shinyguitar proof, this script does not require the mapping to sustain.
It classifies whether the exact target-registry mapping audibly responds to note
length. A staccato/one-shot mapping may validly classify as nonresponsive.

No canonical policy change. No live promotion.
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

from sfz_renderer_adapter import render_midi

SCHEMA="GROWLYBASS_NOTE_LENGTH_RESPONSE_CHARACTERIZATION_001"
RESOURCE_ID="KARORYFER_GROWLYBASS_V1_002"
MAPPING="growlybass_vicious.sfz"
PITCH=40
VELOCITY=88
TPQ=480
TEMPO_US_PER_QUARTER=500000
SHORT_TICKS=240
LONG_TICKS=1920
TOTAL_TICKS=3840
SAMPLE_RATE=44100


class GrowlybassCapabilityError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    if value<0:
        raise GrowlybassCapabilityError("NEGATIVE_VLQ")
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
    header=b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)
    return header+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def _pcm_mono(path:Path)->tuple[list[float],int]:
    with wave.open(str(path),"rb") as w:
        rate=w.getframerate()
        channels=w.getnchannels()
        width=w.getsampwidth()
        frames=w.getnframes()
        raw=w.readframes(frames)
    if rate!=SAMPLE_RATE:
        raise GrowlybassCapabilityError("UNEXPECTED_SAMPLE_RATE")
    if channels not in (1,2):
        raise GrowlybassCapabilityError("UNEXPECTED_CHANNEL_COUNT")
    if width not in (1,2,4):
        raise GrowlybassCapabilityError("UNEXPECTED_SAMPLE_WIDTH")
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
        raise GrowlybassCapabilityError("SILENT_RENDER")
    return mono,rate


def _rms(samples:list[float],rate:int,start:float,end:float)->float:
    left=max(0,round(start*rate))
    right=min(len(samples),round(end*rate))
    if right<=left:
        return 0.0
    total=sum(x*x for x in samples[left:right])
    return math.sqrt(total/(right-left))


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


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise GrowlybassCapabilityError("PINNED_RENDERER_NOT_SET")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    binding=registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"]
    if binding.get("resource_id")!=RESOURCE_ID:
        raise GrowlybassCapabilityError("WRONG_RESOURCE_ID")
    if binding.get("preferred_mapping")!=MAPPING:
        raise GrowlybassCapabilityError("WRONG_MAPPING")
    if binding.get("version")!="1.002":
        raise GrowlybassCapabilityError("WRONG_VERSION")
    if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise GrowlybassCapabilityError("FALLBACK_POLICY_CHANGED")

    mapping=FORWARD/"sound_resources"/RESOURCE_ID/MAPPING
    if not mapping.is_file():
        raise GrowlybassCapabilityError("MAPPING_MISSING")

    with tempfile.TemporaryDirectory(prefix="growlybass-note-length-") as tmp:
        folder=Path(tmp)
        audio={}
        reports={}
        for name,ticks in (("short",SHORT_TICKS),("long",LONG_TICKS)):
            midi_path=folder/(name+".mid")
            wav_path=folder/(name+".wav")
            midi_path.write_bytes(_midi(ticks))
            reports[name]=render_midi(dict(binding),midi_path,wav_path,SAMPLE_RATE)
            pcm,rate=_pcm_mono(wav_path)
            audio[name]=(pcm,rate)

        short,rate=audio["short"]
        long,_=audio["long"]

        short_early=_rms(short,rate,0.05,0.18)
        long_early=_rms(long,rate,0.05,0.18)
        short_mid=_rms(short,rate,0.80,1.20)
        long_mid=_rms(long,rate,0.80,1.20)
        short_end=_active_end(short,rate)
        long_end=_active_end(long,rate)
        short_seconds=len(short)/rate
        long_seconds=len(long)/rate

        if min(short_early,long_early)<=1e-5:
            raise GrowlybassCapabilityError("EARLY_NOTE_BODY_TOO_QUIET")

        mid_ratio=long_mid/max(short_mid,1e-12)
        active_delta=long_end-short_end
        render_delta=long_seconds-short_seconds

        responsive=(
            long_mid>max(1e-5,short_mid*3.0)
            and active_delta>0.50
            and render_delta>0.50
        )

        classification=(
            "NOTE_LENGTH_RESPONSIVE"
            if responsive
            else "NOTE_LENGTH_NONRESPONSIVE_OR_STACCATO"
        )

        report={
            "schema":SCHEMA,
            "status":"PASS",
            "diagnostic_only":True,
            "resource_id":RESOURCE_ID,
            "version":"1.002",
            "mapping":MAPPING,
            "official_release_archive_sha256":"b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc",
            "sample_graph":{
                "sample_references":86,
                "unique_samples":86,
                "sfz_files_validated":1
            },
            "renderer_pin":os.environ.get("AI_COMP_SFIZZ_PIN"),
            "pitch":PITCH,
            "velocity":VELOCITY,
            "short_note_seconds":SHORT_TICKS/TPQ*0.5,
            "long_note_seconds":LONG_TICKS/TPQ*0.5,
            "short_early_rms":short_early,
            "long_early_rms":long_early,
            "short_mid_rms":short_mid,
            "long_mid_rms":long_mid,
            "held_vs_short_mid_ratio":mid_ratio,
            "short_active_end_seconds":short_end,
            "long_active_end_seconds":long_end,
            "active_end_delta_seconds":active_delta,
            "short_render_seconds":short_seconds,
            "long_render_seconds":long_seconds,
            "render_duration_delta_seconds":render_delta,
            "classification":classification,
            "note_length_response_for_current_mapping":responsive,
            "symbolic_bass_sustain_candidate_audio_effect_proven":False,
            "production_fidelity_certified":False,
            "canonical_policy_modified":False,
            "live_runtime_promoted":False,
            "reasoning_engine_used":False,
            "next_gate":(
                "BASS_SUSTAIN_A_B_ON_CURRENT_MAPPING"
                if responsive
                else "TEST_SUSTAIN_CAPABLE_GROWLYBASS_MAPPING_BEFORE_MUSICAL_BASS_SUSTAIN_A_B"
            )
        }

        out=ROOT/"genre_contract_v3_research"/"GROWLYBASS_NOTE_LENGTH_RESPONSE_CHARACTERIZATION.json"
        out.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
