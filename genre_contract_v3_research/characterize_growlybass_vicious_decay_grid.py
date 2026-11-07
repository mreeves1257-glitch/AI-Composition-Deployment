"""Characterize short-note decay timing for Growlybass Vicious at Rock tempo.

Goal: preserve a strong downbeat attack while preventing the audible bass tail
from reading as an upbeat.

The current target-registry mapping remains unchanged:
  growlybass_vicious.sfz

This is not a composition render. It measures the actual acoustic tail produced
by several short MIDI gate lengths at 123 BPM on the exact pinned v1.002
resource and pinned sfizz renderer.

No live promotion. No canonical policy mutation.
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

SCHEMA="GROWLYBASS_VICIOUS_DECAY_GRID_001"
RESOURCE_ID="KARORYFER_GROWLYBASS_V1_002"
MAPPING="growlybass_vicious.sfz"
PITCH=40
VELOCITY=88
TPQ=480
TEMPO_BPM=123.0
TEMPO_US=round(60_000_000/TEMPO_BPM)
SAMPLE_RATE=44100
TOTAL_BEATS=4.0
GATES_BEATS=(0.05,0.075,0.10,0.15,0.20,0.25,0.30,0.40,0.50)


class DecayGridError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    out=[value&0x7F]
    value >>= 7
    while value:
        out.append((value&0x7F)|0x80)
        value >>= 7
    return bytes(reversed(out))


def _midi(gate_beats:float)->bytes:
    note_ticks=max(1,round(gate_beats*TPQ))
    total_ticks=round(TOTAL_BEATS*TPQ)
    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(int(TEMPO_US).to_bytes(3,"big"))
    track.extend(bytes((0x00,0x90,PITCH,VELOCITY)))
    track.extend(_vlq(note_ticks))
    track.extend(bytes((0x80,PITCH,0x00)))
    track.extend(_vlq(total_ticks-note_ticks))
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
        raise DecayGridError(f"UNEXPECTED_WAV_FORMAT::{rate}::{channels}::{width}")
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
        raise DecayGridError("SILENT_RENDER")
    return mono,rate


def _rms(samples:list[float],rate:int,start:float,end:float)->float:
    left=max(0,round(start*rate))
    right=min(len(samples),round(end*rate))
    if right<=left:
        return 0.0
    return math.sqrt(sum(x*x for x in samples[left:right])/(right-left))


def _active_end(samples:list[float],rate:int)->tuple[float,float]:
    early=_rms(samples,rate,0.03,0.12)
    if early<=1e-6:
        raise DecayGridError("EARLY_BODY_TOO_QUIET")
    threshold=max(1e-5,early*0.025)
    width=max(1,round(rate*0.010))
    last=0
    for left in range(0,len(samples),width):
        right=min(len(samples),left+width)
        if right<=left:
            break
        rms=math.sqrt(sum(x*x for x in samples[left:right])/(right-left))
        if rms>=threshold:
            last=right
    return last/rate,threshold


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise DecayGridError("PINNED_RENDERER_NOT_SET")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    binding=registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"]
    if binding.get("resource_id")!=RESOURCE_ID:
        raise DecayGridError("WRONG_RESOURCE")
    if binding.get("preferred_mapping")!=MAPPING:
        raise DecayGridError("WRONG_MAPPING")
    if binding.get("version")!="1.002":
        raise DecayGridError("WRONG_VERSION")
    if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise DecayGridError("FALLBACK_CHANGED")

    mapping=FORWARD/"sound_resources"/RESOURCE_ID/MAPPING
    if not mapping.is_file():
        raise DecayGridError("MAPPING_MISSING")

    beat_seconds=60.0/TEMPO_BPM
    upbeat_seconds=beat_seconds*0.5
    # Aim to decay slightly before the '&' rather than exactly on it.
    target_active_end_seconds=upbeat_seconds-0.020

    rows=[]
    resource=dict(binding)

    with tempfile.TemporaryDirectory(prefix="growlybass-vicious-decay-") as tmp:
        folder=Path(tmp)
        for gate_beats in GATES_BEATS:
            midi_path=folder/f"gate_{str(gate_beats).replace('.','_')}.mid"
            wav_path=folder/f"gate_{str(gate_beats).replace('.','_')}.wav"
            midi_path.write_bytes(_midi(gate_beats))
            render=render_midi(resource,midi_path,wav_path,SAMPLE_RATE)
            if render.get("status")!="AUDIO_RENDER_PASS":
                raise DecayGridError("RENDER_FAIL")

            pcm,rate=_pcm_mono(wav_path)
            active_end,threshold=_active_end(pcm,rate)
            gate_seconds=gate_beats*beat_seconds

            rows.append({
                "gate_beats":gate_beats,
                "gate_seconds":gate_seconds,
                "active_end_seconds":active_end,
                "active_end_beats":active_end/beat_seconds,
                "acoustic_tail_after_noteoff_seconds":max(0.0,active_end-gate_seconds),
                "crosses_upbeat":active_end>=upbeat_seconds,
                "meets_pre_upbeat_target":active_end<=target_active_end_seconds,
                "threshold_rms":threshold,
                "render_seconds":len(pcm)/rate,
            })

    acceptable=[r for r in rows if r["meets_pre_upbeat_target"]]
    selected=max(acceptable,key=lambda r:r["gate_beats"]) if acceptable else None

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "resource_id":RESOURCE_ID,
        "version":"1.002",
        "mapping":MAPPING,
        "archive_sha256":"b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc",
        "renderer_pin":os.environ.get("AI_COMP_SFIZZ_PIN"),
        "tempo_bpm":TEMPO_BPM,
        "beat_seconds":beat_seconds,
        "upbeat_offset_seconds":upbeat_seconds,
        "pre_upbeat_target_seconds":target_active_end_seconds,
        "pitch":PITCH,
        "velocity":VELOCITY,
        "rows":rows,
        "selected_longest_gate_meeting_target":selected,
        "interpretation":(
            "Select the longest MIDI gate whose measured acoustic tail falls at least "
            "20 ms before the half-beat upbeat. This preserves the strongest possible "
            "downbeat body while reducing perceived upbeat resonance."
        ),
        "bass_sustain_extension_rejected":True,
        "registry_modified":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "reasoning_engine_used":False,
        "next_gate":(
            "BUILD_DOWNBEAT_DAMPING_CANDIDATE_USING_SELECTED_GATE"
            if selected else
            "VICIOUS_MAPPING_CANNOT_DECAY_BEFORE_UPBEAT_WITH_TESTED_GATES"
        )
    }

    out=ROOT/"genre_contract_v3_research"/"GROWLYBASS_VICIOUS_DECAY_GRID.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
