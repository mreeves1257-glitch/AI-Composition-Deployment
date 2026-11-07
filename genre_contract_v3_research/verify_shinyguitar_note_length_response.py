"""Isolated Shinyguitar NOTE_LENGTH_RESPONSE proof.

This is NOT a composition listening render. It tests one preserved recorded
electric-guitar resource in isolation through the project's SFZ renderer boundary.

Control variables held constant:
- same SFZ mapping;
- same MIDI pitch;
- same velocity;
- same onset;
- same tempo;
- same total MIDI duration;
- same renderer and sample rate.

Independent variable:
- MIDI note-off time only.

A pass demonstrates that the rendered resource responds causally to note length,
which is the sole new expressive capability required by Rock Core Mode A.
It does not certify full production fidelity or approve the Rock composition.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import os
import struct
import sys
import tempfile
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0,str(RUNTIME))

from sfz_renderer_adapter import render_midi

SCHEMA="SHINYGUITAR_NOTE_LENGTH_RESPONSE_PROOF_001"
RESOURCE_ID="KARORYFER_SHINYGUITAR"
MAPPING="Programs/composer_electric.sfz"
WRAPPER_SHA256="da026ba66ab34a4ebb99c6cda93a24d4bc48e57e252a26db5c1fd6916cbaed35"
PITCH=60
VELOCITY=80
TPQ=480
TEMPO_US_PER_QUARTER=500000  # 120 BPM
SHORT_TICKS=240              # 0.25 sec
LONG_TICKS=1920              # 2.00 sec
TOTAL_TICKS=3840             # 4.00 sec
SAMPLE_RATE=44100


class ShinyguitarNoteLengthProofError(RuntimeError):
    pass


def _vlq(value:int)->bytes:
    if value<0:
        raise ShinyguitarNoteLengthProofError("NEGATIVE_VLQ")
    out=[value&0x7F]
    value >>= 7
    while value:
        out.append((value&0x7F)|0x80)
        value >>= 7
    return bytes(reversed(out))


def _midi(note_ticks:int)->bytes:
    if not 1<=note_ticks<TOTAL_TICKS:
        raise ShinyguitarNoteLengthProofError("NOTE_TICKS_OUTSIDE_TEST")
    track=bytearray()
    # Tempo at tick 0.
    track.extend(b"\x00\xFF\x51\x03")
    track.extend(TEMPO_US_PER_QUARTER.to_bytes(3,"big"))
    # Explicit CC106=0: release-noise layer remains disabled exactly as the
    # Shinyguitar program's default setting specifies.
    track.extend(b"\x00\xB0\x6A\x00")
    # Note on at tick 0.
    track.extend(bytes((0x00,0x90,PITCH,VELOCITY)))
    # Note off is the ONLY changing musical event.
    track.extend(_vlq(note_ticks))
    track.extend(bytes((0x80,PITCH,0x00)))
    # Hold the MIDI file open to the same total duration for both conditions.
    track.extend(_vlq(TOTAL_TICKS-note_ticks))
    track.extend(b"\xFF\x2F\x00")

    header=b"MThd"+struct.pack(">IHHH",6,0,1,TPQ)
    return header+b"MTrk"+struct.pack(">I",len(track))+bytes(track)


def _pcm_mono(path:Path)->tuple[list[float],int]:
    with wave.open(str(path),"rb") as w:
        rate=w.getframerate()
        channels=w.getnchannels()
        width=w.getsampwidth()
        frames=w.getnframes()
        raw=w.readframes(frames)
    if rate!=SAMPLE_RATE:
        raise ShinyguitarNoteLengthProofError("UNEXPECTED_SAMPLE_RATE")
    if channels not in (1,2):
        raise ShinyguitarNoteLengthProofError("UNEXPECTED_CHANNEL_COUNT")
    if width not in (1,2,4):
        raise ShinyguitarNoteLengthProofError("UNEXPECTED_SAMPLE_WIDTH")
    if width==1:
        vals=[(x-128)/128.0 for x in raw]
    elif width==2:
        vals=[x[0]/32768.0 for x in struct.iter_unpack("<h",raw)]
    else:
        vals=[x[0]/2147483648.0 for x in struct.iter_unpack("<i",raw)]
    if channels==1:
        mono=vals
    else:
        mono=[sum(vals[i:i+channels])/channels for i in range(0,len(vals),channels)]
    if not mono or max(abs(x) for x in mono)<=0:
        raise ShinyguitarNoteLengthProofError("SILENT_RENDER")
    return mono,rate


def _rms(samples:list[float],rate:int,start:float,end:float)->float:
    left=max(0,round(start*rate))
    right=min(len(samples),round(end*rate))
    if right<=left:
        raise ShinyguitarNoteLengthProofError("EMPTY_RMS_WINDOW")
    total=sum(x*x for x in samples[left:right])
    return math.sqrt(total/(right-left))


def _active_end(samples:list[float],rate:int)->float:
    # 20 ms windows; activity threshold is relative to a stable early note body.
    early=_rms(samples,rate,0.08,0.20)
    threshold=max(1e-5,early*0.025)
    width=max(1,round(rate*0.020))
    last=0
    for left in range(0,len(samples),width):
        right=min(len(samples),left+width)
        if right<=left:
            break
        rms=math.sqrt(sum(x*x for x in samples[left:right])/(right-left))
        if rms>=threshold:
            last=right
    return last/rate


def main():
    renderer=os.environ.get("AI_COMP_SFZ_RENDERER")
    if not renderer or not Path(renderer).is_file():
        raise ShinyguitarNoteLengthProofError("PINNED_SFIZZ_RENDERER_NOT_SET")

    registry=json.loads((RUNTIME/"target_registry.json").read_text())
    binding=registry["targets"]["INTERNAL"]["instrument_bindings"]["electric_guitar:LEAD_MELODY"]
    if binding.get("resource_id")!=RESOURCE_ID:
        raise ShinyguitarNoteLengthProofError("WRONG_RESOURCE_ID")
    if binding.get("preferred_mapping")!=MAPPING:
        raise ShinyguitarNoteLengthProofError("WRONG_MAPPING")
    if binding.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise ShinyguitarNoteLengthProofError("SYNTHETIC_FALLBACK_POLICY_CHANGED")

    wrapper=RUNTIME/"sound_resources"/RESOURCE_ID/MAPPING
    if not wrapper.is_file():
        raise ShinyguitarNoteLengthProofError("SHINYGUITAR_WRAPPER_MISSING")
    digest=hashlib.sha256(wrapper.read_bytes()).hexdigest()
    if digest!=WRAPPER_SHA256:
        raise ShinyguitarNoteLengthProofError(
            "SHINYGUITAR_WRAPPER_HASH_CHANGED::"+digest
        )

    resource=dict(binding)
    with tempfile.TemporaryDirectory(prefix="shiny-note-length-",dir=str(RUNTIME)) as tmp:
        folder=Path(tmp)
        renders={}
        midi_hashes={}
        reports={}
        for name,note_ticks in (("short",SHORT_TICKS),("long",LONG_TICKS)):
            midi=_midi(note_ticks)
            midi_path=folder/(name+".mid")
            wav_path=folder/(name+".wav")
            midi_path.write_bytes(midi)
            midi_hashes[name]=hashlib.sha256(midi).hexdigest()
            reports[name]=render_midi(resource,midi_path,wav_path,SAMPLE_RATE)
            pcm,rate=_pcm_mono(wav_path)
            renders[name]=(pcm,rate)

        short,rate=renders["short"]
        long,_=renders["long"]

        # Before the short note-off both conditions should be ordinary sounding
        # guitar notes. We do not require sample-identical PCM because Shinyguitar
        # uses round-robin/random region selection.
        short_early=_rms(short,rate,0.08,0.20)
        long_early=_rms(long,rate,0.08,0.20)
        if min(short_early,long_early)<=1e-5:
            raise ShinyguitarNoteLengthProofError("EARLY_NOTE_BODY_TOO_QUIET")

        # After the 0.25 s short note plus its 0.25 s release, the long condition
        # must still carry materially more sustained energy.
        short_mid=_rms(short,rate,0.80,1.20)
        long_mid=_rms(long,rate,0.80,1.20)
        if long_mid<=max(1e-5,short_mid*3.0):
            raise ShinyguitarNoteLengthProofError(
                "NOTE_LENGTH_DID_NOT_CAUSE_SUSTAIN_DIFFERENCE::"+
                json.dumps({"short_mid":short_mid,"long_mid":long_mid},sort_keys=True)
            )

        # The long condition itself must still respond to its later note-off:
        # energy after 2.5 s must be materially lower than while it is held.
        long_after=_rms(long,rate,2.55,2.95)
        if long_after>=long_mid*0.60:
            raise ShinyguitarNoteLengthProofError(
                "LONG_NOTE_DID_NOT_RELEASE_AFTER_LATER_NOTEOFF::"+
                json.dumps({"long_mid":long_mid,"long_after":long_after},sort_keys=True)
            )

        short_end=_active_end(short,rate)
        long_end=_active_end(long,rate)
        if long_end<=short_end+0.75:
            raise ShinyguitarNoteLengthProofError(
                "ACTIVE_AUDIO_DURATION_DID_NOT_TRACK_NOTE_LENGTH::"+
                json.dumps({"short_end":short_end,"long_end":long_end},sort_keys=True)
            )

        summary={
            "schema":SCHEMA,
            "status":"PASS",
            "diagnostic_only":True,
            "resource_id":RESOURCE_ID,
            "mapping":MAPPING,
            "wrapper_sha256":digest,
            "renderer_path":str(Path(renderer).resolve()),
            "renderer_version_pin":os.environ.get("AI_COMP_SFIZZ_PIN"),
            "pitch":PITCH,
            "velocity":VELOCITY,
            "tempo_bpm":120,
            "short_note_seconds":SHORT_TICKS/TPQ*0.5,
            "long_note_seconds":LONG_TICKS/TPQ*0.5,
            "same_total_midi_seconds":TOTAL_TICKS/TPQ*0.5,
            "short_early_rms":short_early,
            "long_early_rms":long_early,
            "short_post_release_rms":short_mid,
            "long_while_held_rms":long_mid,
            "long_post_release_rms":long_after,
            "held_vs_short_post_release_ratio":long_mid/max(short_mid,1e-12),
            "long_post_release_vs_held_ratio":long_after/max(long_mid,1e-12),
            "short_active_end_seconds":short_end,
            "long_active_end_seconds":long_end,
            "active_end_delta_seconds":long_end-short_end,
            "midi_sha256":midi_hashes,
            "render_reports":{
                name:{
                    "frames":report["frames"],
                    "channels":report["channels"],
                    "sample_rate":report["sample_rate"],
                    "peak_dbfs":report["peak_dbfs"],
                    "rms_dbfs":report["rms_dbfs"],
                    "audio_rendered":report["audio_rendered"],
                }
                for name,report in reports.items()
            },
            "note_length_response_certified_for_this_mapping_and_renderer":True,
            "production_fidelity_certified":False,
            "full_composition_audio_approved":False,
            "live_runtime_promoted":False,
            "result":(
                "With pitch, velocity, onset, tempo, mapping and total MIDI length held "
                "constant, changing only note-off time causes the preserved Shinyguitar "
                "render to sustain materially longer and release after the later note-off. "
                "This proves NOTE_LENGTH_RESPONSE for Rock Mode A on this mapping/renderer."
            ),
            "next_gate":"RECORD_CAPABILITY_CERTIFICATE__THEN_NARROW_ROCK_MODE_A_LISTENING_A_B",
        }
        out=ROOT/"genre_contract_v3_research"/"SHINYGUITAR_NOTE_LENGTH_RESPONSE_PROOF.json"
        out.write_text(json.dumps(summary,indent=2)+"\n")
        print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
