"""Profile-authoritative pre-generation compiler for the 55-genre Composer.

This module is built forward from the R8 research proof.  It turns the selected
profile's musical contract into executable inputs *before* theory/note generation.
Genre names are not used to manufacture the semantic plan.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

PROFILE_FIELDS = (
    'groove_behavior','phrase_behavior','harmony_behavior','bass_behavior',
    'percussion_behavior_if_applicable','instrument_role_behavior',
    'ensemble_player_behavior','arrangement_transformation','dynamic_behavior',
    'articulation_behavior','timing_humanization_behavior',
)

# Shared semantic vocabulary carried forward from the R8 collision-resolution proof.
FEATURES = {
    'space':r'\bspace|sparse|silence|rests?|air\b',
    'arpeggio':r'arpegg',
    'legato':r'legato|sustained',
    'rubato':r'rubato|tempo breathing|elastic',
    'solo_coherence':r'single-performer|right/left-hand|left-hand|sole or primary',
    'triple':r'3/4|three-beat|waltz',
    'light_attack':r'brush|light kit|soft attacks?|restrained',
    'riff_vamp':r'riff|vamp',
    'sixteenth':r'sixteenth',
    'interlock':r'interlock',
    'breaks':r'breaks?|dropouts?',
    'layered_perc':r'layered percussion|percussion layers',
    'half_time':r'half-time',
    'lead_centered':r'lead-centered|vocal-like',
    'loop_evolve':r'loop-evolving|evolving textures?|gradual layer',
    'lyrical':r'lyrical|cadence points?',
    'clave':r'clave',
    'montuno':r'montuno',
    'tumbao':r'tumbao',
    'dembow':r'dembow',
    'broken_beat':r'broken|breakbeat|breaks with looseness|sample-like drums',
    'four_floor':r'four-on-floor|four-beat foundation',
    'hypnotic':r'hypnotic|minimal',
    'rolling':r'rolling bass|arpeggiation',
    'long_build':r'16/32-bar|long-form build|breakdown|peak',
    'polyrhythm':r'polyrhythm|organic percussion',
    'stutter':r'stutter|chops?|abrupt edits?',
    'hook':r'hook',
    'laidback':r'laid-back|looseness',
    'ghost':r'ghost',
    'horn_stab':r'horn stabs?|horn hits?',
    'wide_dynamic':r'wide velocity|wide dynamic',
    'automation':r'automation',
    'counterline':r'counterlines?',
    'walking3':r'walking-in-3',
    'walking':r'walking bass|continuous walking',
    'two_beat':r'two-beat|alternating[- ]bass|root/fifth',
    'pedal':r'pedal behavior|pedal harmony|pedal-based|pedal tone|pedal drone',
    'piano_pedal':r'pedal-aware|pedal-shaped',
    'sidechain':r'sidechain',
    'offbeat':r'offbeat',
    'syncopated':r'syncopat',
    'call_response':r'call-response|call/response',
    'static_harmony':r'static harmony|minimal.*harmonic|harmonic simplicity',
    'extended':r'extended|maj7|add9|dominant/minor-seventh|altered dominant|substitution|ii-v',
    'modal':r'modal',
    'chromatic':r'chromatic',
    'blues':r'blues',
    'gospel':r'gospel',
    'functional':r'functional harmony|functional cadence|common-practice|dominant motion|clear tonal',
    'power':r'power-chord|power chord',
    'strong_one':r'strong one',
    'phrase_crossbar':r'cross bar|across 3/4',
    'texture_identity':r'texture/automation rather than melody|timbral movement may replace chord movement',
}

SUPPORTED_PRODUCTION_METERS = ('4/4','3/4','2/4','6/8')
SUPPORTED_FORMS = ('verse_chorus','aba','through_composed')


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def _contract_text(profile: dict[str, Any]) -> str:
    return ' '.join(str(profile.get(field, '')) for field in PROFILE_FIELDS).lower()


def compile_semantic_contract(profile: dict[str, Any]) -> dict[str, Any]:
    text = _contract_text(profile)
    tags = sorted(key for key, pattern in FEATURES.items() if re.search(pattern, text))
    meters = list(profile.get('meter_options') or [])
    tempos = list(profile.get('tempo_bpm_range') or [])
    forms = list(profile.get('form_tendencies') or [])
    return {
        'meters': meters,
        'tempo_range': tempos,
        'forms': forms,
        'tags': tags,
        'contract_fields': {field: profile.get(field) for field in PROFILE_FIELDS},
    }


def _progression_family(contract: dict[str, Any]) -> str:
    tags = set(contract['tags'])
    harmony = str(contract['contract_fields'].get('harmony_behavior') or '').lower()
    if 'static_harmony' in tags or 'texture_identity' in tags:
        return 'static'
    if 'riff_vamp' in tags or 'power' in tags or 'vamp' in harmony:
        return 'riff'
    if 'blues' in tags:
        return 'blues'
    if 'extended' in tags:
        return 'extended'
    if 'modal' in tags:
        return 'modal'
    if 'gospel' in tags:
        return 'gospel'
    if 'functional' in tags:
        return 'functional'
    return 'tonal'


def _progression(quality: str, family: str, seedv: int) -> list[str]:
    major = quality in ('major', 'ionian')
    harmonic_minor = quality == 'harmonic_minor'
    if major:
        pools = {
            'static': [['I','IV'], ['I','vi']],
            'riff': [['I','IV','I','V'], ['I','V','IV','I']],
            'blues': [['I','IV','I','V'], ['I','IV','V','IV']],
            'extended': [['ii','V','I','vi'], ['I','vi','ii','V']],
            'modal': [['I','IV','I','IV'], ['I','vi','IV','I']],
            'gospel': [['I','IV','vi','V'], ['I','vi','IV','V']],
            'functional': [['I','IV','ii','V'], ['I','ii','V','I']],
            'tonal': [['I','V','vi','IV'], ['I','IV','V','I']],
        }
    elif harmonic_minor:
        pools = {
            'static': [['i','VI'], ['i','iv']],
            'riff': [['i','VI','iv','V'], ['i','VI','V','i']],
            'blues': [['i','iv','i','V'], ['i','VI','iv','V']],
            'extended': [['ii°','V','i','VI'], ['i','iv','V','i']],
            'modal': [['i','VI','i','VI'], ['i','iv','i','VI']],
            'gospel': [['i','iv','VI','V'], ['i','VI','iv','V']],
            'functional': [['i','iv','ii°','V'], ['i','VI','V','i']],
            'tonal': [['i','VI','iv','V'], ['i','iv','V','i']],
        }
    else:
        # Natural-minor vocabulary supported by the preserved TheoryEngine.
        pools = {
            'static': [['i','VII'], ['i','VI']],
            'riff': [['i','VII','VI','VII'], ['i','VI','VII','i']],
            'blues': [['i','iv','i','VII'], ['i','iv','VI','VII']],
            'extended': [['ii°','v','i','VI'], ['i','iv','v','i']],
            'modal': [['i','VII','i','VII'], ['i','VI','VII','i']],
            'gospel': [['i','iv','VI','VII'], ['i','VI','iv','VII']],
            'functional': [['i','iv','v','i'], ['i','VI','VII','i']],
            'tonal': [['i','VII','VI','VII'], ['i','iv','VII','i']],
        }
    choices = pools.get(family, pools['tonal'])
    cycle = list(choices[(seedv // 17) % len(choices)])
    # Variation stays within the same semantic family; never replace it with the old universal cycle.
    if len(cycle) > 2 and (seedv // 29) % 2:
        cycle = cycle[1:] + cycle[:1]
    return cycle


def _bass_behavior(contract: dict[str, Any], fallback: str) -> str:
    tags = set(contract['tags'])
    if 'walking' in tags or 'walking3' in tags:
        return 'walking'
    if 'pedal' in tags:
        return 'pedal'
    if 'two_beat' in tags:
        return 'roots_fifths'
    text = str(contract['contract_fields'].get('bass_behavior') or '').lower()
    if 'octave' in text:
        return 'broken_octave'
    if 'root' in text and 'fifth' in text:
        return 'roots_fifths'
    return fallback


def _phrase_bars(contract: dict[str, Any], seedv: int) -> int:
    text = str(contract['contract_fields'].get('phrase_behavior') or '').lower()
    nums = [int(x) for x in re.findall(r'\b(4|8|16)\s*[- ]?bar', text)]
    if not nums:
        return 4
    choices = sorted(set(nums))
    return choices[(seedv // 31) % len(choices)]


def compile_generation_plan(profile: dict[str, Any], baseline: tuple, creation_seed: int = 0) -> dict[str, Any]:
    """Compile the selected profile into executable pre-generation inputs.

    baseline is the existing (tonic, quality, meter, bpm, form, bass_behavior)
    family baseline.  It remains a fallback only; profile contract fields are
    compiled before TheoryEngine or note generation is called.
    """
    tonic, quality, fallback_meter, fallback_bpm, fallback_form, fallback_bass = baseline
    contract = compile_semantic_contract(profile)
    semantic_basis = {
        'meters': contract['meters'], 'tempo_range': contract['tempo_range'],
        'forms': contract['forms'], 'tags': contract['tags'],
        'harmony_behavior': contract['contract_fields'].get('harmony_behavior'),
        'bass_behavior': contract['contract_fields'].get('bass_behavior'),
        'phrase_behavior': contract['contract_fields'].get('phrase_behavior'),
    }
    # Preserve the already-verified Create-New variation seed for tempo/meter/form/key
    # so this integration does not regress existing renderer/sample timing.  Semantic
    # contract data, not the profile ID, still chooses the musical grammar family.
    seedv = int(hashlib.sha256(f"{profile.get('profile_id')}:{creation_seed}".encode()).hexdigest()[:8], 16)
    semantic_seed = int(hashlib.sha256((json.dumps(semantic_basis, sort_keys=True, default=str) + ':' + str(creation_seed)).encode()).hexdigest()[:8], 16)

    tr = contract['tempo_range'] or [fallback_bpm, fallback_bpm]
    lo, hi = int(tr[0]), int(tr[-1])
    bpm = lo + (seedv % max(1, hi - lo + 1)) if hi > lo else lo

    requested_meters = contract['meters'] or [fallback_meter]
    supported_meters = [m for m in requested_meters if m in SUPPORTED_PRODUCTION_METERS]
    if not supported_meters:
        supported_meters = [fallback_meter]
    meter = supported_meters[seedv % len(supported_meters)]

    supported_forms = [f for f in (contract['forms'] or [fallback_form]) if f in SUPPORTED_FORMS]
    form = supported_forms[(seedv // 7) % len(supported_forms)] if supported_forms else fallback_form

    family = _progression_family(contract)
    progression = _progression(quality, family, semantic_seed)
    bass = _bass_behavior(contract, fallback_bass)
    phrase_bars = _phrase_bars(contract, semantic_seed)

    plan = {
        'status': 'PASS',
        'source': 'GENRE_PROFILE_AUTHORITY_PRE_GENERATION',
        'profile_id': profile.get('profile_id'),
        'semantic_contract': semantic_basis,
        'semantic_tags': contract['tags'],
        'tempo_bpm': int(bpm),
        'meter': meter,
        'form': form,
        'phrase_bars': phrase_bars,
        # Do not allow a short motif to become the entire composition. A motif may
        # recur or be transformed inside this window, but literal melody reuse is
        # not eligible until at least sixteen bars of developed material exist.
        'melody_development_bars': 16,
        'literal_melody_reuse_after_bars': 16,
        # Ensemble size belongs to the genre/arrangement, not a global four-player cap.
        'player_limit_policy': 'NO_ARTIFICIAL_GLOBAL_CAP',
        'bass_behavior': bass,
        'harmony_family': family,
        'roman_progression': progression,
        'unsupported_meter_options_preserved': [m for m in requested_meters if m not in SUPPORTED_PRODUCTION_METERS],
        'variation_seed': seedv,
        'seed_basis': 'PRESERVED_PROFILE_VARIATION_SEED_WITH_SEMANTIC_GRAMMAR',
    }
    plan['plan_sha256'] = _hash(plan)
    return plan