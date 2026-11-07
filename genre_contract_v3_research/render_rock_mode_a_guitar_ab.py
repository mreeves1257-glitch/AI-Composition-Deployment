"""Render a narrow Rock Core guitar-only A/B listening comparison.

A = developed Rock Core symbolic score before performance Mode A.
B = identical score after Mode A, where only electric-guitar note durations change.

This is diagnostic listening material only. It does not certify production fidelity,
approve the full Rock composition, or promote anything into the live Composer.
"""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import hashlib
import json
import math
import os
import struct
import sys
import wave

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as execute_before
from rock_v3_core_performance_executor import execute as execute_after, MODE
from sfz_renderer_adapter import render_midi

SAMPLE_RATE=44100
TPQ=480
TAIL_SECONDS=1.0
TRACKS=("HARMONY","LEAD")


class RockModeAListeningError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    if value<0:
        raise RockModeAListeningError("NEGATIVE_VLQ")
    out=[value&0x7F]
    value >>= 7
    while value:
        out.append((value&0x7F)|0x80)
        value >>= 7
    return bytes(reversed(out))


def _midi(events:list[dict],tempo_bpm:float,total_beats:float)->bytes:
    tempo_us=round(60_000_000/tempo_bpm)
    timeline=[]
    for e in events:
        start=round(float(e["start_beat"])*TPQ)
        end=round((float(e["start_beat"])+float(e["duration_beats"]))*TPQ)
        end=max(start+1,end)
        pitch=int(e["midi"]); velocity=max(1,min(127,int(e["velocity"])))
        timeline.append((start,1,bytes((0x90,pitch,velocity))))
        timeline.append((end,0,bytes((0x80,pitch,0))))
    timeline.sort(key=lambda x:(x[0],x[1],x[2][1]))

    track=bytearray()
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(int(tempo_us).to_bytes(3,"big"))
    # Match the isolated capability proof: release-noise layer disabled.
    track.extend(b"\x00\xB0\x6A\x00")
    previous=0
    for tick,_,msg in timeline:
        if tick<previous:
            raise RockModeAListeningError("MIDI_EVENT_ORDER_ERROR")
        track.extend(_vlq(tick-previous))
        track.extend(msg)
        previous=tick
    end_tick=round(total_beats*TPQ)
    if end_tick<previous:
        end_tick=previous
    track.extend(_vlq(end_tick-previous))
    track.extend(b"\xFF\x2F\x00")
    return b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def _read_wav(path:Path)->tuple[np.ndarray,int]:
    with wave.open(str(path),"rb") as w:
        rate=w.getframerate(); channels=w.getnchannels(); width=w.getsampwidth()
        raw=w.readframes(w.getnframes())
    if rate!=SAMPLE_RATE or channels not in (1,2) or width not in (2,4):
        raise RockModeAListeningError(
            f"UNEXPECTED_WAV_FORMAT:{rate}:{channels}:{width}"
        )
    dtype="<i2" if width==2 else "<i4"
    scale=32768.0 if width==2 else 2147483648.0
    x=np.frombuffer(raw,dtype=dtype).astype(np.float64)/scale
    if channels==1:
        x=np.repeat(x[:,None],2,axis=1)
    else:
        x=x.reshape(-1,2)
    return x,rate


def _write_wav(path:Path,data:np.ndarray)->None:
    peak=float(np.max(np.abs(data))) if data.size else 0.0
    if peak<=0:
        raise RockModeAListeningError("SILENT_MIX")
    clipped=np.clip(data,-0.999969,0.999969)
    pcm=np.round(clipped*32767.0).astype("<i2")
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def _mix(stems:dict[str,Path],gains_db:dict[str,float])->np.ndarray:
    arrays=[]
    for track in TRACKS:
        data,_=_read_wav(stems[track])
        gain=10**(float(gains_db[track])/20.0)
        arrays.append(data*gain)
    frames=max(len(x) for x in arrays)
    total=np.zeros((frames,2),dtype=np.float64)
    for x in arrays:
        total[:len(x)] += x
    return total


def main():
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise RockModeAListeningError("PINNED_RENDERER_NOT_SET")

    before=execute_before()
    after=execute_after(MODE)
    if before.get("status")!="PASS" or after.get("status")!="PASS":
        raise RockModeAListeningError("ROCK_EXECUTION_NOT_PASS")
    if before["event_count"]!=after["event_count"] or before["bar_count"]!=40:
        raise RockModeAListeningError("A_B_STRUCTURE_CHANGED")

    # Prove identity again at the listening-render boundary.
    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "start_beat","midi","velocity","section","section_type",
        "source_cell","chord_symbol",
    )
    changed=[]
    for i,(a,b) in enumerate(zip(before["events"],after["events"])):
        for field in identity_fields:
            if a.get(field)!=b.get(field):
                raise RockModeAListeningError("A_B_IDENTITY_CHANGED::"+field)
        if float(a["duration_beats"])!=float(b["duration_beats"]):
            if a.get("track_id") not in TRACKS or a.get("instrument_id")!="electric_guitar":
                raise RockModeAListeningError("NON_GUITAR_DURATION_CHANGED")
            changed.append(i)
    if not changed:
        raise RockModeAListeningError("NO_MODE_A_DURATION_CHANGES")

    registry=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    resources={
        "HARMONY":dict(bindings["electric_guitar:RHYTHM_POWER_CHORDS"]),
        "LEAD":dict(bindings["electric_guitar:LEAD_MELODY"]),
    }
    gains_db={
        "HARMONY":float(resources["HARMONY"].get("target_gain_db",-5.0)),
        "LEAD":float(resources["LEAD"].get("target_gain_db",-6.0)),
    }
    for track,res in resources.items():
        if res.get("resource_id")!="KARORYFER_SHINYGUITAR":
            raise RockModeAListeningError("WRONG_GUITAR_RESOURCE::"+track)
        if res.get("preferred_mapping")!="Programs/composer_electric.sfz":
            raise RockModeAListeningError("WRONG_GUITAR_MAPPING::"+track)
        if res.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
            raise RockModeAListeningError("SYNTHETIC_FALLBACK_CHANGED::"+track)

    out=ROOT/"genre_contract_v3_research"/"rock_mode_a_guitar_ab"
    out.mkdir(parents=True,exist_ok=True)
    total_beats=40*4 + (TAIL_SECONDS*before["tempo_bpm"]/60.0)

    condition_stems={}
    render_reports={}
    for label,packet in (("A_BEFORE_MODE_A",before),("B_AFTER_MODE_A",after)):
        by_track=defaultdict(list)
        for e in packet["events"]:
            if e.get("track_id") in TRACKS:
                by_track[e["track_id"]].append(e)
        stems={}
        render_reports[label]={}
        for track in TRACKS:
            if not by_track[track]:
                raise RockModeAListeningError("MISSING_GUITAR_TRACK::"+track)
            midi_bytes=_midi(by_track[track],float(packet["tempo_bpm"]),total_beats)
            midi_path=out/f"{label}_{track}.mid"
            wav_path=out/f"{label}_{track}.wav"
            midi_path.write_bytes(midi_bytes)
            report=render_midi(resources[track],midi_path,wav_path,SAMPLE_RATE)
            if report.get("status")!="AUDIO_RENDER_PASS":
                raise RockModeAListeningError("GUITAR_STEM_RENDER_FAIL::"+track)
            stems[track]=wav_path
            render_reports[label][track]={
                "midi_sha256":hashlib.sha256(midi_bytes).hexdigest(),
                "wav_sha256":hashlib.sha256(wav_path.read_bytes()).hexdigest(),
                "frames":report["frames"],
                "sample_rate":report["sample_rate"],
                "channels":report["channels"],
            }
        condition_stems[label]=stems

    mixes={label:_mix(stems,gains_db) for label,stems in condition_stems.items()}
    shared_peak=max(float(np.max(np.abs(x))) for x in mixes.values())
    # One common safety gain for both conditions. Do not normalize them separately.
    common_gain=min(1.0,0.92/shared_peak) if shared_peak>0 else 1.0
    outputs={}
    for label,data in mixes.items():
        wav=out/f"{label}.wav"
        _write_wav(wav,data*common_gain)
        outputs[label]={
            "wav_path":str(wav),
            "wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest(),
            "frames":len(data),
        }

    summary={
        "schema":"ROCK_MODE_A_GUITAR_AB_LISTENING_001",
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "bar_count":40,
        "tempo_bpm":before["tempo_bpm"],
        "tracks":list(TRACKS),
        "resource_id":"KARORYFER_SHINYGUITAR",
        "mapping":"Programs/composer_electric.sfz",
        "performance_mode":MODE,
        "duration_changed_event_count":len(changed),
        "only_difference_between_conditions":"ELECTRIC_GUITAR_NOTE_DURATIONS",
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "instrument_changed":False,
        "bass_included":False,
        "drums_included":False,
        "reasoning_engine_used":False,
        "common_mix_gain":common_gain,
        "track_target_gains_db":gains_db,
        "render_reports":render_reports,
        "outputs":outputs,
        "production_fidelity_certified":False,
        "full_rock_composition_approved":False,
        "live_runtime_promoted":False,
        "listening_question":"Does Mode A make the same Rock guitar writing sound more connected/natural without blurring rests, riffs, or lead phrase gaps?",
        "next_gate":"HUMAN_LISTENING_REVIEW_BEFORE_ADDING_ANY_OTHER_PERFORMANCE_VARIABLE",
    }
    report_path=out/"ROCK_MODE_A_GUITAR_AB_LISTENING_REPORT.json"
    report_path.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
