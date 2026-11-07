"""Render a diagnostic Rock Mode A HARMONY maximum-sustain cap sweep.

This does NOT change the canonical Mode A policy. It brackets one existing
parameter for human listening:

- BASELINE: no Mode A HARMONY duration realization
- CAP_1_4: current Mode A HARMONY behavior, but positive extensions capped at 1.4 beats
- CAP_2_0: current Mode A HARMONY behavior, but positive extensions capped at 2.0 beats
- CURRENT_2_8: canonical Mode A HARMONY behavior (current 2.8-beat max)

All existing Mode A shortenings are preserved in the capped candidates. Pitch,
onset, velocity, voicing, event count, instrument identity and all non-HARMONY
roles are untouched. Only the first 8 bars are rendered to keep this listening
gate narrow.

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

from rock_v3_core_development_executor import execute as execute_before
from rock_v3_core_performance_executor import execute as execute_after, MODE
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=8
END_BEAT=BARS*4
CAPS={
    "BASELINE":None,
    "CAP_1_4":1.4,
    "CAP_2_0":2.0,
    "CURRENT_2_8":2.8,
}

class HarmonyCapSweepError(RuntimeError):
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
        timeline.append((start,1,bytes((0x90,int(e["midi"]),max(1,min(127,int(e["velocity"])))))))
        timeline.append((end,0,bytes((0x80,int(e["midi"]),0))))
    timeline.sort(key=lambda x:(x[0],x[1],x[2][1]))

    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(int(tempo_us).to_bytes(3,"big"))
    track.extend(b"\x00\xB0\x6A\x00")  # release-noise layer disabled as in prior proofs
    previous=0
    for tick,_,msg in timeline:
        if tick<previous:
            raise HarmonyCapSweepError("MIDI_ORDER")
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=round(END_BEAT*TPQ)
    if previous>end_tick:
        end_tick=previous
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise HarmonyCapSweepError("PINNED_RENDERER_NOT_SET")

    before=execute_before()
    after=execute_after(MODE)
    if before.get("status")!="PASS" or after.get("status")!="PASS":
        raise HarmonyCapSweepError("SOURCE_NOT_PASS")
    if before["event_count"]!=after["event_count"]:
        raise HarmonyCapSweepError("EVENT_COUNT_CHANGED")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    binding=dict(registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_guitar:RHYTHM_POWER_CHORDS"])
    if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
        raise HarmonyCapSweepError("WRONG_RESOURCE")
    if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
        raise HarmonyCapSweepError("WRONG_MAPPING")
    if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise HarmonyCapSweepError("FALLBACK_CHANGED")

    before_by_key={}
    after_by_key={}
    def key(e:dict):
        return (
            str(e.get("track_id","")),
            float(e["start_beat"]),
            int(e["midi"]),
            str(e.get("section","")),
            str(e.get("chord_symbol","")),
        )
    for e in before["events"]:
        before_by_key[key(e)]=e
    for e in after["events"]:
        after_by_key[key(e)]=e
    if set(before_by_key)!=set(after_by_key):
        raise HarmonyCapSweepError("EVENT_IDENTITY_SET_CHANGED")

    base_events=[
        e for e in before["events"]
        if e.get("track_id")=="HARMONY" and float(e["start_beat"])<END_BEAT
    ]
    if not base_events:
        raise HarmonyCapSweepError("NO_HARMONY_EVENTS")

    out=ROOT/"genre_contract_v3_research"/"rock_mode_a_harmony_cap_sweep"
    out.mkdir(parents=True,exist_ok=True)

    report={
        "schema":"ROCK_MODE_A_HARMONY_CAP_SWEEP_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":MODE,
        "bars":BARS,
        "tempo_bpm":before["tempo_bpm"],
        "resource_id":binding["resource_id"],
        "mapping":binding["preferred_mapping"],
        "conditions":{},
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "voicing_changed":False,
        "event_count_changed":False,
        "lead_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "reasoning_engine_used":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_HARMONY_CAP_SWEEP_LISTENING_REVIEW",
    }

    baseline_count=len(base_events)

    for label,cap in CAPS.items():
        events=[]
        extended=shortened=unchanged=0
        max_duration=0.0

        for b in base_events:
            a=after_by_key[key(b)]
            original=float(b["duration_beats"])
            canonical=float(a["duration_beats"])

            if label=="BASELINE":
                duration=original
            else:
                if canonical>original:
                    duration=min(canonical,float(cap))
                else:
                    # preserve canonical Mode A shortenings
                    duration=canonical

            start=float(b["start_beat"])
            duration=min(duration,_bar_end(start)-start)
            duration=round(duration,6)
            if duration<=0:
                raise HarmonyCapSweepError("NONPOSITIVE_DURATION")
            if start+duration>_bar_end(start)+1e-9:
                raise HarmonyCapSweepError("BAR_CROSSING")

            e=dict(b)
            e["duration_beats"]=duration
            events.append(e)
            max_duration=max(max_duration,duration)

            delta=duration-original
            if delta>1e-9:
                extended+=1
            elif delta<-1e-9:
                shortened+=1
            else:
                unchanged+=1

        if len(events)!=baseline_count:
            raise HarmonyCapSweepError("CONDITION_EVENT_COUNT_DRIFT")

        # Ensure vertical voicing members at identical onsets remain coherent.
        by_start={}
        for e in events:
            by_start.setdefault(float(e["start_beat"]),[]).append(float(e["duration_beats"]))
        incoherent=[
            (start,vals) for start,vals in by_start.items()
            if max(vals)-min(vals)>1e-9
        ]
        if incoherent:
            raise HarmonyCapSweepError("VERTICAL_DURATION_SPLIT::"+json.dumps(incoherent[:5]))

        midi=_midi(events,float(before["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        render=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if render.get("status")!="AUDIO_RENDER_PASS":
            raise HarmonyCapSweepError("RENDER_FAIL::"+label)

        report["conditions"][label]={
            "positive_extension_cap_beats":cap,
            "event_count":len(events),
            "extended_event_count":extended,
            "shortened_event_count":shortened,
            "unchanged_event_count":unchanged,
            "max_resulting_duration_beats":max_duration,
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "wav_frames":render["frames"],
            "wav_channels":render["channels"],
            "wav_sample_rate":render["sample_rate"],
        }

    report_path=out/"ROCK_MODE_A_HARMONY_CAP_SWEEP_REPORT.json"
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
