"""Render three bass-only Rock comparison files.

A_ACCEPTED_VICIOUS_SHORT
    Human-preferred corrected bass-only baseline:
    - all off-beat pitch changes normalized;
    - 0.20-beat gate;
    - growlybass_vicious.sfz.

B_CLEAN_SHORT_CONTROL
    Exact same corrected symbolic bass performance as A, rendered through
    growlybass_clean.sfz. This isolates mapping/timbre.

C_CLEAN_HELD_TONE
    Held-tone candidate:
    - off-beat re-attacks removed;
    - strong-beat attacks only;
    - strong tone sustains toward next strong beat;
    - growlybass_clean.sfz.

First 16 bars only. Bass only. Diagnostic only.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_bass_offbeat_coherence_candidate import execute as execute_corrected
from rock_v3_bass_held_tone_candidate import execute as execute_held
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=16
END_BEAT=BARS*4

class RenderError(RuntimeError):
    pass

def _vlq(value:int)->bytes:
    out=[value&0x7F]
    value >>= 7
    while value:
        out.append((value&0x7F)|0x80)
        value >>= 7
    return bytes(reversed(out))

def _midi(events:list[dict],tempo_bpm:float)->bytes:
    tempo_us=round(60_000_000/tempo_bpm)
    timeline=[]
    for e in events:
        start=round(float(e["start_beat"])*TPQ)
        end=round((float(e["start_beat"])+float(e["duration_beats"]))*TPQ)
        end=max(start+1,end)
        pitch=int(e["midi"])
        vel=max(1,min(127,int(e["velocity"])))
        timeline.append((start,1,bytes((0x90,pitch,vel))))
        timeline.append((end,0,bytes((0x80,pitch,0))))
    timeline.sort(key=lambda x:(x[0],x[1],x[2][1]))
    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(int(tempo_us).to_bytes(3,"big"))
    track.extend(b"\x00\xB0\x6A\x00")
    previous=0
    for tick,_,msg in timeline:
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=max(previous,round(END_BEAT*TPQ))
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+b"MTrk"+struct.pack(">I",len(track))+bytes(track)

def _bass(events:list[dict])->list[dict]:
    return [
        e for e in events
        if str(e.get("track_id","")).upper()=="BASS"
        and float(e["start_beat"])<END_BEAT
    ]

def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise RenderError("PINNED_RENDERER_NOT_SET")

    corrected=execute_corrected()
    held=execute_held()
    if corrected.get("status")!="PASS" or held.get("status")!="PASS":
        raise RenderError("SOURCE_NOT_PASS")

    a=_bass(corrected["events"])
    c=_bass(held["events"])
    if len(a)!=56:
        raise RenderError(f"CORRECTED_FIRST16_COUNT::{len(a)}")
    if len(c)!=27:
        raise RenderError(f"HELD_FIRST16_COUNT::{len(c)}")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    base=dict(registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"])
    if base.get("resource_id")!="KARORYFER_GROWLYBASS_V1_002":
        raise RenderError("WRONG_RESOURCE")
    if base.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RenderError("FALLBACK_CHANGED")

    vicious=dict(base)
    vicious["preferred_mapping"]="growlybass_vicious.sfz"
    clean=dict(base)
    clean["preferred_mapping"]="growlybass_clean.sfz"

    out=ROOT/"genre_contract_v3_research"/"rock_v3_bass_three_way"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("A_ACCEPTED_VICIOUS_SHORT",a,vicious),
        ("B_CLEAN_SHORT_CONTROL",a,clean),
        ("C_CLEAN_HELD_TONE",c,clean),
    ):
        midi=_midi(events,float(corrected["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise RenderError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "mapping":binding["preferred_mapping"],
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_V3_BASS_THREE_WAY_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "bars":BARS,
        "tempo_bpm":corrected["tempo_bpm"],
        "A":{
            "meaning":"human-preferred corrected bass-only baseline",
            "mapping":"growlybass_vicious.sfz",
            "event_count":56,
            "max_gate_beats":0.20,
            "offbeat_reattacks_present":True,
            "different_pitch_offbeats":0
        },
        "B":{
            "meaning":"mapping control: exact same corrected pattern on Clean",
            "mapping":"growlybass_clean.sfz",
            "event_count":56,
            "max_gate_beats":0.20,
            "offbeat_reattacks_present":True,
            "different_pitch_offbeats":0
        },
        "C":{
            "meaning":"held-tone candidate on sustain-capable Clean",
            "mapping":"growlybass_clean.sfz",
            "event_count":27,
            "offbeat_reattacks_present":False,
            "different_pitch_offbeats":0,
            "max_hold_beats":1.50,
            "release_gap_beats":0.20
        },
        "renders":renders,
        "guitars_included":False,
        "drums_included":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "candidate_enabled_live":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_BASS_ONLY_THREE_WAY_LISTENING"
    }
    (out/"ROCK_V3_BASS_THREE_WAY_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
