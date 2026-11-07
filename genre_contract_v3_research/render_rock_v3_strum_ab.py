"""Render a narrow Rock V3 strum A/B comparison.

A = current verified Mode A HARMONY timing (vertical attacks).
B = same Mode A score plus the diagnostic note-off-preserving strum attack stagger.

The current 2.8-beat HARMONY sustain ceiling remains unchanged in both.
Only HARMONY electric-guitar onset staggering differs.

Outputs:
- A_HARMONY_CURRENT.wav
- B_HARMONY_STRUM.wav
- LEAD_TREATED.wav
- 8-bar context mixes are assembled by workflow.

Diagnostic only. No live authority.
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

from rock_v3_core_performance_executor import execute as execute_mode_a, MODE
from rock_v3_strum_candidate_executor import execute as execute_strum
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=8
END_BEAT=BARS*4


class StrumABError(RuntimeError):
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
        velocity=max(1,min(127,int(e["velocity"])))
        timeline.append((start,1,bytes((0x90,pitch,velocity))))
        timeline.append((end,0,bytes((0x80,pitch,0))))
    timeline.sort(key=lambda x:(x[0],x[1],x[2][1]))

    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(int(tempo_us).to_bytes(3,"big"))
    track.extend(b"\x00\xB0\x6A\x00")
    previous=0
    for tick,_,msg in timeline:
        if tick<previous:
            raise StrumABError("MIDI_ORDER")
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=round(END_BEAT*TPQ)
    if previous>end_tick:
        end_tick=previous
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise StrumABError("PINNED_RENDERER_NOT_SET")

    current=execute_mode_a(MODE)
    strum=execute_strum()
    if current.get("status")!="PASS" or strum.get("status")!="PASS":
        raise StrumABError("SOURCE_NOT_PASS")
    if current["event_count"]!=strum["event_count"]:
        raise StrumABError("EVENT_COUNT_DRIFT")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    rhythm_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])

    for binding in (rhythm_binding,lead_binding):
        if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise StrumABError("WRONG_RESOURCE")
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise StrumABError("WRONG_MAPPING")
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise StrumABError("FALLBACK_CHANGED")

    a_h=[
        e for e in current["events"]
        if str(e.get("track_id","")).upper()=="HARMONY"
        and float(e["start_beat"])<END_BEAT
    ]
    b_h=[
        e for e in strum["events"]
        if str(e.get("track_id","")).upper()=="HARMONY"
        and float(e["start_beat"])<END_BEAT
    ]
    lead=[
        e for e in current["events"]
        if str(e.get("track_id","")).upper()=="LEAD"
        and float(e["start_beat"])<END_BEAT
    ]
    if not a_h or not b_h or not lead:
        raise StrumABError("MISSING_EVENTS")

    # A/B must preserve note identity and absolute note-off; only HARMONY start
    # times differ for delayed strings.
    if len(a_h)!=len(b_h):
        raise StrumABError("HARMONY_COUNT_DRIFT")
    onset_changes=0
    note_off_changes=0
    pitch_changes=0
    velocity_changes=0
    for a,b in zip(a_h,b_h):
        if int(a["midi"])!=int(b["midi"]):
            pitch_changes+=1
        if int(a["velocity"])!=int(b["velocity"]):
            velocity_changes+=1
        if abs(float(a["start_beat"])-float(b["start_beat"]))>1e-9:
            onset_changes+=1
        a_end=float(a["start_beat"])+float(a["duration_beats"])
        b_end=float(b["start_beat"])+float(b["duration_beats"])
        if abs(a_end-b_end)>1e-9:
            note_off_changes+=1

    if pitch_changes or velocity_changes or note_off_changes:
        raise StrumABError("A_B_INVARIANT_FAILURE")
    if onset_changes<=0:
        raise StrumABError("NO_STRUM_ONSET_CHANGES")

    out=ROOT/"genre_contract_v3_research"/"rock_v3_strum_ab"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("A_HARMONY_CURRENT",a_h,rhythm_binding),
        ("B_HARMONY_STRUM",b_h,rhythm_binding),
        ("LEAD_TREATED",lead,lead_binding),
    ):
        midi=_midi(events,float(current["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise StrumABError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_V3_STRUM_AB_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bars":BARS,
        "tempo_bpm":current["tempo_bpm"],
        "current_harmony_max_ringing_beats":2.8,
        "strum_note_gap_beats":0.038,
        "strum_span_for_three_notes_beats":0.076,
        "alternate_direction":True,
        "note_off_times_preserved":True,
        "harmony_onset_changed_event_count":onset_changes,
        "harmony_note_off_changed_event_count":0,
        "pitch_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "lead_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "renders":renders,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "strum_candidate_enabled_live":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_STRUM_A_B_LISTENING"
    }
    (out/"ROCK_V3_STRUM_AB_RENDER_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
