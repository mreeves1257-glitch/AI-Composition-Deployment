"""Genre Contract V3 instrument/formation authority.

Diagnostic-branch implementation. This module translates explicit V3 researched
formation identifiers into executable Composer role IDs. It does not infer
missing formations and does not invoke the experimental reasoning engine.

Policy:
- explicit V3 roster -> V3 roster is authoritative;
- no explicit V3 roster -> legacy palette is retained, but labeled FALLBACK;
- ambiguous canonical roles use a per-genre mapping only when the existing
  Composer already has a documented executable role for that formation;
- no silent substitute is allowed for an unmapped V3 roster identifier.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

AUTHORITY_ID = "GENRE_CONTRACT_V3_INSTRUMENT_AUTHORITY_001"

# Mappings are intentionally explicit. Multiple chairs collapse to one executable
# section/instrument role here; chair-level expansion belongs to the arranger.
GENRE_MAPPINGS: dict[str, dict[str, tuple[str, ...]]] = {
    "Big Band": {
        "ALTO_SAX_1": ("alto_sax",), "ALTO_SAX_2": ("alto_sax",),
        "TENOR_SAX_1": ("tenor_sax",), "TENOR_SAX_2": ("tenor_sax",),
        "BARITONE_SAX": ("baritone_sax",),
        "TRUMPET_1": ("trumpet",), "TRUMPET_2": ("trumpet",),
        "TRUMPET_3": ("trumpet",), "TRUMPET_4": ("trumpet",),
        "TROMBONE_1": ("trombone",), "TROMBONE_2": ("trombone",),
        "TROMBONE_3": ("trombone",), "TROMBONE_4": ("trombone",),
        "PIANO": ("piano",), "GUITAR": ("electric_guitar",),
        "BASS": ("double_bass",), "DRUMS": ("drums_ride",),
    },
    "Bluegrass-related": {
        "ACOUSTIC_GUITAR": ("acoustic_guitar",),
        "ACOUSTIC_BASS": ("double_bass",),
        "BANJO": ("banjo",), "MANDOLIN": ("mandolin",),
        "FIDDLE": ("violin",),
    },
    "Samba": {
        "PIANO": ("piano",), "BASS": ("electric_bass",),
        "SURDO_1": ("surdo",), "SURDO_2": ("surdo",), "SURDO_3": ("surdo",),
        "CAIXA_1": ("caixa",), "REPINIQUE_1": ("repinique",),
        "TAMBORIM_1": ("tamborim",), "AGOGO_1": ("agogo_bells",),
        "GANZA_1": ("shaker",),
    },
    "Salsa": {
        "FLUTE_1": ("flute",),
        "TRUMPET_1": ("trumpet",), "TRUMPET_2": ("trumpet",),
        "TENOR_SAX_1": ("tenor_sax",), "TROMBONE_1": ("trombone",),
        "PIANO": ("piano",), "BASS": ("electric_bass",),
        "CONGA_1": ("conga",), "BONGO_1": ("bongo_family",),
        "TIMBALES_1": ("timbales",),
        "PERCUSSION_SHARED_CLAVE_COWBELL": ("claves", "cowbell"),
        "PERCUSSION_SHARED_MARACAS": ("shaker",),
    },
    "Mambo": {
        "ALTO_SAX_1": ("alto_sax",), "ALTO_SAX_2": ("alto_sax",),
        "ALTO_SAX_3": ("alto_sax",),
        "TENOR_SAX_1": ("tenor_sax",), "TENOR_SAX_2": ("tenor_sax",),
        "TENOR_SAX_3": ("tenor_sax",),
        "BARITONE_SAX_1": ("baritone_sax",),
        "TRUMPET_1": ("trumpet",), "TRUMPET_2": ("trumpet",),
        "TRUMPET_3": ("trumpet",), "TRUMPET_4": ("trumpet",),
        "TRUMPET_5": ("trumpet",),
        "PIANO": ("piano",), "BASS": ("double_bass",), "DRUMS": ("drums",),
        "MARACAS_1": ("shaker",), "BONGO_1": ("bongo_family",),
        "CONGA_1": ("conga",), "CONGA_2": ("conga",),
        "TIMBALES_1": ("timbales",),
    },
    "PIANIST": {
        "PIANO": ("piano",),
    },
    "Spiritual": {
        "PIANO": ("piano",), "FLUTE": ("flute",),
        "SCALABLE_STRINGS": ("strings",), "SCALABLE_CHOIR": ("choir",),
    },
}

# Classical has an explicit V3 roster, but its current specialized arranger owns
# chair/section expansion. We record that fact instead of pretending this generic
# translator has replaced the Classical arranger.
CLASSICAL_SPECIALIZED = "Classical"


class GenreV3InstrumentAuthorityError(RuntimeError):
    pass


def _v3_ensemble(profile: dict[str, Any]) -> dict[str, Any]:
    v3 = profile.get("_genre_contract_v3") or {}
    ensemble = v3.get("ensemble")
    return deepcopy(ensemble) if isinstance(ensemble, dict) else {}


def resolve(
    genre_name: str,
    profile: dict[str, Any],
    legacy_parts: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    legacy = list(legacy_parts)
    ensemble = _v3_ensemble(profile)
    roster = list(ensemble.get("instrument_roster") or [])

    if genre_name == CLASSICAL_SPECIALIZED:
        return {
            "status": "PASS",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "authority": "V3_ROSTER_PRESENT__SPECIALIZED_CLASSICAL_ARRANGER_PENDING",
            "v3_roster": roster,
            "parts": legacy,
            "legacy_fallback_used": True,
            "note": (
                "Classical V3 formation exists, but current Classical chair/section "
                "realization remains in the specialized arranger until its V3 variant "
                "binding is repaired."
            ),
        }

    if not roster:
        return {
            "status": "PASS",
            "authority_id": AUTHORITY_ID,
            "genre": genre_name,
            "authority": "LEGACY_PALETTE_FALLBACK__V3_ROSTER_NOT_YET_EXPLICIT",
            "v3_roster": [],
            "parts": legacy,
            "legacy_fallback_used": True,
            "unmapped_v3_ids": [],
        }

    mapping = GENRE_MAPPINGS.get(genre_name)
    if mapping is None:
        raise GenreV3InstrumentAuthorityError(
            f"V3_EXPLICIT_ROSTER_WITHOUT_EXECUTABLE_MAPPING::{genre_name}"
        )

    parts: list[str] = []
    mapped = []
    unmapped = []
    for canonical in roster:
        targets = mapping.get(canonical)
        if not targets:
            unmapped.append(canonical)
            continue
        mapped.append({"v3_id": canonical, "composer_roles": list(targets)})
        for role in targets:
            if role not in parts:
                parts.append(role)

    if unmapped:
        raise GenreV3InstrumentAuthorityError(
            f"V3_ROSTER_UNMAPPED::{genre_name}::{','.join(unmapped)}"
        )
    if not parts:
        raise GenreV3InstrumentAuthorityError(f"V3_ROSTER_RESOLVED_EMPTY::{genre_name}")

    return {
        "status": "PASS",
        "authority_id": AUTHORITY_ID,
        "genre": genre_name,
        "authority": "GENRE_CONTRACT_V3_EXPLICIT_ROSTER",
        "v3_roster": roster,
        "mapped_roles": mapped,
        "parts": parts,
        "legacy_fallback_used": False,
        "unmapped_v3_ids": [],
    }
