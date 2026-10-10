"""Swing-only real trumpet source: pinned VSCO 2 CE original sustain recordings.

Safeguard: original sounds, sample WAVs, Jazz Ballad instruments, balances,
genre profile and MIDI are unchanged. No production registry write.
Downloads ONLY 10 genuine unmodified VSCO trumpet WAVs by immutable Git
commit, verifies exact file lengths and Git blob SHA, writes a SEPARATE
SFZ trumpet program; performs actual sfizz-render note-zone auditions.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import struct
import tempfile
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/"sound_resources"
SOURCE_REPO="sgossner/VSCO-2-CE"
SOURCE_COMMIT="6dd651d55dde97fd4028699be9d4481f26917891"
BANK_ID="JAZZ_VSCO_TRUMPET_SWING_PINNED"
SOURCE_LICENSE="CC0-1.0"
SFZ="Programs/swing-original-vsco-trumpet.sfz"
# Verified directly against upstream raw WAV blobs at the pinned commit.
SAMPLES=[
    ("C3",60,63,60,"efc0c148e06d6cf1b2c5e65efc568635e4fac38f",2677040,
     "d5490467cf68db010843924b975fd71edfc41273",1234136),
    ("G3",64,70,67,"129e67aa9df78209517b461e38d8d1176a0e2861",3010072,
     "a301819024fe8d1fb8cdf86f9b5d0d8121c8c073",1638452),
    ("D4",71,75,74,"5270a6927aa41b90f804df59b9888449aa01a2bb",2878200,
     "815560ece9f2e8d0ad6a33ba24a014345ea59814",1422408),
    ("F4",76,79,77,"c14125cf6f506ed3a5d495fee4130381d050b109",2442252,
     "cb508c5bf2e3c21dc3441194499fc6d0e7344f4b",1269372),
    ("A4",80,83,81,"544285c24f712f098254f0f4677cb96e9c272081",2528080,
     "bbdc0773c636c611b953ed1383f8cf1eb6b53b38",1730412),
]

def fail(why):
    raise ValueError("SWING_RECORDED_TRUMPET:"+why)

def manifest():
    paths=[]
    for name,low,high,center,sha1,size1,sha3,size3 in SAMPLES:
        for vel,sha,size in ((1,sha1,size1),(3,sha3,size3)):
            rel="Brass/Trumpet/sus/Sum_SHTrumpet_sus_"+name+"_v"+str(vel)+"_rr1.wav"
            paths.append({"path":rel,"blob_sha":sha,"byte_length":size,
                          "lowest_note":low,"highest_note":high,
                          "root_note":center,"source_velocity_layer":vel})
    return paths

def fetch_one(item):
    relative=item["path"]
    output=BANK/BANK_ID/relative
    output.parent.mkdir(parents=True,exist_ok=True)
    def check_bytes(raw):
        if len(raw)!=item["byte_length"]:
            fail("PINNED_SAMPLE_SIZE_MISMATCH:"+relative)
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if sha!=item["blob_sha"] or raw[:4]!=b"RIFF" or raw[8:12]!=b"WAVE":
            fail("PINNED_SAMPLE_IDENTITY_MISMATCH:"+relative)
    if output.is_file():
        raw=output.read_bytes()
        check_bytes(raw)
        return relative
    url=("https://raw.githubusercontent.com/"+SOURCE_REPO+"/"+SOURCE_COMMIT+"/"
         +"/".join(urllib.parse.quote(p,safe="") for p in relative.split("/")))
    last=None
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Swing-Audition-Recorded-Samples"})
            with urllib.request.urlopen(request,timeout=100) as fp:
                raw=fp.read(item["byte_length"]+1)
            check_bytes(raw)
            tmp=output.with_suffix(".tmp")
            tmp.write_bytes(raw)
            tmp.replace(output)
            return relative
        except (OSError,ValueError) as exc:
            last=str(exc)
            if attempt<2:time.sleep(attempt+1)
    fail("SOURCE_DOWNLOAD_FAILED:"+relative+":"+str(last))

def write_sfz():
    """Use only vanilla VSCO natural sustained waveforms, not a synth."""
    lines=["// Source: Versilian Studios VSCO2 Community Edition, CC0 1.0",
           "// Original unaltered trumpet/sus WAV; MIDI 60..83.",
           "// No equalizer, envelope adjustment, invented vibrato or mixer modification."]
    for name,low,high,center,*_ in SAMPLES:
        for layer,lv,hv in ((1,1,63),(3,64,127)):
            rel="../Brass/Trumpet/sus/Sum_SHTrumpet_sus_"+name+"_v"+str(layer)+"_rr1.wav"
            lines.append("<region> sample="+rel+" lokey="+str(low)+" hikey="+str(high)
                         +" pitch_keycenter="+str(center)+" lovel="+str(lv)+" hivel="+str(hv))
    output=BANK/BANK_ID/SFZ
    output.parent.mkdir(parents=True,exist_ok=True)
    data="\n".join(lines)+"\n"
    if output.exists() and output.read_text()!=data:
        fail("DO_NOT_OVERWRITE_UNKNOWN_SFZ")
    output.write_text(data,encoding="utf-8")
    return output

def preflight():
    from sfz_renderer_adapter import validate_sfz_samples,render_midi
    midi=ROOT/"swing_trumpet_test_temp.mid"
    report=validate_sfz_samples(BANK/BANK_ID/SFZ)
    if report["sample_references"]!=10:
        fail("TEN_REAL_TRUMPET_SAMPLE_REGIONS_REQUIRED")
    # One original sample per velocity group, but every MIDI key zone covered.
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix="swing_trumpet_audition_") as tmp:
        for note in (60,65,70,74,77,81,83):
            for vel in (50,100):
                path=Path(tmp)/f"note_{note}_{vel}.mid"
                # format0/480ppq native note on and note-off after one beat
                track=(b"\x00\x90"+bytes((note,vel))+
                       b"\x83\x60\x80"+bytes((note,0))+
                       b"\x00\xff\x2f\x00")
                path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,480)+
                                 b"MTrk"+struct.pack(">I",len(track))+track)
                wav=path.with_suffix(".wav")
                binding={"resource_id":BANK_ID,
                         "resource_type":"SFZ_SAMPLE_LIBRARY",
                         "preferred_mapping":SFZ,
                         "library":"VSCO 2 Community Edition / original trumpet",
                         "license":SOURCE_LICENSE,
                         "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
                         "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
                         "target_gain_db":-6.0}
                result=render_midi(binding,path,wav,sample_rate=44100)
                if not result.get("audio_rendered") or result["peak_linear"]<=0:
                    fail("ORIGINAL_TRUMPET_NOT_AUDIBLE:"+str(note)+":"+str(vel))
    return {"status":"SWING_VSCO_REAL_RECORDED_TRUMPET_SAMPLE_ZONES_PASS",
            "source_repo":SOURCE_REPO,"source_commit":SOURCE_COMMIT,
            "source_license":SOURCE_LICENSE,"sample_count":10,
            "keyzone_min":60,"keyzone_max":83,
            "original_sample_wavs_unchanged":True,
            "program":str(BANK/BANK_ID/SFZ),
            "recorded_audio_verified":True,"production_deployed":False}

def main():
    files=manifest()
    with ThreadPoolExecutor(max_workers=5) as pool:
        retrieved=list(pool.map(fetch_one,files))
    if len(retrieved)!=10 or len(set(retrieved))!=10:
        fail("INCOMPLETE_RECORDED_SAMPLE_FETCH")
    write_sfz()
    report=preflight()
    dest=ROOT/"output"/"swing_verified_recorded_trumpet.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print("SWING_REAL_TRUMPET_PINNED_SFZ_AUDITION_PASS",json.dumps(report),flush=True)

if __name__=="__main__":
    main()
