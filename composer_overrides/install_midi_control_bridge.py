"""Guarded installation into a temporary, extracted runtime Output Core.

The archived composer/runtime.b64 is immutable. Build copies this script to
update only the generated composer/runtime/AI_Comp_Executable_Output_Core_001.py.
If the known interface anchor changed, deployment is blocked.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ANCHOR = "            absolute = _midi_pitch_events(track_events, package.ppq, channel)\n"
PATCH = (
    ANCHOR
    + "            from midi_initial_cc_bridge import append_initial_cc\n"
    + "            absolute = append_initial_cc(absolute, package.metadata, track_id, channel)\n"
    + "            from expressive_gesture_bridge import append_expressive_gestures\n"
    + "            absolute = append_expressive_gestures(absolute, package.metadata, track_id, channel, package.ppq, track_events)\n"
)


def install(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if source.count(PATCH) == 1:
        return "ALREADY_INSTALLED"
    if source.count(ANCHOR) != 1:
        candidates = [(i, line) for i, line in enumerate(source.splitlines(), 1)
                      if "_midi_pitch_events" in line or "absolute =" in line]
        print("MIDI_CORE_ACTUAL_CANDIDATE_LINES", candidates[:20], flush=True)
        raise RuntimeError("MIDI_CORE_SIGNATURE_CHANGED_DO_NOT_GUESS")
    path.write_text(source.replace(ANCHOR, PATCH, 1), encoding="utf-8")
    return "INSTALLED"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    args = parser.parse_args()
    print("EXPLICIT_MIDI_CC_BRIDGE", install(args.core), flush=True)
