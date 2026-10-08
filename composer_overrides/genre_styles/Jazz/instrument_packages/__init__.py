"""Load independent per-genre instrument manifests. Never duplicate WAV/SFZ files."""
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
SCHEMA_VERSION = 1


def load_package(style_id: str) -> dict:
    if not style_id or not style_id.replace("_", "").isalnum():
        raise ValueError("INVALID_STYLE_PACKAGE_ID")
    path = DIRECTORY / (style_id + ".json")
    with path.open(encoding="utf-8") as reader:
        package = json.load(reader)
    if package.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("STYLE_PACKAGE_SCHEMA_MISMATCH")
    if package.get("link_mode") != "SHARED_SAMPLE_LIBRARY_REFERENCE":
        raise ValueError("STYLE_PACKAGE_MUST_LINK_SAMPLES")
    if package.get("shared_root") != "sound_resources":
        raise ValueError("STYLE_PACKAGE_MUST_REFERENCE_SHARED_BANK")
    if not isinstance(package.get("instruments"), dict):
        raise ValueError("STYLE_PACKAGE_INVALID_INSTRUMENTS")
    return package
