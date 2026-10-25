"""Resolve production SFZ bindings only to genuine, locally present library assets.

Never substitutes an instrument. A returned path is not proof of playable audio;
SFZ sample preflight and a real render are separate release gates.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def resolve_bindings(root=ROOT):
    root = Path(root)
    registry = json.loads((root / 'target_registry.json').read_text())
    bindings = registry['targets']['INTERNAL']['instrument_bindings']
    library_root = root / 'sound_resources'
    results = {}
    for role, binding in bindings.items():
        resource_id = binding['resource_id']
        preferred = Path(binding['preferred_mapping'])
        if preferred.is_absolute() or '..' in preferred.parts:
            results[role] = {'status': 'INVALID_MAPPING', 'resource_id': resource_id}
            continue
        pack = library_root / resource_id
        candidate = pack / preferred
        if candidate.is_file() and candidate.suffix.lower() == '.sfz':
            results[role] = {'status': 'MAPPING_FOUND', 'resource_id': resource_id,
                             'sfz': str(candidate.relative_to(root))}
        else:
            results[role] = {'status': 'MISSING_MAPPING', 'resource_id': resource_id,
                             'expected': str(candidate.relative_to(root))}
    return results


def preflight_bindings(root=ROOT):
    """Check every exact binding's complete sample graph without changing mappings."""
    from sfz_renderer_adapter import validate_sfz_samples, SFZRendererError
    root = Path(root).resolve()
    resolved = resolve_bindings(root)
    for role, record in resolved.items():
        if record['status'] != 'MAPPING_FOUND':
            continue
        sfz = (root / record['sfz']).resolve()
        # Do not follow a symlink out of the designated resource pack.
        pack = (root / 'sound_resources' / record['resource_id']).resolve()
        if not sfz.is_relative_to(pack):
            record['status'] = 'INVALID_MAPPING'
            record.pop('sfz', None)
            continue
        try:
            record['samples'] = validate_sfz_samples(sfz, allowed_root=pack)
            record['status'] = 'SAMPLE_SET_READY'
        except (SFZRendererError, OSError, UnicodeError) as exc:
            record['status'] = 'SAMPLE_SET_INCOMPLETE'
            record['detail'] = str(exc)
    return resolved


if __name__ == '__main__':
    results = preflight_bindings()
    output = ROOT / 'PRODUCTION_RESOURCE_RESOLUTION_2026-10-10.json'
    output.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({'sample_ready': sum(v['status'] == 'SAMPLE_SET_READY' for v in results.values()),
                      'total': len(results), 'report': str(output)}, indent=2))