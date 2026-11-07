"""Audit existing Rock drum writing against approved Bass D.

Read-only symbolic analysis. No audio and no mutations.

Questions:
- How often does the current kick coincide with approved strong-beat bass?
- How many approved bass attacks have no kick?
- How many kick attacks occur without bass?
- Are kick/snare/hat attacks already on authored source-pattern timing?
- What velocities/beat positions dominate?

This does not decide that any drum pattern is good or bad. It establishes the
existing relationship before any drum-performance work.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_approved_performance_package import build

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_DRUMS_VS_APPROVED_BASS_AUDIT.json"
EPS=1e-9


class AuditError(RuntimeError):
    pass


def _key(value:float)->float:
    return round(float(value),6)


def _local(value:float)->float:
    return round(float(value)%4.0,6)


def _integer(value:float)->bool:
    return abs(value-round(value))<=EPS


def main()->None:
    package=build()
    if package.get("status")!="PASS":
        raise AuditError("APPROVED_PACKAGE_NOT_PASS")

    events=package["score_events"]
    tracks=defaultdict(list)
    for e in events:
        tracks[str(e.get("track_id","")).upper()].append(e)
    for role in tracks:
        tracks[role].sort(key=lambda e:(_key(e["start_beat"]),int(e.get("midi",0))))

    bass=tracks.get("BASS",[])
    kick=tracks.get("KICK",[])
    snare=tracks.get("SNARE",[])
    hat=tracks.get("HAT",[])

    if not bass:
        raise AuditError("NO_BASS_EVENTS")
    if not kick:
        raise AuditError("NO_KICK_EVENTS")
    if not snare:
        raise AuditError("NO_SNARE_EVENTS")
    if not hat:
        raise AuditError("NO_HAT_EVENTS")

    bass_onsets={_key(e["start_beat"]) for e in bass}
    kick_onsets={_key(e["start_beat"]) for e in kick}
    coincident=sorted(bass_onsets & kick_onsets)
    bass_without_kick=sorted(bass_onsets-kick_onsets)
    kick_without_bass=sorted(kick_onsets-bass_onsets)

    kick_local=Counter(str(_local(e["start_beat"])) for e in kick)
    snare_local=Counter(str(_local(e["start_beat"])) for e in snare)
    hat_local=Counter(str(_local(e["start_beat"])) for e in hat)
    kick_vel=Counter(int(e["velocity"]) for e in kick)
    snare_vel=Counter(int(e["velocity"]) for e in snare)
    hat_vel=Counter(int(e["velocity"]) for e in hat)

    # Per-bar relationship for inspection.
    bars=[]
    bar_count=int(package["bar_count"])
    for bar in range(bar_count):
        left=bar*4.0
        right=left+4.0
        b=[e for e in bass if left<=float(e["start_beat"])<right]
        k=[e for e in kick if left<=float(e["start_beat"])<right]
        s=[e for e in snare if left<=float(e["start_beat"])<right]
        h=[e for e in hat if left<=float(e["start_beat"])<right]
        if not (b or k or s or h):
            continue
        bset={_key(e["start_beat"]) for e in b}
        kset={_key(e["start_beat"]) for e in k}
        bars.append({
            "bar_index":bar,
            "bass_local_beats":[_local(e["start_beat"]) for e in b],
            "kick_local_beats":[_local(e["start_beat"]) for e in k],
            "snare_local_beats":[_local(e["start_beat"]) for e in s],
            "hat_local_beats":[_local(e["start_beat"]) for e in h],
            "bass_kick_coincident_count":len(bset&kset),
            "bass_without_kick_count":len(bset-kset),
            "kick_without_bass_count":len(kset-bset),
        })

    report={
        "schema":"ROCK_V3_DRUMS_VS_APPROVED_BASS_AUDIT_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bar_count":bar_count,
        "tempo_bpm":package["tempo_bpm"],
        "approved_bass_profile_id":package["approved_role_profiles"]["BASS"]["profile_id"],
        "event_counts":{
            "BASS":len(bass),
            "KICK":len(kick),
            "SNARE":len(snare),
            "HAT":len(hat),
        },
        "bass_rule":{
            "strong_beat_only":all(_integer(float(e["start_beat"])) for e in bass),
            "offbeat_reattacks":False,
        },
        "kick_bass_relationship":{
            "bass_unique_onsets":len(bass_onsets),
            "kick_unique_onsets":len(kick_onsets),
            "coincident_onsets":len(coincident),
            "bass_onsets_with_kick_fraction":round(len(coincident)/max(1,len(bass_onsets)),6),
            "kick_onsets_with_bass_fraction":round(len(coincident)/max(1,len(kick_onsets)),6),
            "bass_without_kick_onsets":bass_without_kick,
            "kick_without_bass_onsets":kick_without_bass,
            "coincident_onsets_list":coincident,
        },
        "beat_position_histograms":{
            "KICK":dict(sorted(kick_local.items(),key=lambda kv:float(kv[0]))),
            "SNARE":dict(sorted(snare_local.items(),key=lambda kv:float(kv[0]))),
            "HAT":dict(sorted(hat_local.items(),key=lambda kv:float(kv[0]))),
        },
        "velocity_histograms":{
            "KICK":dict(sorted(kick_vel.items())),
            "SNARE":dict(sorted(snare_vel.items())),
            "HAT":dict(sorted(hat_vel.items())),
        },
        "bars":bars,
        "interpretation_limits":[
            "This audit describes existing authored timing only.",
            "It does not approve or reject drum writing.",
            "No drum hit, velocity, timing, resource, or mix level is changed.",
            "Human listening is not required for this audit.",
        ],
        "new_performance_variables_added":False,
        "audio_generated":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "next_gate":"DECIDE_WHETHER_EXISTING_KICK_BASS_RELATIONSHIP_NEEDS_ANY_CHANGE_BEFORE_AUDIO"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
