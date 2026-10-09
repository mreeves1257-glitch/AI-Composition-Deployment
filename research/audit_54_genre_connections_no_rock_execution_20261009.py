"""Read-only component audit for 54 genres. Never execute, test or edit Rock.

Rock is deliberately excluded from this automated executable audit by user
instruction. Its nine previously filed track-to-recorded-bank references are
reported separately by documentary inspection, never tested.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "composer_overrides" / "genre_styles"
sys.path.insert(0, str(ROOT / "composer_overrides"))
from genre_styles.genre_owned_interpreter_dispatch import connect_selected_genre_components
from genre_styles.source_pattern_library import read_pack
from genre_styles.shared_interpreter_router import ORIGINAL_STAGE_ORDER

def need(value, reason):
    if not value: raise AssertionError(reason)

def run():
    index=json.loads((STYLE/"index.json").read_text())
    registry=json.loads((STYLE/"GENRE_INTERPRETER_REGISTRY_R1.json").read_text())
    # ROCK MUST NEVER BE PASSED TO ANY FUNCTION HERE. Only the 54 others.
    names=[x for x in index["genre_to_family_file"] if x!="ROCK"]
    need(len(names)==54,"EXPECTED_54_NON_ROCK_GENRES")
    result=[]
    c=Counter()
    for genre in names:
        path=index["genre_to_family_file"][genre]
        family=path.split("/")[0]
        profile=json.loads((STYLE/family/"profile.json").read_text())["profiles"][genre]
        entry=registry["per_genre"][genre]
        slot=json.loads((ROOT/entry["slot_file"]).read_text())
        data=json.loads((STYLE/family/"SOURCE_RESOURCE_BINDINGS_R1.json").read_text())
        rs=[x for x in data["genres"] if x["genre"]==genre]
        need(len(rs)==1,"MISSING_OR_DUPLICATE_SOURCE_RECORD:"+genre)
        record=rs[0]
        full=data["full_genre_track_sound_maps"][genre]
        tracks=profile["individual_instrument_tracks"]
        mapped=full["full_genre_tracks"]
        need(profile["musical_definition"]["profile_id"]==
             slot["source_profile_id"]==entry["profile_id"]==
             record["profile_id"]==full["profile_id"],
             "WRONG_GENRE_PROFILE_JOIN:"+genre)
        need(profile["seven_stage_plan"]["stage_count"]==7 and
             profile["seven_stage_plan"]["stage_order"]==list(ORIGINAL_STAGE_ORDER) and
             profile["seven_stage_plan"]["enable_runtime_connections"] is False,
             "SEVEN_STAGE_OR_LIVE_DRIFT:"+genre)
        need(slot["activated_in_live_composer"] is False and
             slot["source_specific_note_score_approved_for_production"] is False and
             entry.get("backend_file", slot["backend_file"])==slot["backend_file"],
             "INTERPRETER_ACTIVE_OR_WRONG_BACKEND:"+genre)
        if genre not in ("Jazz Waltz","Salsa"):
            need(slot["backend_file"]=="composer_overrides/genre_styles/source_pattern_library.py",
                 "MISSING_OWN_SYMBOLIC_BACKEND:"+genre)
        need(len(tracks)==len(mapped)>0 and
             len({x["track_id"] for x in tracks})==len(tracks) and
             list(full["requested_separate_stems"]) == [x["track_id"] for x in tracks],
             "FULL_TRACK_LIST_NOT_ORIGINAL:"+genre)
        for a,b in zip(tracks,mapped):
            need(a["track_id"]==b["track_id"] and
                 a.get("instrument_id")==b.get("original_instrument_id") and
                 a.get("original_palette_group")==b.get("original_palette_group") and
                 b["independent_audio_stem_required"] is True,
                 "SOURCE_INSTRUMENT_SUBSTITUTION:"+genre)
            need(b.get("preflight_verified_for_this_genre") is not True,
                 "UNVERIFIED_AUDIO_FLAG_FALSELY_MARKED_PASS:"+genre)
            if b.get("resource_id"):
                need(b.get("sfz_path") and b.get("registry_binding_id") and
                     b["mapping_state"]==
                     "RECORDED_PROGRAM_IDENTITY_REFERENCE_NOT_NEW_ROUTE_AUDIO_VERIFIED",
                     "PROGRAM_REFERENCE_NOT_EXACT:"+genre)
            else:
                need(b["mapping_state"]==
                     "BLOCKED_NO_EXACT_PROGRAM_OR_CONTEXTUAL_KIT_MAPPING",
                     "MISSING_BANK_FALSELY_SUPPORTED:"+genre)
        seed, ref=read_pack(genre)
        source_roles=record["role_bindings"]
        need({x["role"] for x in seed["roles"]}==set(source_roles) and
             all(source_roles[x["role"]]["original_instrument_id"]==x["instrument_id"]
                 for x in seed["roles"]),
             "SEED_TO_SOUND_ROLE_DRIFT:"+genre)
        need(len(seed["sections"])==7 and len(seed["chords"])==7 and
             seed["recorded_source_binding"]=="UNVERIFIED_NOT_CONNECTED",
             "UNAUTHORIZED_SOURCE_SEED_STATE:"+genre)
        declared=profile["musical_definition"]["meter_options"]
        need(seed["meter"] in declared,"WRONG_GENRE_METER:"+genre)
        stage3=dict(status="PASS",palette=list(dict.fromkeys(
            x["instrument_id"] for x in seed["roles"])),
            meter=seed["meter"],tempo_bpm=seed["tempo_bpm"])
        # No exact registry fixture: this is a connection/guard audit, not a
        # fake recorded-sample or full-length Composer playback test.
        wired=connect_selected_genre_components(
            genre,original_stage3_result=stage3,target_bindings={})
        need(wired["genre"]==genre and wired["profile_id"]==entry["profile_id"] and
             wired["stage4_to_stage5_performance"]["handler_count"]==22 and
             wired["stage4_to_stage5_performance"]["shared_22_capability_handlers_connected"] is True and
             wired["original_event_list_unchanged"] is True and
             wired["live_composer_events_replaced"] is False and
             wired["audio_render_authorized"] is False and
             wired["live_deployment_authorized"] is False and
             wired["stage5_to_stage6_recorded_stems"]["renderer_executed"] is False and
             wired["stage6_to_stage7_independent_3d_mixer"]["mixer_executed"] is False,
             "LIVE_OR_ROUTING_STATUS_UNSAFE:"+genre)
        pinned=[t["track_id"] for t in mapped if t.get("resource_id")]
        blocked=[t["track_id"] for t in mapped if not t.get("resource_id")]
        blocked_roles=[r for r,x in source_roles.items()
                       if x["lookup_policy"]=="BLOCKED_UNVERIFIED"]
        c.update(nonrock_genres=1,original_tracks=len(tracks),
                 exact_full_track_identity_references=len(pinned),
                 blocked_full_track_sound_programs=len(blocked),
                 original_source_roles=len(source_roles),
                 source_roles_with_declared_pins=len(source_roles)-len(blocked_roles),
                 source_roles_blocked=len(blocked_roles),
                 owned_source_scores=int(genre not in ("Jazz Waltz","Salsa")),
                 external_midi_input_needed=int(genre in ("Jazz Waltz","Salsa")))
        result.append(dict(genre=genre,family=family,
              source_roles=len(source_roles),unresolved_source_roles=blocked_roles,
              full_tracks=len(tracks),recorded_program_references=pinned,
              full_tracks_without_exact_program=blocked,
              interpreter=wired["stage3_to_interpreter"]["status"],
              stage4=wired["interpreter_to_original_stage4"]["status"],
              capability_handlers=22,all_seven_stage_references=True,
              recorded_stems_verified=False,live_audio_ready=False,
              connection_blockers=wired["connection_blockers"]))
    need(c["nonrock_genres"]==54 and c["original_tracks"]==306 and
         c["exact_full_track_identity_references"]==57 and
         c["blocked_full_track_sound_programs"]==249 and
         c["original_source_roles"]==229 and
         c["source_roles_with_declared_pins"]==99 and
         c["source_roles_blocked"]==130 and
         c["owned_source_scores"]==52 and
         c["external_midi_input_needed"]==2,
         "NONROCK_AUDIT_COUNTS_DRIFT")
    out=ROOT/"audit_outputs"
    out.mkdir(exist_ok=True)
    doc={
        "scope":"54_NON_ROCK_EXECUTABLE_AUDIT_NO_ROCK_TESTS",
        "status":"DEVELOPMENT_CONNECTIONS_PASS_AUDIO_NOT_READY",
        "source":"GitHub audit development branch checkout",
        "counts":dict(c),
        "rock_policy":"ROCK_NEVER_EXECUTED_OR_TESTED",
        "production_changed":False,
        "audible_audio_verified":False,
        "genres":result,
    }
    (out/"audit_54_genre_component_connections.json").write_text(
        json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    headings=["# Automated audit — 54 non-Rock genres (Rock not tested)",
      "",
      "**Scope:** Stage/genre identity, registry links, genre-owned symbolic",
      "patterns, 22 handler references, exact instrument identity candidates,",
      "and blocked source/track programs. This did not render audio, modify",
      "recorded samples, execute Rock, or deploy.",
      "",
      "**Result:** Development connections present; zero verified end-to-end",
      "audio paths established by this audit.",
      "",
      "| Genre | Family | Seed roles | Seed blocked | Full tracks | Full blocked | Stage 3→4 |",
      "|---|---|---:|---:|---:|---:|---|"]
    for r in result:
        headings.append(f"| {r['genre']} | {r['family']} | {r['source_roles']} | "+
           f"{len(r['unresolved_source_roles'])} | {r['full_tracks']} | "+
           f"{len(r['full_tracks_without_exact_program'])} | "+
           f"{r['interpreter']} |")
    (out/"audit_54_genre_component_connections.md").write_text(
        "\n".join(headings)+"\n")
    print("NON_ROCK_54_CONNECTION_AUDIT_PASS_WITH_AUDIO_BLOCKERS",dict(c))
    print("ROCK_NEVER_CALLED_OR_TESTED")
    return doc

if __name__=="__main__": run()
