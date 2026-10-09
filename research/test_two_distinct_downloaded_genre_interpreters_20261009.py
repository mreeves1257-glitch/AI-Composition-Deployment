"""Prove genuine external style-program output enters its OWN genre interpreter.

Public GPL MMA remains a standalone program. Project-owned individual
Jazz Waltz and Salsa translators produce typed score events, NOT sampled WAVs.
This preserves all original audio, the seven-stage Composer, and 3D mixer.
"""
from __future__ import annotations
from pathlib import Path
import json,sys,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.Jazz.jazz_waltz_genre_interpreter import (
    interpret_genre as jazz_waltz)
from genre_styles.Latin.salsa_genre_interpreter import (
    interpret_genre as salsa)
from genre_styles.external_style_midi_reader import StyleMidiInterfaceError
from genre_styles.genre_owned_interpreter_dispatch import dispatch_stage3_to4_genre_owned

OUT=ROOT/"research_artifacts"/"two_unique_genre_interpreter_proofs_20261009"

def must(flag,why):
    if not flag:raise AssertionError(why)

def run(jazz_path,salsa_path):
    j=jazz_waltz(jazz_path,selected_genre="Jazz Waltz")
    s=salsa(salsa_path,selected_genre="Salsa")
    jazz_stage3={"status":"PASS","palette":["double_bass","piano","drums"],
                 "meter":"3/4","tempo_bpm":156}
    salsa_stage3={"status":"PASS","palette":["bass","piano","latin percussion"],
                  "meter":"4/4","tempo_bpm":190}
    jazz_handoff=dispatch_stage3_to4_genre_owned(
        "Jazz Waltz",source_midi_path=jazz_path,
        original_stage3_result=jazz_stage3)
    salsa_handoff=dispatch_stage3_to4_genre_owned(
        "Salsa",source_midi_path=salsa_path,
        original_stage3_result=salsa_stage3)
    must(jazz_handoff["musical_event_count"]==j["event_count"] and
         jazz_handoff["stage4_candidate_events"]==j["actual_music_events"] and
         jazz_handoff["stage3_clock_verified"]["meter"]=="3/4",
         "JAZZ_WALTZ_NOT_DIRECTED_FROM_OWN_INTERPRETER")
    must(salsa_handoff["musical_event_count"]==s["event_count"] and
         salsa_handoff["stage4_candidate_events"]==s["actual_music_events"] and
         salsa_handoff["stage3_clock_verified"]["meter"]=="4/4",
         "SALSA_NOT_DIRECTED_FROM_OWN_INTERPRETER")
    waiting=dispatch_stage3_to4_genre_owned(
        "Swing",source_midi_path=jazz_path,
        original_stage3_result={"status":"PASS","palette":["piano"],
                                "meter":"4/4","tempo_bpm":160})
    must(waiting["status"]=="BLOCKED_GENRE_OWNED_BACKEND_NOT_YET_IMPLEMENTED" and
         waiting["musical_event_count"]==0,
         "NONIMPLEMENTED_GENRE_FAKED_A_SONG")
    for name,stage3,midi in [
        ("Jazz Waltz",{"status":"PASS","palette":["double_bass"],"meter":"4/4","tempo_bpm":156},jazz_path),
        ("Salsa",{"status":"PASS","palette":["piano"],"meter":"3/4","tempo_bpm":190},salsa_path)]:
        try:dispatch_stage3_to4_genre_owned(
            name,source_midi_path=midi,original_stage3_result=stage3)
        except StyleMidiInterfaceError as e:
            must("STAGE3_CLOCK_MISMATCH" in str(e),
                 "WRONG_INTERPRETER_FAILURE_REASON")
        else:raise AssertionError("WRONG_GENRE_CLOCK_ACCEPTED:"+name)
    must(j["genre"]=="Jazz Waltz" and j["meter"]=="3/4" and
         j["tempo_bpm"]==156 and j["bars"]==8,
         "JAZZ_WALTZ_INTERPRETER_NOT_3_4")
    must(s["genre"]=="Salsa" and s["meter"]=="4/4" and
         s["tempo_bpm"]==190 and s["bars"]==8,
         "SALSA_INTERPRETER_NOT_4_4")
    must(j["event_count"]>=150 and s["event_count"]>=250,
         "STYLE_PROGRAM_DID_NOT_GENERATE_REAL_ENOUGH_EVENTS")
    must(j["event_count"]!=s["event_count"] and
         j["source_track_roles"]!=s["source_track_roles"],
         "TWO_STYLE_PROGRAMS_SHOULD_NOT_HAVE_IDENTICAL_PATTERNS")
    must(j["source_percussion_note_classes"]["RIDE_CYMBAL"]>0 and
         j["jazz_3_4_walking_bass_and_ride_verified"],
         "JAZZ_WALTZ_RIDE_AND_BASS_NOT_PERFORMED")
    must(s["latin_percussion_roles"]["CLAVES"]>0 and
         s["latin_percussion_roles"]["LOW_BONGO"]>0 and
         s["two_bar_clave_periodicity_observed"] and
         not s["exact_2_3_vs_3_2_clave_orientation_verified"],
         "SALSA_CLAVE_SOURCE_CYCLE_NOT_DISTINCT")
    for label,score in (("jazz_waltz",j),("salsa",s)):
        must(score["distinct_style_language_executed"] is True and
             score["audio_render_authorized"] is False and
             score["production_enabled"] is False and
             score["native_recorded_programs_mapped"] is False and
             score["live_composer_events_replaced"] is False,
             "FALSE_CLAIM_SOURCE_PROGRAM_IS_RECORDED_MUSIC:"+label)
        must(all(e["real_SFZ_sample_program_verified"] is False and
                 e["stage4_status"]=="INTERPRETED_SOURCE_NOTE_NOT_AUTHORIZED_FOR_AUDIO"
                 for e in score["actual_music_events"]),
             "SOURCE_SAMPLE_MAPPING_FABRICATED:"+label)
    def rejected(f,source,expected,wrong):
        try:f(source,selected_genre=wrong)
        except StyleMidiInterfaceError as e:
            must("CROSS_GENRE_FORBIDDEN" in str(e),
                 "CROSS_GENRE_REJECTED_FOR_WRONG_REASON")
        else:raise AssertionError("CROSS_GENRE_STYLE_FALLBACK_ALLOWED:"+expected)
    rejected(jazz_waltz,jazz_path,"Jazz Waltz","Salsa")
    rejected(salsa,salsa_path,"Salsa","Jazz Waltz")
    try:jazz_waltz(salsa_path)
    except StyleMidiInterfaceError as e:must("WRONG_GENRE_METER" in str(e),"JAZZ_METER_CROSSOVER_GUARD_WRONG")
    else:raise AssertionError("SALSA_ROUTED_AS_JAZZ_WALTZ")
    try:salsa(jazz_path)
    except StyleMidiInterfaceError as e:must("WRONG_GENRE_METER" in str(e),"SALSA_METER_CROSSOVER_GUARD_WRONG")
    else:raise AssertionError("JAZZ_ROUTED_AS_SALSA")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"Jazz_Waltz_8_Bar_Interpreted_Stage4_Source_Notes.json").write_text(json.dumps(j,indent=2)+"\n")
    (OUT/"Salsa_8_Bar_Interpreted_Stage4_Source_Notes.json").write_text(json.dumps(s,indent=2)+"\n")
    evidence={"status":"GENRE_OWNED_INTERPRETER_EXECUTION_VERIFIED_NOT_AUDIO_APPROVED",
          "separately_licensed_software":"OFFICIAL_MMA_25.05.0_GPLv2",
          "original_generated_style_files":["lib/stdlib/jazzwaltz.mma","lib/stdlib/salsa.mma"],
          "jazz":{"tempo":156,"meter":"3/4","events":j["event_count"],
                  "tracks":j["source_track_roles"]},
          "salsa":{"tempo":190,"meter":"4/4","events":s["event_count"],
                   "tracks":s["source_track_roles"],
                   "percussion":s["latin_percussion_roles"]},
          "per_genre_music_interpretation_engines_functional":True,
          "stage3_to4_genre_dispatch_worked_without_generic_fallback":True,
          "real_SFZ_programs_installed_or_verified_for_these_genres":False,
          "genre_audition_approval":False,"live_composer_activated":False,
          "original_rock_interpreter_or_frozen_hard_copy_changed":False}
    (OUT/"PROOF_MANIFEST.json").write_text(json.dumps(evidence,indent=2)+"\n")
    (OUT/"README.txt").write_text(
       "JAZZ WALTZ and SALSA: 2 distinct independently executing musical interpreters\n"
       "from official separately licensed MMA style programs. These are typed\n"
       "source MIDI events. They are NOT mapped to native recorded SFZ programs,\n"
       "are NOT finished audio, and are NOT activated in the live Composer.\n"
       "3/4 Jazz ride/walking bass MUST NOT become 4/4 Salsa/clave;\n"
       "Latin claves/guiro/cowbell/bongo are NOT Rock drums. License audit\n"
       "and source sound mapping remain required before any audio rendering.\n")
    archive=OUT.parent/"TWO_ACTUAL_GENRE_SPECIFIC_INTERPRETERS_JAZZ_WALTZ_SALSA_2026-10-09.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.iterdir()):
            z.write(f,f.name)
    must(archive.stat().st_size>1000,"EMPTY_PROOF_ARCHIVE")
    print("TWO_ACTUAL_DISTINCT_GENRE_MUSICAL_INTERPRETERS_PASS",
          json.dumps({**evidence,"bytes":archive.stat().st_size},sort_keys=True))

def prove_original_composer_to_mma_only(mma_home, *, isolated_wurlitzer_audio=False):
    """ONE selected genre: original Composer -> standalone MMA -> MIDI -> its interpreter.

    No Rock execution; no sampled sound; no changes to imported or live files.
    """
    import tempfile
    from genre_styles.genre_owned_interpreter_dispatch import compose_to_original_mma
    from genre_styles.source_pattern_library import read_pack

    source, _ = read_pack("Jazz Waltz")
    # Seven authoritative source chords plus the eighth-bar final cadence
    # already used in the preserved Jazz Waltz MMA proof procedure.
    authored_chords = [c["symbol"] for c in source["chords"]]
    must(len(authored_chords) == 7, "SOURCE_CHORDS_CHANGED")
    eighth_bar_cadence = "Cmaj7"
    chord_bars = authored_chords + [eighth_bar_cadence]
    stage3 = {
        "status": "PASS",
        "palette": ["double_bass", "electric_piano", "flute", "brush_drums"],
        "meter": "3/4", "tempo_bpm": 156,
    }
    structure = {
        "genre": "Jazz Waltz", "meter": "3/4",
        "tempo_bpm": 156, "chord_bars": chord_bars,
    }
    mma_home = Path(mma_home)
    originals = [
        mma_home / "mma.py",
        mma_home / "lib" / "stdlib" / "jazzwaltz.mma",
    ]
    must(all(p.is_file() for p in originals), "EXTERNAL_MMA_ORIGINAL_MISSING")
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    with tempfile.TemporaryDirectory(prefix="composer_to_mma_proof_") as output:
        # Use MMA's actual groove, compiled via the documented original CLI.
        result = compose_to_original_mma(
            "Jazz Waltz",
            composer_structure=structure,
            original_stage3_result=stage3,
            selected_groove="JazzWaltz",
            external_mma_home=mma_home,
            isolated_output_root=output,
        )
        must(result["status"] ==
             "COMPOSER_TO_UNMODIFIED_MMA_TO_TYPE1_MIDI_CONFIRMED" and
             result["midi_note_events"] >= 150 and
             result["standard_midi_type"] == 1 and
             result["existing_genre_interpreter_received_midi"] is True and
             result["original_composer_chord_bars"] == len(chord_bars) and
             result["recorded_sfz_programs_verified"] is False and
             result["live_composer_activated"] is False and
             result["finished_audio_rendered"] is False,
             "COMPOSER_TO_MMA_TO_OWN_INTERPRETER_NOT_VERIFIED")
        midi = Path(result["isolated_midi_output"])
        song = Path(result["isolated_song_input"])
        must(midi.read_bytes()[:4] == b"MThd" and
             f"Groove JazzWaltz" in song.read_text() and
             all(f"{i} {chord}" in song.read_text()
                 for i, chord in enumerate(chord_bars, 1)),
             "COMPOSER_CHORDS_NOT_DELIVERED_TO_ORIGINAL_MMA")
        for changed, badgroove, badchords in [
            ({**structure, "tempo_bpm": 170}, "JazzWaltz", chord_bars),
            (structure, "BasicRock", chord_bars),
            (structure, "JazzWaltz", ["Dm7", "Groove BasicRock"]),
        ]:
            try:
                compose_to_original_mma(
                    "Jazz Waltz",
                    composer_structure={**changed, "chord_bars": badchords},
                    original_stage3_result=stage3,
                    selected_groove=badgroove,
                    external_mma_home=mma_home,
                    isolated_output_root=output,
                )
            except Exception as e:
                must("COMPOSER_MMA" in str(e),
                     "WRONG_HANDOFF_SAFETY_REJECTION:" + str(e)[:200])
            else:
                raise AssertionError("UNAUTHORIZED_GENRE_INPUT_ACCEPTED")
        from genre_styles.genre_owned_interpreter_dispatch import (
            connect_selected_genre_components,
        )
        # A genuine preexisting Composer event stays absolutely authoritative.
        original_events = [{
            "track_id":"ELECTRIC_PIANO","instrument_id":"electric_piano",
            "start_beat":0.0,"duration_beats":1.0,"midi":60,"velocity":88,
        }]
        unchanged = json.dumps(original_events, sort_keys=True)
        receipt = connect_selected_genre_components(
            "Jazz Waltz",
            original_stage3_result=stage3,
            original_composer_events=original_events,
            source_midi_path=midi,
        )
        handoff = receipt["interpreter_to_original_stage4"]
        print("MIDI_TO_STAGE4_DIAGNOSTIC", json.dumps({
            "mma_generated":result["midi_note_events"],
            "interpreter_received":receipt["stage3_to_interpreter"],
            "stage4":handoff,
            "blockers":receipt["connection_blockers"],
        }, sort_keys=True), flush=True)
        # MMA's own Rskip/SeqRnd variation changes note counts between
        # independent executions. Test faithful accounting, not a fixed count.
        must(receipt["stage3_to_interpreter"]["musical_event_count"] ==
             result["midi_note_events"] and
             handoff["candidate_event_count"] > 0 and
             handoff["source_midi_event_count"] == result["midi_note_events"] and
             handoff["blocked_source_note_count"] > 0 and
             handoff["candidate_event_count"] +
             handoff["blocked_source_note_count"] == result["midi_note_events"],
             "SOURCE_MIDI_EVENTS_LOST_OR_FAKED")
        must(receipt["original_event_list_unchanged"] is True and
             receipt["audio_render_authorized"] is False and
             receipt["live_composer_events_replaced"] is False and
             json.dumps(original_events, sort_keys=True) == unchanged,
             "ORIGINAL_LIVE_COMPOSER_EVENTS_UNEXPECTEDLY_CHANGED")
        must(handoff["unfilled_original_genre_tracks"] and
             "FLUTE" in handoff["unfilled_original_genre_tracks"] and
             "MMA_SOURCE_NOT_FULLY_MAPPED_TO_ORIGINAL_GENRE_TRACKS" in
             receipt["connection_blockers"],
             "UNMAPPED_ORIGINAL_INSTRUMENTS_NOT_PROTECTED")
        # Reuse precisely the saved original full-genre sound map; no rewritten
        # percussion bank, style, original instrument or synthetic substitute.
        import json as _json
        from genre_styles.source_pattern_composer_handoff import (
            prepare_external_midi_composer_handoff,
        )
        mapfile = _json.loads((ROOT /
            "composer_overrides/genre_styles/Jazz/SOURCE_RESOURCE_BINDINGS_R1.json"
        ).read_text())
        profilefile = _json.loads((ROOT /
            "composer_overrides/genre_styles/Jazz/profile.json"
        ).read_text())
        source_notes = dispatch_stage3_to4_genre_owned(
            "Jazz Waltz", source_midi_path=midi,
            original_stage3_result=stage3,
        )
        candidate_receipt = prepare_external_midi_composer_handoff(
            source_notes,
            original_genre_profile=profilefile["profiles"]["Jazz Waltz"],
            recorded_full_track_map=mapfile[
                "full_genre_track_sound_maps"]["Jazz Waltz"],
            original_stage3_result=stage3,
            existing_events=original_events,
        )
        sound_candidates = candidate_receipt["candidate_stage4_events"]
        must(len(sound_candidates) == handoff["candidate_event_count"] and
             sound_candidates and
             all(event["track_id"] == "ELECTRIC_PIANO" and
                 event["instrument_id"] == "electric_piano" and
                 event["resource_id"] == "GREG_SULLIVAN_E_PIANOS" and
                 event["preferred_mapping"] ==
                 "Wurlitzer EP200/composer-wurlitzer.sfz" and
                 event["audit_status"] ==
                 "REHEARSAL_REFERENCE_ONLY_ORIGINAL_SFZ_NOT_PREFLIGHTED"
                 for event in sound_candidates),
             "WRONG_OR_SUBSTITUTED_ORIGINAL_RECORDED_SOUND_CANDIDATE")
        must(any(n["reason"] == "MMA_INSTRUMENT_NOT_IN_ORIGINAL_SELECTED_TRACKS"
                 for n in candidate_receipt["blocked_note_details"]) and
             any(n["reason"] ==
                 "ORIGINAL_TRACK_EXACT_RECORDED_PROGRAM_NOT_VERIFIED"
                 for n in candidate_receipt["blocked_note_details"]) and
             candidate_receipt["individual_stems_verified"] is False and
             candidate_receipt["audio_render_authorized"] is False,
             "UNVERIFIED_MMA_INSTRUMENT_WAS_SILENTLY_REPLACED")
        if isolated_wurlitzer_audio:
            prove_original_wurlitzer_program_wav(
                candidate_receipt, source_midi_sha256=result["source_midi_sha256"],
                tempo_bpm=stage3["tempo_bpm"],
            )
        print("MMA_MIDI_TO_ORIGINAL_COMPOSER_STAGE4_IDENTITIES_PASS",
              json.dumps({
                  "genre":"Jazz Waltz",
                  "MMA_midi_notes":result["midi_note_events"],
                  "exact_recorded_program_reference_notes":len(sound_candidates),
                  "blocked_notes":handoff["blocked_source_note_count"],
                  "only_reference_track":"ELECTRIC_PIANO",
                  "original_tracks_missing_midi":
                      handoff["unfilled_original_genre_tracks"],
                  "existing_composer_events_unchanged":True,
                  "full_song_audio_ready":False,
                  "live_activated":False,
              }, sort_keys=True), flush=True)
        print("COMPOSER_TO_ORIGINAL_MMA_TO_TYPE1_MIDI_HANDOFF_PASS",
              json.dumps({k: result[k] for k in (
                  "genre", "style_groove", "standard_midi_type",
                  "midi_note_events", "existing_genre_interpreter_received_midi",
                  "original_program_files_untouched", "live_composer_activated",
                  "finished_audio_rendered",
              )}, sort_keys=True), flush=True)
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    must(before == after, "EXTERNAL_ARRANGER_PROGRAM_OR_STYLE_CHANGED")



def prove_original_wurlitzer_program_wav(candidate_receipt, *,
                                        source_midi_sha256, tempo_bpm):
    """Isolated real recorded-piano audition of actual MMA Stage-4 candidates.

    Pinned original EP200 audio/SFZ must remain byte-identical. The existing
    compatibility adapter may write its separate *derivative* SFZ, but no
    source file, Composer event, other track or deployed service is altered.
    Partial piano audition is not approval of a whole-genre performance.
    """
    import os
    import re
    import mido
    import hashlib
    from collections import Counter
    import real_electric_piano_probe as original_probe
    from sfz_renderer_adapter import render_midi

    bank_root_raw = os.environ.get("AI_COMP_RESOURCE_BANK")
    renderer_raw = os.environ.get("AI_COMP_SFZ_RENDERER")
    must(bank_root_raw and renderer_raw, "ISOLATED_RECORDED_BANK_OR_RENDERER_MISSING")
    bank_root = Path(bank_root_raw).resolve()
    bank = bank_root / "GREG_SULLIVAN_E_PIANOS"
    original = bank / "Wurlitzer EP200" / "Wurlitzer EP200.sfz"
    derivative = bank / "Wurlitzer EP200" / "composer-wurlitzer.sfz"
    must(original.is_file() and
         not derivative.exists(), "WURLITZER_ORIGINAL_MISSING_OR_DERIVATIVE_PREEXISTS")
    sample_dir = bank / "Wurlitzer EP200" / "Samples"
    sources = [original, *sorted(sample_dir.glob("*.flac"))]
    must(len(sources) > 35, "WURLITZER_FULL_RECORDED_SAMPLE_LIBRARY_MISSING")
    source_hashes = {
        str(p.relative_to(bank)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources
    }
    # Use the ORIGINAL existing compatibility code, not a new SFZ translator.
    original_probe.BANK = bank
    original_probe.ORIGINAL = original
    original_probe.COMPATIBLE = derivative
    original_probe.prepare()
    must(derivative.is_file() and original.read_bytes() != derivative.read_bytes(),
         "SEPARATE_SFIZZ_COMPATIBLE_PROGRAM_NOT_PRODUCED")

    candidates = candidate_receipt["candidate_stage4_events"]
    must(candidates and len(candidates) >= 20 and
         candidate_receipt["candidate_event_count"] == len(candidates) and
         candidate_receipt["blocked_note_count"] > 0 and
         candidate_receipt["production_enabled"] is False and
         candidate_receipt["audio_render_authorized"] is False and
         candidate_receipt["existing_composer_events_unchanged"] is True,
         "ELECTRIC_PIANO_SOURCE_SCOPE_INVALID")
    must(all(n["track_id"] == "ELECTRIC_PIANO" and
             n["instrument_id"] == "electric_piano" and
             n["expected_target_binding_id"] == "electric_piano" and
             n["resource_id"] == "GREG_SULLIVAN_E_PIANOS" and
             n["preferred_mapping"] ==
             "Wurlitzer EP200/composer-wurlitzer.sfz" and
             n["source_midi_channel"] != 9 and
             n["audit_status"] ==
             "REHEARSAL_REFERENCE_ONLY_ORIGINAL_SFZ_NOT_PREFLIGHTED"
             for n in candidates), "WRONG_OR_UNAPPROVED_AUDIO_TRACK_ROUTED")

    # Verify real note AND velocity coverage against existing recorded SFZ
    # region definitions. Do not transpose pitches or alter musical velocity.
    regions = []
    group = {}
    for line in derivative.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("<group>"):
            group = dict((k, int(v)) for k,v in re.findall(
                r"\b(lokey|hikey|lovel|hivel)=(\d+)", stripped))
        if stripped.startswith("<region>"):
            p = {**group, **dict((k, int(v)) for k,v in re.findall(
                r"\b(lokey|hikey|lovel|hivel)=(\d+)", stripped))}
            if "sample=" in stripped:
                regions.append((p.get("lokey", 0), p.get("hikey", 127),
                                p.get("lovel", 1), p.get("hivel", 127)))
    must(len(regions) >= 35, "WURLITZER_ORIGINAL_SFZ_REGIONS_MISSING")
    uncovered = sorted(set(
        (n["midi"],n["velocity"]) for n in candidates
        if not any(lo <= n["midi"] <= hi and
                   lowv <= n["velocity"] <= highv
                   for lo,hi,lowv,highv in regions)))
    must(not uncovered,
         "WURLITZER_RECORDED_NOTE_OR_VELOCITY_ZONE_MISSING:" +
         repr(uncovered[:16]))

    # Convert the already preserved Stage4 candidate events to a SINGLE
    # recorded-instrument audition MIDI; never adopt the partial score as a
    # production-ready full song. sfizz_render reads this standard MIDI.
    work = Path(os.environ.get("AI_COMP_ISOLATED_AUDIO_WORK", "/tmp/composer_ep200_probe"))
    work.mkdir(parents=True, exist_ok=True)
    source_midi = work / "jazz_waltz_original_piano_only.mid"
    audio_wav = work / "jazz_waltz_original_wurlitzer_only.wav"
    ticks = 480
    midi_file = mido.MidiFile(type=1, ticks_per_beat=ticks)
    clock = mido.MidiTrack()
    clock.append(mido.MetaMessage("time_signature", numerator=3, denominator=4,
                                  time=0))
    clock.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo_bpm),
                                  time=0))
    clock.append(mido.MetaMessage("end_of_track", time=0))
    midi_file.tracks.append(clock)
    piano = mido.MidiTrack()
    piano.append(mido.MetaMessage("track_name", name="ELECTRIC_PIANO", time=0))
    changes = []
    for item in candidates:
        start = round(item["start_beat"] * ticks)
        end = round((item["start_beat"] + item["duration_beats"]) * ticks)
        must(0 <= start < end and end <= 1024 * ticks,
             "INVALID_AUDIO_AUDITION_MIDI_TIMING")
        pitch = item["midi"]
        vel = item["velocity"]
        must(type(pitch) is int and 0 <= pitch <= 127 and
             type(vel) is int and 1 <= vel <= 127,
             "INVALID_OR_SUBSTITUTED_AUDIO_MIDI_NOTE")
        changes.append((start, 1, pitch, vel))
        changes.append((end, 0, pitch, 0))
    changes.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    previous_tick = 0
    for tick, is_on, pitch, vel in changes:
        piano.append(mido.Message(
            "note_on" if is_on else "note_off", channel=0, note=pitch,
            velocity=vel, time=tick-previous_tick,
        ))
        previous_tick = tick
    piano.append(mido.MetaMessage("end_of_track", time=0))
    midi_file.tracks.append(piano)
    midi_file.save(source_midi)
    must(len([msg for msg in mido.MidiFile(source_midi).tracks[1]
              if msg.type == "note_on" and msg.velocity > 0]) ==
         len(candidates), "AUDIO_RENDER_MIDI_DROPPED_OR_ADDED_NOTES")
    resource = {
        "resource_id":"GREG_SULLIVAN_E_PIANOS",
        "resource_type":"SFZ_SAMPLE_LIBRARY",
        "preferred_mapping":"Wurlitzer EP200/composer-wurlitzer.sfz",
        "library":"Greg Sullivan E-Pianos / Wurlitzer EP200",
        "license":"CC-BY-3.0",
        "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    }
    rendered = render_midi(resource, source_midi, audio_wav, sample_rate=44100)
    must(rendered["audio_rendered"] is True and
         rendered["status"] == "AUDIO_RENDER_PASS" and
         rendered["peak_linear"] > 0.0001 and
         rendered["rms_linear"] > 0.00001 and
         rendered["measured_samples"] > 44100 and
         audio_wav.stat().st_size > 100000,
         "ELECTRIC_PIANO_AUDIO_INVALID_OR_NEAR_SILENT")
    unchanged = {
        str(p.relative_to(bank)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources
    }
    must(source_hashes == unchanged,
         "ORIGINAL_ELECTRIC_PIANO_SFZ_OR_RECORDINGS_CHANGED")
    report = {
        "status":"ISOLATED_ORIGINAL_WURLITZER_ARRANGER_NOTE_AUDIO_PASS",
        "genre":"Jazz Waltz",
        "original_recorded_instrument":"Greg Sullivan Wurlitzer EP200",
        "original_library_commit":
            "8c3e581acda3594b553948ff0222d4f84a698376",
        "license":"CC-BY-3.0",
        "source_arranger_midi_sha256":source_midi_sha256,
        "original_unaltered_source_files":len(sources),
        "source_files_hash_verified_unchanged":True,
        "separate_compatibility_SFZ_only":True,
        "recorded_region_count":len(regions),
        "all_actual_piano_note_and_velocity_zones_covered":True,
        "actual_original_piano_notes_rendered":len(candidates),
        "blocked_other_instruments_not_rendered":
            candidate_receipt["blocked_note_count"],
        "sfz_sample_references":rendered["sample_references"],
        "sample_rate":rendered["sample_rate"],
        "frames":rendered["frames"],
        "channels":rendered["channels"],
        "peak_dbfs":rendered["peak_dbfs"],
        "rms_dbfs":rendered["rms_dbfs"],
        "wav_file_size_bytes":audio_wav.stat().st_size,
        "finished_multitrack_song":False,
        "full_genre_audio_ready":False,
        "original_composer_events_replaced":False,
        "live_service_deployed":False,
    }
    (work / "original_wurlitzer_audio_verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (work / "ATTRIBUTION.txt").write_text(
        "Greg Sullivan E-Pianos / Wurlitzer EP200: recorded samples by "
        "Greg Sullivan; SFZ conversion credited in original program to "
        "kinwie. CC-BY-3.0. Isolated demonstration of unchanged "
        "original recorded samples through sfizz. MIDI notes authored "
        "by the separately licensed MMA 25.05 JazzWaltz arranger.\n"
        "This contains ONLY the Wurlitzer track, not a finished song "
        "or a representative complete Jazz Waltz arrangement.\n",
        encoding="utf-8",
    )
    print("ORIGINAL_WURLITZER_ISOLATED_STAGE4_AUDIO_PASS",
          json.dumps(report, sort_keys=True), flush=True)


if __name__=="__main__":
    if len(sys.argv) == 3 and sys.argv[1] in ("--composer-mma", "--composer-mma-audio"):
        prove_original_composer_to_mma_only(
            sys.argv[2],
            isolated_wurlitzer_audio=sys.argv[1] == "--composer-mma-audio",
        )
    else:
        must(len(sys.argv)==3,"USAGE: script.py jazzwaltz.mid salsa.mid OR --composer-mma /path/to/original/mma")
        run(sys.argv[1],sys.argv[2])
