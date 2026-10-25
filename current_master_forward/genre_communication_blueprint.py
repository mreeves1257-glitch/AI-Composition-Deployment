"""Shared Orchestra-style communication blueprint for non-Classical genres.

This module copies only the proven assembly/communication order. It never copies
Classical musical content into another genre. Classical remains on its existing
specialized path unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json

BLUEPRINT_ID = 'GENRE_COMMUNICATION_BLUEPRINT_V2_WITH_INSTRUMENT_SEPARATOR'
SEQUENCE = (
    'GENRE_RECOGNITION',
    'GENRE_INTERPRETER',
    'ADAPTIVE_ARRANGEMENT',
    'MUSICAL_PERFORMANCE_REALIZATION',
    'INSTRUMENT_SEPARATION_REGISTRATION',
    'GENRE_MIX_PROMINENCE_PLAN',
    'PERFORMANCE_CAPABILITY_REQUIREMENTS',
    'INSTRUMENT_CAPABILITY_RESOURCE_RESOLVER',
    'VERIFIED_RENDERING_HANDOFF',
    'EXISTING_INSTRUMENT_RENDERER',
    'ORIGINAL_3D_MIXER',
)

# Carry the complete genre contract, not only the subset used by the legacy
# semantic compiler. This keeps genre identity intact across every handoff.
INSTRUCTION_FIELDS = (
    'tempo_bpm_range', 'meter_options', 'form_tendencies', 'groove_behavior',
    'phrase_behavior', 'harmony_behavior', 'bass_behavior',
    'percussion_behavior_if_applicable', 'instrument_role_behavior',
    'ensemble_player_behavior', 'arrangement_transformation', 'dynamic_behavior',
    'articulation_behavior', 'timing_humanization_behavior',
    'continuous_performance_control', 'sound_effects_intent',
    'mix_prominence_intent', 'production_mastering_intent',
    'manufacturer_adapter_requirements', 'resolution_policy',
)


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def build(name, profile, requested_parts, interpreted, generation_plan, controlled_input=None):
    """Create the immutable communication packet before note generation/assembly."""
    if name == 'Classical':
        raise ValueError('CLASSICAL_USES_EXISTING_SPECIALIZED_PATH')
    if interpreted.get('genre') != name or interpreted.get('profile_id') != profile.get('profile_id'):
        raise ValueError('COMMUNICATION_BLUEPRINT_INTERPRETER_MISMATCH')
    parts = list(requested_parts)
    if parts != list(interpreted.get('requested_instrument_parts', [])):
        raise ValueError('COMMUNICATION_BLUEPRINT_PARTS_MISMATCH')
    instructions = {field: copy.deepcopy(profile.get(field)) for field in INSTRUCTION_FIELDS if field in profile}
    from genre_recognition_fingerprints import validate as validate_recognition_fingerprint
    recognition_fingerprint = validate_recognition_fingerprint(
        interpreted.get('genre_recognition_fingerprint'), genre=name,
        profile_id=profile['profile_id'], requested_parts=parts)
    packet = {
        'genre': name,
        'profile_id': profile['profile_id'],
        'genre_specific_instructions': instructions,
        'genre_recognition_fingerprint': copy.deepcopy(recognition_fingerprint),
        'requested_instrument_parts': parts,
        'arrangement_policy': interpreted.get('arrangement_policy'),
        'player_limit_policy': 'NO_ARTIFICIAL_GLOBAL_CAP',
        'melody_development_bars': max(16, int((generation_plan or {}).get('melody_development_bars', 16))),
        'generation_plan': copy.deepcopy(generation_plan),
    }
    if controlled_input is not None:
        packet['controlled_input'] = copy.deepcopy(controlled_input)
    return {
        'status': 'PASS',
        'blueprint_id': BLUEPRINT_ID,
        'sequence': list(SEQUENCE),
        'instruction_packet': packet,
        'instruction_packet_sha256': _sha(packet),
        'rule': 'GENRE_IDENTITY_INSTRUCTIONS_AND_DISTINCT_INSTRUMENT_REGISTRATIONS_SURVIVE_EVERY_HANDOFF',
    }


def validate(blueprint, *, genre=None, profile_id=None, requested_parts=None, generation_plan=None):
    if not isinstance(blueprint, dict) or blueprint.get('blueprint_id') != BLUEPRINT_ID:
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_MISSING_OR_INVALID')
    if blueprint.get('sequence') != list(SEQUENCE):
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_SEQUENCE_INVALID')
    packet = blueprint.get('instruction_packet') or {}
    if _sha(packet) != blueprint.get('instruction_packet_sha256'):
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_HASH_MISMATCH')
    if genre is not None and packet.get('genre') != genre:
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_GENRE_MISMATCH')
    if profile_id is not None and packet.get('profile_id') != profile_id:
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_PROFILE_MISMATCH')
    if requested_parts is not None and list(packet.get('requested_instrument_parts', [])) != list(requested_parts):
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_PARTS_MISMATCH')
    if generation_plan is not None and packet.get('generation_plan') != generation_plan:
        raise ValueError('GENRE_COMMUNICATION_BLUEPRINT_PLAN_MISMATCH')
    from genre_recognition_fingerprints import validate as validate_recognition_fingerprint
    validate_recognition_fingerprint(packet.get('genre_recognition_fingerprint'),
        genre=packet.get('genre'), profile_id=packet.get('profile_id'),
        requested_parts=packet.get('requested_instrument_parts', []))
    return packet