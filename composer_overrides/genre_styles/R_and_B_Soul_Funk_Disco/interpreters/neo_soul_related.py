"""Dedicated interpreter boundary for Neo-Soul-related; no Composer-owned interpreter."""
import json
from pathlib import Path

GENRE = "Neo-Soul-related"
FAMILY = "R_and_B_Soul_Funk_Disco"
PROFILE_FILE = Path(__file__).resolve().parents[1] / "profile.json"


def interpret(midi_handoff, *, instrument_ids=None):
    """Validate this genre's MIDI handoff and return its original performance rules.

    This is a genre-owned interpreter boundary, not an audio renderer. It refuses
    cross-genre input and does not silently replace recorded instruments.
    """
    if not isinstance(midi_handoff, dict) or midi_handoff.get("genre") != GENRE:
        raise ValueError("WRONG_GENRE_INTERPRETER:" + GENRE)
    if not midi_handoff.get("midi_events") and not midi_handoff.get("midi_file"):
        raise ValueError("MIDI_HANDOFF_REQUIRED:" + GENRE)
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    rules = data["profiles"][GENRE]["musical_definition"]
    return {"genre": GENRE, "profile_id": rules["profile_id"],
            "genre_performance_rules": rules,
            "original_instrument_ids": list(instrument_ids or []),
            "midi_handoff": midi_handoff,
            "renderer_connection": "PENDING_VERIFIED_ORIGINAL_SFZ_BINDINGS",
            "approved_3d_mixer_unchanged": True}
