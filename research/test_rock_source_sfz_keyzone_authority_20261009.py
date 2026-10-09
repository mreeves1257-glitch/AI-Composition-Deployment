"""Audit Rock's exact candidate note numbers against authentic upstream SFZ ranges.

Reads public, commit-pinned *text* program definitions, not any recording WAVs.
This cannot prove the sample graph exists on the deploy or sounds correct.
No production changes, sample downloads, proprietary Yamaha/Korg sound banks,
mixer changes, MIDI rewrite or license substitutions are performed.
"""
from __future__ import annotations
from collections import defaultdict
import re
from pathlib import Path
import sys
import urllib.request
import json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.source_pattern_library import compile_original_source_seed

UPSTREAM={
  "BASS":("sfzinstruments/karoryfer.growlybass",
          "4f483268fc66b5a6d5781d421c0d11b8d08d3fc6",
          "growlybass_clean.sfz"),
  "HARMONY":("sfzinstruments/karoryfer.shinyguitar",
          "57243cca85277dbcc120ce17c6178032f93c80f3",
          "Programs/electric_one.sfz"),
}
DRUM_PROGRAM={
  "KICK":("composer-kick-lite.sfz",36),
  "SNARE":("composer-snare-lite.sfz",38),
  "HAT":("composer-hihat-lite.sfz",42),
}

def source_text(role):
    repo,sha,path=UPSTREAM[role]
    url=f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data=r.read(180000)
    if not data or len(data)>=180000:
        raise RuntimeError("PROGRAM_TEXT_TRUNCATED:"+role)
    return data.decode("utf-8")

def group_playable_keys(sfz, *, guitar=False):
    keys=set()
    for group in re.split(r"(?m)^\s*<group>\s*",sfz)[1:]:
        a=re.search(r"(?m)^\s*lokey=(\d+)",group)
        b=re.search(r"(?m)^\s*hikey=(\d+)",group)
        if not a or not b or not re.search(r"(?m)^\s*sample=",group):
            continue
        lo=int(a.group(1));hi=int(b.group(1))
        if not 0<=lo<=hi<=127:raise ValueError("INVALID_SOURCE_SFZ_ZONE")
        if guitar:
            cc107=re.search(r"(?m)^\s*hicc107=(\d+)",group)
            cc100=re.search(r"(?m)^\s*hicc100=(\d+)",group)
            if cc107 and int(cc107.group(1))<0:continue
            if cc100 and int(cc100.group(1))<0:continue
            # The original build uses Shinyguitar main.sfz with initial
            # set_cc100=0 and set_cc107=0: includes electric_one layers.
            # Check only groups with this selected CC layer.
            if cc107 and 0>int(cc107.group(1)):continue
        keys.update(range(lo,hi+1))
    return keys

def generated_drum_sfzs(build):
    blocks={}
    for role,(name,key) in DRUM_PROGRAM.items():
        expression=r"cat > \"\$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/"+re.escape(name)+r"\" <<'SFZ'\n(.*?)\nSFZ"
        match=re.search(expression,build,re.S)
        if not match:raise AssertionError("ORIGINAL_BUILDER_PROGRAM_NOT_FOUND:"+name)
        sfz=match.group(1)
        if not re.search(r"(?m)^<global>\s+key="+str(key)+r"(?:\s|$)",sfz):
            raise AssertionError("DRUM_SOURCE_NOTE_NOT_EXACT:"+role)
        if not re.search(r"(?m)^\s*sample=",sfz):
            raise AssertionError("NO_REFERENCED_RECORDED_DRUM_SAMPLE:"+role)
        blocks[role]={key}
    return blocks

def main():
    seed=compile_original_source_seed("ROCK")
    assert seed["recorded_audio_authorized"] is False
    notes=defaultdict(list)
    for n in seed["symbolic_note_events"]:
        notes[n["role"]].append(n["midi"])
    allowed={role:group_playable_keys(source_text(role),guitar=(role=="HARMONY"))
             for role in UPSTREAM}
    build=(ROOT/"build_current_composer.sh").read_text()
    # Builder must select exactly the program path used in the guarded
    # source-identity resolver; source bank existence still unknown.
    assert '"preferred_mapping":"Programs/composer-electric.sfz"' in build
    assert '"preferred_mapping":"growlybass_clean.sfz"' in build
    assert 'set_cc107=0' in build
    allowed.update(generated_drum_sfzs(build))
    assert set(notes)==set(allowed),"UNEXPECTED_ROCK_PATTERN_ROLE_NOT_SOURCE_CHECKED"
    rejected={role:sorted(set(seq)-allowed[role]) for role,seq in notes.items()}
    if any(rejected.values()):
        raise AssertionError("ROCK_SOURCE_NOTE_OUTSIDE_REFERENCE_SFZ_ZONE:"+str(rejected))
    print("ROCK_ORIGINAL_SOURCE_SFZ_KEYZONE_REFERENCES_PASS",json.dumps({
       "note_events_checked":sum(len(v) for v in notes.values()),
       "recording_programs_checked":len(notes),
       "melodic_source_ranges":{r:[min(allowed[r]),max(allowed[r])] for r in UPSTREAM},
       "authoring_reference":{r:"@".join((v[0],v[1][:12])) for r,v in UPSTREAM.items()},
       "drum_midi_notes":{r:v[1] for r,v in DRUM_PROGRAM.items()},
       "source_sample_bytes_installed_or_verified":False,
       "real_sound_or_expression_verified":False,
       "midi_audio_render_authorized":False
    },sort_keys=True))
if __name__=="__main__":main()
