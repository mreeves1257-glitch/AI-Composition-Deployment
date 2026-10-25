"""Profile-authoritative, non-destructive interpreter-to-event linkage for all 55 genres.

No new instrument is claimed renderable unless the existing resource resolver supports it.
"""
from collections import Counter

PROFILE_INSTRUCTIONS = (
    'instrument_role_behavior','ensemble_player_behavior','arrangement_transformation',
    'phrase_behavior','harmony_behavior','bass_behavior','percussion_behavior_if_applicable',
    'dynamic_behavior','articulation_behavior','timing_humanization_behavior',
    'continuous_performance_control','manufacturer_adapter_requirements',
    'mix_prominence_intent','sound_effects_intent','production_mastering_intent',
)



def allocate_parts(interpreted):
    """Preserve each distinct requested part; never impose a universal four-part limit."""
    return [{'part_id': part, 'instrument_id': part, 'source': 'genre_interpreter'}
            for part in interpreted['requested_instrument_parts']]


def bridge_events(interpreted, allocated, events):
    """Fail closed if any interpreted instrument was dropped during event generation."""
    if not events:
        raise ValueError('GENRE_INTERPRETER_NO_EVENTS')
    counts = Counter(e.get('instrument_id') for e in events)
    missing = [p['instrument_id'] for p in allocated if not counts[p['instrument_id']]]
    if missing:
        raise ValueError('GENRE_INTERPRETER_EVENT_PART_LOSS: '+','.join(missing))
    return {'status':'PASS','requested_part_count':len(allocated),
            'generated_event_count':len(events),'instrument_event_counts':dict(counts),
            'missing_parts':[]}


def pass_through_expression(interpreted, events):
    """Carry instructions as metadata; do not pretend renderer executed unsupported controls."""
    return {'genre_specific_instructions':dict(interpreted['musical_instructions']),
            'expression_execution_status':'INSTRUCTIONS_PRESERVED_NOT_RENDER_VERIFIED',
            'event_count':len(events)}


def interpret_genre(name, profile, requested_parts):
    """Interpret the selected genre before theory/event generation.

    This is the authoritative pre-generation handoff.  Event validation remains
    in link_genre after generation, but the musical instructions exist first.
    """
    installed = profile.get('genre_execution_pipeline')
    # The profile owns these six musical interpretation stages.  The shared
    # INSTRUMENT_SEPARATION_REGISTRATION gate is an engine-level routing integrity
    # stage inserted after realization; it does not become a second interpreter.
    required = ['GENRE_RECOGNITION','GENRE_INTERPRETER','ADAPTIVE_ARRANGEMENT',
                'MUSICAL_PERFORMANCE_REALIZATION','INSTRUMENT_CAPABILITY_RESOURCE_RESOLVER',
                'VERIFIED_RENDERING_HANDOFF']
    if not installed or installed.get('owner_profile_id') != profile.get('profile_id'):
        raise ValueError('GENRE_SPECIFIC_INTERPRETER_NOT_INSTALLED')
    if installed.get('interpreter_count') != 1 or installed.get('stages') != required:
        raise ValueError('GENRE_SPECIFIC_INTERPRETER_SEQUENCE_INVALID')
    if not profile or not profile.get('profile_id'):
        raise ValueError('GENRE_INTERPRETER_PROFILE_MISSING')
    if not requested_parts or len(requested_parts) != len(set(requested_parts)):
        raise ValueError('GENRE_INTERPRETER_PARTS_INVALID')
    from genre_recognition_fingerprints import build as build_recognition_fingerprint, validate as validate_recognition_fingerprint
    recognition_fingerprint = build_recognition_fingerprint(name, profile, requested_parts)
    validate_recognition_fingerprint(recognition_fingerprint, genre=name, profile_id=profile['profile_id'], requested_parts=requested_parts)
    return {
        'genre': name, 'profile_id': profile['profile_id'],
        'musical_instructions': {k: profile[k] for k in PROFILE_INSTRUCTIONS if k in profile},
        'requested_instrument_parts': list(requested_parts),
        'genre_recognition_fingerprint': recognition_fingerprint,
        'arrangement_policy': 'GENRE_SPECIFIC_NO_GLOBAL_PLAYER_LIMIT',
        'interpretation_stage': 'PRE_GENERATION',
    }


def link_genre(name, profile, requested_parts, events, interpreted=None):
    if interpreted is None:
        interpreted = interpret_genre(name, profile, requested_parts)
    elif interpreted.get('profile_id') != profile.get('profile_id') or interpreted.get('genre') != name:
        raise ValueError('PRE_GENERATION_INTERPRETATION_MISMATCH')
    allocated=allocate_parts(interpreted)
    bridge=bridge_events(interpreted,allocated,events)
    expression=pass_through_expression(interpreted,events)
    # A single interpreter is authoritative. These are successive execution gates,
    # not additional interpreters; retain the existing legacy keys for callers.
    from genre_recognition_fingerprints import validate as validate_recognition_fingerprint
    fingerprint = validate_recognition_fingerprint(interpreted.get('genre_recognition_fingerprint'), genre=name, profile_id=profile['profile_id'], requested_parts=requested_parts)
    recognition={'genre':name,'profile_id':profile['profile_id'],'status':'PASS',
                 'fingerprint':fingerprint,
                 'recognition_mode':fingerprint['recognition_mode'],
                 'nearest_neighbors':fingerprint['nearest_neighbors'],
                 'disambiguation_rules':fingerprint['disambiguation_rules']}
    arrangement={'requested_parts':list(requested_parts),'allocated_parts':allocated,
                 'policy':'GENRE_SPECIFIC_NO_GLOBAL_PLAYER_LIMIT'}
    realization={'status':'PASS','event_count':len(events),'event_bridge':bridge,
                 'expression_metadata':expression}
    resources={'status':'PENDING_EXISTING_INSTRUMENT_RESOLVER',
               'requested_instruments':list(requested_parts)}
    handoff={'status':'PASS_EVENT_COVERAGE_ONLY', 'render_verified':False,
             'missing_parts':bridge['missing_parts']}
    return {'status':'PASS','interpreter':interpreted,'allocation':allocated,
            'event_bridge':bridge,'enhancement_expression_passthrough':expression,
            'execution_sequence':['GENRE_RECOGNITION','GENRE_INTERPRETER',
              'ADAPTIVE_ARRANGEMENT','MUSICAL_PERFORMANCE_REALIZATION',
              'INSTRUMENT_SEPARATION_REGISTRATION','GENRE_MIX_PROMINENCE_PLAN',
              'PERFORMANCE_CAPABILITY_REQUIREMENTS','INSTRUMENT_CAPABILITY_RESOURCE_RESOLVER','VERIFIED_RENDERING_HANDOFF'],
            'genre_recognition':recognition,'adaptive_arrangement':arrangement,
            'musical_performance_realization':realization,
            'instrument_separation_registration':{'status':'PENDING_ENGINE_SEPARATOR',
                'policy':'PRESERVE_GENRE_NATIVE_PART_IDENTITIES'},
            'genre_mix_prominence_plan':{'status':'PENDING_ENGINE_MIX_PLAN',
                'policy':'COMPILE_PROFILE_MIX_HIERARCHY_AFTER_SEPARATION'},
            'performance_capability_requirements':{'status':'PENDING_ENGINE_CAPABILITY_PLAN',
                'policy':'TARGET_MUST_VERIFY_ARTICULATION_TIMING_AND_CONTINUOUS_CONTROL_CAPABILITIES'},
            'instrument_capability_resource_resolver':resources,
            'verified_rendering_handoff':handoff}
