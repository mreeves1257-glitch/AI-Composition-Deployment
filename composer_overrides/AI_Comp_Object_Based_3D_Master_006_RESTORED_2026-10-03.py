"""AI Composition — Object-Based 3D Master 006 — RESTORED
Restored from protected 2026-09-26/27 contract. Metadata/object-master builder only.
Does not modify upstream composition, rendering, stems, or scene geometry.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json

MASTER_ID="AI_COMP_3D_OBJECT_MASTER_006"

class Master006Error(ValueError): pass

def sha256_file(path):
    p=Path(path)
    if not p.is_file(): raise Master006Error(f"SOURCE_AUDIO_MISSING:{p}")
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def build_object_master(scene, represented_note_events=None, production_resource_ready=False):
    if scene.get("status")!="PASS_SCENE_009":
        raise Master006Error("VALIDATED_SCENE_009_REQUIRED")
    sources=scene.get("sources") or []
    if not sources: raise Master006Error("NO_AUDIO_OBJECTS")
    objects=[]
    seen=set()
    for s in sources:
        sid=s.get("source_id")
        if not sid or sid in seen: raise Master006Error("INVALID_OR_DUPLICATE_SOURCE_ID")
        seen.add(sid)
        pos=s.get("position") or {}
        if not all(k in pos and isinstance(pos[k],(int,float)) for k in ("x","y","z")):
            raise Master006Error("COMPLETE_NUMERIC_3D_DATA_REQUIRED")
        audio=s.get("audio_ref")
        if not audio: raise Master006Error("AUDIO_REFERENCE_REQUIRED")
        actual_hash=sha256_file(audio)
        provenance=s.get("provenance") or {}
        declared=provenance.get("audio_sha256")
        if declared and declared!=actual_hash:
            raise Master006Error(f"AUDIO_SHA256_MISMATCH:{sid}")
        objects.append({
            "object_id":sid,
            "source_id":sid,
            "audio_ref":str(audio),
            "audio_sha256":actual_hash,
            "instrument_id":s.get("instrument_id"),
            "role":s.get("role"),
            "foreground_background_state":s.get("foreground_background_state"),
            "relative_prominence_intent":s.get("prominence"),
            "source_resource_provenance":provenance,
            "spatial_mode":s.get("mode"),
            "position":dict(pos),
            "extent":s.get("extent"),
            "environment":s.get("environment"),
            "movement":s.get("movement")
        })
    status="PASS_PRODUCTION_RESOURCE" if production_resource_ready else "PASS_RESOURCE_FIXTURE_ONLY"
    return {
        "master_id":MASTER_ID,
        "status":status,
        "authoritative_3d_master":True,
        "coordinate_system":scene.get("coordinate_system"),
        "scene_id":scene.get("scene_id"),
        "listener":scene.get("listener"),
        "legacy_profile_reference":scene.get("legacy_profile_reference"),
        "audio_object_count":len(objects),
        "represented_note_events":represented_note_events,
        "audio_objects":objects,
        "independent_source_stems_preserved":True,
        "source_identity_preserved":True,
        "source_resource_provenance_preserved":True,
        "numeric_3d_placement_preserved":True,
        "spatial_send_intent_preserved":True,
        "derivative_law":{
            "stereo":{"authoritative_master":False},
            "binaural":{"authoritative_master":False},
            "multichannel":{"authoritative_master":False}
        }
    }

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("scene_json"); ap.add_argument("output_json")
    ap.add_argument("--represented-note-events",type=int,default=None)
    ap.add_argument("--production-resource-ready",action="store_true")
    a=ap.parse_args()
    scene=json.loads(Path(a.scene_json).read_text(encoding="utf-8"))
    master=build_object_master(scene,a.represented_note_events,a.production_resource_ready)
    Path(a.output_json).write_text(json.dumps(master,indent=2),encoding="utf-8")
    print(json.dumps(master,indent=2))