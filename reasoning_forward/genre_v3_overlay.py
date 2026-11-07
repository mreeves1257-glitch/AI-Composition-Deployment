"""Runtime-safe qualitative Genre Contract v3 overlay.

This module is deliberately narrow:
- it preserves every legacy profile field unchanged;
- it attaches only the sanitized qualitative overlay generated from the frozen
  Genre Contract v3 snapshot;
- it never loads research evidence, unapproved quantitative percentages,
  experimental audition renderers, or the experimental reasoning engine;
- Classical and Big Band remain protected metadata-only anchors.
"""
from __future__ import annotations
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parent
OVERLAY_PATH = ROOT / 'genre_v3_safe_overlay.json'
EXPECTED_OVERLAY_ID = 'GENRE_V3_SAFE_QUALITATIVE_OVERLAY_2026-11-07'
PROTECTED_ANCHORS = {'Classical', 'Big Band'}

class GenreV3OverlayError(RuntimeError):
    pass


def load_overlay(path: str | Path = OVERLAY_PATH) -> dict:
    data = json.loads(Path(path).read_text())
    if data.get('overlay_id') != EXPECTED_OVERLAY_ID:
        raise GenreV3OverlayError('V3_OVERLAY_ID_MISMATCH')
    genres = data.get('genres')
    if not isinstance(genres, dict) or len(genres) != 55:
        raise GenreV3OverlayError('V3_OVERLAY_GENRE_COUNT_INVALID')
    return data


def attach_profile(genre_name: str, profile: dict, overlay: dict | None = None) -> dict:
    overlay = overlay or load_overlay()
    item = (overlay.get('genres') or {}).get(genre_name)
    if item is None:
        raise GenreV3OverlayError(f'V3_OVERLAY_GENRE_MISSING::{genre_name}')
    if item.get('profile_id') != profile.get('profile_id'):
        raise GenreV3OverlayError(f'V3_OVERLAY_PROFILE_ID_MISMATCH::{genre_name}')
    out = copy.deepcopy(profile)
    out['v3_runtime_overlay'] = copy.deepcopy(item)
    out['v3_overlay_mode'] = item.get('runtime_mode')
    return out


def augment_profiles(profiles: dict[str, dict], overlay: dict | None = None) -> dict[str, dict]:
    overlay = overlay or load_overlay()
    if len(profiles) != 55:
        raise GenreV3OverlayError('LEGACY_PROFILE_COUNT_NOT_55')
    if set(profiles) != set(overlay['genres']):
        missing = sorted(set(profiles) - set(overlay['genres']))
        extra = sorted(set(overlay['genres']) - set(profiles))
        raise GenreV3OverlayError(f'V3_OVERLAY_NAME_SET_MISMATCH::missing={missing}::extra={extra}')
    return {name: attach_profile(name, profile, overlay) for name, profile in profiles.items()}


def runtime_enabled(profile: dict) -> bool:
    return profile.get('v3_overlay_mode') == 'SAFE_QUALITATIVE_SUPPLEMENT'