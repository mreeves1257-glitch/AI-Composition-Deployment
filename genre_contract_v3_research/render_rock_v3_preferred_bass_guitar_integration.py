"""Render one focused 8-bar Rock integration check.

Fixed, human-preferred diagnostic treatments:
BASS D
- held-tone strong-beat bass only;
- growlybass_clean.sfz body;
- same-pitch/same-onset growlybass_vicious.sfz transient at -9 dB;
- transient gate 0.20 beat;
- no offbeat bass re-attacks.

GUITAR
- HARMONY Mode A max ringing 2.8 beats;
- safe note-off-preserving strum;
- treated LEAD unchanged.

No drums. No new performance variables. Diagnostic only.
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

from rock_v3_bass_held_tone_candidate import execute as execute_bass
from rock_v3_strum_candidate_executor import execute as execute_guitar
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=8
END_BEAT=BARS*4
ATTACK_GATE_BEATS=0.20

class IntegrationError(RuntimeError):
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

def _window(events:list[dict],track:str)->list[dict]:
    return [
        deepcopy(e) for e in events
        if str(e.get("track_id","")).upper()==track
        and float(e["start_beat"])<END_BEAT
    ]

def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise IntegrationError("PINNED_RENDERER_NOT_SET")

    bass=execute_bass()
    guitar=execute_guitar()
    if bass.get("status")!="PASS" or guitar.get("status")!="PASS":
        raise IntegrationError("SOURCE_NOT_PASS")
    if float(bass["tempo_bpm"])!=float(guitar["tempo_bpm"]):
        raise IntegrationError("TEMPO_MISMATCH")

    held=_window(bass["events"],"BASS")
    harmony=_window(guitar["events"],"HARMONY")
    lead=_window(guitar["events"],"LEAD")
    if not held or not harmony or not lead:
        raise IntegrationError("MISSING_ROLE_EVENTS")

    attack=[]
    for e in held:
        a=deepcopy(e)
        a["duration_beats"]=min(float(a["duration_beats"]),ATTACK_GATE_BEATS)
        attack.append(a)

    for b,a in zip(held,attack):
        if (
            float(b["start_beat"])!=float(a["start_beat"])
            or int(b["midi"])!=int(a["midi"])
            or int(b["velocity"])!=int(a["velocity"])
        ):
            raise IntegrationError("ATTACK_LAYER_IDENTITY_CHANGED")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]

    bass_base=dict(bindings["electric_bass_guitar"])
    harmony_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])

    clean=dict(bass_base)
    clean["preferred_mapping"]="growlybass_clean.sfz"
    vicious=dict(bass_base)
    vicious["preferred_mapping"]="growlybass_vicious.sfz"

    if clean.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise IntegrationError("BASS_FALLBACK_CHANGED")
    for binding in (harmony_binding,lead_binding):
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise IntegrationError("WRONG_GUITAR_MAPPING")

    out=ROOT/"genre_contract_v3_research"/"rock_v3_preferred_bass_guitar_integration"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("BASS_HELD_BODY",held,clean),
        ("BASS_CRISP_ATTACK",attack,vicious),
        ("HARMONY_APPROVED",harmony,harmony_binding),
        ("LEAD_TREATED",lead,lead_binding),
    ):
        midi=_midi(events,float(guitar["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        rr=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if rr.get("status")!="AUDIO_RENDER_PASS":
            raise IntegrationError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "mapping":binding["preferred_mapping"],
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":rr["frames"],
            "sample_rate":rr["sample_rate"],
            "channels":rr["channels"],
        }

    report={
        "schema":"ROCK_V3_PREFERRED_BASS_GUITAR_INTEGRATION_001",
        "status":"PASS",
        "diagnostic_only":True,
        "bars":BARS,
        "tempo_bpm":guitar["tempo_bpm"],
        "bass":{
            "treatment":"HUMAN_PREFERRED_D",
            "held_mapping":"growlybass_clean.sfz",
            "attack_mapping":"growlybass_vicious.sfz",
            "attack_gain_db":-9.0,
            "attack_gate_beats":0.20,
            "offbeat_reattacks":False,
        },
        "guitar":{
            "harmony_max_ringing_beats":2.8,
            "safe_strum":True,
            "treated_lead":True,
            "harmony_gain_db":harmony_binding.get("target_gain_db",-5.0),
            "lead_gain_db":lead_binding.get("target_gain_db",-6.0),
        },
        "drums_included":False,
        "new_performance_variables_added":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "listening_approval":False,
        "renders":renders,
        "next_gate":"OBJECTIVE_MIX_HEADROOM_AND_BALANCE_CHECK__THEN_SINGLE_HUMAN_CLIP"
    }
    (out/"ROCK_V3_PREFERRED_BASS_GUITAR_INTEGRATION_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
