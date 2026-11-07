"""Objective Big Rusty drum-resource/render preflight for current Rock writing.

No musical mutation and no human listening required.

This test:
- uses the exact pinned Big Rusty commit;
- validates the complete Programs/01-full.sfz sample graph;
- confirms the active Rock drum notes are MIDI 36 kick, 38 snare, 42 closed hat;
- confirms those notes match the publisher keymap;
- renders the existing first 8 bars of KICK, SNARE and HAT separately;
- requires each role render to be non-silent and structurally valid.

It does NOT:
- change timing, velocity, hit count, note number, mapping, gain or mix;
- approve musical quality;
- certify production fidelity;
- promote live runtime.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
import math
import os
import re
import struct
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_approved_performance_package import build as build_package
from sfz_renderer_adapter import probe_original_sfz, validate_sfz_samples

SCHEMA="ROCK_V3_DRUM_RESOURCE_RENDER_PREFLIGHT_001"
RESOURCE_ID="KARORYFER_BIG_RUSTY_DRUMS"
MAPPING="Programs/01-full.sfz"
PINNED_COMMIT="f07ce00df34a46b6b08375be56fe116cf15782bc"
SAMPLE_RATE=44100
TPQ=480
BARS=8
END_BEAT=BARS*4.0
EXPECTED_NOTES={"KICK":36,"SNARE":38,"HAT":42}
EXPECTED_KEY_MACROS={"KICK":"kickkey","SNARE":"sncenterkey","HAT":"htclstkey"}


class PreflightError(RuntimeError):
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
    previous=0
    for tick,_,msg in timeline:
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=max(previous,round(END_BEAT*TPQ))
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return (
        b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+
        b"MTrk"+struct.pack(">I",len(track))+bytes(track)
    )


def _audio_stats(path:Path)->dict:
    with wave.open(str(path),"rb") as w:
        rate=w.getframerate()
        channels=w.getnchannels()
        width=w.getsampwidth()
        frames=w.getnframes()
        raw=w.readframes(frames)

    if rate!=SAMPLE_RATE:
        raise PreflightError(f"WRONG_SAMPLE_RATE::{path.name}::{rate}")
    if channels not in (1,2):
        raise PreflightError(f"WRONG_CHANNEL_COUNT::{path.name}::{channels}")
    if width not in (1,2,4):
        raise PreflightError(f"WRONG_SAMPLE_WIDTH::{path.name}::{width}")
    if frames<=0:
        raise PreflightError(f"EMPTY_RENDER::{path.name}")

    if width==1:
        vals=[(x-128)/128.0 for x in raw]
    elif width==2:
        vals=[x[0]/32768.0 for x in struct.iter_unpack("<h",raw)]
    else:
        vals=[x[0]/2147483648.0 for x in struct.iter_unpack("<i",raw)]

    if channels==2:
        mono=[
            (vals[i]+vals[i+1])*0.5
            for i in range(0,len(vals)-1,2)
        ]
    else:
        mono=vals

    if not mono:
        raise PreflightError(f"NO_PCM::{path.name}")
    peak=max(abs(x) for x in mono)
    rms=math.sqrt(sum(x*x for x in mono)/len(mono))
    if peak<=1e-5 or rms<=1e-7:
        raise PreflightError(f"SILENT_OR_NEAR_SILENT::{path.name}::{peak}::{rms}")

    return {
        "sample_rate":rate,
        "channels":channels,
        "sample_width_bytes":width,
        "frames":frames,
        "duration_seconds":round(frames/rate,6),
        "peak":peak,
        "peak_dbfs":20*math.log10(max(peak,1e-12)),
        "rms":rms,
        "rms_dbfs":20*math.log10(max(rms,1e-12)),
    }


def _publisher_keymap(bank:Path)->dict[str,int]:
    text=(bank/"Programs/keymap/keymap.sfz").read_text()
    found={}
    for macro in EXPECTED_KEY_MACROS.values():
        pattern=r"^#define\s+\$"+re.escape(macro)+r"\s+(\d+)\s*$"
        m=re.search(pattern,text,re.M)
        if not m:
            raise PreflightError("KEY_MACRO_MISSING::"+macro)
        found[macro]=int(m.group(1))
    return found


def main()->None:
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise PreflightError("PINNED_RENDERER_NOT_SET")

    package=build_package()
    if package.get("status")!="PASS":
        raise PreflightError("APPROVED_ROCK_PACKAGE_NOT_PASS")

    bank=FORWARD/"sound_resources"/RESOURCE_ID
    mapping_path=bank/MAPPING
    if not mapping_path.is_file():
        raise PreflightError("BIG_RUSTY_MAPPING_MISSING")

    acquisition=FORWARD/"BIG_RUSTY_COMPLETE_ACQUISITION.json"
    if not acquisition.is_file():
        raise PreflightError("COMPLETE_ACQUISITION_REPORT_MISSING")
    acq=json.loads(acquisition.read_text())
    if acq.get("status")!="PASS" or acq.get("pinned_commit")!=PINNED_COMMIT:
        raise PreflightError("PINNED_ACQUISITION_NOT_VERIFIED")
    if acq.get("publisher_files_modified") is not False:
        raise PreflightError("PUBLISHER_FILES_MODIFIED")

    graph=validate_sfz_samples(mapping_path,allowed_root=bank)
    if graph.get("sample_references",0)<=0 or graph.get("unique_samples",0)<=0:
        raise PreflightError("FULL_MAPPING_SAMPLE_GRAPH_EMPTY")

    keymap=_publisher_keymap(bank)
    for role,note in EXPECTED_NOTES.items():
        macro=EXPECTED_KEY_MACROS[role]
        if keymap[macro]!=note:
            raise PreflightError(
                f"PUBLISHER_KEYMAP_MISMATCH::{role}::{keymap[macro]}::{note}"
            )

    target=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=target["targets"]["INTERNAL"]["instrument_bindings"]
    bind_keys={
        "KICK":"kick_drum_rock",
        "SNARE":"snare_drum",
        "HAT":"hi_hat",
    }

    score=package["score_events"]
    role_reports={}
    out=ROOT/"genre_contract_v3_research"/"rock_v3_drum_resource_preflight"
    out.mkdir(parents=True,exist_ok=True)

    for role,binding_key in bind_keys.items():
        binding=dict(bindings[binding_key])
        if binding.get("resource_id")!=RESOURCE_ID:
            raise PreflightError("WRONG_RESOURCE_ID::"+role)
        if binding.get("preferred_mapping")!=MAPPING:
            raise PreflightError("ACTIVE_MAPPING_DRIFT::"+role)
        if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise PreflightError("FALLBACK_POLICY_DRIFT::"+role)

        events=[
            deepcopy(e) for e in score
            if str(e.get("track_id","")).upper()==role
            and float(e["start_beat"])<END_BEAT
        ]
        if not events:
            raise PreflightError("NO_EVENTS::"+role)
        if {int(e["midi"]) for e in events}!={EXPECTED_NOTES[role]}:
            raise PreflightError(
                "ROLE_NOTE_DRIFT::"+role+"::"+
                json.dumps(sorted({int(e["midi"]) for e in events}))
            )

        midi=_midi(events,float(package["tempo_bpm"]))
        midi_path=out/(role+".mid")
        wav_path=out/(role+".wav")
        midi_path.write_bytes(midi)
        rr=probe_original_sfz(binding,midi_path,wav_path,SAMPLE_RATE)
        if rr.get("status")!="DIAGNOSTIC_AUDIO_ONLY_NOT_CERTIFIED":
            raise PreflightError("DIAGNOSTIC_PROBE_FAIL::"+role)
        if rr.get("production_gate")!="UNCHANGED_BLOCKED":
            raise PreflightError("PRODUCTION_GATE_CHANGED::"+role)

        stats=_audio_stats(wav_path)
        role_reports[role]={
            "binding_key":binding_key,
            "event_count":len(events),
            "midi_note":EXPECTED_NOTES[role],
            "publisher_key_macro":EXPECTED_KEY_MACROS[role],
            "publisher_key_value":keymap[EXPECTED_KEY_MACROS[role]],
            "target_gain_db":binding.get("target_gain_db"),
            "resource_id":binding.get("resource_id"),
            "mapping":binding.get("preferred_mapping"),
            "fallback_policy":binding.get("fallback_policy"),
            "midi_sha256":hashlib.sha256(midi).hexdigest(),
            "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "render_report":{
                "status":rr.get("status"),
                "frames":rr.get("frames"),
                "production_gate":rr.get("production_gate"),
                "sfz_path":rr.get("sfz_path"),
            },
            "audio_stats":stats,
        }

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bars":BARS,
        "tempo_bpm":package["tempo_bpm"],
        "resource_id":RESOURCE_ID,
        "pinned_commit":PINNED_COMMIT,
        "active_mapping":MAPPING,
        "complete_sample_graph":graph,
        "publisher_keymap":{
            role:{
                "macro":EXPECTED_KEY_MACROS[role],
                "midi":keymap[EXPECTED_KEY_MACROS[role]],
            }
            for role in ("KICK","SNARE","HAT")
        },
        "role_reports":role_reports,
        "existing_timing_preserved":True,
        "existing_velocity_preserved":True,
        "existing_hit_count_preserved":True,
        "existing_midi_notes_preserved":True,
        "mapping_changed":False,
        "target_gain_changed":False,
        "mix_generated":False,
        "human_listening_required":False,
        "musical_quality_approved":False,
        "production_fidelity_certified":False,
        "publisher_files_modified":False,
        "synthetic_fallback_used":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "next_gate":"OBJECTIVE_DRUM_TRANSIENT_AND_ROLE_BALANCE_CHARACTERIZATION_WITH_EXISTING_WRITING__NO_MUTATION"
    }
    (out/"ROCK_V3_DRUM_RESOURCE_RENDER_PREFLIGHT.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
