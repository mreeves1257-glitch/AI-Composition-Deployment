"""Genre Contract V3 explicit-roster to executable event-role authority.

Diagnostic-branch bridge only. This module does not generate notes and does not
invoke the experimental reasoning engine.

Policy:
- If V3 names an explicit roster and a resource mapping is known, V3 owns the
  instrument-role decision.
- Duplicate chairs collapse to one event-role identity here; chair/player
  multiplicity remains arrangement metadata, not duplicate instrument authority.
- If V3 does not yet name an explicit roster, this module returns NOT_READY and
  callers may retain the legacy palette only as an explicitly labeled fallback.
- Classical is intentionally excluded here because its specialized composition
  path must receive a resolved V3 period/ensemble package rather than only a
  roster substitution.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

AUTHORITY_ID = "GENRE_V3_EXPLICIT_ROSTER_AUTHORITY_001"

# Canonical V3 roster labels -> existing Composer event roles.
# A canonical role may expand to more than one event role only where the V3
# roster itself explicitly combines percussion responsibilities.
ROLE_MAP = {
    # Common tonal / melodic roles
    "PIANO": ("piano",),
    "GUITAR": ("electric_guitar",),
    "ACOUSTIC_GUITAR": ("acoustic_guitar",),
    "ACOUSTIC_BASS": ("double_bass",),
    "BASS": None,  # resolved by genre-specific resource adapter below
    "BANJO": ("banjo",),
    "MANDOLIN": ("mandolin",),
    "FIDDLE": ("violin",),
    "FLUTE": ("flute",),
    "SCALABLE_STRINGS": ("strings",),
    "SCALABLE_CHOIR": ("choir",),

    # Big-band / horn roles
    "ALTO_SAX": ("alto_sax",),
    "TENOR_SAX": ("tenor_sax",),
    "BARITONE_SAX": ("baritone_sax",),
    "TRUMPET": ("trumpet",),
    "TROMBONE": ("trombone",),

    # Latin percussion roles
    "SURDO": ("surdo",),
    "CAIXA": ("caixa",),
    "REPINIQUE": ("repinique",),
    "TAMBORIM": ("tamborim",),
    "AGOGO": ("agogo_bells",),
    "GANZA": ("shaker",),
    "CONGA": ("conga",),
    "BONGO": ("bongo_family",),
    "TIMBALES": ("timbales",),
    "MARACAS": ("shaker",),
    "DRUMS": None,  # genre-specific
    "PERCUSSION_SHARED_CLAVE_COWBELL": ("claves", "cowbell"),
    "PERCUSSION_SHARED_MARACAS": ("shaker",),
}

GENRE_RESOURCE_ADAPTER = {
    "Big Band": {
        "BASS": ("double_bass",),
        "DRUMS": ("drums_ride",),
    },
    "Bluegrass-related": {
        "BASS": ("double_bass",),
    },
    "Samba": {
        "BASS": ("electric_bass",),
    },
    "Salsa": {
        "BASS": ("electric_bass",),
    },
    "Mambo": {
        "BASS": ("double_bass",),
        "DRUMS": ("drums",),
    },
    "PIANIST": {},
    "Spiritual": {},
}

SUPPORTED_EXPLICIT_GENRES = tuple(GENRE_RESOURCE_ADAPTER)


def _base_label(canonical: str) -> str:
    # Remove chair/player suffixes while preserving compound role names.
    for prefix in (
        "ALTO_SAX", "TENOR_SAX", "BARITONE_SAX",
        "TRUMPET", "TROMBONE",
        "SURDO", "CAIXA", "REPINIQUE", "TAMBORIM", "AGOGO", "GANZA",
        "CONGA", "BONGO", "TIMBALES", "MARACAS", "FLUTE",
    ):
        if canonical == prefix or canonical.startswith(prefix + "_"):
            return prefix
    return canonical


def resolve(genre_name: str, profile: dict[str, Any]) -> dict[str, Any]:
    if genre_name == "Classical":
        return {
            "status": "CLASSICAL_REQUIRES_VARIANT_PACKAGE",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "event_roles": [],
            "mappings": [],
        }

    v3 = profile.get("_genre_contract_v3") or {}
    ensemble = v3.get("ensemble") or {}
    roster = list(ensemble.get("instrument_roster") or [])
    if not roster:
        return {
            "status": "V3_EXPLICIT_ROSTER_NOT_READY",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "event_roles": [],
            "mappings": [],
        }

    if genre_name not in GENRE_RESOURCE_ADAPTER:
        return {
            "status": "V3_ROSTER_MAPPING_NOT_APPROVED",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "canonical_roster": deepcopy(roster),
            "event_roles": [],
            "mappings": [],
        }

    genre_map = GENRE_RESOURCE_ADAPTER[genre_name]
    event_roles = []
    mappings = []
    unresolved = []

    for canonical in roster:
        base = _base_label(str(canonical))
        roles = genre_map.get(base)
        if roles is None:
            roles = ROLE_MAP.get(base)
        if not roles:
            unresolved.append(canonical)
            continue
        for role in roles:
            if role not in event_roles:
                event_roles.append(role)
        mappings.append({
            "canonical_roster_role": canonical,
            "canonical_base_role": base,
            "event_roles": list(roles),
        })

    if unresolved:
        return {
            "status": "V3_ROSTER_RESOURCE_MAPPING_INCOMPLETE",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "canonical_roster": deepcopy(roster),
            "event_roles": event_roles,
            "mappings": mappings,
            "unresolved": unresolved,
        }

    return {
        "status": "PASS",
        "authority_id": AUTHORITY_ID,
        "authority": "GENRE_CONTRACT_V3_EXPLICIT_ROSTER",
        "genre": genre_name,
        "canonical_roster": deepcopy(roster),
        "event_roles": event_roles,
        "mappings": mappings,
        "fallback_used": False,
    }
