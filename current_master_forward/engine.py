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
        self.theory_module_profiles = module.profiles
        self.instrument = InstrumentProgram(ROOT / 'instrument_library.json')
        self.target = TargetProgram(ROOT / 'target_registry.json')
        self.performance = PerformanceExecutor()

    @staticmethod
    def _hash(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def run(self, genre_name, target_id='INTERNAL', mode='normal', controlled_input=None, audio_backend=None, tuning_reference_hz=440):
        from musical_tuning import validate_reference
        tuning_reference_hz = validate_reference(tuning_reference_hz)
        selection = self.genre.select(genre_name)
        audio_backend = audio_backend or os.environ.get('AI_COMP_AUDIO_BACKEND', 'PRESERVED')
        if audio_backend not in ('PRESERVED', 'APPROVED_SF2'):
            raise ValueError('UNKNOWN_AUDIO_BACKEND')
        if tuning_reference_hz != 440 and audio_backend != 'APPROVED_SF2':
            raise ValueError('432_TUNING_REQUIRES_APPROVED_SF2_AUDIO_BACKEND')
        if controlled_input is not None:
            from controlled_genre_input import create_controlled
            theory = create_controlled(self.theory, genre_name, self.theory_module_profiles[genre_name], controlled_input, mode)
        else:
            theory = self.theory.create_new(genre_name, mode=mode, remember=False)
        if theory.get('status') != 'PASS':
            return {'status': 'BLOCKED', 'stage': 'THEORY', 'reason': theory['status'],
                    'genre': genre_name, 'theory_package': theory}
        if selection['profile'].get('profile_id') != theory['profile_id']:
            raise ValueError('GENRE_PROFILE_ID_MISMATCH')
        linkage=theory.get('genre_interpreter_linkage')
        if linkage is None or linkage.get('status')!='PASS':
            raise ValueError('GENRE_INTERPRETER_LINKAGE_MISSING')
        if linkage['interpreter']['profile_id']!=selection['profile']['profile_id']:
            raise ValueError('GENRE_INTERPRETER_PROFILE_ID_MISMATCH')
        from genre_recognition_fingerprints import validate as validate_recognition_fingerprint
        recognition_fingerprint = validate_recognition_fingerprint(
            linkage['interpreter'].get('genre_recognition_fingerprint'), genre=genre_name,
            profile_id=selection['profile']['profile_id'], requested_parts=theory.get('palette', []))
        blueprint=None
        if genre_name != 'Classical':
            from genre_communication_blueprint import validate as validate_communication_blueprint, SEQUENCE
            blueprint=theory.get('communication_blueprint')
            validate_communication_blueprint(blueprint,genre=genre_name,profile_id=selection['profile'].get('profile_id'),requested_parts=theory.get('palette',[]),generation_plan=theory.get('pre_generation_genre_plan',{}))
        if not theory.get('events'):
            raise ValueError('EMPTY_COMPOSITION_EVENTS')
        used = {event['instrument_id'] for event in theory['events']}
        missing_parts = sorted(set(theory.get('palette', [])) - used)
        if missing_parts:
            return {'status': 'BLOCKED', 'stage': 'THEORY', 'genre': genre_name,
                    'reason': 'DECLARED_INSTRUMENT_PART_NOT_GENERATED', 'missing': missing_parts}
        # Execute the profile's dynamic contour BEFORE instrument separation. V1 is
        # deliberately conservative: no pitch/timing/duration/instrument mutation.
        from genre_performance_realization import realize as realize_genre_performance
        realization = realize_genre_performance(
            genre_name, selection['profile'], theory['events'],
            generation_plan=theory.get('pre_generation_genre_plan',{}),
            meter=theory.get('meter','4/4'), bars=theory.get('bars'))
        theory = dict(theory, events=realization['events'],
                      musical_performance_realization=realization['manifest'])
        # Preserve each arranged instrument/section as an independent registration
        # before resource resolution.  This is a routing/identity stage only; it
        # never invents notes or instruments.
        from instrument_separator import separate_events, verify_instrument_resolution
        separated = separate_events(genre_name, theory['events'])
        from genre_mix_prominence_plan import build as build_mix_prominence, validate as validate_mix_prominence
        mix_prominence = build_mix_prominence(genre_name, selection['profile'], separated['manifest']['registrations'],
                                              separated['events'], self.theory_module_profiles)
        validate_mix_prominence(mix_prominence, separated['manifest']['registrations'])
        from genre_performance_capability_requirements import build as build_capability_requirements, validate as validate_capability_requirements
        capability_requirements = build_capability_requirements(genre_name, selection['profile'], separated['manifest']['registrations'],
                                                                 separated['events'], self.theory_module_profiles)
        validate_capability_requirements(capability_requirements, separated['manifest']['registrations'])
        theory = dict(theory, events=separated['events'],
                      instrument_separator=separated['manifest'],
                      genre_mix_prominence_plan=mix_prominence,
                      performance_capability_requirements=capability_requirements,
                      authority='THEORY_ONLY', program='THEORY')
        instruments = self.instrument.resolve_events(theory['events'])
        instruments = dict(instruments, genre_mix_prominence_plan=mix_prominence,
                           performance_capability_requirements=capability_requirements)
        if instruments.get('status') == 'BLOCKED':
            return {'status': 'BLOCKED', 'stage': 'INSTRUMENT', 'genre': genre_name,
                    'reason': 'INSTRUMENT_PROFILE_MISSING', 'missing': instruments['missing']}
        separator_resolution = verify_instrument_resolution(separated['manifest'], instruments)
        instruments = dict(instruments, instrument_separator_resolution=separator_resolution)
        if blueprint is not None:
            instruments=dict(instruments,genre_communication_blueprint=blueprint,communication_stage='INSTRUMENT_CAPABILITY_RESOURCE_RESOLVER')
        target = self.target.resolve(target_id, instruments)
        if target.get('status') == 'BLOCKED':
            return {'status': 'BLOCKED', 'stage': 'TARGET', 'genre': genre_name,
                    'reason': target['reason'], 'missing': target.get('missing', [])}
        if blueprint is not None:
            target=dict(target,genre_communication_blueprint=blueprint,communication_stage='VERIFIED_RENDERING_HANDOFF')
        performance = self.performance.execute(theory, instruments, target, theory['events'])
        if performance['events'] != theory['events']:
            raise ValueError('PERFORMANCE_EVENT_LOSS')
        modules = {'genre': selection, 'theory': theory, 'instrument': instruments,
                   'target': target, 'performance': performance,
                   'genre_recognition_fingerprint': recognition_fingerprint}
        # Commit history only after a successful complete internal handoff.
        result = {'status': ('PERFORMANCE_READY_RESOURCE_REQUIRED' if target.get('status')=='RESOURCE_REQUIRED' else 'READY_FOR_OUTPUT_HANDOFF'), 'genre': genre_name,
                'resource_requirements':target.get('missing',[]),
                'order': ['GENRE_SELECTION', 'THEORY', 'MUSICAL_PERFORMANCE_REALIZATION', 'INSTRUMENT_SEPARATOR', 'GENRE_MIX_PROMINENCE_PLAN', 'PERFORMANCE_CAPABILITY_REQUIREMENTS', 'INSTRUMENT', 'TARGET', 'PERFORMANCE_VALIDATION', 'OUTPUT_HANDOFF'],
                'module_hashes': {key: self._hash(value) for key, value in modules.items()},
                'modules': modules, 'engine_manipulation': False,
                'audio_rendered': False, 'tuning_reference_hz': tuning_reference_hz}
        if blueprint is not None:
            result['communication_blueprint']=blueprint
            result['genre_communication_order']=list(SEQUENCE)
        if audio_backend == 'APPROVED_SF2':
            result['status'] = 'READY_FOR_OUTPUT_HANDOFF'
            result['output_handoff'] = execute_output_handoff(result)
            from approved_audio_pipeline import render
            result['audio_render'] = render(result)
            result['audio_rendered'] = True
            self.theory._remember(theory['composition_fingerprint'])
            result['status'] = 'AUDIO_RENDER_PASS'
            result['order'] += ['EXECUTABLE_OUTPUT_CORE_001', 'APPROVED_SF2_RENDER', 'ORIGINAL_OBJECT_3D_MIXER']
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
        self.theory._remember(theory['composition_fingerprint'])
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the internal AI Composition chain; audio output remains separate.')
    parser.add_argument('genre')
    parser.add_argument('--target', default='INTERNAL')
    args = parser.parse_args()
    print(json.dumps(AICompositionEngine().run(args.genre, args.target), indent=2))