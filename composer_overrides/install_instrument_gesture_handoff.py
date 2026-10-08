"""Guarded link into extracted output_handoff.py. Archive is immutable.

Connect the Composer's existing MusicalEvent.articulation with the source-
verified MIDI gesture mapping only when the target resolved its exact SFZ.
Do NOT change the composer engine, genre stages, target bindings or audio mixer.
"""
from __future__ import annotations

import argparse
from pathlib import Path


BEFORE_IMPORT = ("    fingerprint=theory.get('composition_fingerprint','')\n"
                 "    return CompositionExecutionPackage(\n")
AFTER_IMPORT = ("    fingerprint=theory.get('composition_fingerprint','')\n"
                "    from instrument_gesture_handoff import route_explicit_note_gestures\n"
                "    return CompositionExecutionPackage(\n")

BEFORE_METADATA = (
    "        events=tuple(events), metadata=(('genre',engine_result['genre']),"
    "('source_fingerprint',fingerprint),('handoff','OCT03_TO_SEP27_OUTPUT_CORE'),"
    "('midi_routing',json.dumps(routing)))\n"
)
AFTER_METADATA = (
    "        events=tuple(events), metadata=route_explicit_note_gestures(\n"
    "            tuple(events), engine_result['modules']['target'].get('resolved_resources', []),\n"
    "            (('genre',engine_result['genre']),('source_fingerprint',fingerprint),\n"
    "             ('handoff','OCT03_TO_SEP27_OUTPUT_CORE'),('midi_routing',json.dumps(routing)))\n"
    "        )\n"
)


def install(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if source.count(AFTER_IMPORT) == 1 and source.count(AFTER_METADATA) == 1:
        return "ALREADY_INSTALLED"
    if source.count(BEFORE_IMPORT) != 1 or source.count(BEFORE_METADATA) != 1:
        raise RuntimeError("OUTPUT_HANDOFF_SOURCE_SIGNATURE_CHANGED_STOP_WITHOUT_EDIT")
    edited = source.replace(BEFORE_IMPORT, AFTER_IMPORT, 1)
    edited = edited.replace(BEFORE_METADATA, AFTER_METADATA, 1)
    path.write_text(edited, encoding="utf-8")
    return "INSTALLED"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", type=Path, required=True)
    args = parser.parse_args()
    print("INSTRUMENT_GESTURE_OUTPUT_HANDOFF", install(args.handoff), flush=True)
