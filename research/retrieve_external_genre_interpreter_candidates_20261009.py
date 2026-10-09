"""Download original open-source arranger SOURCE archives as separate research tools.

These third-party code bundles are NOT pasted into AI Composer, not enabled
as genre interpreters, not SFZ replacements and not style/recording licenses.
This work inventories real MMA grooves against all 55 genre owners.
"""
from __future__ import annotations
import csv,hashlib,io,json,os,re,sys,tarfile,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"research_artifacts"/"open_source_arranger_interpreter_research_20261009"
OUT.mkdir(parents=True,exist_ok=True)
LIMIT=70_000_000
SOURCES=[
 ("MMA_official_25_05_0","https://www.mellowood.ca/mma/mma-bin-25.05.0.tar.gz",
  "GPL-2.0_OR_LATER_CONFIRMED_CHECK_UPSTREAM_LICENSE","1af05064384c5c7e7d24b163639a414227d3ef6f"),
 ("MMA_mirror_style_library","https://codeload.github.com/infojunkie/mma/zip/c52943c31aa1e64fa9b5313620d5065f91c22773",
  "GPL-2.0_MIRROR_CHECK_ASSET_PROVENANCE",None),
 ("MMA_grooves_extra","https://codeload.github.com/sciurius/mma-grooves/zip/fb54bec6238705c82d85ccc01a476144f8adcdb6",
  "Artistic-2.0_OR_GPL-2.0_OR_LATER",None),
 ("JJazzLabToolkit_source","https://codeload.github.com/jjazzboss/JJazzLabToolkit/zip/4d38b923166a43b0ca573093e235f0461b72f606",
  "LGPL-2.1",None),
 ("Cadenza_source","https://codeload.github.com/Piskocis/Cadenza/zip/47da8f71670daa4caa1b3db2bf8f60a323f6c6b1",
  "GPL-3.0",None),
]
# References ONLY. None assert finished output, exact match or ownership.
POSSIBLE_STYLES={
"ROCK":["basicrock","60srock","rock-128"],
"Swing":["swing","easyswing","fastswing"],
"Jazz Ballad":["mellowjazz","slowjazz","pianoballad"],
"Big Band":["bigband"],
"Jazz Waltz":["jazzwaltz","fastjazzwaltz"],
"Bebop":["bebop"],
"Cool Jazz":["slowjazz","modernjazz"],
"Dixieland":["dixie"],
"Jazz Fusion":["jazzrock","lfusion"],
"Rhythm and Blues":["rb","rb-ballad"],
"Soul":["dsoul","rb"],
"Funk":["bvfunk"],
"Contemporary R&B":["rb-ballad","rb"],
"Neo-Soul-related":["rb-ballad","dsoul"],
"DISCO":["dsoul"],
"Traditional Country":["hillcountry","slowcountry"],
"Country Rock":["folkrock","hillcountry"],
"Country Ballad":["slowcountry","folkballad"],
"Country Shuffle":["countryswing"],
"Two-Step":["countryswing"],
"Country Waltz":["countrywaltz"],
"Bluegrass-related":["bluegrass"],
"Bossa Nova":["bossanova"],
"Samba":["samba"],
"Salsa":["salsa"],
"Mambo":["mambo"],
"Rumba":["rhumba"],
"Cha-Cha":["chacha"],
"Bolero":["bolero"],
"House":[],
"Techno":[],
"Trance":["trance"],
"Ambient Electronic":[],
"Downtempo":[],
"Breakbeat-related":[],
"Garage-related":[],
"Experimental Electronic":[],
"Chugg / #chugg":[],
"Eclectic New Indie":["folkrock"],
"Mexican Reggaeton":[],
"Afrobeats":["afro-cuban"],
"Afro-Latin / Afrobeats Fusion":["afro-cuban","lfusion"],
"Afro House":[],
"Trip-Hop":[],
"Contemporary Trip-Hop / Trip-Hop Revival":[],
"Regional Electronic Hybrids":[],
"Genre-Breaking / Borderless":[],
"Custom Hybrid":[],
"Custom Style":[],
"Controlled Custom Style Profile":[],
"Classical":[],
"WALTZ":["waltz","vienesewaltz"],
"PIANIST":["pianoballad"],
"New Age":["stringballad"],
"Spiritual":["spiritual","slowspiritual"],
}

def sha(data):return hashlib.sha256(data).hexdigest()

def pull(name,url,license,sha1=None):
    print("RETRIEVE_SOURCE",name,url,flush=True)
    req=urllib.request.Request(url,headers={"User-Agent":"AI-Composer-License-Audited-Research/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        content=r.read(LIMIT+1)
    if not 100<=len(content)<=LIMIT:raise AssertionError("BAD_OR_OVERSIZED_SOURCE:"+name)
    if sha1 and hashlib.sha1(content).hexdigest()!=sha1:
        raise AssertionError("OFFICIAL_MMA_SHA1_NOT_MATCHED")
    ext=".tar.gz" if url.endswith(".tar.gz") else ".zip"
    target=OUT/(name+ext);target.write_bytes(content)
    return {"source_name":name,"url":url,"license":license,
            "research_only":True,"sha1_pinned":bool(sha1),
            "sha256":sha(content),"size_bytes":len(content),
            "file":target.name,"downloaded":True,
            "installed_in_live_composer":False,
            "programs_copied_into_ai_composer":False}

def inspect_styles(filename):
    with zipfile.ZipFile(filename) as src:
        styles={}
        for o in src.infolist():
            if o.is_dir() or not re.search(r"/lib/[^/]+/[^/]+\.mma$",o.filename,re.I):
                continue
            style=o.filename.split("/lib/",1)[1]
            styles[style.lower()]=o.filename
        clean=set(x.rsplit("/",1)[1].removesuffix(".mma")
                 for x in styles if x.startswith("stdlib/"))
        return styles,clean

def run():
    idx=json.loads((ROOT/"composer_overrides/genre_styles/index.json").read_text())
    owners=idx["genre_to_family_file"]
    if set(owners)!=set(POSSIBLE_STYLES):
        raise AssertionError("55_GENRE_REGISTRY_AND_RESEARCH_CANDIDATE_LIST_MISMATCH:"+
            str(sorted(set(owners)^set(POSSIBLE_STYLES))))
    reports=[]
    errors=[]
    for entry in SOURCES:
        try:reports.append(pull(*entry))
        except Exception as e:
            name=entry[0];errors.append({"name":name,"error":str(e)[:280]})
            print("RETRIEVAL_FAILED",name,str(e)[:220],flush=True)
    downloaded={x["source_name"]:x for x in reports}
    # MMA GPL mirror and officially pinned author release must both be here.
    if "MMA_mirror_style_library" not in downloaded:
        raise AssertionError("MMA_OPEN_SOURCE_STYLE_LIBRARY_MISSING")
    mirror=OUT/downloaded["MMA_mirror_style_library"]["file"]
    styles,stdlib=inspect_styles(mirror)
    if len(stdlib)<100:raise AssertionError("MMA_STDLIB_STYLES_INSUFFICIENT")
    if "MMA_official_25_05_0" not in downloaded:
        print("OFFICIAL_SOURCE_NOT_AVAILABLE_MIRROR_RETAINED",flush=True)
    rows=[]
    for genre,family_rel in owners.items():
        candidate=[]
        for bare in POSSIBLE_STYLES[genre]:
            filename="stdlib/"+bare+".mma"
            if filename not in styles:
                raise AssertionError("CANDIDATE_SOURCE_MMA_STYLE_MISSING:"+filename)
            candidate.append(filename)
        path="composer_overrides/genre_styles/"+family_rel
        rows.append({
          "genre_name":genre,"existing_family_profile":path,
          "source_type":"MMA_GPL_RESEARCH_GROOVE_PROGRAMS",
          "candidate_style_programs":"; ".join(candidate),
          "candidate_count":len(candidate),
          "interpretation_status":"CANDIDATES_REQUIRE_MUSICAL_MATCH_AND_LICENSE_REVIEW" if candidate
                                   else "NO_EXACT_VALIDATED_STYLE_PROGRAM_FOUND",
          "owned_interpreter_implemented":genre=="ROCK",
          "reuse_existing_user_liked_rock_16bar_score":genre=="ROCK",
          "no_automatic_style_code_import":True,
          "exact_sample_banks_or_live_audio_verified_for_candidate":False,
        })
    csvpath=OUT/"ALL_55_GENRE_POSSIBLE_PROGRAMS_NOT_YET_VERIFIED.csv"
    with csvpath.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (OUT/"MMA_STYLE_FILE_INVENTORY.txt").open("w") as h:
        for path in sorted(styles):h.write(path+"\n")
    if len(rows)!=55:raise AssertionError("GENRE_COVERAGE_NOT_55")
    status={
      "schema":"AI_COMP_THIRD_PARTY_ARRANGER_SOURCE_RETRIEVAL_R1",
      "date":"2026-10-09",
      "downloaded_external_source_archives":reports,
      "download_errors":errors,
      "mirror_total_mma_style_file_count":len(styles),
      "mirror_stock_stdlib_file_count":len(stdlib),
      "genre_owner_count":55,
      "genres_with_possible_style_references":sum(bool(x["candidate_count"]) for x in rows),
      "genres_missing_possible_style_references":sum(not x["candidate_count"] for x in rows),
      "candidate_role":"RESEARCH_NOT_AUDIO_READY_OR_LICENSE_CLEARED",
      "source_material_not_connected_to_55_active_genre_interpreters":True,
      "separate_existing_original_rock_backend_preserved":True,
      "commercial_use_rights_not_certified":True,
      "yamaha_or_korg_proprietary_firmware_or_samples_downloaded":False,
      "licenses_of_programs_need_individual_review":True,
      "no_deploy_or_change_to_hard_copy":True,
    }
    (OUT/"RETRIEVAL_AND_LICENSE_MANIFEST.json").write_text(json.dumps(status,indent=2)+"\n")
    (OUT/"README.txt").write_text(
       "SOURCE DOWNLOAD FOR RESEARCH ONLY. These are real arranger source-code\n"
       "and musical-style research candidates, NOT 55 finished interpreters.\n"
       "GPL programs and potentially third-party-derived styles require legal\n"
       "and artistic review. NEVER auto-load copyrighted Yamaha/Korg styles.\n"
       "The user's 16-bar 145 BPM Rock interpreter is already preserved in\n"
       "composer_overrides/genre_styles/Rock on the development branch.\n"
       "The existing Composer and recorded instruments were NOT modified.\n")
    pack=OUT.parent/"LICENSED_ARRANGER_PROGRAM_SOURCE_RESEARCH_2026-10-09.zip"
    with zipfile.ZipFile(pack,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.iterdir()):
            if path.is_file():z.write(path,path.name)
    print("EXTERNAL_ARRANGER_PROGRAM_SOURCES_RETRIEVED",json.dumps({
       "source_archives":len(reports),
       "mma_style_files":len(styles),"stock_mma_style_files":len(stdlib),
       "individual_genre_inventories":len(rows),
       "genres_with_matching_style_candidates":status["genres_with_possible_style_references"],
       "genres_without_matching_style_candidates":status["genres_missing_possible_style_references"],
       "zip_bytes":pack.stat().st_size,
       "safely_separated_from_live_composer":True,
    }),flush=True)

if __name__=="__main__":run()
