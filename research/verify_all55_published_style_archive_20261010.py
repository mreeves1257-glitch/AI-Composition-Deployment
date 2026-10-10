"""Protect one authoritative 55-genre published-style source catalog.

Offline, deterministic verification. Check unique original genre identities,
source status classifications, byte-identical original upstream Git blob IDs,
stored GPL license, and START HERE navigation. Do not run musical renderers,
alter original 55 genre definitions or convert references into 'active' audio.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STYLES=ROOT/"composer_overrides"/"genre_styles"
RESEARCH=ROOT/"research"
CATALOG=RESEARCH/"ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json"
START=RESEARCH/"AI_COMPOSER_GENRE_INSTRUCTIONS_START_HERE.md"

def need(ok:bool, reason:str):
    if not ok:
        raise AssertionError("55_GENRE_PUBLISHED_STYLE_ARCHIVE:"+reason)

def git_blob_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\x00"+data).hexdigest()

def main():
    index=json.loads((STYLES/"index.json").read_text())
    catalog=json.loads(CATALOG.read_text())
    start=START.read_text()
    expected=set(index["genre_to_family_file"])
    entries=catalog["per_genre"]
    need(len(entries)==55 and len(expected)==55 and index["profile_count"]==55,
         "MUST_CONTAIN_ALL_ORIGINAL_55")
    names=[x["genre"] for x in entries]
    need(set(names)==expected and len(set(names))==55,
         "MISSING_DUPLICATED_OR_RENAMED_GENRE")
    need(len(index["family_memberships"])==13,"FAMILY_STRUCTURE_CHANGED")
    counts=Counter(x["source_status"] for x in entries)
    expected_counts={
        "EXISTING_LISTENING_REFERENCE":1,
        "DIRECT_STYLE_REFERENCE":22,
        "RELATED_ONLY_PRESERVE_WORKING_AUDIO":1,
        "RELATED_STYLE_NOT_IDENTICAL":13,
        "NO_VERIFIED_EXACT_STYLE":18,
    }
    need(dict(counts)==expected_counts and catalog["counts"]==expected_counts,
         "SOURCE_MATCH_COUNTS_CHANGED_WITHOUT_RESEARCH_REVIEW")
    need(catalog["no_automatic_substitution"] is True
         and catalog["not_actuated_or_deployed"] is True,
         "MUST_NOT_CALL_REFERENCES_LIVE_PRODUCTION")
    commit=catalog["library"]["commit"]
    need(commit=="c52943c31aa1e64fa9b5313620d5065f91c22773",
         "UPSTREAM_REVISION_DRIFT")
    root=RESEARCH/"genre_reference_sources"/"mma"
    license=(root/"UPSTREAM_GPL2_LICENSE.txt").read_text()
    need("GNU GENERAL PUBLIC LICENSE" in license and "Version 2" in license,
         "SOURCE_LICENSE_NOT_ARCHIVED")
    verified_copies=set()
    for entry in entries:
        name=entry["genre"]
        path=index["genre_to_family_file"][name]
        family=Path(path).parent.name
        need(entry["family"]==family,"GENRE_FAMILY_CHANGED:"+name)
        need(entry["current_genre_definitions_and_recorded_sources_preserved"] is True,
             "GENRE_SOUNDS_NOT_PRESERVED:"+name)
        need(entry["production_audio_ready_by_this_document"] is False
             and entry["source_selected_for_active_song"] is False,
             "UNVERIFIED_GENRE_REFERENCES_ACCIDENTALLY_DEPLOYED:"+name)
        status=entry["source_status"]
        if status=="NO_VERIFIED_EXACT_STYLE":
            need(entry["authoritative_style_file"] is None
                 and entry["upstream_git_blob_sha"] is None
                 and entry["retained_licensed_local_copy"] is None,
                 "UNVERIFIED_GENRE_MUST_NOT_HAVE_FAKE_EXACT_STYLE:"+name)
            continue
        relative=entry["authoritative_style_file"]
        need(isinstance(relative,str) and relative.startswith("lib/")
             and relative.endswith(".mma")
             and ".." not in Path(relative).parts,
             "INVALID_EXTERNAL_STYLE_FILE:"+name)
        sha=entry["upstream_git_blob_sha"]
        need(isinstance(sha,str) and len(sha)==40
             and all(c in "0123456789abcdef" for c in sha),
             "NO_PINNED_STYLE_GIT_BLOB:"+name)
        original_url=("https://github.com/infojunkie/mma/blob/"
                      +commit+"/"+relative)
        need(entry["upstream_source_link"]==original_url,
             "UNPINNED_OR_WRONG_REFERENCE_LINK:"+name)
        local=entry["retained_licensed_local_copy"]
        if local:
            need(local=="research/genre_reference_sources/mma/"+relative,
                 "WRONG_ARCHIVE_LOCATION:"+name)
            content=(ROOT/local).read_bytes()
            need(git_blob_sha(content)==sha,
                 "ORIGINAL_STYLE_MODIFIED_IN_ARCHIVE:"+name)
            verified_copies.add(local)
        else:
            need(status in ("RELATED_STYLE_NOT_IDENTICAL",
                            "RELATED_ONLY_PRESERVE_WORKING_AUDIO"),
                 "DIRECT_STYLE_REFERENCE_MUST_RETAIN_ORIGINAL:"+name)
    need(len(verified_copies)==23,
         "NOT_EXACTLY_23_VERIFIED_UNCHANGED_STYLE_FILES")
    need("ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json" in start
         and "EXISTING_PUBLISHED_GENRE_STYLE_SETUP_INSTRUCTIONS_2026-10-10.md" in start
         and "genre_reference_sources/mma/" in start
         and "Swing" in start,
         "START_HERE_DOES_NOT_POINT_TO_PRESERVED_SOURCES")
    full={
        "status":"PUBLISHED_INSTRUCTIONS_ARCHIVE_ALL_55_GENRES_VERIFIED",
        "genre_count":55,"family_count":13,
        "preserved_identical_upstream_style_files":len(verified_copies),
        "source_status_counts":dict(sorted(counts.items())),
        "upstream_immutable_commit":commit,
        "original_gpl2_license_present":True,
        "one_authoritative_catalog":str(CATALOG.relative_to(ROOT)),
        "one_continuity_page":str(START.relative_to(ROOT)),
        "original_genre_settings_altered":False,
        "instrument_or_mix_settings_altered":False,
        "live_deployment_activated":False,
        "audio_verification_claimed":False
    }
    out=ROOT/"research_artifacts"/"ALL55_SAVED_INSTRUCTIONS_ARCHIVE_AUDIT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(full,indent=2)+"\n")
    print("ALL_55_WRITTEN_GENRE_STYLE_INSTRUCTIONS_ARCHIVE_PASS",
          json.dumps(full,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
