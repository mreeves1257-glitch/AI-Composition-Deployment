"""Pure MIDI-clock handoff used by external MMA genre styles.

Keep every actual source note, drum channel, instrument program, velocity,
tempo, meter, and track identity. MMA's own original MIDI often uses 192 PPQ;
the existing Composer genre MIDI receiver requires 480 PPQ. This module ONLY
converts absolute event positions; it does not author or edit music/samples.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import mido

PPQ=480

def normalize_original_mma_midi(source_path:str|Path,
                                destination_path:str|Path,
                                target_ppq:int=PPQ)->dict:
    src=Path(source_path)
    dst=Path(destination_path)
    if not src.is_file() or src.resolve()==dst.resolve():
        raise ValueError("MMA_SOURCE_MIDI_MUST_BE_PRESERVED")
    original=mido.MidiFile(str(src))
    if original.type!=1 or original.ticks_per_beat<=0 or target_ppq!=480:
        raise ValueError("UNSUPPORTED_REAL_MMA_MIDI_TIMEBASE")
    normalized=mido.MidiFile(type=1,ticks_per_beat=target_ppq)
    max_error=Fraction(0,1)
    events_count=0
    note_count=0
    for track in original.tracks:
        new_track=mido.MidiTrack()
        old_abs=0
        new_abs=0
        for msg in track:
            old_abs+=msg.time
            # Round the original ABSOLUTE beat position, never each delta
            # individually: avoids accumulating drift across long songs.
            new_tick=round(Fraction(old_abs*target_ppq,original.ticks_per_beat))
            if new_tick<new_abs:
                raise ValueError("MIDI_ORDER_CHANGED")
            new_track.append(msg.copy(time=new_tick-new_abs))
            error=abs(Fraction(new_tick,target_ppq)-
                      Fraction(old_abs,original.ticks_per_beat))
            max_error=max(max_error,error)
            new_abs=new_tick
            events_count+=1
            if msg.type=="note_on" and msg.velocity>0:
                note_count+=1
        normalized.tracks.append(new_track)
    if max_error>Fraction(1,2*target_ppq):
        raise ValueError("MMA_MIDI_BEAT_TIME_ERROR")
    if note_count<1 or events_count<note_count:
        raise ValueError("ORIGINAL_MMA_MIDI_HAS_NO_NOTES")
    dst.parent.mkdir(parents=True,exist_ok=True)
    normalized.save(str(dst))
    check=mido.MidiFile(str(dst))
    if check.type!=1 or check.ticks_per_beat!=target_ppq or len(check.tracks)!=len(original.tracks):
        raise ValueError("NORMALIZED_TYPE1_TRACKS_OR_480PPQ_LOST")
    for old,new in zip(original.tracks,check.tracks):
        if len(old)!=len(new):
            raise ValueError("NORMALIZED_INSTRUMENT_MIDI_EVENTS_LOST")
        old_abs,new_abs=0,0
        for a,b in zip(old,new):
            old_abs+=a.time
            new_abs+=b.time
            if a.copy(time=0)!=b.copy(time=0):
                raise ValueError("ORIGINAL_MMA_PLAYED_NOTE_OR_META_CHANGED")
            if abs(Fraction(new_abs,target_ppq)-
                   Fraction(old_abs,original.ticks_per_beat))>Fraction(1,2*target_ppq):
                raise ValueError("CONVERTED_MIDI_BEAT_DRIFT")
    return {
        "status":"ORIGINAL_MMA_MIDI_480PPQ_CLOCK_NORMALIZATION_PASS",
        "source_ppq":original.ticks_per_beat,
        "target_ppq":target_ppq,
        "type1":True,
        "number_of_tracks":len(check.tracks),
        "original_events_retained":events_count,
        "original_note_on_events_retained":note_count,
        "max_original_beat_position_error":float(max_error),
        "all_original_note_velocities_and_programs_unchanged":True,
        "all_original_drums_and_channels_unchanged":True,
        "original_tempo_and_meter_unchanged":True,
        "recorded_sfz_instruments_not_yet_bound":True,
    }
