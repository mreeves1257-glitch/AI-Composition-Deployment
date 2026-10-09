"""Rock phrase composition experiment — OFF unless AI_COMP_ROCK_CHORD_GRAMMAR_V1=1.

This replaces only pre-existing Rock LEAD notes with short composed melodic
phrases grounded in the *actual generated* rhythm-guitar chords and bass root.
It preserves all sample files, other tracks, tempo, 3D mixer and other genres.
It is an experimental arrangement, not a claim of artistic quality.
"""
from __future__ import annotations

from collections import defaultdict
import os
import math

SWITCH = "AI_COMP_ROCK_CHORD_GRAMMAR_V1"
POLICY = "ROCK_CHORD_ONLY_MELODIC_GRAMMAR_RESEARCH"
LEAD_RANGE = (60, 78)
PHRASE_GRAMMARS = {
    "VERSE": {
        "CALL": ((0.0, "root", .85), (1.0, "third", .43),
                 (1.75, "fifth", .60), (3.0, "third", .74)),
        "ANSWER": ((0.0, "fifth", .52), (.75, "third", .53),
                   (1.5, "root", .78), (2.75, "root", .90)),
    },
    "LIFT": {
        "CALL": ((0.0, "third", .65), (.75, "fifth", .45),
                 (1.5, "root_high", .70), (2.5, "fifth", .42),
                 (3.25, "third", .58)),
        "ANSWER": ((0.0, "fifth", .62), (1.0, "root_high", .77),
                   (2.25, "third", .55), (3.0, "root", .92)),
    },
    "BRIDGE": {
        "CALL": ((0.0, "third", .95), (1.5, "fifth", .65),
                 (2.5, "root", 1.15)),
        "ANSWER": ((0.0, "root", .7), (1.0, "third", .6),
                   (2.0, "fifth", .55), (3.0, "root", .93)),
    },
}


def _role(bar):
    section = bar // 16
    return ("VERSE", "LIFT", "VERSE", "LIFT", "BRIDGE", "LIFT")[section % 6]


def _triads(events, beats_per_bar):
    guitars = defaultdict(set)
    bass = defaultdict(list)
    for event in events:
        track = str(event.get("track_id", "")).upper()
        bar = int(float(event["start_beat"]) // beats_per_bar)
        local = float(event["start_beat"]) - bar * beats_per_bar
        if track == "HARMONY" and 0 <= local < .6:
            guitars[bar].add(int(event["midi"]) % 12)
        if track == "BASS" and 0 <= local < .6:
            bass[bar].append((local, int(event["midi"]) % 12))
    out = {}
    for bar, tones in guitars.items():
        if len(tones) < 3:
            continue
        root = min(bass.get(bar, [(0.0, min(tones))]))[1]
        if root not in tones:
            continue
        order = sorted(tones, key=lambda pc: (pc-root) % 12)
        if len(order) >= 3:
            out[bar] = (order[0], order[1], order[2])
    return out


def _pitch(pc, target):
    notes = [p for p in range(LEAD_RANGE[0], LEAD_RANGE[1]+1) if p % 12 == pc]
    if not notes:
        raise ValueError("LEAD_REGISTER_CHORD_TONE_MISSING")
    return min(notes, key=lambda x: (abs(x-target), x))


def compose_rock_melody(events, genre, *, flag=None, beats_per_bar=4.0):
    out = [dict(e) for e in events]
    if flag is None:
        flag = os.environ.get(SWITCH, "") == "1"
    if flag is not True or str(genre).upper() != "ROCK":
        return out
    if not math.isclose(float(beats_per_bar), 4.0):
        return out
    triads = _triads(out, beats_per_bar)
    leadbars = defaultdict(list)
    for i, event in enumerate(out):
        if (str(event.get("track_id", "")).upper() == "LEAD"
                and str(event.get("instrument_id", "")) in ("lead_guitar", "electric_guitar")):
            leadbars[int(float(event["start_beat"]) // 4)].append(i)
    replaced = {}
    discarded = set()
    for bar, indices in sorted(leadbars.items()):
        if bar not in triads or len(indices) < 3:
            continue
        indices.sort(key=lambda i: float(out[i]["start_beat"]))
        role = _role(bar)
        motif = "CALL" if bar % 4 == 1 else "ANSWER"
        grammar = list(PHRASE_GRAMMARS[role][motif])
        phrase = bar // 4
        if phrase % 4 == 1 and role != "BRIDGE":
            pos, degree, length = grammar[1]
            grammar[1] = (round(pos + .25, 3), degree, max(.28, length-.13))
        if len(grammar) > len(indices):
            continue
        root, third, fifth = triads[bar]
        pcs = {"root": root, "third": third, "fifth": fifth, "root_high": root}
        previous = None
        for j, (offset, degree, dur) in enumerate(grammar):
            source = out[indices[j]]
            target = (67 if j == 0 else previous) + (
                3 if degree in ("fifth", "root_high") else (-2 if j > 1 else 0)
            )
            pitch = _pitch(pcs[degree], target)
            if degree == "root_high" and j > 0:
                higher = [p for p in range(max(LEAD_RANGE[0], pitch+1), LEAD_RANGE[1]+1)
                          if p % 12 == root]
                if higher and higher[0]-previous <= 9:
                    pitch = higher[0]
            previous = pitch
            source["start_beat"] = round(4*bar+offset, 6)
            source["duration_beats"] = min(float(dur), 4-offset-.06)
            source["midi"] = pitch
            base = 86 if role == "LIFT" else (73 if role == "BRIDGE" else 78)
            source["velocity"] = max(45, min(
                115, base + (7 if j == 0 else 0) - 2*j +
                (3 if motif == "ANSWER" and j == len(grammar)-1 else 0)
            ))
            source["articulation"] = "rock_melodic_phrase"
            replaced[indices[j]] = source
        discarded.update(indices[len(grammar):])
    return [replaced.get(i, e) for i, e in enumerate(out) if i not in discarded]
