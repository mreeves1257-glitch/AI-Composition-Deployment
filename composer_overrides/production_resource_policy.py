"""Production instrument-resource gate for AI Composer.

An instrument ROLE in the musical score is not a playable sound. Only explicitly
approved, recorded-sample SFZ banks may render production audio. This module
does not choose substitutes or alter composition, MIDI, or the 3D mix.
"""
from __future__ import annotations
import json
from pathlib import PurePosixPath
from typing import Any

APPROVED_SAMPLE_BANKS = {
    "FREEPATS_WORLD_PERCUSSION": {"library": "FreePats World Percussion", "license": "CC0-1.0"},
    "GREG_SULLIVAN_E_PIANOS": {"library": "Greg Sullivan E-Pianos / Wurlitzer EP200", "license": "CC-BY-3.0"},
    "KARORYFER_GROWLYBASS_V1_002": {"library": "Karoryfer Growlybass", "license": "CC0"},
    "KARORYFER_SHINYGUITAR": {"library": "Karoryfer Shinyguitar", "license": "CC0-1.0"},
    "KARORYFER_BIG_RUSTY_DRUMS": {"library": "Karoryfer Big Rusty Drums", "license": "CC0-1.0"},
}

# Source-pinned authentic recordings, Jazz Ballad ONLY. Existing five banks unchanged.
APPROVED_SAMPLE_BANKS.update({
    "JAZZ_MEATBASS_PINNED": {"library": "Karoryfer Meatbass / recorded pizzicato", "license": "CC0-1.0"},
    "JAZZ_VSCO_CLARINET_PINNED": {"library": "VSCO 2 Community Edition / recorded clarinet", "license": "CC0-1.0"},
    "JAZZ_SWIRLY_BRUSH_PINNED": {"library": "Karoryfer Swirly Drums / recorded brush kit", "license": "CC0-1.0"},
})

# New banks enter this allowlist only through the checked-in, SHA-pinned
# onboarding manifest. Build preflight must audition every mapped note before
# these resources can reach a live Render service.
from pathlib import Path
_manifest = Path(__file__).with_name("verified_future_instruments.json")
if _manifest.is_file():
    _data = json.loads(_manifest.read_text(encoding="utf-8"))
    from sample_bank_onboarding import validate_manifest
    validate_manifest(_data)
    for _bank in _data["new_banks"]:
        _rid = _bank["resource_id"]
        if _rid in APPROVED_SAMPLE_BANKS:
            raise ValueError("ONBOARD_BANK_PROVENANCE_COLLISION:" + _rid)
        APPROVED_SAMPLE_BANKS[_rid] = {"library": _bank["library"], "license": _bank["license"]}

class ProductionResourceBlocked(ValueError):
    pass

def require_recorded_sample_resource(binding: dict[str, Any]) -> None:
    """Fail closed before SFZ preflight; actual sample files are checked there."""
    if not isinstance(binding, dict):
        raise ProductionResourceBlocked("RESOURCE_NOT_DECLARED")
    if binding.get("resource_type") != "SFZ_SAMPLE_LIBRARY":
        raise ProductionResourceBlocked("NON_SAMPLE_RESOURCE_BLOCKED")
    if binding.get("fallback_policy") != "NO_SYNTHETIC_SUBSTITUTION":
        raise ProductionResourceBlocked("FALLBACK_NOT_DISABLED")
    rid = binding.get("resource_id")
    approved = APPROVED_SAMPLE_BANKS.get(rid)
    if not approved:
        raise ProductionResourceBlocked("UNVERIFIED_SAMPLE_BANK:" + str(rid))
    if binding.get("library") != approved["library"] or binding.get("license") != approved["license"]:
        raise ProductionResourceBlocked("SAMPLE_PROVENANCE_MISMATCH:" + str(rid))
    mapping = binding.get("preferred_mapping")
    if not isinstance(mapping, str) or not mapping or "\\" in mapping:
        raise ProductionResourceBlocked("INVALID_SAMPLE_MAPPING")
    path = PurePosixPath(mapping)
    if path.is_absolute() or any(part in ("..", ".") for part in mapping.split("/")) or path.suffix.lower() != ".sfz":
        raise ProductionResourceBlocked("INVALID_SAMPLE_MAPPING")

def audit_bindings(registry: dict[str, Any]) -> dict[str, Any]:
    bindings = registry["targets"]["INTERNAL"].get("instrument_bindings", {})
    production = []
    blocked = []
    for instrument_id, resource in sorted(bindings.items()):
        try:
            require_recorded_sample_resource(resource)
            production.append(instrument_id)
        except ProductionResourceBlocked as exc:
            blocked.append({"instrument_id": instrument_id, "reason": str(exc)})
    return {
        "policy": "RECORDED_SAMPLE_BANKS_ONLY_NO_SYNTHETIC_SUBSTITUTION",
        "approved_resource_bank_ids": sorted(APPROVED_SAMPLE_BANKS),
        "sample_backed_binding_ids": production,
        "legacy_or_unverified_binding_ids": blocked,
        "warning": "Registry approval alone does not prove installed samples or audible output. SFZ preflight must pass.",
    }

def self_test() -> None:
    for bank_id, provenance in APPROVED_SAMPLE_BANKS.items():
        real = {"resource_type": "SFZ_SAMPLE_LIBRARY", "resource_id": bank_id,
                "library": provenance["library"], "license": provenance["license"],
                "preferred_mapping": "Programs/test.sfz", "fallback_policy": "NO_SYNTHETIC_SUBSTITUTION"}
        require_recorded_sample_resource(real)
        for alteration in [
            {"resource_type": "GM_PROGRAM"},
            {"fallback_policy": "ALLOW_SYNTHETIC_FALLBACK"},
            {"resource_id": "UNKNOWN_FAKE_LIBRARY"},
            {"preferred_mapping": "../fake.sfz"},
            {"preferred_mapping": "Programs/fake.wav"},
            {"license": "UNVERIFIED"},
        ]:
            test = dict(real, **alteration)
            try:
                require_recorded_sample_resource(test)
            except ProductionResourceBlocked:
                continue
            raise AssertionError("UNVERIFIED_INSTRUMENT_ACCEPTED:" + str(alteration))
    for invalid in (None, {}, {"render_model": "PLUCKED_BASS_CLEAR"}):
        try:
            require_recorded_sample_resource(invalid)
        except ProductionResourceBlocked:
            continue
        raise AssertionError("LEGACY_FAKE_INSTRUMENT_ACCEPTED")

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--audit-registry", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("PRODUCTION_REAL_INSTRUMENT_POLICY_TEST PASS", flush=True)
    if args.audit_registry:
        report = audit_bindings(json.loads(args.audit_registry.read_text()))
        print("PRODUCTION_INSTRUMENT_RESOURCE_AUDIT " + json.dumps(report, sort_keys=True), flush=True)
