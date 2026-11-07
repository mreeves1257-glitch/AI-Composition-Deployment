"""Verify the symbolic Rock V3 bass sustain candidate executor.

No audio. No live enablement.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar
from rock_v3_bass_sustain_candidate_executor import execute as execute_bass

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_SUSTAIN_CANDIDATE_EXECUTION_VERIFY.json"


class VerifyError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    source=execute_preferred_guitar()
    cand=execute_bass()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")
    if cand["bass_event_count"]!=147:
        raise VerifyError("BASS_EVENT_COUNT_DRIFT")
    if cand["bass_duration_changed_event_count"]!=58:
        raise VerifyError("BASS_CHANGE_COUNT_DRIFT")

    section_counts=Counter()
    min_ext=None
    max_ext=0.0
    min_gap=None

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()

        identity_fields=(
            "track_id","role","instrument_id","source_instrument_id",
            "start_beat","midi","velocity","section","section_type",
            "source_cell","chord_symbol",
        )
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise VerifyError("IDENTITY_MUTATION::"+field)

        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])

        if track!="BASS" and abs(adur-bdur)>1e-9:
            raise VerifyError("NON_BASS_DURATION_MUTATION")

        if track=="BASS" and adur>bdur+1e-9:
            extension=adur-bdur
            start=float(after["start_beat"])
            section_counts[str(after.get("section","UNKNOWN"))]+=1
            min_ext=extension if min_ext is None else min(min_ext,extension)
            max_ext=max(max_ext,extension)

            if start+adur>_bar_end(start)+1e-9:
                raise VerifyError("BAR_BOUNDARY_CROSSING")

    manifest=cand["bass_duration_change_manifest"]
    if len(manifest)!=58:
        raise VerifyError("MANIFEST_COUNT_DRIFT")

    for item in manifest:
        gap=float(item["gap_to_next_attack_beats"])
        if gap<0:
            raise VerifyError("NEXT_ATTACK_OVERLAP")
        min_gap=gap if min_gap is None else min(min_gap,gap)

    expected_sections={
        "INTRO_1":2,
        "VERSE_1":14,
        "CHORUS_1":12,
        "VERSE_2":14,
        "CHORUS_2":12,
        "OUTRO_1":4,
    }
    if dict(section_counts)!=expected_sections:
        raise VerifyError("SECTION_CHANGE_DISTRIBUTION_DRIFT::"+repr(dict(section_counts)))

    if abs(float(min_ext)-0.225)>1e-9:
        raise VerifyError("MIN_EXTENSION_DRIFT")
    if abs(float(max_ext)-0.615)>1e-9:
        raise VerifyError("MAX_EXTENSION_DRIFT")
    if abs(float(min_gap)-0.275)>1e-9:
        raise VerifyError("MIN_GAP_DRIFT")

    report={
        "schema":"ROCK_V3_BASS_SUSTAIN_CANDIDATE_EXECUTION_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_preferred_guitar_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "bass_event_count":147,
        "bass_duration_changed_event_count":58,
        "section_change_counts":expected_sections,
        "minimum_extension_beats":0.225,
        "maximum_extension_beats":0.615,
        "minimum_gap_to_next_attack_beats":0.275,
        "next_attack_overlap_count":0,
        "bar_boundary_crossing_count":0,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "guitar_changed_by_bass_candidate":False,
        "lead_changed_by_bass_candidate":False,
        "drums_changed":False,
        "preferred_harmony_max_ringing_beats":2.8,
        "preferred_safe_strum_preserved":True,
        "candidate_enabled":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"ISOLATED_BASS_SUSTAIN_AUDIO_A_B__PREFERRED_GUITAR_CONTEXT_FIXED"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
