#!/usr/bin/env python3
"""Read-only inventory of all genre family/profile connections. No audio or deployment."""
import json
from pathlib import Path
root=Path("composer_overrides/genre_styles")
index=json.loads((root/"index.json").read_text())
assert index["family_count"]==13 and index["profile_count"]==55
rows=[]
for family,members in index["family_memberships"].items():
    profile=root/family/"profile.json"
    assert profile.is_file(),f"Missing family profile: {profile}"
    for genre in members:
        assert index["genre_to_family_file"][genre]==f"{family}/profile.json"
        package=root/"Jazz"/"instrument_packages"/(genre.lower().replace(" ","_")+".json") if family=="Jazz" else None
        status="NOT_YET_CONNECTED"
        if package and package.is_file():
            p=json.loads(package.read_text())
            status=p.get("binding_status","UNSPECIFIED")
        rows.append({"family":family,"genre":genre,"profile_file":str(profile),"jazz_package":str(package) if package else None,"connection_status":status,"production_activated_by_inventory":False})
assert len(rows)==55 and len({x["genre"] for x in rows})==55
out=Path("all-55-genre-connection-inventory");out.mkdir(exist_ok=True)
(out/"inventory.json").write_text(json.dumps({"family_count":13,"profile_count":55,"genres":rows},indent=2)+"\n")
print(json.dumps({"families":13,"profiles":55,"jazz_profiles":sum(x["family"]=="Jazz" for x in rows),"non_jazz_profiles":sum(x["family"]!="Jazz" for x in rows)},indent=2))
