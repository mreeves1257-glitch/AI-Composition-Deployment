"""Safe MIDI timing bridge for EXECUTED upstream MMA arrangements.

Published MMA Swing emits Type-1 192-PPQ MIDI; the original AI Composer
genre-specific MIDI input contract requires Type-1 480 PPQ. This faithfully
resamples message *timing only* on a separate file; it DOES NOT choose styles,
replace notes, change velocity/program/timbre, or authorize GM synth audio.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import mido


class MIDIClockBridgeError(ValueError):
    pass


def ensure(ok,reason):
    if not ok:
        raise MIDIClockBridgeError("ORIGINAL_MMA_MIDI_CLOCK_BRIDGE:"+reason)


def _notes(midi):
    return sorted([
        (tindex, round(beat,7), msg.channel, msg.note, msg.velocity)
        for tindex,track in enumerate(midi.tracks)
        for beat,msg in _absolute_beat(track,midi.ticks_per_beat)
        if msg.type=="note_on" and msg.velocity>0
    ])


def _absolute_beat(track,ppq):
    tick=0
    for msg in track:
        tick+=msg.time
        yield tick/ppq,msg


def original_mma_to_original_composer_ppq(source:str|Path,
                                          target:str|Path)->dict:
    source=Path(source);target=Path(target)
    ensure(source.is_file(),"MMA_MIDI_SOURCE_MISSING")
    ensure(source.resolve()!=target.resolve(),
           "NEVER_OVERWRITE_ORIGINAL_MMA_MIDI")
    raw=source.read_bytes()
    original=mido.MidiFile(source)
    ensure(original.type==1 and original.ticks_per_beat>0,
           "MMA_NOT_TYPE1_VALID_CLOCK")
    ensure(original.ticks_per_beat!=480,
           "NO_CONVERSION_NEEDED_DO_NOT_REWRITE_EXISTING_SONG")
    converted=mido.MidiFile(type=1,ticks_per_beat=480)
    max_error=0.0
    notes_in=0
    for old_track in original.tracks:
        new_track=mido.MidiTrack()
        src_absolute=0
        out_absolute=0
        for msg in old_track:
            src_absolute+=msg.time
            true_tick=src_absolute*480/original.ticks_per_beat
            rounded=round(true_tick)
            max_error=max(max_error,abs(true_tick-rounded))
            ensure(rounded>=out_absolute,
                   "CLOCK_ROUNDING_MOVED_A_NOTE_BACKWARD")
            # Message identity and routing preserved, including all ORIGINAL
            # track names, velocities, note-off pairs and percussion channels.
            new_track.append(msg.copy(time=rounded-out_absolute))
            out_absolute=rounded
            if msg.type=="note_on" and msg.velocity>0:
                notes_in+=1
        converted.tracks.append(new_track)
    ensure(notes_in>100,"NO_ACTUAL_MMA_ACCOMPANIMENT")
    target.parent.mkdir(parents=True,exist_ok=True)
    converted.save(target)
    saved=mido.MidiFile(target)
    ensure(saved.type==1 and saved.ticks_per_beat==480,
           "MIDI_CLOCK_NOT_STANDARDIZED")
    a=_notes(original)
    b=_notes(saved)
    ensure(len(a)==len(b)==notes_in,"ORIGINAL_MUSICAL_NOTES_LOST")
    # 0.5 of a 480-PPQ tick is the maximum permissible timing roundoff.
    for n1,n2 in zip(a,b):
        ensure(n1[0]==n2[0] and n1[2:]==n2[2:],
               "MUSICAL_INSTRUMENT_OR_VELOCITY_CHANGED")
        ensure(abs(n1[1]-n2[1])<=(0.51/480),
               "MUSICAL_BEAT_POSITION_CHANGED")
    ensure(source.read_bytes()==raw,"UPSTREAM_MMA_OUTPUT_ALTERED")
    return {
        "status":"MMA_PUBLISHED_STYLE_TO_AI_COMPOSER_480PPQ_PASS",
        "original_midi_sha256":hashlib.sha256(raw).hexdigest(),
        "output_midi_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "input_ppq":original.ticks_per_beat,"output_ppq":saved.ticks_per_beat,
        "input_type":original.type,"output_type":saved.type,
        "independent_tracks":len(saved.tracks)-1,
        "musical_note_on_events":notes_in,
        "max_tick_quantization_error":max_error,
        "preserved_note_pitches":True,"preserved_velocities":True,
        "preserved_midi_channels_and_program_events":True,
        "source_file_untouched":True,"sampled_audio_verified":False,
        "general_midi_audio_not_authorized":True,
    }
