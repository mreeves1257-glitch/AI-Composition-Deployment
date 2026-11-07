"""Conservative compatibility gate for the original Karoryfer production mappings.

Based on publisher's SFZ definitions, not a replacement for a full SFZ engine.
No source instruments or original target registry are modified.
"""
from pathlib import Path

# Confirmed against upstream Programs/electric_one.sfz (master) and
# Programs/01-full.sfz (main), 2026-10-10.
UPSTREAM_REQUIREMENTS = {
    'KARORYFER_SHINYGUITAR': {
        'mapping': 'Programs/electric_one.sfz',
        'features': ('CC100 pickup blend / crossfade', 'CC106 release noise / envelope',
                     'CC107 voice selection', 'velocity curves', 'random round robin'),
        'required_backend': 'full SFZ engine with controller and crossfade support',
    },
    'KARORYFER_BIG_RUSTY_DRUMS': {
        'mapping': 'Programs/01-full.sfz',
        'features': ('nested #include mapping graph', 'SFZ #define macros',
                     'CC4 hi-hat pedal', 'per-drum microphone and articulation controls'),
        'required_backend': 'full SFZ engine with preprocessor and controller support',
    },
}


def assess_production_mapping(resource_id: str, mapping: str, backend: str = 'internal_005') -> dict:
    """Fail closed: internal 005 is NOT compatible with these exact mappings."""
    item = UPSTREAM_REQUIREMENTS.get(resource_id)
    if not item or mapping != item['mapping']:
        return {'status': 'NOT_ASSESSED', 'resource_id': resource_id, 'mapping': mapping}
    if backend == 'internal_005':
        return {'status': 'REQUIRES_FULL_SFZ_BACKEND', 'resource_id': resource_id,
                'mapping': mapping, 'features': list(item['features']),
                'required_backend': item['required_backend']}
    return {'status': 'BACKEND_COMPATIBILITY_NOT_YET_VERIFIED', 'resource_id': resource_id,
            'mapping': mapping, 'backend': backend, 'required_backend': item['required_backend']}
