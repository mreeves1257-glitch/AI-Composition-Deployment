"""Render a valid 16-bar Rock V3 bass-sustain A/B on Growlybass Clean.

A = current BASS durations.
B = same BASS notes with the bounded sustain candidate.

Fixed in both:
- research bass mapping: growlybass_clean.sfz
- HARMONY max ringing = 2.8 beats
- safe note-off-preserving HARMONY strum
- treated LEAD unchanged

The Composer target registry is not modified. Clean is applied only to the local
resource binding copy used for this diagnostic render.

No drums are added. The only A/B musical difference is BASS duration.
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

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar
from rock_v3_bass_sustain_candidate_executor import execute as execute_bass_candidate
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=16
END_BEAT=BARS*4
CLEAN_MAPPING="growlybass_clean.sfz"


class BassCleanABError(RuntimeError):
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
            raise BassCleanABError("MIDI_ORDER")
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=round(END_BEAT*TPQ)
    if previous>end_tick:
        end_tick=previous
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
        raise BassCleanABError("PINNED_RENDERER_NOT_SET")

    source=execute_preferred_guitar()
    candidate=execute_bass_candidate()
    if source.get("status")!="PASS" or candidate.get("status")!="PASS":
        raise BassCleanABError("SOURCE_NOT_PASS")
    if source["event_count"]!=candidate["event_count"]:
        raise BassCleanABError("EVENT_COUNT_DRIFT")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]

    bass_binding=dict(bindings["electric_bass_guitar"])
    if bass_binding.get("resource_id")!="KARORYFER_GROWLYBASS_V1_002":
        raise BassCleanABError("WRONG_BASS_RESOURCE")
    if bass_binding.get("version")!="1.002":
        raise BassCleanABError("WRONG_BASS_VERSION")
    if bass_binding.get("production_preferred_mapping")!=CLEAN_MAPPING:
        raise BassCleanABError("REGISTRY_PRODUCTION_PREFERRED_MAPPING_CHANGED")
    if bass_binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise BassCleanABError("BASS_FALLBACK_CHANGED")

    # Research-only local override; registry stays untouched.
    bass_binding["preferred_mapping"]=CLEAN_MAPPING

    harmony_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])
    for binding in (harmony_binding,lead_binding):
        if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise BassCleanABError("WRONG_GUITAR_RESOURCE")
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise BassCleanABError("WRONG_GUITAR_MAPPING")
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise BassCleanABError("GUITAR_FALLBACK_CHANGED")

    a_bass=_role(source["events"],"BASS")
    b_bass=_role(candidate["events"],"BASS")
    harmony=_role(source["events"],"HARMONY")
    lead=_role(source["events"],"LEAD")

    if not a_bass or not b_bass or not harmony or not lead:
        raise BassCleanABError("MISSING_ROLE_EVENTS")
    if len(a_bass)!=len(b_bass):
        raise BassCleanABError("BASS_COUNT_DRIFT")

    changed=0
    for a,b in zip(a_bass,b_bass):
        if int(a["midi"])!=int(b["midi"]):
            raise BassCleanABError("PITCH_CHANGED")
        if abs(float(a["start_beat"])-float(b["start_beat"]))>1e-9:
            raise BassCleanABError("ONSET_CHANGED")
        if int(a["velocity"])!=int(b["velocity"]):
            raise BassCleanABError("VELOCITY_CHANGED")
        if abs(float(a["duration_beats"])-float(b["duration_beats"]))>1e-9:
            changed+=1

    if changed!=23:
        raise BassCleanABError(f"EXPECTED_23_CHANGED_BASS_EVENTS_IN_FIRST16::{changed}")

    out=ROOT/"genre_contract_v3_research"/"rock_v3_bass_sustain_clean_ab"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("A_BASS_CLEAN_CURRENT_DURATION",a_bass,bass_binding),
        ("B_BASS_CLEAN_SUSTAIN",b_bass,bass_binding),
        ("HARMONY_APPROVED",harmony,harmony_binding),
        ("LEAD_TREATED",lead,lead_binding),
    ):
        midi=_midi(events,float(source["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise BassCleanABError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_V3_BASS_SUSTAIN_CLEAN_AB_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bars":BARS,
        "tempo_bpm":source["tempo_bpm"],
        "changed_bass_event_count_in_window":changed,
        "bass_resource_id":bass_binding["resource_id"],
        "bass_mapping":CLEAN_MAPPING,
        "bass_mapping_scope":"RESEARCH_ONLY_LOCAL_BINDING_OVERRIDE",
        "registry_current_mapping":bindings["electric_bass_guitar"]["preferred_mapping"],
        "registry_production_preferred_mapping":bindings["electric_bass_guitar"]["production_preferred_mapping"],
        "registry_modified":False,
        "clean_mapping_note_length_characterization":{
            "workflow_run":42395101164,
            "artifact_id":13582853415,
            "sample_references":240,
            "unique_samples":240,
            "active_end_delta_seconds":1.72,
            "note_length_responsive":True,
        },
        "preferred_harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "guitar_changed":False,
        "lead_changed":False,
        "drums_included":False,
        "renders":renders,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "bass_candidate_enabled_live":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_BASS_SUSTAIN_CLEAN_MAPPING_A_B_LISTENING"
    }
    (out/"ROCK_V3_BASS_SUSTAIN_CLEAN_AB_RENDER_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
