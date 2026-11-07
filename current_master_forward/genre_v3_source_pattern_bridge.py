"""V3-governed access to the project's original symbolic genre source patterns.

This bridge deliberately does NOT restore the old staged interpreter runtime.
It reuses only the original project-authored symbolic pattern packs, under
current Genre Contract V3 authority.

No note generation, no audio generation, no reasoning engine.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import snapshot_for

REPO = Path(__file__).resolve().parents[1]
STYLE_ROOT = REPO / "composer_overrides" / "genre_styles"
INDEX_PATH = STYLE_ROOT / "index.json"
PACK_NAME = "SOURCE_PATTERN_LIBRARY_R1.json"
PACK_SCHEMA = "AI_COMP_GENRE_ORIGINAL_SOURCE_PATTERNS_R1"
SECTION_NAMES = (
    "INTRO", "VERSE_A", "VERSE_RESPONSE", "FILL",
    "CHORUS_B", "CHORUS_RESPONSE", "ENDING",
)
VARIATIONS = ("INTRO", "A1", "A2", "FILL", "B1", "B2", "OUTRO")


class GenreV3SourcePatternError(RuntimeError):
    pass


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GenreV3SourcePatternError("SOURCE_PATTERN_FILE_MISSING::" + str(path))
    return json.loads(path.read_text())


def _index() -> dict[str, Any]:
    idx = _read(INDEX_PATH)
    if idx.get("profile_count") != 55 or len(idx.get("genre_to_family_file", {})) != 55:
        raise GenreV3SourcePatternError("GENRE_STYLE_INDEX_NOT_55")
    if idx.get("family_count") != 13:
        raise GenreV3SourcePatternError("GENRE_STYLE_INDEX_NOT_13_FAMILIES")
    return idx


def _pack_path(genre_name: str) -> Path:
    idx = _index()
    rel = idx["genre_to_family_file"].get(genre_name)
    if not rel:
        raise GenreV3SourcePatternError("GENRE_NOT_IN_STYLE_INDEX::" + genre_name)
    family = Path(rel).parent
    return STYLE_ROOT / family / PACK_NAME


def load_seed(genre_name: str) -> dict[str, Any]:
    snapshot = snapshot_for(genre_name)
    path = _pack_path(genre_name)
    pack = _read(path)

    if pack.get("schema_version") != PACK_SCHEMA:
        raise GenreV3SourcePatternError("SOURCE_PATTERN_SCHEMA_MISMATCH::" + genre_name)
    if pack.get("audio_verified") is not False:
        raise GenreV3SourcePatternError("SOURCE_PATTERN_MUST_REMAIN_AUDIO_UNVERIFIED::" + genre_name)
    if pack.get("musical_approval") != "NOT_AUDITIONED":
        raise GenreV3SourcePatternError("SOURCE_PATTERN_APPROVAL_STATUS_CHANGED::" + genre_name)

    entries = [x for x in pack.get("genres", []) if x.get("genre") == genre_name]
    if len(entries) != 1:
        raise GenreV3SourcePatternError("SOURCE_PATTERN_GENRE_NOT_UNIQUE::" + genre_name)
    seed = deepcopy(entries[0])

    if seed.get("profile_id") != snapshot.get("profile_id"):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_PROFILE_ID_DRIFT::" + genre_name)
    if seed.get("authoring_status") != "ORIGINAL_PROJECT_SEED_NOT_AUDITIONED":
        raise GenreV3SourcePatternError("SOURCE_PATTERN_AUTHORING_STATUS_CHANGED::" + genre_name)
    if seed.get("source_ownership") != "ORIGINAL_PROJECT_AUTHORED_SYMBOLIC_SEED":
        raise GenreV3SourcePatternError("SOURCE_PATTERN_OWNERSHIP_CHANGED::" + genre_name)
    if seed.get("recorded_source_binding") != "UNVERIFIED_NOT_CONNECTED":
        raise GenreV3SourcePatternError("SOURCE_PATTERN_RESOURCE_STATE_CHANGED::" + genre_name)

    meter = seed.get("meter")
    allowed_meters = list(snapshot.get("meter_options") or [])
    if meter not in allowed_meters:
        raise GenreV3SourcePatternError(
            f"SOURCE_PATTERN_METER_OUTSIDE_V3::{genre_name}::{meter}"
        )

    tempo = seed.get("tempo_bpm")
    tempos = list(snapshot.get("tempo_bpm_range") or [])
    if len(tempos) < 2 or type(tempo) is not int or not int(tempos[0]) <= tempo <= int(tempos[-1]):
        raise GenreV3SourcePatternError(
            f"SOURCE_PATTERN_TEMPO_OUTSIDE_V3::{genre_name}::{tempo}"
        )

    sections = seed.get("sections") or []
    if len(sections) != 7 or [x.get("name") for x in sections] != list(SECTION_NAMES):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_SECTION_SHAPE_INVALID::" + genre_name)
    if not all(x.get("bars") == 1 for x in sections):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_SECTION_LENGTH_INVALID::" + genre_name)

    chords = seed.get("chords") or []
    if len(chords) != 7 or [x.get("bar") for x in chords] != list(range(7)):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_CHORD_SHAPE_INVALID::" + genre_name)

    roles = seed.get("roles") or []
    role_ids = [x.get("role") for x in roles]
    if not role_ids or len(role_ids) != len(set(role_ids)):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_ROLE_IDS_INVALID::" + genre_name)

    patterns = seed.get("patterns") or []
    if {x.get("role") for x in patterns} != set(role_ids) or len(patterns) != len(role_ids):
        raise GenreV3SourcePatternError("SOURCE_PATTERN_ROLE_PATTERN_MISMATCH::" + genre_name)

    for section, variation in zip(sections, VARIATIONS):
        expected = {role: variation for role in role_ids}
        if section.get("variation_by_role") != expected:
            raise GenreV3SourcePatternError(
                "SOURCE_PATTERN_SECTION_VARIATION_MISMATCH::" + genre_name
            )

    for pattern in patterns:
        if pattern.get("kind") not in ("CHORD_RELATIVE", "DRUM_ABSOLUTE", "ABSOLUTE_MIDI"):
            raise GenreV3SourcePatternError("SOURCE_PATTERN_KIND_INVALID::" + genre_name)
        if pattern.get("retrigger") not in ("STOP_AT_CHORD", "HOLD_THROUGH_CHORD"):
            raise GenreV3SourcePatternError("SOURCE_PATTERN_RETRIGGER_INVALID::" + genre_name)
        variations = pattern.get("variations")
        if not isinstance(variations, dict) or set(variations) != set(VARIATIONS):
            raise GenreV3SourcePatternError("SOURCE_PATTERN_VARIATIONS_INVALID::" + genre_name)
        if not all(isinstance(v, list) for v in variations.values()):
            raise GenreV3SourcePatternError("SOURCE_PATTERN_VARIATION_PAYLOAD_INVALID::" + genre_name)

    result = {
        "status": "PASS",
        "authority": "GENRE_CONTRACT_V3_OVER_ORIGINAL_SYMBOLIC_SOURCE_SEED",
        "genre": genre_name,
        "profile_id": snapshot.get("profile_id"),
        "source_pattern_file": str(path.relative_to(REPO)),
        "family": pack.get("family"),
        "seed_id": seed.get("seed_id"),
        "meter": meter,
        "tempo_bpm": tempo,
        "roles": deepcopy(roles),
        "sections": deepcopy(sections),
        "chords": deepcopy(chords),
        "patterns": deepcopy(patterns),
        "v3_contract_sha256": (snapshot.get("_genre_contract_v3_source") or {}).get("contract_sha256"),
        "source_seed_sha256": _sha(seed),
        "audio_authority": False,
        "musical_audition_approved": False,
        "live_runtime_authority": False,
        "compatibility_status": "STRUCTURALLY_COMPATIBLE__MUSICAL_REVALIDATION_REQUIRED",
        "rule": (
            "V3 genre identity and current research remain authoritative. This seed may "
            "supply machine-readable symbolic behavior only after current structural "
            "checks; it may not override V3 or imply musical/listening approval."
        ),
    }
    result["bridge_sha256"] = _sha(result)
    return result


def audit_all() -> dict[str, Any]:
    idx = _index()
    results = {}
    for genre in idx["genre_to_family_file"]:
        results[genre] = load_seed(genre)
    if len(results) != 55:
        raise GenreV3SourcePatternError("SOURCE_PATTERN_V3_COVERAGE_NOT_55")
    return {
        "status": "PASS",
        "genre_count": 55,
        "family_count": 13,
        "audio_authority": False,
        "live_runtime_authority": False,
        "results": results,
    }
