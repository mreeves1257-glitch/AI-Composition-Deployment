"""Research-only Stage5 live-recording guitar attack experiment.

Only re-times near-simultaneous HARMONY note attacks in the exact pinned
16bar Rock score. This does not regenerate the MMA notes, transpose pitches,
change any other instrument, modify source SFZ, change bass balance, or assume
the human-like result is approved. It is an auditionable single-variable A/B.
"""
from __future__ import annotations

import copy
from collections import defaultdict

MAX_CLUSTER_GAP_BEATS=0.047
STRUM_NOTE_GAP_BEATS=0.038  # 15.7 ms at the selected 145 BPM
CAP_STRUM_SPAN_BEATS=0.14
SIGNATURE="ROCK_SHINYGUITAR_STRUM_ATTACK_TIMING_V1"

def _require(flag,reason):
    if not flag: raise ValueError(reason)

def apply_guitar_attack_strum(rock_score):
    _require(rock_score.get("status")=="PINNED_MMA_ROCK_SCORE_INTERPRETED","NOT_APPROVED_PINNED_ROCK_SCORE")
    _require(rock_score.get("genre")=="ROCK","NOT_ROCK")
    original=rock_score["notes"]
    _require(len(original)==420,"SOURCE_420_EVENTS_REQUIRED")
    result=copy.deepcopy(rock_score)
    notes=result["notes"]
    harm=[n for n in notes if n["track_id"]=="HARMONY"]
    harm.sort(key=lambda x:(x["start_beat"],x["midi"]))
    clusters=[]
    for e in harm:
        if not clusters or e["start_beat"]-clusters[-1][-1]["start_beat"]>MAX_CLUSTER_GAP_BEATS:
            clusters.append([e])
        else:clusters[-1].append(e)
    changed_groups=0
    changed_notes=0
    transformations=[]
    for idx,cluster in enumerate(clusters):
        if len(cluster)<2:continue
        # Avoid mistaking two repeated same-pitch lead strokes for a chord;
        # only stable distinct pitches can be an instrument strum.
        pitches=[n["midi"] for n in cluster]
        if len(pitches)!=len(set(pitches)):continue
        if len(cluster)>4:continue
        base=min(n["start_beat"] for n in cluster)
        # Alternate down/up based on the series of chord attacks.
        direction="DOWN" if changed_groups%2==0 else "UP"
        ordered=sorted(cluster,key=lambda n:n["midi"],reverse=direction=="UP")
        for i,n in enumerate(ordered):
            before=n["start_beat"]
            after=round(base+min(i*STRUM_NOTE_GAP_BEATS,CAP_STRUM_SPAN_BEATS),6)
            _require(0<=after<64,"STRUM_OUT_OF_SONG")
            n["start_beat"]=after
            n["articulation"]="recorded_guitar_"+direction.lower()+"stroke_attack"
            if before!=after:changed_notes+=1
        transformations.append({"attack_index":idx,"direction":direction,"chord_size":len(cluster),"anchor":base,"source_pitches":pitches,"new_onset_beats":[n["start_beat"] for n in ordered]})
        changed_groups+=1
    _require(changed_groups>6,"SOURCE_MMA_DOES_NOT_HAVE_ENOUGH_CHORD_ATTACKS")
    # No source samples, MIDI notes, velocities, bass, percussion, or master touched.
    assert len(notes)==420
    assert sorted((n["track_id"],n["midi"],n["velocity"]) for n in notes)==sorted(
        (n["track_id"],n["midi"],n["velocity"]) for n in original)
    for a,b in zip((n for n in original if n["track_id"]!="HARMONY"),
                   (n for n in notes if n["track_id"]!="HARMONY")):
        assert a==b, "UNRELATED_INSTRUMENT_CHANGED"
    report={"signature":SIGNATURE,"original_note_count":420,
            "note_total_preserved":True,"changed_guitar_attack_groups":changed_groups,
            "changed_guitar_note_onsets":changed_notes,
            "changed_roles":["HARMONY"],"electric_bass_and_every_drum_role_unchanged":True,
            "source_program_changed":False,"genre_playback_claim":"AUDITION_REQUIRED",
            "transformations":transformations}
    result["notes"].sort(key=lambda e:(e["start_beat"],e["track_id"],e["midi"]))
    return result,report
