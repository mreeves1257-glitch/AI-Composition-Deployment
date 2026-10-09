"""Fetch independent open-source music arrangers into audit-only ZIPs.

NOT a production install or runtime change. All external copyrights/licenses
must be respected. Prefer original author's stable MMA release and checksum.
Fall back to identified third-party GitHub mirror only if original unavailable,
labeled unambiguously as MIRROR, never as official 25.05.0.
"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tarfile
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import zipfile

DEST=Path("research/external_interpreter_sources_20261008")
DEST.mkdir(parents=True,exist_ok=True)
EXPECTED_MMA_SHA1="1af05064384c5c7e7d24b163639a414227d3ef6f"

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            d=dict(attrs)
            if d.get("href"):self.hrefs.append(d["href"])

def grab(url, dest, limit=40_000_000):
    request=Request(url,headers={"User-Agent":"AI-Composer-Research-Archivist/1.0",
                                 "Accept":"application/octet-stream,text/html;q=.9,*/*;q=.8"})
    with urlopen(request,timeout=40) as response, dest.open("wb") as target:
        length=0
        while True:
            part=response.read(1<<18)
            if not part:break
            length+=len(part)
            if length>limit:
                raise ValueError("RESEARCH_DOWNLOAD_TOO_LARGE")
            target.write(part)
    return length

def sha(path,kind):
    h=hashlib.new(kind)
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def inspect_tar(path):
    with tarfile.open(path,"r:gz") as archive:
        names=archive.getnames()
    return {"file_count":len(names),
            "example_files":sum(n.endswith(".mma") and "/egs/" in "/"+n for n in names),
            "libraries":sum("/lib/" in "/"+n and n.endswith(".mma") for n in names),
            "doc_files":sum("/docs/" in "/"+n for n in names)}

def inspect_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        test=z.testzip()
    if test is not None:
        raise ValueError("ZIP_CRC_INVALID:"+test)
    return {"file_count":len(names),"license_present":any(n.rsplit("/",1)[-1].upper().startswith(("LICENSE","COPYING")) for n in names),
            "java_source_files":sum(n.endswith(".java") for n in names),
            "groove_files":sum(n.lower().endswith(".mma") for n in names)}

def mma():
    stable_name="mma-bin-25.05.0.tar.gz"
    dest=DEST/stable_name
    failure=[]
    for base in ("https://www.mellowood.ca/mma/downloads.html",
                 "https://mellowood.ca/mma/downloads.html"):
        try:
            request=Request(base,headers={"User-Agent":"Mozilla/5.0"})
            with urlopen(request,timeout=30) as response:
                html=response.read(500000).decode("utf-8","replace")
                final=response.url
            parser=LinkParser();parser.feed(html)
            matches=[urljoin(final,x) for x in parser.hrefs
                     if x.split("?")[0].split("/")[-1]==stable_name]
            if not matches:raise ValueError("OFFICIAL_STABLE_DOWNLOAD_LINK_ABSENT")
            url=matches[0]
            if urlparse(url).hostname not in ("mellowood.ca","www.mellowood.ca"):
                raise ValueError("NON_VENDOR_OFFICIAL_FILE_HOST")
            grab(url,dest)
            actual=sha(dest,"sha1")
            if actual!=EXPECTED_MMA_SHA1:
                dest.unlink(missing_ok=True)
                raise ValueError("OFFICIAL_SHA1_CHECK_FAILED:"+actual)
            info=inspect_tar(dest)
            return {"name":"MMA — Musical MIDI Accompaniment",
                    "distribution":"OFFICIAL_STABLE_25.05.0",
                    "source_url":url,"official_sha1_expected":EXPECTED_MMA_SHA1,
                    "official_sha1_verified":True,"license":"GNU GPL; see upstream license",
                    "file":stable_name,"sha256":sha(dest,"sha256"),
                    "bytes":dest.stat().st_size,**info}
        except Exception as error:
            dest.unlink(missing_ok=True)
            failure.append(str(error))
    # Keep mirror clearly separate: original official source could not be checked.
    mirror=DEST/"MMA_GITHUB_MIRROR_SOURCE_NOT_OFFICIAL_RELEASE.zip"
    url="https://codeload.github.com/infojunkie/mma/zip/refs/heads/master"
    grab(url,mirror)
    info=inspect_zip(mirror)
    return {"name":"MMA — Musical MIDI Accompaniment",
            "distribution":"THIRD_PARTY_GITHUB_MIRROR_NOT_OFFICIAL_RELEASE",
            "source_url":"https://github.com/infojunkie/mma",
            "mirror_archive_download_url":url,
            "official_sha1_verified":False,"official_attempts":failure,
            "license":"GPL-2.0; original authors retained",
            "file":mirror.name,"sha256":sha(mirror,"sha256"),
            "bytes":mirror.stat().st_size,**info}

def jjazzlab():
    # Source reference, not the compiled Java 25+ toolkit jar.
    url="https://codeload.github.com/jjazzboss/JJazzLabToolkit/zip/refs/heads/main"
    archive=DEST/"JJazzLabToolkit_Source_Research_Only.zip"
    grab(url,archive)
    info=inspect_zip(archive)
    if not info["license_present"] or info["java_source_files"]==0:
        raise ValueError("JJAZZLAB_TOOLKIT_SOURCE_INVALID")
    return {"name":"JJazzLab Toolkit (source)",
            "distribution":"OPEN_SOURCE_TOOLKIT_MAIN_BRANCH_UNPINNED",
            "source_url":"https://github.com/jjazzboss/JJazzLabToolkit",
            "source_archive_url":url,
            "license":"LGPL-2.1; read bundled license",
            "compatibility":"Java 25+ required for current developer Toolkit",
            "file":archive.name,"sha256":sha(archive,"sha256"),
            "bytes":archive.stat().st_size,**info}

def main():
    entries=[]
    for fn in (mma,jjazzlab):
        try:
            entry=fn()
            print("SOURCE_FETCH_VERIFIED",json.dumps(entry,sort_keys=True),flush=True)
            entries.append(entry)
        except Exception as exc:
            print("SOURCE_FETCH_NOT_VERIFIED",fn.__name__,repr(exc),flush=True)
            entries.append({"name":fn.__name__,"status":"FETCH_FAILED","error":str(exc)})
    report={"research_date":"2026-10-08","sandbox_only":True,
            "live_composer_modified":False,"plug_or_control_panel_modified":False,
            "instrument_library_modified":False,"runtime_integration_performed":False,
            "interpretation_note":"MMA translates symbolic accompaniment directives to multi-track MIDI; JJazzLab Toolkit is a broader Java backing-track/music generation framework. Neither is a confirmed plug-and-play replacement for original AI Composer.",
            "licensing_note":"Research/reference originals only: Do not transplant GPL/LGPL code into project without evaluating license obligations. Upstream style files and sound banks are not supplied/authorized by this research package.",
            "sources":entries}
    (DEST/"FETCH_MANIFEST.json").write_text(json.dumps(report,indent=2)+"\n")
    readme="""# EXTERNAL MUSIC ARRANGER INTERPRETER SOURCE RESEARCH
Date: 2026-10-08 America/Chicago

These are **unmodified external source archives** supplied separately to
evaluate their music grammar, arrangement structures, and output interoperability.
Nothing is installed in the user's Composer, Plug, Control Panel, sample banks,
genre definitions or final 3D mixer.

MMA official archive is authenticated against upstream published SHA1 only
when FETCH_MANIFEST reports official_sha1_verified=true. Otherwise the archive
is plainly labeled an UNVERIFIED MIRROR and must not be called official.
JJazzLab Toolkit archive is source code, not a ready-to-run Java binary.

Inspect FETCH_MANIFEST.json for provenance, licenses, sizes, hashes and
the differences between official releases and GitHub mirrors. Study how
section variations, independent drums/bass/chords and MIDI are represented.
Do not automatically activate or deploy these programs.
"""
    (DEST/"READ_ME_FIRST.md").write_text(readme)
    if not any("file" in x for x in entries):
        raise RuntimeError("ALL_RETRIEVALS_FAILED")
    print("EXTERNAL_INTERPRETER_RESEARCH_SOURCES_SAVED",len([x for x in entries if "file" in x]),flush=True)

if __name__=="__main__":
    main()
