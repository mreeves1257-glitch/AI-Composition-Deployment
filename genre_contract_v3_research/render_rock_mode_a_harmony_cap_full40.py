"""Render full-40-bar Rock Mode A HARMONY cap diagnostic.

Produces:
- HARMONY_CAP_2_0.wav : canonical Mode A HARMONY durations with positive
  extensions capped at 2.0 beats; canonical shortenings preserved.
- HARMONY_CURRENT_2_8.wav : canonical Mode A HARMONY durations unchanged.
- LEAD_TREATED.wav : canonical Mode A LEAD durations unchanged.

The script does NOT modify the canonical performance plan or live Composer.
Pitch, onset, velocity, voicing, event count, instrument identity, lead policy,
bass, drums and reasoning remain untouched.
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

from rock_v3_core_development_executor import execute as execute_before
from rock_v3_core_performance_executor import execute as execute_after, MODE
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BAR_COUNT=40
TOTAL_BEATS=BAR_COUNT*4
CAP=2.0


class Full40HarmonyCapError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    if value<0:
        raise Full40HarmonyCapError("NEGATIVE_VLQ")
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
            raise Full40HarmonyCapError("MIDI_ORDER")
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=round(TOTAL_BEATS*TPQ)
    if previous>end_tick:
        end_tick=previous
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def _identity(e:dict)->tuple:
    return (
        str(e.get("track_id","")),
        str(e.get("role","")),
        str(e.get("instrument_id","")),
        str(e.get("source_instrument_id","")),
        float(e["start_beat"]),
        int(e["midi"]),
        int(e["velocity"]),
        str(e.get("section","")),
        str(e.get("section_type","")),
        str(e.get("source_cell","")),
        str(e.get("chord_symbol","")),
    )


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise Full40HarmonyCapError("PINNED_RENDERER_NOT_SET")

    before=execute_before()
    after=execute_after(MODE)
    if before.get("status")!="PASS" or after.get("status")!="PASS":
        raise Full40HarmonyCapError("SOURCE_NOT_PASS")
    if int(before["bar_count"])!=BAR_COUNT or int(after["bar_count"])!=BAR_COUNT:
        raise Full40HarmonyCapError("BAR_COUNT_DRIFT")
    if len(before["events"])!=len(after["events"]):
        raise Full40HarmonyCapError("EVENT_COUNT_DRIFT")

    for b,a in zip(before["events"],after["events"]):
        if _identity(b)!=_identity(a):
            raise Full40HarmonyCapError("CANONICAL_IDENTITY_DRIFT")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    rhythm_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])

    for binding in (rhythm_binding,lead_binding):
        if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise Full40HarmonyCapError("WRONG_RESOURCE")
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise Full40HarmonyCapError("WRONG_MAPPING")
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise Full40HarmonyCapError("FALLBACK_CHANGED")

    harmony_cap=[]
    harmony_current=[]
    lead_treated=[]
    trimmed_note_events=0
    trimmed_gestures=set()
    canonical_shortenings=0
    preserved_shortenings=0

    for b,a in zip(before["events"],after["events"]):
        track=str(b.get("track_id","")).upper()
        if track=="HARMONY":
            current=dict(a)
            candidate=dict(a)
            original=float(b["duration_beats"])
            canonical=float(a["duration_beats"])
            if canonical>original:
                capped=min(canonical,CAP)
                candidate["duration_beats"]=round(capped,6)
                if capped<canonical-1e-9:
                    trimmed_note_events+=1
                    trimmed_gestures.add((float(b["start_beat"]),str(b.get("section",""))))
            else:
                candidate["duration_beats"]=canonical
                if canonical<original-1e-9:
                    canonical_shortenings+=1
                    if abs(float(candidate["duration_beats"])-canonical)<=1e-9:
                        preserved_shortenings+=1

            start=float(candidate["start_beat"])
            if start+float(candidate["duration_beats"])>_bar_end(start)+1e-9:
                raise Full40HarmonyCapError("CAP_CROSSED_BAR_BOUNDARY")
            harmony_cap.append(candidate)
            harmony_current.append(current)

        elif track=="LEAD":
            lead_treated.append(dict(a))

    if trimmed_note_events!=78 or len(trimmed_gestures)!=26:
        raise Full40HarmonyCapError(
            f"CAP_2_0_EXPECTED_TRIM_COUNTS_DRIFT::{trimmed_note_events}::{len(trimmed_gestures)}"
        )
    if canonical_shortenings!=preserved_shortenings:
        raise Full40HarmonyCapError("CANONICAL_SHORTENING_LOST")
    if not harmony_cap or not harmony_current or not lead_treated:
        raise Full40HarmonyCapError("MISSING_ROLE_EVENTS")

    out=ROOT/"genre_contract_v3_research"/"rock_mode_a_harmony_cap_full40"
    out.mkdir(parents=True,exist_ok=True)

    items=(
        ("HARMONY_CAP_2_0",harmony_cap,rhythm_binding),
        ("HARMONY_CURRENT_2_8",harmony_current,rhythm_binding),
        ("LEAD_TREATED",lead_treated,lead_binding),
    )
    renders={}
    for label,events,binding in items:
        midi=_midi(events,float(before["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise Full40HarmonyCapError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_MODE_A_HARMONY_CAP_FULL40_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":MODE,
        "bar_count":BAR_COUNT,
        "tempo_bpm":before["tempo_bpm"],
        "candidate_harmony_cap_beats":CAP,
        "canonical_harmony_cap_beats":2.8,
        "trimmed_harmony_note_event_count":trimmed_note_events,
        "trimmed_harmony_vertical_gesture_count":len(trimmed_gestures),
        "canonical_harmony_shortening_event_count":canonical_shortenings,
        "preserved_canonical_harmony_shortening_event_count":preserved_shortenings,
        "renders":renders,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "voicing_changed":False,
        "event_count_changed":False,
        "lead_policy_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"FULL40_CONTEXT_MIX_AND_HUMAN_LISTENING",
    }
    (out/"ROCK_MODE_A_HARMONY_CAP_FULL40_RENDER_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
