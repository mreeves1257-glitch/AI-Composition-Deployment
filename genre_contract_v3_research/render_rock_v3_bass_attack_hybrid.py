"""Render bass-only held-tone + crisp attack hybrid candidates.

Baseline C:
- verified Rock held-tone candidate;
- growlybass_clean.sfz;
- strong-beat attacks only, no offbeat re-attacks;
- sustained body.

Attack layer:
- exact same strong-beat onsets, pitches, velocities and event count as C;
- 0.20-beat MIDI gate;
- growlybass_vicious.sfz;
- intended only as transient definition, not as a second rhythmic bass line.

Listening outputs are mixed by workflow:
- C_CLEAN_HELD_BASELINE
- D_HYBRID_ATTACK_M9 (Vicious transient at -9 dB)
- E_HYBRID_ATTACK_M6 (Vicious transient at -6 dB)

First 16 bars, bass only, diagnostic only.
"""
from __future__ import annotations

from copy import deepcopy
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

from rock_v3_bass_held_tone_candidate import execute as execute_held
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=16
END_BEAT=BARS*4
ATTACK_GATE_BEATS=0.20

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

def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise RenderError("PINNED_RENDERER_NOT_SET")

    held=execute_held()
    if held.get("status")!="PASS":
        raise RenderError("HELD_SOURCE_NOT_PASS")

    clean_events=[
        deepcopy(e) for e in held["events"]
        if str(e.get("track_id","")).upper()=="BASS"
        and float(e["start_beat"])<END_BEAT
    ]
    if len(clean_events)!=27:
        raise RenderError(f"EXPECTED_27_HELD_EVENTS::{len(clean_events)}")

    attack_events=[]
    for e in clean_events:
        a=deepcopy(e)
        a["duration_beats"]=min(float(a["duration_beats"]),ATTACK_GATE_BEATS)
        a["bass_attack_layer"]=True
        a["bass_attack_layer_mapping"]="growlybass_vicious.sfz"
        attack_events.append(a)

    for c,a in zip(clean_events,attack_events):
        if float(c["start_beat"])!=float(a["start_beat"]):
            raise RenderError("ATTACK_ONSET_CHANGED")
        if int(c["midi"])!=int(a["midi"]):
            raise RenderError("ATTACK_PITCH_CHANGED")
        if int(c["velocity"])!=int(a["velocity"]):
            raise RenderError("ATTACK_VELOCITY_CHANGED")
        if float(a["duration_beats"])>ATTACK_GATE_BEATS+1e-9:
            raise RenderError("ATTACK_GATE_EXCEEDED")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    base=dict(registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_bass_guitar"])
    if base.get("resource_id")!="KARORYFER_GROWLYBASS_V1_002":
        raise RenderError("WRONG_RESOURCE")
    if base.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RenderError("FALLBACK_CHANGED")

    clean_binding=dict(base)
    clean_binding["preferred_mapping"]="growlybass_clean.sfz"
    vicious_binding=dict(base)
    vicious_binding["preferred_mapping"]="growlybass_vicious.sfz"

    out=ROOT/"genre_contract_v3_research"/"rock_v3_bass_attack_hybrid"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("C_CLEAN_HELD_BASELINE",clean_events,clean_binding),
        ("VICIOUS_ATTACK_LAYER",attack_events,vicious_binding),
    ):
        midi=_midi(events,float(held["tempo_bpm"]))
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
        "schema":"ROCK_V3_BASS_ATTACK_HYBRID_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "bars":BARS,
        "tempo_bpm":held["tempo_bpm"],
        "held_event_count":len(clean_events),
        "attack_event_count":len(attack_events),
        "attack_gate_beats":ATTACK_GATE_BEATS,
        "attack_layer_same_onsets":True,
        "attack_layer_same_pitches":True,
        "attack_layer_same_velocities":True,
        "offbeat_reattacks":False,
        "different_pitch_offbeats":0,
        "held_mapping":"growlybass_clean.sfz",
        "attack_mapping":"growlybass_vicious.sfz",
        "mix_candidates_db":[-9.0,-6.0],
        "guitars_included":False,
        "drums_included":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "candidate_enabled_live":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_LISTENING_HELD_BASELINE_VS_LIGHT_AND_MEDIUM_ATTACK_LAYER",
        "renders":renders
    }
    (out/"ROCK_V3_BASS_ATTACK_HYBRID_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
