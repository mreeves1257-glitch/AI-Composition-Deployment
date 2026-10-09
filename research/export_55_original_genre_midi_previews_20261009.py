"""Export original 55 genre source-pattern seeds into standard Type-1 MIDI.

Research-only downloadable material. Uses Mido 1.3.3 (MIT licensed).
One independent MIDI track per authored role. Never substitutes General MIDI
instrument sounds for the unverified real SFZ programs, modifies source banks,
or promotes these seven-bar sketches into full songs. NO audio is produced.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import zipfile

try:
    import mido
except ImportError as exc:
    raise RuntimeError("MIDO_NOT_INSTALLED: pip install mido==1.3.3") from exc

PROJECT = Path(__file__).resolve().parents[1]
TICKS_PER_BEAT=480
MIDI_PACKAGE_SCHEMA="AI_COMP_55_ORIGINAL_SEVEN_BAR_MIDI_PREVIEW_V1"

import sys
sys.path.insert(0,str(PROJECT/"composer_overrides"))
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.shared_interpreter_router import listed_genres


def _ticks(value) -> int:
    ticks=Fraction(str(value))*TICKS_PER_BEAT
    if ticks.denominator!=1:
        raise ValueError("NON_INTEGER_MIDI_CLOCK:"+str(value))
    if ticks<0:
        raise ValueError("NEGATIVE_MIDI_CLOCK")
    return int(ticks)


def _name_safe(text: str) -> str:
    safe=re.sub(r"[^A-Za-z0-9_-]+","_",str(text)).strip("_")
    if not safe:raise ValueError("INVALID_GENRE_FILE_NAME")
    return safe


def export_genre_midi(plan: dict, dest: Path) -> dict:
    """Writes Type-1 SMF with role-isolated note events, not a rendered WAV."""
    if plan.get("recorded_audio_authorized") is not False:
        raise ValueError("MIDI_PREVIEW_MUST_NOT_AUTHORIZE_AUDIO")
    info=plan["source_pattern_contract"]
    if info["musical_audition_approved"] or info["production_enabled"]:
        raise ValueError("INVALID_UNAUDITIONED_PATTERN_SCOPE")
    genre=plan["genre"]
    notes=plan["symbolic_note_events"]
    if not notes: raise ValueError("EMPTY_MUSIC")
    meter=plan["meter"]
    numerator,denominator=[int(x) for x in meter.split("/")]
    tempo=int(round(mido.bpm2tempo(plan["tempo_bpm"])))
    midi=mido.MidiFile(type=1,ticks_per_beat=TICKS_PER_BEAT)
    conductor=mido.MidiTrack()
    conductor.append(mido.MetaMessage("track_name",name="CONDUCTOR_"+genre,time=0))
    conductor.append(mido.MetaMessage("text",
        text="ORIGINAL PROJECT SYMBOLIC SOURCE SEED; 7 bars; NOT AUDITIONED; NO SFZ AUDIO APPROVAL",time=0))
    conductor.append(mido.MetaMessage("set_tempo",tempo=tempo,time=0))
    conductor.append(mido.MetaMessage("time_signature",numerator=numerator,
        denominator=denominator,time=0))
    conductor.append(mido.MetaMessage("end_of_track",time=0))
    midi.tracks.append(conductor)
    grouped=defaultdict(list)
    for n in notes:
        if n["status"]!="SYMBOLIC_ONLY" or not 0<=int(n["midi"])<=127:
            raise ValueError("UNVERIFIED_OR_INVALID_NOTE")
        start=_ticks(n["start_beat"]);end=start+_ticks(n["duration_beats"])
        if end<=start:raise ValueError("ZERO_DURATION_NOTE")
        grouped[n["role"]].append((start,end,n))
    if len(grouped)>15: raise ValueError("MIDI1_TOO_MANY_SIMULTANEOUS_ROLE_CHANNELS")
    by_role={}
    all_events=0
    channels=[i for i in range(16) if i!=9]
    for i,role in enumerate(sorted(grouped)):
        channel=channels[i]
        source=grouped[role]
        track=mido.MidiTrack()
        track.append(mido.MetaMessage("track_name",name=role,time=0))
        # Role identity is descriptive; no GM program change because original
        # recorded SFZ identity and pitch zones have not yet been audio-verified.
        track.append(mido.MetaMessage("text",
            text="TRACK_ROLE="+role+"; SFZ_SOURCE_AND_NOTE_ZONES_NOT_VERIFIED; UNRENDERED",time=0))
        events=[]
        for start,end,n in source:
            events.append((start,1,mido.Message("note_on",note=n["midi"],
                velocity=n["velocity"],channel=channel,time=0)))
            events.append((end,0,mido.Message("note_off",note=n["midi"],
                velocity=0,channel=channel,time=0)))
        events.sort(key=lambda x:(x[0],x[1],x[2].note))
        tick=0
        for at,_,event in events:
            event.time=at-tick
            track.append(event);tick=at
        track.append(mido.MetaMessage("end_of_track",time=0))
        midi.tracks.append(track)
        by_role[role]={"notes":len(source),"midi_channel":channel,
                        "source_instrument_verified":False}
        all_events+=len(source)
    dest.parent.mkdir(parents=True,exist_ok=True)
    midi.save(str(dest))
    check=mido.MidiFile(str(dest))
    if check.type!=1 or len(check.tracks)!=len(grouped)+1:
        raise ValueError("MIDI_ROUNDTRIP_FAILED")
    size=dest.stat().st_size
    return {"genre":genre,"profile_id":plan["genre_profile_id"],
        "family":plan["family"],"midi_file":dest.name,
        "meter":meter,"tempo_bpm":plan["tempo_bpm"],
        "role_count":len(grouped),"source_roles":by_role,
        "note_event_count":all_events,
        "file_bytes":size,
        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
        "audio_rendered":False,"instrument_sample_programs_verified":False}


def export_all(destination: Path) -> dict:
    destination=Path(destination)
    midis=destination/"midi"
    midis.mkdir(parents=True,exist_ok=True)
    all_genres=listed_genres()
    if len(all_genres)!=55: raise ValueError("GENRE_INDEX_CHANGED")
    result=[]
    seen_names=set()
    for genre in all_genres:
        plan=compile_original_source_seed(genre)
        index=len(result)+1
        out=f"{index:02d}_{_name_safe(genre)}.mid"
        if out in seen_names:raise ValueError("DUPLICATE_FILENAME")
        seen_names.add(out)
        result.append(export_genre_midi(plan,midis/out))
    if len(result)!=55:raise ValueError("MISSING_GENRES")
    manifest={"schema":MIDI_PACKAGE_SCHEMA,
        "research_only":True,"created_from_project_original_patterns":True,
        "audio_included":False,"audition_verified":False,
        "midi_library":{"name":"Mido","version":"1.3.3","license":"MIT",
                         "homepage":"https://github.com/mido/mido"},
        "genre_count":55,"total_note_events":sum(x["note_event_count"] for x in result),
        "all_roles_independent":True,
        "all_55_source_patterns_remain_original_unmodified":True,
        "no_audio_or_render_service_changed":True,
        "genres":result}
    (destination/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (destination/"README.txt").write_text(
        "AI Composer Original Genre Pattern MIDI Preview — 2026-10-09\n\n"
        "55 seven-bar original symbolic note demonstrations. NOT complete songs.\n"
        "Each instrument role has its own standard MIDI track. MIDI contains\n"
        "NO real SFZ samples, so generic MIDI playback on a phone will NOT\n"
        "sound like the authentic recorded instruments in the Composer.\n"
        "Do NOT replace the Composer's existing note events with these files.\n"
        "No samples, Yamaha/Korg styles, or proprietary arranger data included.\n"
        "The existing live Plug, Control Panel and separate 3D mixer are unchanged.\n\n"
        "For every genre, see MANIFEST.json for authoring source and note counts.\n"
    )
    archive=destination/"55_original_genre_midi_previews_2026-10-09.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=8) as z:
        for file in sorted(midis.glob("*.mid")):
            z.write(file,"midi/"+file.name)
        z.write(destination/"MANIFEST.json","MANIFEST.json")
        z.write(destination/"README.txt","README.txt")
    manifest["archive"]=archive.name
    manifest["archive_bytes"]=archive.stat().st_size
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=export_all(args.output)
    print("ALL_55_SEPARATE_MIDI_PREVIEWS_EXPORTED",
          json.dumps({"genres":result["genre_count"],"notes":result["total_note_events"],
                      "bytes":result["archive_bytes"],"archive":result["archive"],
                      "live_audio_enabled":False}))
