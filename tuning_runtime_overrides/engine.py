"""October 2 working composition chain. No audio synthesis or genre substitution."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os

from genre_selector import GenreSelector
from instrument_program import InstrumentProgram
from target_program import TargetProgram
from performance_executor import PerformanceExecutor
from output_handoff import execute_output_handoff, preflight_audio_resources, execute_audio_render

ROOT = Path(__file__).resolve().parent


class AICompositionEngine:
    def __init__(self, history_path=None):
        self.genre = GenreSelector(
            ROOT / 'genre_registry_WORKING_GENRE_COMPLETE_2026-10-02_182810_CDT.json',
            ROOT / 'genre_menu_catalog_WORKING_2026-09-28.json')
        source = ROOT / 'AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py'
        spec = importlib.util.spec_from_file_location('composition_genre_adapter', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.theory = module.GenreExecutionAdapter(history_path=history_path)
        self.instrument = InstrumentProgram(ROOT / 'instrument_library.json')
        self.target = TargetProgram(ROOT / 'target_registry.json')
        self.performance = PerformanceExecutor()

    @staticmethod
    def _hash(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def run(self, genre_name, target_id='INTERNAL', mode='normal', render_audio=True, analyze_audio=True, tuning_reference_hz=440):
        with self.theory.history_lock():
            return self._run(genre_name, target_id, mode, render_audio, analyze_audio, tuning_reference_hz)

    def _run(self, genre_name, target_id='INTERNAL', mode='normal', render_audio=True, analyze_audio=True, tuning_reference_hz=440):
        from musical_tuning import validate_reference
        tuning_reference_hz = validate_reference(tuning_reference_hz)
        selection = self.genre.select(genre_name)
        theory = self.theory.create_new(genre_name, mode=mode, remember=False)
        if theory.get('status') != 'PASS':
            return {'status': 'BLOCKED', 'stage': 'THEORY', 'reason': theory['status'],
                    'genre': genre_name, 'theory_package': theory}
        if selection['profile'].get('profile_id') != theory['profile_id']:
            raise ValueError('GENRE_PROFILE_ID_MISMATCH')
        if not theory.get('events'):
            raise ValueError('EMPTY_COMPOSITION_EVENTS')
        used = {event['instrument_id'] for event in theory['events']}
        missing_parts = sorted(set(theory.get('palette', [])) - used)
        if missing_parts:
            return {'status': 'BLOCKED', 'stage': 'THEORY', 'genre': genre_name,
                    'reason': 'DECLARED_INSTRUMENT_PART_NOT_GENERATED', 'missing': missing_parts}
        theory = dict(theory, authority='THEORY_ONLY', program='THEORY')
        instruments = self.instrument.resolve_events(theory['events'])
        if instruments.get('status') == 'BLOCKED':
            return {'status': 'BLOCKED', 'stage': 'INSTRUMENT', 'genre': genre_name,
                    'reason': 'INSTRUMENT_PROFILE_MISSING', 'missing': instruments['missing']}
        target = self.target.resolve(target_id, instruments)
        if target.get('status') == 'BLOCKED':
            return {'status': 'BLOCKED', 'stage': 'TARGET', 'genre': genre_name,
                    'reason': target['reason'], 'missing': target.get('missing', [])}
        performance = self.performance.execute(theory, instruments, target, theory['events'])
        if performance['events'] != theory['events']:
            raise ValueError('PERFORMANCE_EVENT_LOSS')
        modules = {'genre': selection, 'theory': theory, 'instrument': instruments,
                   'target': target, 'performance': performance}
        # Commit history only after a successful complete internal handoff.
        self.theory._remember(theory['composition_fingerprint'], theory['musical_content_fingerprint'])
        result = {'status': ('PERFORMANCE_READY_RESOURCE_REQUIRED' if target.get('status')=='RESOURCE_REQUIRED' else 'READY_FOR_OUTPUT_HANDOFF'), 'genre': genre_name,
                'resource_requirements':target.get('missing',[]),
                'order': ['GENRE_SELECTION', 'THEORY', 'INSTRUMENT', 'TARGET', 'PERFORMANCE', 'OUTPUT_HANDOFF'],
                'module_hashes': {key: self._hash(value) for key, value in modules.items()},
                'modules': modules, 'engine_manipulation': False,
                'audio_rendered': False, 'tuning_reference_hz': tuning_reference_hz}
        if target_id=='INTERNAL' and (ROOT/'resource_connections.json').is_file():
            # Musical data handoff is independent of installed sound resources.
            result['output_handoff']=execute_output_handoff(dict(result,status='READY_FOR_OUTPUT_HANDOFF'))
            result['order'].append('EXECUTABLE_OUTPUT_CORE_001')
            from approved_audio_render import preflight, render
            result['audio_resource_preflight']=preflight(result)
            result['order'].append('EXACT_APPROVED_RESOURCE_PREFLIGHT')
            if render_audio:
                result['audio_render']=render(result,result['output_handoff'])
                result['audio_rendered']=bool(result['audio_render'].get('audio_rendered'))
                if result['audio_rendered']:
                    result['status']='AUDIO_RENDER_PASS'
                    result['order'].extend(['APPROVED_SOURCE_STEM_RENDER','ORIGINAL_3D_MIXER','FINISHED_MUSIC'])
                    if analyze_audio:
                        from composition_analysis import analyze
                        result['analysis'] = analyze(result, result['audio_render'],
                            Path(result['audio_render']['wav_path']).parent/'analysis')
                        result['order'].append('ADVISORY_AUDIO_ANALYSIS')
                else:
                    result['status']=result['audio_render']['status']
                    result['reason']=result['audio_render'].get('reason')
            else:
                result['status']='MIDI_READY_AUDIO_NOT_REQUESTED'
            return result
        if result['status'] == 'READY_FOR_OUTPUT_HANDOFF':
            result['output_handoff'] = execute_output_handoff(result)
            result['order'].append('EXECUTABLE_OUTPUT_CORE_001')
            result['audio_resource_preflight'] = preflight_audio_resources(result)
            result['order'].append('AUDIO_RESOURCE_PREFLIGHT')
            if os.environ.get('AI_COMP_APPROVED_SF2_SUBSTITUTE') == '1' and result['audio_resource_preflight'].get('status') != 'AUDIO_RENDER_RESOURCES_READY':
                from substitute_resource_gate import preflight_substitute
                result['original_audio_resource_preflight'] = result['audio_resource_preflight']
                result['audio_resource_preflight'] = preflight_substitute(result)
                result['order'].append('EXPLICIT_SF2_RESOURCE_RECOGNITION')
            if result['audio_resource_preflight'].get('status') == 'SUBSTITUTE_RESOURCE_RECOGNIZED':
                from substitute_live_bridge import run as render_approved_substitute
                bridge = render_approved_substitute(genre_name, engine_result=result)
                result['audio_render'] = bridge
                result['audio_rendered'] = bool(bridge.get('full_composer_to_render_certified'))
                result['order'].append('APPROVED_SF2_AND_RECORDED_BASS_RENDER')
            elif result['audio_resource_preflight'].get('status') == 'AUDIO_RENDER_RESOURCES_READY':
                result['audio_render'] = execute_audio_render(result, result['output_handoff'])
                result['audio_rendered'] = bool(result['audio_render'].get('audio_rendered'))
                result['order'].append('SFZ_AUDIO_RENDER')
            else:
                result['audio_render'] = result['audio_resource_preflight']
        if result.get('audio_render') and not result['audio_rendered']:
            result['status'] = result['audio_render']['status']
            result['reason'] = result['audio_render'].get('reason')
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the internal AI Composition chain; audio output remains separate.')
    parser.add_argument('genre')
    parser.add_argument('--target', default='INTERNAL')
    args = parser.parse_args()
    print(json.dumps(AICompositionEngine().run(args.genre, args.target), indent=2))
