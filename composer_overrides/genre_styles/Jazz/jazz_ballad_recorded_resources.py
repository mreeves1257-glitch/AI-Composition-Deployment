#!/usr/bin/env python3
"""Targeted Jazz Ballad recorded-sample onboarding. Rock and mixer unchanged.

Recorded bass, clarinet, and brush drum samples are pinned by exact upstream
Git commit, byte count, and Git blob SHA. All SFZ sample graphs and instrument
MIDI auditions must pass before the candidate target registry is replaced.
"""
from __future__ import annotations
import hashlib
import json
import os
import struct
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "sound_resources"
TARGET = ROOT / "target_registry.json"
META = {"JAZZ_MEATBASS_PINNED":{"lib":"Karoryfer Meatbass / recorded pizzicato","license":"CC0-1.0","owner":"sfzinstruments/karoryfer.meatbass"},"JAZZ_VSCO_CLARINET_PINNED":{"lib":"VSCO 2 Community Edition / recorded clarinet","license":"CC0-1.0","owner":"sgossner/VSCO-2-CE"},"JAZZ_SWIRLY_BRUSH_PINNED":{"lib":"Karoryfer Swirly Drums / recorded brush kit","license":"CC0-1.0","owner":"sfzinstruments/karoryfer.swirly-drums"}}
FILES = [["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c2_vl2_rr1.wav","72ff2814d7014fd89b71f4f3a030635a5b6381ff",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c2_vl2_rr2.wav","8de0e1f4e42b465070ec422370a1088ece06b4f0",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c2_vl3_rr1.wav","e7d2bd7691e8edd0c6eb2267ebfb255d87a0a1ec",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c2_vl3_rr2.wav","8f0b34ef52a85a86603fb9868b25b70870cef9cf",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb2_vl2_rr1.wav","51c092696d95a3a550993ca515a3c88f77a4e5ef",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb2_vl2_rr2.wav","812a684de67f7f5e6a9c67d2e3ad54cf31b91a1c",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb2_vl3_rr1.wav","1236318b295fd1b0d076e53eca9b5e26f6bdd6d9",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb2_vl3_rr2.wav","1b229b940e3c9d91bad91af69d96225d1ad2ee13",532000],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb2_vl2_rr1.wav","4dcbf457dfed9db0b50f878874f35df5d2b73b40",532002],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb2_vl2_rr2.wav","7e181cd8e138cd7374ecf9ea13cfc4a196b70275",532002],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb2_vl3_rr1.wav","46b8ed447872dc977759e3ea79a0d605cb95e022",532002],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb2_vl3_rr2.wav","110e5d7f36915b02f45d04e080d6bf1260220d8e",532002],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/a2_vl2_rr1.wav","cd079d1436d0ce84e938e1d6636028d80838eea6",505540],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/a2_vl2_rr2.wav","a7c1a8e29d27bfe3983d8c91464088ad557a360c",505540],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/a2_vl3_rr1.wav","e137d720ff285d6e8dc07e1a5a291c133eaa9075",505540],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/a2_vl3_rr2.wav","c001fdd429142d1a9555f11a8072a4f2c56540b2",505540],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c3_vl2_rr1.wav","4c70edddb21f883cff86123ade5297d60dc19980",505542],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c3_vl2_rr2.wav","2aa5f637d237ef41526933a076a965e19e0bb3e3",505542],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c3_vl3_rr1.wav","37314c2039544c6b0362533a8e60bba82d163a3c",505542],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/c3_vl3_rr2.wav","30578fb6f423cb08d3f0609c44dc39364d0a3eb9",505542],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb3_vl2_rr1.wav","29090cc44aae4545b5d316c7601c70bc0fafb615",479082],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb3_vl2_rr2.wav","f5fb95b3e34e5fdf18ebfdc2d6ddfe1d5774d210",479082],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb3_vl3_rr1.wav","2a5bf43c8f9fae2ab69405c83b235cc0cf9fe7c0",479082],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/eb3_vl3_rr2.wav","4fd0c71e46446291e17f5aad445085e13e54cc4e",479082],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb3_vl2_rr1.wav","5a842990a0dc72a40341a4b591b4f213308f6908",426162],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb3_vl2_rr2.wav","277a03b3be81ad00b1f3270155796ad4771fbc49",426162],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb3_vl3_rr1.wav","d6594e34d2c014a66e0b324d43138f1ab3fdb5df",426162],["JAZZ_MEATBASS_PINNED","sfzinstruments/karoryfer.meatbass","ac9e859564bda286ab5ec672d00ff1aa2fef2895","Samples/pizz/gb3_vl3_rr2.wav","24dff460e4be29e0809e1685dd4dfa4d5cac7429",426162],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_D3_v1_rr1_sum.wav","8f3f973a0d69c3c721f1eb8b27f208c80bd17ceb",2230948],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_D3_v2_rr1_sum.wav","dfffae60b3793d9687b2cb2c9b3850f593c723c6",1876188],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_D3_v3_rr1_sum.wav","aa7a1f5f31cef8d36552072d9f275b7940c879c0",1856124],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_F3_v1_rr1_sum.wav","31ac755ac1dff319c409505d26706d9851bb7e92",1762976],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_F3_v2_rr1_sum.wav","1a445b0610a060c571574916d140344fc60922b2",2069572],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_F3_v3_rr1_sum.wav","fc79b6d0f5b3420f4e24b0392484b43a864a6d50",1743712],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_A#3_v1_rr1_sum.wav","f8db827226f661779d8965737fa0850d8275be9a",1599888],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_A#3_v2_rr1_sum.wav","c80415402c31b050eb51796e17fba541a24a57a0",1791140],["JAZZ_VSCO_CLARINET_PINNED","sgossner/VSCO-2-CE","6dd651d55dde97fd4028699be9d4481f26917891","Woodwinds/Clarinet/susLong/DCClar_susLong_A#3_v3_rr1_sum.wav","08f1508a646a60a8795861688932e38955cc8ba0",2059160],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/hat_closed/hh_closed_vl4_rr1.wav","86641ea2b6ea3d09c2ebe0ab7f32ba6cd99a86b2",88342],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/marching_kick/marching_kick_vl4_rr1_reso.wav","da413f582b3bd6c5f9515ffc5cca6bf794d0c4fd",88276],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/hat_closed/hh_closed_vl8_rr1.wav","820db77c232949bb3165127c540766e09817dbc5",88342],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/marching_kick/marching_kick_vl8_rr1_reso.wav","4f2f8a9c07958fea76b56b583fd76bf007bba7cb",88276],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/hat_closed/hh_closed_vl12_rr1.wav","0cc67fc498ae80fed42f0531423e91893b028f34",88342],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/marching_kick/marching_kick_vl12_rr1_reso.wav","60fc9aabf4d3ef769235fb2e7ccd193e174598a3",88276],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/snare_stir/stir_dl1_rr1.wav","d4727a0a4dd21209695c8834f432670b286c59f7",1149618],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/snare_stir/stir_dl1_rr2.wav","fdb91e1f35f287a629ffdb7e9054070874bdf061",1149630],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/snare_stir/stir_dl1_rr3.wav","6744d121f45989ddb530b6d956d854b94f9ac2a2",1149630],["JAZZ_SWIRLY_BRUSH_PINNED","sfzinstruments/karoryfer.swirly-drums","c40dafe0011cb2e54c0c220ff0fa308a11fc60f5","Samples/snare_stir/stir_dl1_rr4.wav","328ae561e7713ac80ef273e8da76e2f7c197ae5e",1149630]]


def require(ok, reason):
    if not ok:
        raise RuntimeError("JAZZ_BALLAD_RESOURCE_BLOCKED:" + reason)


def fetch_recorded(item):
    rid, repository, revision, relative, expected_sha, expected_bytes = item
    output = BANK / rid / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_file():
        data = output.read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if len(data) == expected_bytes and digest == expected_sha:
            return rid
    url = "https://raw.githubusercontent.com/" + repository + "/" + revision + "/" + "/".join(
        urllib.parse.quote(name, safe="") for name in relative.split("/")
    )
    error = "UNKNOWN"
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AI-Composer-Jazz-Audio/1"})
            with urllib.request.urlopen(request, timeout=100) as stream:
                data = stream.read(expected_bytes + 1)
            require(len(data) == expected_bytes, "SOURCE_BYTE_COUNT:" + relative)
            digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            require(digest == expected_sha, "SOURCE_GIT_HASH:" + relative)
            require(data[:4] == b"RIFF" and data[8:12] == b"WAVE", "NOT_REAL_WAV:" + relative)
            temporary = output.with_suffix(".part")
            temporary.write_bytes(data)
            temporary.replace(output)
            return rid
        except (OSError, ValueError) as exc:
            error = str(exc)
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError("JAZZ_RECORDED_SAMPLE_DOWNLOAD_FAILED:" + relative + ":" + error)


def program(rid, filename, lines):
    path = BANK / rid / "Programs" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), "DONOT_OVERWRITE_EXISTING_PROGRAM:" + filename)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "Programs/" + filename


def create_programs():
    # Native concert pitch from Karoryfer Meatbass pizz_basic.sfz.
    lines = ["// Original recorded Karoryfer Meatbass, pizzicato",
             "<global> ampeg_attack=0.003 ampeg_release=0.10"]
    for name, low, high, center in (
        ("c2",35,37,36), ("eb2",38,40,39), ("gb2",41,43,42),
        ("a2",44,46,45), ("c3",47,49,48), ("eb3",50,52,51),
        ("gb3",53,55,54),
    ):
        lines.append(f"<group> lokey={low} hikey={high} pitch_keycenter={center} seq_length=2")
        for layer,lo,hi in ((2,1,85),(3,86,127)):
            for rr in (1,2):
                lines.append(f"<region> sample=../Samples/pizz/{name}_vl{layer}_rr{rr}.wav "
                             f"lovel={lo} hivel={hi} seq_position={rr}")
    bass = program("JAZZ_MEATBASS_PINNED", "jazz-pizzicato.sfz", lines)

    # Original recorded VSCO clarinet sustaining groups, source key ranges.
    lines = ["// Recorded VSCO clarinet native velocity layers",
             "<global> ampeg_attack=0.016 ampeg_release=0.18"]
    for name,lo,hi,center in (("D3",60,63,62),("F3",64,67,65),("A#3",68,71,70)):
        for layer,vel_lo,vel_hi in ((1,1,41),(2,42,83),(3,84,127)):
            lines.append(f"<region> sample=../Woodwinds/Clarinet/susLong/"
                         f"DCClar_susLong_{name}_v{layer}_rr1_sum.wav "
                         f"lokey={lo} hikey={hi} pitch_keycenter={center} "
                         f"lovel={vel_lo} hivel={vel_hi}")
    clarinet = program("JAZZ_VSCO_CLARINET_PINNED","jazz-clarinet.sfz",lines)

    # Dedicated Swirly brush-kit mappings; do not modify Rock drums.
    kick=["// Karoryfer Swirly recorded soft kick"]
    hat=["// Karoryfer Swirly recorded closed hi-hat"]
    for layer,lo,hi in ((4,1,43),(8,44,85),(12,86,127)):
        kick.append(f"<region> sample=../Samples/marching_kick/"
                    f"marching_kick_vl{layer}_rr1_reso.wav key=36 lovel={lo} hivel={hi}")
        hat.append(f"<region> sample=../Samples/hat_closed/"
                   f"hh_closed_vl{layer}_rr1.wav key=42 lovel={lo} hivel={hi}")
    kick_name=program("JAZZ_SWIRLY_BRUSH_PINNED","jazz-brush-kick.sfz",kick)
    hat_name=program("JAZZ_SWIRLY_BRUSH_PINNED","jazz-brush-hat.sfz",hat)
    snare=["// Real brush stirring from Swirly, four round-robin performances",
           "<group> key=38 seq_length=4 loop_mode=one_shot"]
    for rr in (1,2,3,4):
        snare.append(f"<region> sample=../Samples/snare_stir/stir_dl1_rr{rr}.wav seq_position={rr}")
    snare_name=program("JAZZ_SWIRLY_BRUSH_PINNED","jazz-brush-snare.sfz",snare)
    return {
       "double_bass":("JAZZ_MEATBASS_PINNED",bass,[36,40,52],28),
       "clarinet_bb":("JAZZ_VSCO_CLARINET_PINNED",clarinet,[60,63,67,71],9),
       "kick_drum_rock:brush_drums":("JAZZ_SWIRLY_BRUSH_PINNED",kick_name,[36],3),
       "snare_drum:brush_drums":("JAZZ_SWIRLY_BRUSH_PINNED",snare_name,[38],4),
       "hi_hat:brush_drums":("JAZZ_SWIRLY_BRUSH_PINNED",hat_name,[42],3),
    }


def write_midi(path, note):
    # MIDI format 0, single real note then note-off at one beat.
    track = b"\x00\x90" + bytes([note,82]) + b"\x83\x60\x80" + bytes([note,0]) + b"\x00\xff\x2f\x00"
    path.write_bytes(b"MThd" + struct.pack(">IHHH",6,0,1,480) +
                     b"MTrk" + struct.pack(">I",len(track)) + track)


def main():
    from production_resource_policy import require_recorded_sample_resource
    from sfz_renderer_adapter import validate_sfz_samples,render_midi
    registry=json.loads(TARGET.read_text(encoding="utf-8"))
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    with ThreadPoolExecutor(max_workers=6) as workers:
        retrieved=list(workers.map(fetch_recorded,FILES))
    require(len(retrieved)==47,"EXPECTED_ALL_RECORDED_FILES")
    print("JAZZ_BALLAD_PINNED_RECORDED_SAMPLES_PASS",len(retrieved),flush=True)
    mappings=create_programs()
    new_bindings={}
    with tempfile.TemporaryDirectory(prefix="jazz-recorded-audition-") as directory:
        for key,(rid,sfz_path,test_notes,expected_count) in mappings.items():
            require(key not in bindings,"WOULD_OVERWRITE_WORKING_BINDING:" + key)
            data=META[rid]
            candidate={"resource_id":rid,"resource_type":"SFZ_SAMPLE_LIBRARY",
                "preferred_mapping":sfz_path,"library":data["lib"],
                "license":data["license"],
                "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
                "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION","target_gain_db":-6.0,
                "attribution":data["owner"]+" ("+data["license"]+")"}
            require_recorded_sample_resource(candidate)
            report=validate_sfz_samples(BANK/rid/sfz_path)
            require(report["sample_references"]==expected_count,"INCOMPLETE_SFZ_GRAPH:"+key)
            for note in test_notes:
                midi=Path(directory)/(key.replace(":","_")+str(note)+".mid")
                wav=midi.with_suffix(".wav")
                write_midi(midi,note)
                audio=render_midi(candidate,midi,wav,sample_rate=44100)
                require(audio.get("audio_rendered")==True and audio["peak_linear"]>0,
                        "AUDITION_EMPTY:"+key+":"+str(note))
            new_bindings[key]=candidate
            print("JAZZ_BALLAD_RECORDED_ROLE_PASS",key,len(test_notes),flush=True)
    # Source IDs remain exactly the same as the original genre score.
    # InstrumentProgram maps 'brush_drums' to these 3 virtual instrument IDs.
    from instrument_program import InstrumentProgram
    from target_program import TargetProgram
    import importlib.util
    adapter_path=ROOT/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
    spec=importlib.util.spec_from_file_location("recorded_jazz_adapter",adapter_path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    jazz=module.GenreExecutionAdapter().resolve("Jazz Ballad",mode="normal",creation_seed=0)
    instruments=InstrumentProgram(ROOT/"instrument_library.json").resolve_events(jazz["events"])
    require(instruments.get("status")=="PASS","JAZZ_INSTRUMENT_PROFILE_RESOLUTION")
    requested=set()
    for record in instruments["source_requests"]:
        identifier,source=record["instrument_id"],record["source_instrument_id"]
        k=identifier+":"+source
        if k in new_bindings:
            requested.add(k)
        elif identifier in new_bindings:
            requested.add(identifier)
    require(requested==set(new_bindings),"JAZZ_REAL_ROLES_INCOMPLETE:"+str(sorted(requested)))
    bindings.update(new_bindings)
    target=TargetProgram(TARGET)
    target.registry=registry
    result=target.resolve("INTERNAL",instruments)
    require(result.get("status")=="PASS","JAZZ_TARGET_ROUTING:"+str(result.get("missing")))
    require(any(part["instrument_id"]=="electric_piano" for part in result["resolved_resources"]),
            "JAZZ_PIANO_LOST")
    tmp=TARGET.with_suffix(".jazz-staged")
    tmp.write_text(json.dumps(registry,indent=2)+"\n",encoding="utf-8")
    tmp.replace(TARGET)
    print("JAZZ_BALLAD_RECORDED_TARGET_ROUTE_PASS",
          json.dumps({"instrument_bindings":sorted(new_bindings),"full_mixer_verified":False},
                     sort_keys=True),flush=True)


if __name__=="__main__":
    main()
