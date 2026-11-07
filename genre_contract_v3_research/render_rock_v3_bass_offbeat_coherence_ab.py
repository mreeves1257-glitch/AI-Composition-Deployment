"""Render strict 16-bar Rock bass all-offbeat coherence A/B.

A = current BASS writing/articulation on growlybass_vicious.sfz.
B = same score with verified all-offbeat coherence candidate:
    - max 0.20-beat BASS gate;
    - every off-beat/subdivision BASS attack matches immediately preceding
      BASS pitch;
    - pitch changes remain allowed only on strong integer beats.

Fixed in both:
- exact Growlybass v1.002 / growlybass_vicious.sfz;
- HARMONY max ringing = 2.8 beats;
- safe HARMONY strum;
- treated LEAD unchanged.

No drums in this gate. Diagnostic only.
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

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_offbeat_coherence_candidate import execute as execute_candidate
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


def _role(events:list[dict],track:str)->list[dict]:
    return [
        e for e in events
        if str(e.get("track_id","")).upper()==track
        and float(e["start_beat"])<END_BEAT
    ]


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise RenderError("PINNED_RENDERER_NOT_SET")

    source=execute_source()
    cand=execute_candidate()
    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise RenderError("SOURCE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise RenderError("EVENT_COUNT_DRIFT")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    bass_binding=dict(bindings["electric_bass_guitar"])
    harmony_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])

    if bass_binding.get("resource_id")!="KARORYFER_GROWLYBASS_V1_002":
        raise RenderError("WRONG_BASS_RESOURCE")
    if bass_binding.get("preferred_mapping")!="growlybass_vicious.sfz":
        raise RenderError("WRONG_BASS_MAPPING")
    if bass_binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RenderError("BASS_FALLBACK_CHANGED")

    for binding in (harmony_binding,lead_binding):
        if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise RenderError("WRONG_GUITAR_RESOURCE")
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise RenderError("WRONG_GUITAR_MAPPING")
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise RenderError("GUITAR_FALLBACK_CHANGED")

    a_bass=_role(source["events"],"BASS")
    b_bass=_role(cand["events"],"BASS")
    harmony=_role(source["events"],"HARMONY")
    lead=_role(source["events"],"LEAD")

    if len(a_bass)!=56 or len(b_bass)!=56:
        raise RenderError("EXPECTED_56_BASS_EVENTS_IN_FIRST16")

    duration_changes=0
    pitch_changes=0
    onset_changes=0
    velocity_changes=0
    for a,b in zip(a_bass,b_bass):
        if float(a["start_beat"])!=float(b["start_beat"]):
            onset_changes+=1
        if int(a["velocity"])!=int(b["velocity"]):
            velocity_changes+=1
        if abs(float(a["duration_beats"])-float(b["duration_beats"]))>1e-9:
            duration_changes+=1
        if int(a["midi"])!=int(b["midi"]):
            pitch_changes+=1

    if onset_changes or velocity_changes:
        raise RenderError("BASS_TIMING_OR_VELOCITY_CHANGED")
    if duration_changes!=56:
        raise RenderError(f"EXPECTED_56_DURATION_CHANGES::{duration_changes}")
    if pitch_changes!=14:
        raise RenderError(f"EXPECTED_14_OFFBEAT_PITCH_CHANGES::{pitch_changes}")

    out=ROOT/"genre_contract_v3_research"/"rock_v3_bass_offbeat_coherence_ab"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("A_BASS_CURRENT",a_bass,bass_binding),
        ("B_BASS_ALL_OFFBEAT_COHERENT",b_bass,bass_binding),
        ("HARMONY_APPROVED",harmony,harmony_binding),
        ("LEAD_TREATED",lead,lead_binding),
    ):
        midi=_midi(events,float(source["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise RenderError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_V3_BASS_OFFBEAT_COHERENCE_AB_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "bars":BARS,
        "tempo_bpm":source["tempo_bpm"],
        "bass_resource_id":bass_binding["resource_id"],
        "bass_mapping":bass_binding["preferred_mapping"],
        "candidate_max_gate_beats":0.20,
        "duration_changed_bass_event_count_in_window":duration_changes,
        "pitch_changed_bass_event_count_in_window":pitch_changes,
        "different_pitch_offbeats_after_candidate":0,
        "preferred_harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "onset_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "guitar_changed":False,
        "lead_changed":False,
        "drums_included":False,
        "renders":renders,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "candidate_enabled_live":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_LISTENING_ALL_OFFBEAT_COHERENCE"
    }
    (out/"ROCK_V3_BASS_OFFBEAT_COHERENCE_AB_RENDER_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
