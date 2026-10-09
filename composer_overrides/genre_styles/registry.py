"""Explicit style-file directory. Shared engine knows filenames, not genre music."""
from importlib import import_module

GENRE_STYLE_MODULES = {
    "ROCK": "Rock.rock",
    "Swing": "Jazz.swing",
    "Jazz Ballad": "Jazz.jazz_ballad",
    "Big Band": "Jazz.big_band",
    "Jazz Waltz": "Jazz.jazz_waltz",
    "Bebop": "Jazz.bebop",
    "Cool Jazz": "Jazz.cool_jazz",
    "Dixieland": "Jazz.dixieland",
    "Jazz Fusion": "Jazz.jazz_fusion",
}
JAZZ_GENRE_PROFILES = {
    "Swing": "JAZZ_SWING_V1",
    "Jazz Ballad": "JAZZ_BALLAD_V1",
    "Big Band": "BIG_BAND_V1",
    "Jazz Waltz": "JAZZ_WALTZ_V1",
    "Bebop": "BEBOP_V1",
    "Cool Jazz": "COOL_JAZZ_V1",
    "Dixieland": "DIXIELAND_V1",
    "Jazz Fusion": "JAZZ_FUSION_V1",
}


def get_style(genre_name, profile):
    if genre_name not in GENRE_STYLE_MODULES or not isinstance(profile, dict):
        return None
    module = import_module("." + GENRE_STYLE_MODULES[genre_name], __package__)
    if module.GENRE_NAME != genre_name:
        return None
    # A reserved Jazz name is not a developed style; keep this path inactive
    # until Jazz Ballad becomes an approved musical template.
    if getattr(module, "DEVELOPMENT_STATUS", None) == "NOT_STARTED":
        return None
    if module.GENRE_PROFILE_ID != profile.get("profile_id"):
        return None
    if profile.get("resolution_policy") != "AUTOMATIC_BASELINE_ALLOWED":
        return None
    return module


def get_shared_musical_interpreter_link(genre_name: str) -> dict:
    """One shared Stage 3-to-4 interpreter package; 55 original genre rules.

    Explicit opt-in only. Does not replace get_style(), activate the Composer
    or launch third-party engines.
    """
    from .shared_interpreter_router import resolve
    return resolve(genre_name)


def handoff_shared_interpreted_events(genre_name: str, *,
                                     song_structure: dict,
                                     selected_instruments: list,
                                     arranger_events: list) -> dict:
    """Source-validate per-track MIDI-derived parts before original Stage 4."""
    from .shared_interpreter_router import stage3_to_stage4
    return stage3_to_stage4(
        genre_name, song_structure=song_structure,
        selected_instruments=selected_instruments,
        arranger_events=arranger_events,
    )
