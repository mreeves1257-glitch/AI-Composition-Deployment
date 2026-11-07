"""Render a harmony-locked Classical audition using the experimental reasoning layer.

Authority boundary:
- current_master_forward.classical_composition owns every pitch, chord, duration,
  articulation, and velocity;
- reasoning_engine_v0_1 may only influence density/space by suppressing selected
  already-generated secondary-player events;
- no pitch may be created, shifted, reharmonized, or transposed here.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import mido

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "current_master_forward"
RUNTIME = ROOT / "composer" / "runtime"
for p in (ROOT / "experimental_reasoning", MASTER, RUNTIME):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from classical_composition import CHORDS, make_plan, realize
from classical_reasoning_bridge_v0_1 import build_classical_reasoning_report
from approved_audio_pipeline import (
    CLASSICAL_GOLDEN_SECTION_CONTROLS,
    CLASSICAL_GOLDEN_SECTION_PROGRAMS,
)
from render_substitute_universal import render_track
from original_mixer_adapter import mix

SECTIONS = [
    ("VIOLIN_I", "violin"),
    ("VIOLIN_II", "violin"),
    ("VIOLA", "viola"),
    ("CELLO", "cello"),
    ("DOUBLE_BASS", "double_bass"),
    ("FLUTE", "concert_flute"),
    ("OBOE", "oboe"),
    ("CLARINET", "clarinet_bb"),
    ("BASSOON", "bassoon"),
    ("HORN", "horn_f"),
    ("TRUMPET", "trumpet_c"),
    ("TROMBONE", "tenor_trombone"),
    ("TUBA", "bass_tuba"),
    ("TIMPANI", "timpani"),
]
CHANNELS = [0,1,2,3,4,5,6,7,8,10,11,12,13,14]

# Secondary desks are the only events the reasoning test is allowed to suppress.
# Core desks/voices are always retained. This is not a gain/EQ patch.
SECONDARY_GROUP = {
    "VIOLIN_I_2": "upper",
    "VIOLA_2": "middle",
    "CELLO_2": "low",
    "DOUBLE_BASS_2": "low",
    "FLUTE_2": "upper",
    "CLARINET_2": "middle",
    "HORN_2": "middle",
}

FORMAL = {"A":"statement", "B":"contrast", "A_RETURN":"return", "CODA":"coda"}


def section_for_player(player_id: str) -> str:
    p = str(player_id or "").upper()
    if p.startswith("VIOLIN_I_"): return "VIOLIN_I"
    if p.startswith("VIOLIN_II_"): return "VIOLIN_II"
    if p.startswith("VIOLA_"): return "VIOLA"
    if p.startswith("CELLO_"): return "CELLO"
    if p.startswith("DOUBLE_BASS_"): return "DOUBLE_BASS"
    if p.startswith("FLUTE_"): return "FLUTE"
    if p.startswith("OBOE_"): return "OBOE"
    if p.startswith("CLARINET_"): return "CLARINET"
    if p.startswith("BASSOON_"): return "BASSOON"
    if p.startswith("HORN_"): return "HORN"
    if p.startswith("TRUMPET_"): return "TRUMPET"
    if p.startswith("TROMBONE_"): return "TROMBONE"
    if p.startswith("TUBA_"): return "TUBA"
    if p.startswith("TIMPANI_"): return "TIMPANI"
    raise ValueError("CLASSICAL_SECTION_UNRESOLVED:" + p)


def load_profile():
    path = MASTER / "genre_registry_WORKING_GENRE_COMPLETE_2026-10-02_182810_CDT.json"
    data = json.loads(path.read_text())
    return data["detailed_or_new_profiles"]["Classical"]


def reasoning_by_section(plan):
    report = build_classical_reasoning_report(
        profile=load_profile(), plan=plan, creation_seed=0, mode="quick"
    )
    return report, {
        x["classical_section"]: x["reasoning_packet"]["decisions"]
        for x in report["sections"]
    }


def keep_secondary(event, decisions) -> bool:
    pid = str(event.get("player_id") or "")
    group = SECONDARY_GROUP.get(pid)
    if group is None:
        return True

    bar = int(event["plan_bar"])
    local = (bar - 1) % 8
    formal = FORMAL[str(event["section"])]
    target_energy = float(decisions[str(event["section"])]["energy"]["target"])
    motion = str(decisions[str(event["section"])]["energy"]["motion"])

    # Translate reasoning-only density intent conservatively:
    # low secondary desks receive the most breathing room; upper color can remain
    # more active. Return/build restores some density; coda/release thins it.
    if group == "low":
        period = 4 if target_energy <= 0.50 else 3
    elif group == "middle":
        period = 3 if target_energy <= 0.50 else 2
    else:
        period = 2

    if motion == "BUILD":
        period = max(2, period - 1)
    elif motion == "PULL_BACK" or formal == "coda":
        period += 1

    # Keep phrase-opening/cadential support, otherwise create intentional space.
    if local in (0, 7):
        return True
    return (bar % period) == 0


def validate_original_harmony(events, plan):
    bars = {int(b["bar"]): b for b in plan["bars"]}
    bad = []
    for e in events:
        if e["instrument_id"] == "timpani":
            continue
        b = bars[int(e["plan_bar"])]
        chord = CHORDS[b["quality"]][b["roman"]]
        pcs = {(int(b["tonic_pc"]) + int(x)) % 12 for x in chord}
        if int(e["midi"]) % 12 not in pcs:
            bad.append((e["plan_bar"], e["player_id"], e["midi"], sorted(pcs)))
    if bad:
        raise RuntimeError("REAL_CLASSICAL_HARMONY_VALIDATION_FAILED:" + repr(bad[:12]))


def make_filtered_events(plan):
    source = realize(plan)
    validate_original_harmony(source, plan)
    report, decisions = reasoning_by_section(plan)
    filtered = [e for e in source if keep_secondary(e, decisions)]

    # Hard subset guard: no new pitch, timing, duration, velocity or articulation.
    def sig(e):
        return (
            e["player_id"], e["instrument_id"], int(e["midi"]),
            round(float(e["start_beat"]), 5), round(float(e["duration_beats"]), 5),
            int(e["velocity"]), str(e["articulation"]), str(e["section"]),
        )
    source_sigs = {sig(e) for e in source}
    added = [sig(e) for e in filtered if sig(e) not in source_sigs]
    if added:
        raise RuntimeError("REASONING_ADAPTER_CREATED_OR_CHANGED_NOTE:" + repr(added[:8]))

    validate_original_harmony(filtered, plan)
    return source, filtered, report, decisions


def build_midi(plan, events, out_path: Path):
    tpb = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name="Classical Reasoning Audition", time=0))
    # Tempo changes from the real Classical plan.
    tempo_events = []
    for item in plan["tempo_map"]:
        tick = int(round(float(item["start_beat"]) * tpb))
        tempo_events.append((tick, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(float(item["bpm"])), time=0)))
    prev = 0
    for tick, msg in sorted(tempo_events, key=lambda x:x[0]):
        meta.append(msg.copy(time=tick-prev))
        prev = tick
    mid.tracks.append(meta)

    by_section = defaultdict(list)
    # Dedupe exact same section note at exact same time/duration; population is
    # section metadata, not linear identical-note gain.
    dedupe = {}
    for e in events:
        sec = section_for_player(e["player_id"])
        key = (sec, round(float(e["start_beat"]),5), round(float(e["duration_beats"]),5), int(e["midi"]))
        old = dedupe.get(key)
        if old is None or int(e["velocity"]) > int(old["velocity"]):
            dedupe[key] = e
    for e in dedupe.values():
        by_section[section_for_player(e["player_id"])].append(e)

    for channel, (sec, iid) in zip(CHANNELS, SECTIONS):
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=sec, time=0))
        program = int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec])
        ctl = CLASSICAL_GOLDEN_SECTION_CONTROLS[sec]
        tr.append(mido.Message("program_change", channel=channel, program=program, time=0))
        tr.append(mido.Message("control_change", channel=channel, control=10, value=int(ctl["pan"]), time=0))
        tr.append(mido.Message("control_change", channel=channel, control=11, value=int(ctl["expression"]), time=0))
        tr.append(mido.Message("control_change", channel=channel, control=91, value=int(ctl["reverb"]), time=0))
        abs_msgs = []
        for e in by_section.get(sec, []):
            start = int(round(float(e["start_beat"]) * tpb))
            end = int(round((float(e["start_beat"]) + float(e["duration_beats"])) * tpb))
            note = int(e["midi"]); vel = int(e["velocity"])
            abs_msgs.append((start, 1, mido.Message("note_on", channel=channel, note=note, velocity=vel, time=0)))
            abs_msgs.append((end, 0, mido.Message("note_off", channel=channel, note=note, velocity=0, time=0)))
        prev = 0
        for tick, order, msg in sorted(abs_msgs, key=lambda x:(x[0],x[1])):
            tr.append(msg.copy(time=max(0, tick-prev)))
            prev = tick
        mid.tracks.append(tr)
    mid.save(out_path)
    return mid, by_section


def render(mid, out_dir: Path):
    stems = out_dir / "stems"; mixed = out_dir / "mixed"
    stems.mkdir(parents=True, exist_ok=True); mixed.mkdir(parents=True, exist_ok=True)
    sf = RUNTIME / "replacement_instruments" / "TimGM6mb.sf2"
    if not sf.is_file():
        raise RuntimeError("APPROVED_SOUNDFONT_MISSING:" + str(sf))

    rendered = []
    for idx, (sec, iid) in enumerate(SECTIONS, 1):
        wav = stems / f"{idx:02d}_{sec}.wav"
        program = int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec])
        rep = render_track(mid, idx, sf, wav, "melodic", program=program, tuning_reference_hz=440)
        rep.update(track_id=sec, instrument_id=iid, program=program, wav_path=str(wav))
        rendered.append(rep)

    perf = []
    profiles = []
    bindings = []
    for idx, (sec, iid) in enumerate(SECTIONS, 1):
        profiles.append({"track_id":sec, "instrument_id":iid, "role":sec})
        bindings.append({"track_id":sec, "resource":{
            "renderer":"TIMGM6MB_APPROVED_SUBSTITUTE",
            "soundfont":str(sf),
            "program":int(CLASSICAL_GOLDEN_SECTION_PROGRAMS[sec]),
            "target_gain_db":0.0,
            "substitute":True,
        }})
        t = 0
        for msg in mid.tracks[idx]:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                perf.append({"track_id":sec, "instrument_id":iid, "pitch":msg.note, "velocity":msg.velocity})

    fingerprint = hashlib.sha256(json.dumps(perf, sort_keys=True).encode()).hexdigest()
    engine_result = {"genre":"Classical","modules":{
        "instrument":{"profiles":profiles},
        "target":{"resolved_resources":bindings},
        "performance":{"events":perf},
        "theory":{"composition_fingerprint":fingerprint},
    }}
    stem_manifest = {"tracks":[
        {"track_id":r["track_id"],"instrument_id":r["instrument_id"],"wav_path":r["wav_path"]}
        for r in rendered
    ]}
    manifest_path = out_dir / "stem_manifest.json"
    manifest_path.write_text(json.dumps(stem_manifest, indent=2))
    result = mix(manifest_path, mixed, genre="Classical", engine_result=engine_result)
    wav_path = Path(result["wav_path"]) if result.get("wav_path") else next(mixed.rglob("stereo_derivative.wav"))
    return result, wav_path


def main():
    out = Path(os.environ.get("CLASSICAL_REASONING_OUT", "listening/reasoning_real_classical"))
    out.mkdir(parents=True, exist_ok=True)
    plan = make_plan(seed=0, mode="quick", bpm=76)
    source, filtered, reasoning_report, decisions = make_filtered_events(plan)
    midi_path = out / "Classical_Reasoning_v01_RealHarmony.mid"
    mid, by_section = build_midi(plan, filtered, midi_path)
    mix_result, wav_path = render(mid, out)

    mp3 = out / "Classical_Reasoning_v01_RealHarmony.mp3"
    subprocess.run([
        "ffmpeg","-y","-hide_banner","-loglevel","error",
        "-i",str(wav_path),"-codec:a","libmp3lame","-q:a","2",str(mp3)
    ], check=True)

    summary = {
        "status":"PASS",
        "authority_boundary":"REAL_CLASSICAL_ENGINE_PITCHES__REASONING_DENSITY_ONLY",
        "source_event_count":len(source),
        "filtered_event_count":len(filtered),
        "events_removed":len(source)-len(filtered),
        "new_or_transposed_notes_introduced":False,
        "all_non_timpani_notes_validated_against_bar_chord":True,
        "reasoning_bridge_status":reasoning_report["status"],
        "kick_present":reasoning_report["kick_present"],
        "section_reasoning":{
            k:{
                "energy":v["energy"],
                "density":v["density"],
                "harmony":v["harmony"],
                "transition":v["transition"],
            } for k,v in decisions.items()
        },
        "section_event_counts":{k:len(v) for k,v in by_section.items()},
        "mixer_status":mix_result.get("status"),
        "midi":str(midi_path),
        "wav":str(wav_path),
        "mp3":str(mp3),
    }
    (out / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
