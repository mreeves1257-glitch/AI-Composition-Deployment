"""Verify Rock V3 bass downbeat damping + upbeat tone guard.

No audio. No live enablement.

Required result:
- 147 bass events total;
- 146 ordinary bass durations shortened to 0.20 beat;
- final sustained arrival remains exempt;
- exactly 3 half-beat upbeat pitch locks;
- every locked upbeat matches the preceding bass pitch;
- no onset, velocity, event-count, guitar, lead, or drum mutation.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_downbeat_damping_candidate_executor import (
    execute as execute_candidate,
    GATE_BEATS,
)

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_DOWNBEAT_DAMPING_CANDIDATE_VERIFY.json"

class VerifyError(RuntimeError):
    pass


def _is_half_beat_upbeat(start:float)->bool:
    local=start%4.0
    frac=local-int(local)
    return abs(frac-0.5)<=1e-9


def main()->None:
    source=execute_source()
    cand=execute_candidate()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")
    if cand["bass_event_count"]!=147:
        raise VerifyError("BASS_EVENT_COUNT_DRIFT")
    if cand["bass_duration_shortened_event_count"]!=146:
        raise VerifyError("DURATION_CHANGE_COUNT_DRIFT")
    if cand["different_pitch_half_beat_upbeat_lock_count"]!=3:
        raise VerifyError("UPBEAT_PITCH_LOCK_COUNT_DRIFT")

    onset_changes=0
    velocity_changes=0
    non_bass_changes=0
    duration_extensions=0
    final_bar_bass=[]

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()
        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1

        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])
        if adur>bdur+1e-9:
            duration_extensions+=1

        changed=(abs(adur-bdur)>1e-9 or int(before["midi"])!=int(after["midi"]))
        if changed and track!="BASS":
            non_bass_changes+=1

        if track=="BASS" and int(float(after["start_beat"])//4)==39:
            final_bar_bass.append((before,after))

    if onset_changes:
        raise VerifyError("ONSET_CHANGED")
    if velocity_changes:
        raise VerifyError("VELOCITY_CHANGED")
    if non_bass_changes:
        raise VerifyError("NON_BASS_MUTATION")
    if duration_extensions:
        raise VerifyError("DURATION_EXTENDED")

    # Every ordinary changed duration must be exactly the measured gate.
    for x in cand["duration_change_manifest"]:
        if abs(float(x["after_duration_beats"])-GATE_BEATS)>1e-9:
            raise VerifyError("NON_GATE_DURATION_FOUND")
        if float(x["before_duration_beats"])<=GATE_BEATS+1e-9:
            raise VerifyError("SHORT_NOTE_CHANGED_UNNECESSARILY")

    # The 3 pitch locks must be half-beat upbeats and must match prior tone.
    for x in cand["pitch_lock_manifest"]:
        if not _is_half_beat_upbeat(float(x["start_beat"])):
            raise VerifyError("PITCH_LOCK_NOT_HALF_BEAT_UPBEAT")
        if int(x["after_midi"])!=int(x["prior_midi"]):
            raise VerifyError("UPBEAT_NOT_LOCKED_TO_PRIOR_TONE")
        if int(x["before_midi"])==int(x["after_midi"]):
            raise VerifyError("PITCH_LOCK_DID_NOT_CHANGE_PITCH")

    # Final arrival remains intact.
    if len(final_bar_bass)!=1:
        raise VerifyError("FINAL_BAR_BASS_COUNT_DRIFT")
    before,after=final_bar_bass[0]
    if float(before["duration_beats"])!=float(after["duration_beats"]):
        raise VerifyError("FINAL_SUSTAIN_CHANGED")
    if int(before["midi"])!=int(after["midi"]):
        raise VerifyError("FINAL_PITCH_CHANGED")

    report={
        "schema":"ROCK_V3_BASS_DOWNBEAT_DAMPING_CANDIDATE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "bass_event_count":147,
        "ordinary_bass_duration_shortened_event_count":146,
        "gate_beats":GATE_BEATS,
        "different_pitch_half_beat_upbeat_lock_count":3,
        "pitch_lock_locations":[
            {
                "start_beat":x["start_beat"],
                "section":x["section"],
                "before_midi":x["before_midi"],
                "after_midi":x["after_midi"],
            }
            for x in cand["pitch_lock_manifest"]
        ],
        "final_sustained_arrival_preserved":True,
        "onset_changed_event_count":0,
        "velocity_changed_event_count":0,
        "duration_extended_event_count":0,
        "non_bass_mutation_count":0,
        "event_count_changed":False,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "resource_basis":{
            "mapping":"growlybass_vicious.sfz",
            "decay_grid_run":42395436023,
            "selected_gate_beats":0.20,
            "measured_active_end_beats":0.451,
            "crosses_half_beat_upbeat":False
        },
        "upbeat_pitch_basis":{
            "analysis_run":42395484055,
            "half_beat_upbeat_event_count":29,
            "same_pitch_upbeat_event_count":26,
            "different_pitch_upbeat_event_count":3
        },
        "audio_generated":False,
        "candidate_enabled":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"16_BAR_CURRENT_MAPPING_A_B__BASELINE_VS_DAMPED_SAME_TONE_UPBEATS"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
