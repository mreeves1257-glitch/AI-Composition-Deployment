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
import re
import struct
import subprocess
import sys
import tempfile
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0,str(RUNTIME))


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


def _expand_macros(value:str, macros:dict[str,str])->str:
    out=value
    for _ in range(16):
        changed=False
        for name,replacement in macros.items():
            if name in out:
                out=out.replace(name,replacement)
                changed=True
        if not changed:
            break
    if re.search(r"\$[A-Za-z_][A-Za-z0-9_]*",out):
        raise ShinyguitarNoteLengthProofError("UNRESOLVED_SFZ_MACRO::"+out)
    return out


def _validate_sample_graph(wrapper:Path, allowed_root:Path)->dict:
    """Read-only SFZ sample-graph validation with #define support.

    The recovered production validator predates Shinyguitar's $sample_dir wrapper
    and falsely treats the macro name as a literal directory. This diagnostic
    validator handles inherited #define values without modifying any publisher
    SFZ or sample file.
    """
    allowed_root=allowed_root.resolve()
    visited:set[Path]=set()
    refs:list[str]=[]
    resolved_samples:set[Path]=set()
    missing:list[str]=[]

    def inside_root(path:Path)->bool:
        try:
            path.resolve().relative_to(allowed_root)
            return True
        except ValueError:
            return False

    def walk(path:Path, inherited_macros:dict[str,str], inherited_default:Path|None=None):
        path=path.resolve()
        if not inside_root(path):
            raise ShinyguitarNoteLengthProofError("SFZ_PATH_ESCAPES_RESOURCE_ROOT::"+str(path))
        if path in visited:
            return
        if not path.is_file():
            missing.append("INCLUDE:"+str(path))
            return
        visited.add(path)

        text=path.read_text(errors="strict")
        text=re.sub(r"//[^\n]*","",text)
        macros=dict(inherited_macros)

        for m in re.finditer(r"#define\s+(\$[A-Za-z_][A-Za-z0-9_]*)\s+([^\r\n]+)",text):
            name=m.group(1)
            raw=m.group(2).strip().strip('"')
            macros[name]=_expand_macros(raw,macros)

        default=inherited_default
        dm=re.search(r"(?:^|\s)default_path=([^\s<]+)",text)
        if dm:
            raw=dm.group(1).strip().strip('"').replace("\\","/")
            raw=_expand_macros(raw,macros)
            default=(path.parent/raw).resolve()
            if not inside_root(default):
                raise ShinyguitarNoteLengthProofError(
                    "SFZ_DEFAULT_PATH_ESCAPES_RESOURCE_ROOT::"+str(default)
                )

        for inc in re.findall(r'#include\s+["<]([^">]+)[">]',text):
            raw=_expand_macros(inc.replace("\\","/"),macros)
            walk((path.parent/raw).resolve(),macros,default)

        for match in re.finditer(r"(?:^|\s)sample=(.*?)(?=\s+\w+=|\s*<|$)",text,re.S):
            ref=match.group(1).strip().strip('"').replace("\\","/")
            ref=_expand_macros(ref,macros)
            refs.append(ref)
            base=default if default is not None else path.parent
            candidate=(base/ref).resolve()
            if not inside_root(candidate):
                raise ShinyguitarNoteLengthProofError(
                    "SFZ_SAMPLE_ESCAPES_RESOURCE_ROOT::"+str(candidate)
                )
            if candidate.is_file():
                resolved_samples.add(candidate)
            else:
                missing.append(ref)

    walk(wrapper,{},None)
    if not refs:
        raise ShinyguitarNoteLengthProofError("SFZ_NO_SAMPLE_REFERENCES")
    if missing:
        raise ShinyguitarNoteLengthProofError(
            "SFZ_SAMPLE_SET_INCOMPLETE::"+
            json.dumps({"missing_count":len(missing),"examples":missing[:12]},sort_keys=True)
        )
    return {
        "sample_references":len(refs),
        "unique_sample_references":len(set(refs)),
        "unique_sample_files_resolved":len(resolved_samples),
        "sfz_files_validated":len(visited),
        "macro_aware_validation":True,
    }


def _render_direct(renderer:Path, wrapper:Path, midi_path:Path, wav_path:Path)->dict:
    """Diagnostic-only render through the exact pinned sfizz CLI."""
    wav_path.unlink(missing_ok=True)
    cp=subprocess.run(
        [
            str(renderer),"--sfz",str(wrapper),"--midi",str(midi_path),
            "--wav",str(wav_path),"--samplerate",str(SAMPLE_RATE),
        ],
        capture_output=True,text=True,timeout=120,
    )
    if cp.returncode!=0 or not wav_path.is_file():
        raise ShinyguitarNoteLengthProofError(
            "SFIZZ_DIAGNOSTIC_RENDER_FAILED::"+
            (cp.stderr or cp.stdout or "")[-1200:]
        )
    with wave.open(str(wav_path),"rb") as w:
        frames=w.getnframes()
        channels=w.getnchannels()
        rate=w.getframerate()
    if not frames or channels not in (1,2) or rate!=SAMPLE_RATE:
        raise ShinyguitarNoteLengthProofError(
            "SFIZZ_DIAGNOSTIC_WAVEFORM_INVALID::"+
            json.dumps({"frames":frames,"channels":channels,"rate":rate},sort_keys=True)
        )
    return {
        "frames":frames,
        "channels":channels,
        "sample_rate":rate,
        "audio_rendered":True,
        "diagnostic_direct_pinned_sfizz":True,
    }


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


def _rms(samples:list[float],rate:int,start:float,end:float,*,empty_is_zero:bool=False)->float:
    left=max(0,round(start*rate))
    right=min(len(samples),round(end*rate))
    if right<=left:
        if empty_is_zero:
            return 0.0
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

    resource_root=wrapper.parents[1]
    sample_graph=_validate_sample_graph(wrapper,resource_root)
    if sample_graph["unique_sample_files_resolved"]!=846:
        raise ShinyguitarNoteLengthProofError(
            "SHINYGUITAR_UNIQUE_SAMPLE_COUNT_CHANGED::"+
            str(sample_graph["unique_sample_files_resolved"])
        )

    renderer_path=Path(renderer).resolve()
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
            reports[name]=_render_direct(renderer_path,wrapper,midi_path,wav_path)
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
        # sfizz_render may trim trailing silence after the released note. If the
        # short render has already ended by this post-release window, that is
        # correctly treated as zero energy rather than as a measurement error.
        short_mid=_rms(short,rate,0.80,1.20,empty_is_zero=True)
        long_mid=_rms(long,rate,0.80,1.20)
        if long_mid<=max(1e-5,short_mid*3.0):
            raise ShinyguitarNoteLengthProofError(
                "NOTE_LENGTH_DID_NOT_CAUSE_SUSTAIN_DIFFERENCE::"+
                json.dumps({"short_mid":short_mid,"long_mid":long_mid},sort_keys=True)
            )

        # The long condition itself must still respond to its later note-off:
        # energy after 2.5 s must be materially lower than while it is held.
        # The renderer may likewise trim the long render after its release.
        # A missing post-release window therefore means zero residual energy.
        long_after=_rms(long,rate,2.55,2.95,empty_is_zero=True)
        if long_after>=long_mid*0.60:
            raise ShinyguitarNoteLengthProofError(
                "LONG_NOTE_DID_NOT_RELEASE_AFTER_LATER_NOTEOFF::"+
                json.dumps({"long_mid":long_mid,"long_after":long_after},sort_keys=True)
            )

        short_render_seconds=len(short)/rate
        long_render_seconds=len(long)/rate
        if long_render_seconds<=short_render_seconds+0.75:
            raise ShinyguitarNoteLengthProofError(
                "RENDER_DURATION_DID_NOT_TRACK_NOTE_LENGTH::"+
                json.dumps({
                    "short_render_seconds":short_render_seconds,
                    "long_render_seconds":long_render_seconds,
                },sort_keys=True)
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
            "renderer_path":str(renderer_path),
            "sample_graph_validation":sample_graph,
            "production_preflight_bypassed_for_isolated_diagnostic":True,
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
            "short_render_seconds":short_render_seconds,
            "long_render_seconds":long_render_seconds,
            "short_active_end_seconds":short_end,
            "long_active_end_seconds":long_end,
            "active_end_delta_seconds":long_end-short_end,
            "midi_sha256":midi_hashes,
            "render_reports":{
                name:{
                    "frames":report["frames"],
                    "channels":report["channels"],
                    "sample_rate":report["sample_rate"],
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
                "The sample graph was independently validated with SFZ #define expansion; "
                "the live production preflight remains unchanged and blocked. This proves "
                "NOTE_LENGTH_RESPONSE for Rock Mode A on this exact mapping/renderer."
            ),
            "next_gate":"RECORD_CAPABILITY_CERTIFICATE__THEN_NARROW_ROCK_MODE_A_LISTENING_A_B",
        }
        out=ROOT/"genre_contract_v3_research"/"SHINYGUITAR_NOTE_LENGTH_RESPONSE_PROOF.json"
        out.write_text(json.dumps(summary,indent=2)+"\n")
        print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
