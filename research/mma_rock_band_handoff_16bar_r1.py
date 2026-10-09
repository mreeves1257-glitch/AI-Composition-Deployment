"""Rock Arranger Handoff R1 — external MMA score -> exact existing SFZ roles.

Research-only, isolated from deployed composer. Official MMA 25.05.0 remains
an independent GPL process; this independent bridge *consumes standard MIDI*
and uses only project-written glue plus existing immutable Karoryfer programs.

16 bars: external MMA groove provides section-by-section bass, chord guitar
and timekeeping; a typed arranger transition adds an audible snare sixteenth
roll, descending tom fill and chorus-arrival crash. Compare MMA foundation
against the SAME MMA foundation with explicitly interpreted fill intentions.

This proves translation to real source audio; not proof of musical excellence.
"""
from __future__ import annotations
import argparse, collections, copy, hashlib, json, os
from pathlib import Path
import shutil, subprocess, sys, tarfile, tempfile, wave
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
OUT=ROOT/"research"/"mma_rock_handoff_r1_output"
MMA_URL="https://www.mellowood.ca/mma/mma-bin-25.05.0.tar.gz"
MMA_SHA1="1af05064384c5c7e7d24b163639a414227d3ef6f"
TEMPO=145
BARS=16
PPQ=480
# Exact destinations: each separate recorded drum component gets its own
# source-SFZ program and final independent audio stem.
ROLES={
    "HARMONY":("electric_guitar:RHYTHM_POWER_CHORDS","electric_guitar","RHYTHM_POWER_CHORDS",0),
    "BASS":("electric_bass_guitar","electric_bass_guitar","BASS",1),
    "KICK":("kick_drum_rock","kick_drum_rock","KICK_PULSE",2),
    "SNARE":("snare_drum","snare_drum","SNARE_BACKBEAT",3),
    "HAT":("hi_hat","hi_hat","HI_HAT",4),
    "TOMS":("tom_tom","tom_tom","TOM_FILL",5),
    "CRASH":("crash_cymbal","crash_cymbal","CRASH_ACCENT",6),
}
# These are not interchangeable General MIDI instruments. Open hat is an
# explicitly acknowledged closed-hat approximation in the current kit.
# Tambourine 54 has NO matching selected Rock role: omitted, counted.
GM_DRUM={
    36:("KICK",36,"exact_recorded_kick"),
    38:("SNARE",38,"exact_recorded_snare"),
    46:("HAT",42,"open_hat_to_available_closed_hat_APPROXIMATION"),
}
NAME_ROUTES={"Bass":"BASS","Chord-Clean":"HARMONY"}
# Named high-level instruction language, distinct from note-level MIDI.
INTENTS=(
    {"kind":"SECTION_CHANGE","at_bar":8,"from":"VERSE","to":"CHORUS"},
    {"kind":"SIXTEENTH_SNARE_ROLL","bar":7,"start":2.50,"until":3.25,
     "intensities":[42,55,70,85]},
    {"kind":"DESCENDING_TOM_FILL","bar":7,"beats":[3.50,3.75],
     "pitches":[47,43],"intensities":[88,100]},
    {"kind":"CHORUS_CRASH_ARRIVAL","bar":8,"beat":0.0,"velocity":98},
    {"kind":"SECTION_CHANGE","at_bar":16,"from":"CHORUS","to":"END"},
    {"kind":"SIXTEENTH_SNARE_ROLL","bar":15,"start":2.50,"until":3.25,
     "intensities":[40,57,72,88]},
    {"kind":"DESCENDING_TOM_FILL","bar":15,"beats":[3.50,3.75],
     "pitches":[47,43],"intensities":[89,101]},
)

def need(value,message):
    if not value:raise AssertionError(message)

def sha(path):
    d=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):d.update(part)
    return d.hexdigest()

def get_mma():
    OUT.mkdir(parents=True,exist_ok=True)
    work=OUT/"external_mma_official"
    main=work/"mma-bin-25.05.0"/"mma.py"
    if main.is_file():
        return main
    work.mkdir(parents=True,exist_ok=True)
    archive=work/"mma-official.tar.gz"
    with urlopen(Request(MMA_URL,headers={"User-Agent":"AI-Composer-External-MMA-Research/1.0"}),timeout=50) as r:
        data=r.read(9_000_000)
    need(hashlib.sha1(data).hexdigest()==MMA_SHA1,"UPSTREAM_MMA_CHECKSUM_FAIL")
    archive.write_bytes(data)
    # Reject symlinks, paths outside extraction root, special files.
    with tarfile.open(archive,"r:gz") as f:
        for member in f:
            rel=Path(member.name)
            need(not rel.is_absolute() and ".." not in rel.parts and (member.isfile() or member.isdir() or member.issym() or member.islnk()),
                 "UNSAFE_EXTERNAL_ARCHIVE_ENTRY")
            if member.issym() or member.islnk():
                continue  # External author's symbolic links not required to interpret.
            dest=(work/rel).resolve()
            need(dest.is_relative_to(work.resolve()),"EXTERNAL_ARCHIVE_PATH_ESCAPE")
            if member.isdir():
                dest.mkdir(parents=True,exist_ok=True)
            else:
                need(member.size <5_000_000,"SOURCE_FILE_OVER_SIZE_LIMIT")
                dest.parent.mkdir(parents=True,exist_ok=True)
                source=f.extractfile(member)
                need(source is not None,"SOURCE_ARCHIVE_EXTRACT_ERROR")
                with source, dest.open("wb") as out:
                    shutil.copyfileobj(source,out)
    need(main.is_file(),"MMA_EXECUTABLE_NOT_FOUND")
    return main

def make_song(mma_py):
    source=OUT/"MMA_Rock_16Bar_Two_Sections.mma"
    bars=("Dm","Bb","F","C","Dm","Bb","Gm","A7",
          "Dm","Bb","F","C","Dm","Bb","Gm","A7")
    lines=["// Research passage; no licensed guitar/drum samples included",
           "Tempo 145","Groove BasicRock"]
    for i,chord in enumerate(bars,1):
        if i==9: lines.append("Groove BasicRock4")
        lines.append(f"{i} {chord}")
    source.write_text("\n".join(lines)+"\n")
    midi=OUT/"MMA_Rock_16Bar_Two_Sections.mid"
    env=dict(os.environ);env["PYTHONPATH"]=str(mma_py.parent)
    # Generate the external MMA interpreter's named-style index in isolation.
    index=subprocess.run([sys.executable,str(mma_py),"-G"],cwd=mma_py.parent,
                         capture_output=True,text=True,timeout=80,env=env)
    need(index.returncode==0,"MMA_GROOVE_INDEX_FAILED:"+index.stderr[-600:])
    p=subprocess.run([sys.executable,str(mma_py),"-f",str(midi),str(source)],
                     cwd=mma_py.parent,text=True,capture_output=True,timeout=100,env=env)
    need(p.returncode==0 and midi.is_file(),"MMA_INTERPRETER_FAILED:"+p.stderr[-600:]+p.stdout[-300:])
    return source,midi

def note_event(track,midi,velocity,start,duration,art="interpreted_midi_note"):
    need(track in ROLES,"UNKNOWN_SOURCE_TRACK")
    need(0<=midi<=127 and 1<=velocity<=127 and duration>0 and start>=0 and start<64,
         "UNPLAYABLE_NOTE_FROM_INTERPRETER")
    return {"track_id":track,
            "instrument_id":ROLES[track][1],
            "start_beat":round(start,6),
            "duration_beats":round(min(duration,64-start),6),
            "midi":int(midi),"velocity":int(velocity),"articulation":art}

def split_external_midi(midifile):
    import mido
    mf=mido.MidiFile(midifile)
    need(mf.type==1,"MMA_IS_NOT_MULTITRACK_MIDI")
    need(mf.ticks_per_beat>0,"MMA_BAD_RESOLUTION")
    mapping_report=collections.Counter()
    unsupported=collections.Counter()
    ignored=collections.Counter()
    parts=collections.defaultdict(list)
    for tr in mf.tracks:
        names=[m.name for m in tr if m.type=="track_name"]
        name=names[-1] if names else ""
        enabled=name=="Drum" or name in NAME_ROUTES
        absolute=0
        voices=collections.defaultdict(collections.deque)
        for msg in tr:
            absolute+=msg.time
            if msg.type not in ("note_on","note_off"):
                continue
            ison=msg.type=="note_on" and msg.velocity>0
            isoff=msg.type=="note_off" or (msg.type=="note_on" and msg.velocity==0)
            key=(getattr(msg,"channel",0),int(msg.note))
            if ison:
                voices[key].append((absolute,int(msg.velocity)))
            elif isoff and voices[key]:
                tick,velocity=voices[key].popleft()
                beat=tick/mf.ticks_per_beat
                duration=(absolute-tick)/mf.ticks_per_beat
                if not 0<=beat<64 or duration<=0:continue
                if name=="Drum":
                    if key[0]!=9:
                        raise AssertionError("EXTERNAL_DRUM_NOT_ON_GM_CHANNEL_10")
                    mapping=GM_DRUM.get(int(msg.note))
                    if mapping is None:
                        unsupported[msg.note]+=1
                        continue
                    track,pitch,policy=mapping
                    mapping_report[policy]+=1
                    parts[track].append(note_event(track,pitch,velocity,beat,
                        min(duration,.13),"mma_gm_drum_interpreted"))
                elif name in NAME_ROUTES:
                    track=NAME_ROUTES[name]
                    mapping_report["separate_"+track]+=1
                    parts[track].append(note_event(track,int(msg.note),velocity,beat,
                        max(.10,min(duration,1.15)),"mma_chord_or_bass"))
                else:
                    ignored[name]+=1
    need(all(parts.get(track) for track in ("HARMONY","BASS","KICK","SNARE","HAT")),
         "MMA_REQUIRED_BAND_PART_MISSING")
    need(set(unsupported).issubset({54}),"UNSUPPORTED_MMA_DRUM_KIT_NOT_DOCUMENTED:"+str(unsupported))
    for notes in parts.values():
        notes.sort(key=lambda e:(e["start_beat"],e["midi"]))
    return dict(parts),dict(mapping_report),dict(unsupported),dict(ignored)

def compile_transition_intents(baseline):
    """Local typed intent -> executable recorded-source note compiler.

    All external MMA notes pass through untouched except conflicting snare
    strokes in the intended short fill window; the custom roll and tom series
    are *not* claimed as native Yamaha/Korg/MMA automatic arrangement.
    """
    parts=copy.deepcopy(baseline)
    trace=[]
    for i,intent in enumerate(INTENTS):
        kind=intent["kind"]
        if kind=="SECTION_CHANGE":
            trace.append({"index":i,"intent":kind,"musical_target_bar":intent["at_bar"],
                          "emitted_notes":0,"cross_part_boundary":True})
            continue
        bar=intent["bar"]
        need(bar in (7,8,15),"UNAUTHORIZED_ARRANGEMENT_SECTION")
        added=[]
        if kind=="SIXTEENTH_SNARE_ROLL":
            start=bar*4+intent["start"]
            need(round(intent["until"]-intent["start"],6)==.75 and len(intent["intensities"])==4,
                 "NOT_A_FOUR_STROKE_SIXTEENTH_ROLL")
            # Avoid overlapping the source backbeat exactly under the roll.
            old=parts["SNARE"]
            parts["SNARE"]=[e for e in old if not (start-.0001<=e["start_beat"]<=start+.75+.0001)]
            for j,vel in enumerate(intent["intensities"]):
                added.append(note_event("SNARE",38,vel,start+j*.25,.09,"interpreted_snare_16th_roll"))
        elif kind=="DESCENDING_TOM_FILL":
            need(list(intent["pitches"])==[47,43],"UNAUTHORIZED_TOM_MAPPING")
            for beat,pitch,vel in zip(intent["beats"],intent["pitches"],intent["intensities"]):
                added.append(note_event("TOMS",pitch,vel,bar*4+beat,.1,"interpreted_tom_descent"))
        elif kind=="CHORUS_CRASH_ARRIVAL":
            need(bar==8 and intent["beat"]==0.0,"CHORUS_ARRIVAL_NOT_ALIGNED")
            added.append(note_event("CRASH",49,intent["velocity"],bar*4,.20,"interpreted_section_crash"))
            need(any(abs(e["start_beat"]-(bar*4))<.05 for e in parts["BASS"]),
                 "BASS_NOT_CONNECTED_TO_CHORUS_ARRIVAL")
            need(any(abs(e["start_beat"]-(bar*4))<.05 for e in parts["HARMONY"]),
                 "GUITAR_NOT_CONNECTED_TO_CHORUS_ARRIVAL")
        else:raise AssertionError("UNRECOGNIZED_MUSICAL_INTENT")
        for event in added:parts.setdefault(event["track_id"],[]).append(event)
        trace.append({"index":i,"intent":kind,"section_bar":bar,
                      "emitted_notes":len(added),"output_tracks":sorted({x["track_id"] for x in added}),
                      "note_onsets":[e["start_beat"] for e in added]})
    for events in parts.values():events.sort(key=lambda e:(e["start_beat"],e["midi"]))
    need(len([e for e in parts.get("TOMS",[])])==4,"TOM_FILL_NOT_INTERPRETED")
    need(len(parts.get("CRASH",[]))==1,"CHORUS_NOT_ACCENTED")
    return parts,trace

def midi_from_score(notes,resource,outfile):
    import mido
    seq=[]
    initial=resource.get("midi_mapping",{}).get("initial_cc",{})
    for c,v in initial.items():
        c=int(c);v=int(v);need(0<=c<=127 and 0<=v<=127,"INVALID_SOURCE_MIDI_CC")
        seq.append((0,-2,mido.Message("control_change",channel=0,control=c,value=v,time=0)))
    for note in notes:
        on=int(round(note["start_beat"]*PPQ))
        off=int(round((note["start_beat"]+note["duration_beats"])*PPQ))
        need(off>on,"ZERO_LENGTH_NOTE")
        seq.append((on,1,mido.Message("note_on",channel=0,note=note["midi"],velocity=note["velocity"])))
        seq.append((off,0,mido.Message("note_off",channel=0,note=note["midi"],velocity=0)))
    seq.sort(key=lambda t:(t[0],t[1]))
    track=mido.MidiTrack()
    track.append(mido.MetaMessage("set_tempo",tempo=round(60e6/TEMPO),time=0))
    prev=0
    for tick,_,msg in seq:
        msg.time=tick-prev;prev=tick;track.append(msg)
    track.append(mido.MetaMessage("end_of_track",time=0))
    out=mido.MidiFile(type=0,ticks_per_beat=PPQ);out.tracks.append(track)
    out.save(outfile)
    return sha(outfile)

def render(parts,version):
    from sfz_renderer_adapter import render_midi
    from genre_styles.Rock.rock_balance_contract import apply_rock_balance
    from genre_styles.Rock.recorded_subkick import prepare_recorded_subkick
    runtime_reg=RUNTIME/"target_registry.json"
    bindings=json.loads(runtime_reg.read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    os.environ["AI_COMP_RESOURCE_BANK"]=str(RUNTIME/"sound_resources")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(ROOT/".composer_tools"/"bin"/"sfizz_render")
    outdir=OUT/version;outdir.mkdir(parents=True,exist_ok=True)
    notes=[n for events in parts.values() for n in events]
    need(notes,"EMPTY_ROCK_INTERPRETER_SCORE")
    engine={"genre":"ROCK","modules":{
        "theory":{"composition_fingerprint":"MMA_OFFICIAL_PLUS_TYPED_ROCK_16BAR_"+version},
        "instrument":{"profiles":[]},"target":{"resolved_resources":[]},
        "performance":{"events":notes}}}
    stems=[]
    for track in ROLES:
        if not parts.get(track):continue
        key,instrument,role,_=ROLES[track]
        resource=copy.deepcopy(bindings[key])
        need(resource["resource_type"]=="SFZ_SAMPLE_LIBRARY","NON_RECORDED_SOURCE")
        engine["modules"]["instrument"]["profiles"].append({
           "track_id":track,"instrument_id":instrument,"role":role})
        engine["modules"]["target"]["resolved_resources"].append({
           "track_id":track,"instrument_id":instrument,"resource":resource})
        midi_file=outdir/(track.lower()+".mid")
        midi_hash=midi_from_score(parts[track],resource,midi_file)
        wav=outdir/(track.lower()+".wav")
        result=render_midi(resource,midi_file,wav,sample_rate=44100)
        need(result.get("audio_rendered") and wav.is_file(),"SFZ_RECORDED_SOURCE_FAILED:"+track)
        stems.append({"track_id":track,"instrument_id":instrument,"wav_path":str(wav)})
        print("SOURCE_TRACK_RENDERED",version,track,"notes",len(parts[track]),
              "library",resource["resource_id"],"midi_sha256",midi_hash,flush=True)
    need(len(stems)>=5,"INSUFFICIENT_REAL_BAND_STEMS")
    engine=apply_rock_balance(engine)
    prepared,with_sub=prepare_recorded_subkick(engine,stems,outdir)
    need(len(with_sub)==len(stems)+1 and with_sub[-1]["track_id"]=="SUBKICK",
         "ORIGINAL_RECORDED_SUBKICK_MISSING")
    job=outdir/"standalone_final_mixer_job.json"
    job.write_text(json.dumps({"engine_result":prepared,"stems":with_sub}))
    proc=subprocess.run([sys.executable,str(RUNTIME/"standalone_3d_mixer.py"),str(job),
                         str(outdir/"final_audio")],capture_output=True,text=True,timeout=180)
    need(proc.returncode==0,"ORIGINAL_3D_MIXER_ERROR:"+proc.stderr[-1000:]+proc.stdout[-500:])
    obj=json.loads(proc.stdout.strip())
    need(obj.get("status")=="AUDIO_RENDER_PASS","3D_MIXER_FAILED:"+repr(obj))
    final=Path(obj["wav_path"])
    with wave.open(str(final),"rb") as f:
        dur=f.getnframes()/f.getframerate()
        spec=(f.getframerate(),f.getnchannels(),f.getsampwidth())
    need(spec==(44100,2,2) and 26<dur<34,"INVALID_16BAR_ROCK_AUDIO")
    final_out=OUT/("MMA_Rock_16Bar_Foundation_3D.wav" if version=="foundation" else
                   "MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav")
    shutil.copyfile(final,final_out)
    report={"status":"REAL_SFZ_AND_ORIGINAL_3D_PASS","version":version,
            "tempo_bpm":TEMPO,"song_bars":BARS,"sample_rate":44100,
            "final_duration_s":round(dur,3),"stems":[x["track_id"] for x in with_sub],
            "source_sample_count":len(stems),"note_counts":{t:len(parts[t]) for t in parts},
            "final_name":final_out.name,"final_sha256":sha(final_out),
            "live_composer_changed":False,"recorded_samples_modified":False}
    (outdir/"REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MMA_ROCK_ORIGINAL_3D_STEREO_PASS",json.dumps(report),flush=True)
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mma_path=get_mma()
    script,midi=make_song(mma_path)
    baseline,mapping,unmapped,ignored=split_external_midi(midi)
    candidate,trace=compile_transition_intents(baseline)
    same=lambda p:{key:p[key] for key in p if key not in ("SNARE","TOMS","CRASH")}
    need(same(baseline)==same(candidate),"OTHER_BAND_MIDI_NOT_PROTECTED")
    need(all(len(candidate[k])>=len(baseline.get(k,[]))-2 for k in ("SNARE","HAT","BASS","KICK") if k in candidate),"BAND_LOST")
    original=render(baseline,"foundation")
    filled=render(candidate,"interpreted_fill")
    summary={
        "status":"REAL_EXTERNAL_MUSICAL_LANGUAGE_INTERPRETED_THROUGH_ORIGINAL_ROCK_INSTRUMENTS",
        "official_external_interpreter":"MMA_25.05.0_SHA1_VERIFIED",
        "input_score":script.name,"external_midi":midi.name,
        "original_source_compiler_integrated":False,
        "research_boundary":"external_MMA_MIDI_as_data_then_independent_typed_arranger_instruction_compiler",
        "originals_unmodified":True,"sample_libs_unchanged":True,
        "gm_drum_remap":GM_DRUM,"unmapped_external_drum_notes":unmapped,
        "ignored_external_extra_guitars":ignored,
        "mapped_sources":mapping,
        "declared_intents":INTENTS,
        "interpretation_trace":trace,
        "other_tracks_identical_before_audio":True,
        "reference_audio":original,
        "interpreted_audio":filled,
        "audibility_or_realism_artistically_approved":False,
        "license_notice":"MMA runs as separate GPL process; no GPL source copied into proprietary Composer runtime.",
        "deployed":False,
    }
    (OUT/"HANDOFF_PROOF.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("EXTERNAL_MMA_TO_RECORDED_ROCK_BRIDGE_PASS",json.dumps({
        "external_midi_tracks":"drums/bass/guitar",
        "recorded_stem_tracks":filled["stems"],
        "verified_typed_intents":len(trace),
        "snare_sixteenth_rolls":2,"tom_fills":2,"chorus_crashes":1,
        "gm54_unsupported_count":unmapped.get(54,0),
        "same_3D_as_original":True,"originals_unmodified":True
    }),flush=True)

if __name__=="__main__":
    main()
