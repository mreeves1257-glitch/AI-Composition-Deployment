"""Render Rock V3 bass pitch-coherence A/B on current Growlybass Vicious.

A = current bass writing under the approved guitar treatment.
B = pitch-coherence repair:
    - never extends bass;
    - shortens prior notes before different-pitch attacks to leave acoustic space;
    - pitch-locks ultra-close 0.25-beat pitch flips to the prior tone.

Fixed in both:
- Growlybass Vicious v1.002 (current registry mapping)
- HARMONY max ringing = 2.8 beats
- safe note-off-preserving HARMONY strum
- treated LEAD unchanged
- no drums in this gate

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

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_pitch_coherence_candidate_executor import execute as execute_candidate
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
BARS=16
END_BEAT=BARS*4


class BassPitchCoherenceABError(RuntimeError):
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
    previous=0
    for tick,_,msg in timeline:
        if tick<previous:
            raise BassPitchCoherenceABError("MIDI_ORDER")
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
        raise BassPitchCoherenceABError("PINNED_RENDERER_NOT_SET")

    source=execute_source()
    candidate=execute_candidate()
    if source.get("status")!="PASS" or candidate.get("status")!="PASS":
        raise BassPitchCoherenceABError("SOURCE_NOT_PASS")
    if source["event_count"]!=candidate["event_count"]:
        raise BassPitchCoherenceABError("EVENT_COUNT_DRIFT")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]

    bass_binding=dict(bindings["electric_bass_guitar"])
    if bass_binding.get("resource_id")!="KARORYFER_GROWLYBASS_V1_002":
        raise BassPitchCoherenceABError("WRONG_BASS_RESOURCE")
    if bass_binding.get("preferred_mapping")!="growlybass_vicious.sfz":
        raise BassPitchCoherenceABError("WRONG_BASS_MAPPING")
    if bass_binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise BassPitchCoherenceABError("BASS_FALLBACK_CHANGED")

    harmony_binding=dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"])
    lead_binding=dict(bindings["electric_guitar:LEAD_MELODY"])
    for binding in (harmony_binding,lead_binding):
        if binding.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise BassPitchCoherenceABError("WRONG_GUITAR_RESOURCE")
        if binding.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise BassPitchCoherenceABError("WRONG_GUITAR_MAPPING")
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise BassPitchCoherenceABError("GUITAR_FALLBACK_CHANGED")

    a_bass=_role(source["events"],"BASS")
    b_bass=_role(candidate["events"],"BASS")
    harmony=_role(source["events"],"HARMONY")
    lead=_role(source["events"],"LEAD")
    if not a_bass or not b_bass or not harmony or not lead:
        raise BassPitchCoherenceABError("MISSING_ROLE_EVENTS")
    if len(a_bass)!=len(b_bass):
        raise BassPitchCoherenceABError("BASS_COUNT_DRIFT")

    duration_changed=0
    pitch_changed=0
    onset_changed=0
    velocity_changed=0
    extension_count=0

    for a,b in zip(a_bass,b_bass):
        if abs(float(a["start_beat"])-float(b["start_beat"]))>1e-9:
            onset_changed+=1
        if int(a["velocity"])!=int(b["velocity"]):
            velocity_changed+=1
        ad=float(a["duration_beats"])
        bd=float(b["duration_beats"])
        if abs(ad-bd)>1e-9:
            duration_changed+=1
            if bd>ad+1e-9:
                extension_count+=1
        if int(a["midi"])!=int(b["midi"]):
            pitch_changed+=1

    if onset_changed or velocity_changed or extension_count:
        raise BassPitchCoherenceABError("A_B_INVARIANT_FAILURE")
    if duration_changed<=0 and pitch_changed<=0:
        raise BassPitchCoherenceABError("NO_CANDIDATE_CHANGES")

    out=ROOT/"genre_contract_v3_research"/"rock_v3_bass_pitch_coherence_ab"
    out.mkdir(parents=True,exist_ok=True)

    renders={}
    for label,events,binding in (
        ("A_BASS_CURRENT",a_bass,bass_binding),
        ("B_BASS_PITCH_COHERENT",b_bass,bass_binding),
        ("HARMONY_APPROVED",harmony,harmony_binding),
        ("LEAD_TREATED",lead,lead_binding),
    ):
        midi=_midi(events,float(source["tempo_bpm"]))
        midi_path=out/(label+".mid")
        wav_path=out/(label+".wav")
        midi_path.write_bytes(midi)
        report=render_midi(binding,midi_path,wav_path,SAMPLE_RATE)
        if report.get("status")!="AUDIO_RENDER_PASS":
            raise BassPitchCoherenceABError("RENDER_FAIL::"+label)
        renders[label]={
            "event_count":len(events),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "frames":report["frames"],
            "sample_rate":report["sample_rate"],
            "channels":report["channels"],
        }

    report={
        "schema":"ROCK_V3_BASS_PITCH_COHERENCE_AB_RENDER_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bars":BARS,
        "tempo_bpm":source["tempo_bpm"],
        "bass_mapping":"growlybass_vicious.sfz",
        "bass_resource_id":"KARORYFER_GROWLYBASS_V1_002",
        "bass_duration_shortened_event_count_in_window":duration_changed,
        "bass_pitch_locked_event_count_in_window":pitch_changed,
        "bass_duration_extended_event_count":0,
        "bass_onset_changed_event_count":0,
        "bass_velocity_changed_event_count":0,
        "preferred_harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
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
        "next_gate":"HUMAN_BASS_PITCH_COHERENCE_A_B_LISTENING"
    }
    (out/"ROCK_V3_BASS_PITCH_COHERENCE_AB_RENDER_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
