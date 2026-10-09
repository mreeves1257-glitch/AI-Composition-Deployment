"""Project-authored shared technical parser for EXTERNAL arranger-produced MIDI.

Music authority stays in genre-owned interpreter backends. This parser reads
notes/clock from standard MIDI; it neither imports/copyleft-copies external
GPL program source nor makes genre decisions or switches production events.
"""
from __future__ import annotations
from collections import defaultdict,Counter
from pathlib import Path
import hashlib

class StyleMidiInterfaceError(ValueError): pass

def require(condition, reason):
    if not condition: raise StyleMidiInterfaceError(reason)

def read_arranger_style_midi(path, *, meter, tempo_bpm, required_tracks):
    """Parse external authored score, reject tempo/meter mismatch and orphan notes.

    No MIDI note is mapped to a physical SFZ without a later separate audit.
    """
    import mido
    data=Path(path).read_bytes()
    require(data[:4]==b"MThd","NOT_A_REAL_MIDI_FILE")
    song=mido.MidiFile(file=__import__("io").BytesIO(data))
    require(song.type==1 and song.ticks_per_beat>0,
            "EXTERNAL_SOURCE_NOT_MULTITRACK_MIDI")
    tick=song.ticks_per_beat
    conductor=song.tracks[0]
    t=[(x.numerator,x.denominator) for x in conductor
       if x.type=="time_signature"]
    times=[x.tempo for x in conductor if x.type=="set_tempo"]
    require(len(t)==1 and t[0]==tuple(meter),"WRONG_GENRE_METER")
    require(len(times)==1 and abs(mido.tempo2bpm(times[0])-tempo_bpm)<0.05,
            "WRONG_GENRE_ENSEMBLE_TEMPO")
    notes=[]
    present=set()
    for tr in song.tracks[1:]:
        labels=[x.name for x in tr if x.type=="track_name"]
        require(len(labels)==1,"MIDI_TRACK_NOT_NAMED_UNIQUELY")
        name=labels[0]
        require(name not in present,"DUPLICATE_MIDI_TRACK_NAME")
        present.add(name)
        time=0
        holds=defaultdict(list)
        for event in tr:
            time+=event.time
            if event.type not in ("note_on","note_off"):continue
            key=(event.channel,event.note)
            ison=(event.type=="note_on" and event.velocity>0)
            if ison:holds[key].append((time,event.velocity))
            elif holds[key]:
                start,vel=holds[key].pop(0)
                duration=time-start
                require(duration>0,"NONPOSITIVE_NOTE_DURATION")
                start_beats=round(start/tick,6)
                length=round(duration/tick,6)
                require(start_beats>=0 and length>0,"INVALID_MIDI_BEATS")
                notes.append({"source_track":name,"source_midi_note":event.note,
                              "channel":event.channel,"velocity":vel,
                              "start_beat":start_beats,"duration_beats":length})
            else: raise StyleMidiInterfaceError("NOTE_OFF_WITHOUT_NOTE_ON:"+name)
        require(not any(holds.values()),"UNCLOSED_MIDI_NOTES:"+name)
    require(set(required_tracks).issubset(present),
            "MISSING_GENRE_STYLE_TRACKS:"+str(set(required_tracks)-present))
    require(len(notes)>10,"ARRANGER_STYLE_DID_NOT_GENERATE_NOTES")
    notes.sort(key=lambda x:(x["start_beat"],x["source_track"],x["source_midi_note"]))
    return {"source_sha256":hashlib.sha256(data).hexdigest(),
            "ticks_per_beat":tick,"time_signature":list(t[0]),
            "tempo_bpm":tempo_bpm,"tracks":sorted(present),
            "note_count":len(notes),"events":notes}
