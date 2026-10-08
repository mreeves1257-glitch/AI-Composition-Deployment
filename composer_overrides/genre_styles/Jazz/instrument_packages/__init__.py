"""Resolve each Jazz style's *links* to one canonical Jazz instrument library.

No WAV/SFZ data is duplicated. An instrument may be available in the common
pool without yet being validated for a particular Jazz subgenre; metadata
preserves that distinction and never claims successful playback prematurely.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
JAZZ_ROOT = DIRECTORY.parent
PACKAGE_SCHEMA = 2
LIBRARY_SCHEMA = 1
CATALOG_REFERENCE = "../instrument_library.json"


def load_package(style_id: str) -> dict:
    if not isinstance(style_id, str) or not style_id or not style_id.replace("_", "").isalnum():
        raise ValueError("INVALID_STYLE_PACKAGE_ID")
    with (DIRECTORY / (style_id + ".json")).open(encoding="utf-8") as file:
        style = json.load(file)
    if style.get("schema_version") != PACKAGE_SCHEMA:
        raise ValueError("JAZZ_STYLE_PACKAGE_SCHEMA_MISMATCH")
    if style.get("link_mode") != "JAZZ_INSTRUMENT_POOL_LINK" or style.get("library") != CATALOG_REFERENCE:
        raise ValueError("JAZZ_STYLE_PACKAGE_LINK_INVALID")
    if not isinstance(style.get("roles"), dict) or not style["roles"]:
        raise ValueError("JAZZ_STYLE_PACKAGE_HAS_NO_ROLES")

    with (JAZZ_ROOT / "instrument_library.json").open(encoding="utf-8") as file:
        library = json.load(file)
    if (library.get("schema_version") != LIBRARY_SCHEMA
            or library.get("library") != "Jazz"
            or library.get("link_mode") != "SHARED_SAMPLE_LIBRARY_REFERENCE"
            or library.get("shared_root") != "sound_resources"):
        raise ValueError("JAZZ_SHARED_INSTRUMENT_LIBRARY_INVALID")
    entries = library.get("instruments")
    if not isinstance(entries, dict):
        raise ValueError("JAZZ_INSTRUMENT_CATALOG_MISSING")
    status = style.get("binding_status")
    resolved = {}
    for role, resource_key in style["roles"].items():
        if not isinstance(role, str) or not isinstance(resource_key, str):
            raise ValueError("JAZZ_STYLE_INSTRUMENT_LINK_INVALID")
        source = entries.get(resource_key)
        if not isinstance(source, dict):
            raise ValueError("JAZZ_STYLE_INSTRUMENT_NOT_IN_CATALOG:" + resource_key)
        if not all(source.get(key) for key in ("instrument_id", "registry_binding", "resource_id", "sfz")):
            raise ValueError("JAZZ_STYLE_INSTRUMENT_RESOURCE_UNRESOLVED:" + role)
        resource = deepcopy(source)
        resource["catalog_key"] = resource_key
        resource["style_binding_status"] = status
        resolved[role] = resource
    return {
        "schema_version": PACKAGE_SCHEMA,
        "genre": style["genre"],
        "link_mode": library["link_mode"],
        "shared_root": library["shared_root"],
        "resource_type": library["resource_type"],
        "fallback_policy": library["fallback_policy"],
        "source_library": "Jazz/instrument_library.json",
        "style_reference": "Jazz/instrument_packages/" + style_id + ".json",
        "binding_status": status,
        "instruments": resolved,
    }
