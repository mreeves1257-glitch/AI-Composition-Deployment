"""Actual ROCK event coverage gate; never equate bass-only audio with finished ROCK."""
from collections import Counter
from pathlib import Path
import json, tempfile
from engine import AICompositionEngine
from production_resource_resolver import preflight_bindings

ROLE_BINDINGS = {
    'electric_bass': ('electric_bass_guitar',),
    'electric_guitar': ('electric_guitar:RHYTHM_POWER_CHORDS',),
    'lead_guitar': ('electric_guitar:LEAD_MELODY',),
    'drums': ('kick_drum_rock','snare_drum','hi_hat','ride_cymbal','crash_cymbal','tom_drum','tom_tom'),
}

def inspect_rock(root=None):
    root = Path(root or Path(__file__).resolve().parent)
    with tempfile.TemporaryDirectory() as td:
        result = AICompositionEngine(history_path=Path(td)/'history.json').run('ROCK', mode='quick')
    counts = Counter(e['instrument_id'] for e in result['modules']['performance']['events'])
    resources = preflight_bindings(root)
    roles = {}
    for instrument, count in sorted(counts.items()):
        bindings = ROLE_BINDINGS.get(instrument, ())
        ready = bool(bindings) and all(resources.get(b, {}).get('status') == 'SAMPLE_SET_READY' for b in bindings)
        roles[instrument] = {'events': count, 'resource_ready': ready,
                             'bindings': {b: resources.get(b, {}).get('status','NOT_DECLARED') for b in bindings},
                             'status': 'RESOURCE_READY_AUDIO_NOT_YET_VERIFIED' if ready else 'BLOCKED_MISSING_RECORDED_LIBRARY'}
    return {'genre':'ROCK', 'total_original_events':sum(counts.values()),
            'roles':roles, 'full_audio_ready':all(v['resource_ready'] for v in roles.values()),
            'full_audio_verified':False,
            'note':'Bass-only WAV proof does not constitute a complete ROCK render.'}

if __name__ == '__main__':
    report=inspect_rock()
    output=Path(__file__).resolve().parent/'ROCK_FULL_INSTRUMENT_GATE_2026-10-10.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
