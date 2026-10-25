"""October 3 AI Composition Sandbox -> preserved September 27 Output Core handoff.
No composition, theory, instrument, or target decisions are made here.
"""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
from dataclasses import replace
import os

from AI_Comp_Executable_Output_Core_001 import (
    CompositionExecutionPackage, MusicalEvent, TimeSignature,
    OutputManager, RenderRequest, OutputType, write_output_package,
)

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get('AI_COMP_OUTPUT_ROOT', str(ROOT.parent / 'AI_Comp_Outputs'))) / 'render_handoff'


def _fraction(value):
    return Fraction(str(value)).limit_denominator(9600)


def build_execution_package(engine_result):
    theory = engine_result['modules']['theory']
    meter = theory['meter']
    if isinstance(meter, dict):
        beats = int(meter.get('numerator', meter.get('beats', 4)))
        beat_type = int(meter.get('denominator', meter.get('beat_type', 4)))
    elif isinstance(meter, str) and '/' in meter:
        beats, beat_type = (int(x) for x in meter.split('/', 1))
    else:
        beats, beat_type = 4, 4
    # Stage 3: reject loss or corruption of the per-note performance schedule.
    # This validates existing instructions; it never invents articulation or dynamics.
    performance = engine_result['modules'].get('performance', {})
    schedule = performance.get('articulation_event_schedule')
    if schedule is None or len(schedule) != len(theory['events']):
        raise ValueError('OUTPUT_ARTICULATION_SCHEDULE_MISSING_OR_INCOMPLETE')
    for index, (item, source) in enumerate(zip(schedule, theory['events'])):
        if item.get('event_index') != index:
            raise ValueError('OUTPUT_ARTICULATION_SCHEDULE_ORDER_MISMATCH')
        for field in ('track_id', 'articulation', 'start_beat', 'duration_beats', 'velocity', 'dynamic'):
            if item.get(field) != source.get(field):
                raise ValueError('OUTPUT_ARTICULATION_SCHEDULE_SOURCE_MISMATCH::' + field)
    events=[]
    for i,e in enumerate(theory['events'],1):
        midi=e.get('midi')
        if midi is None:
            continue
        events.append(MusicalEvent(
            event_id=f"E{i:06d}", track_id=str(e['track_id']), instrument_id=str(e['instrument_id']),
            start_beats=_fraction(e['start_beat']), duration_beats=_fraction(e['duration_beats']),
            midi_note=int(midi), velocity=max(1,min(127,int(e.get('velocity',80)))),
            articulation=e.get('articulation'), dynamic=e.get('dynamic')
        ))
    if not events:
        raise ValueError('OUTPUT_HANDOFF_NO_PITCHED_EVENTS')
    routing = {}
    for e in theory['events']:
        route = routing.setdefault(str(e['track_id']), {'percussion': False})
        route['percussion'] |= bool(e.get('drum'))
    for item in engine_result['modules']['target'].get('resolved_resources', []):
        route = routing.setdefault(str(item['track_id']), {'percussion': False})
        route.update(item.get('resource', {}).get('midi_mapping', {}))
    # Big Rusty brush articulations are selected by per-kit-member CCs.
    # Keep this in MIDI routing/output, not composition theory.
    for e in theory['events']:
        if e.get('instrument_id') != 'brush_drums':
            continue
        route = routing.setdefault(str(e['track_id']), {'percussion': True})
        if e.get('drum') == 'snare':
            route.setdefault('initial_cc', {})['25'] = 80
        elif e.get('drum') == 'ride':
            route.setdefault('initial_cc', {})['28'] = 80
        elif e.get('drum') == 'hat':
            route.setdefault('initial_cc', {})['27'] = 80
        elif e.get('drum') == 'tom':
            route.setdefault('initial_cc', {})['26'] = 80
    fingerprint=theory.get('composition_fingerprint','')
    is_classical=engine_result.get('genre','').strip().lower() == 'classical'
    orchestra_players=int(theory.get('orchestral_player_count',0) or 0)
    # The legacy Classical CC11 expression path was designed for the four-player
    # chamber pilot and allocates scarce MIDI channels per overlapping voice. A
    # full orchestra uses ordinary multitrack polyphony/dynamics instead of being
    # forced back to four players by that implementation detail.
    chamber_expression=is_classical and orchestra_players <= 4
    return CompositionExecutionPackage(
        package_id='COMP__'+fingerprint[:16]+('_A432' if engine_result.get('tuning_reference_hz',440)==432 else ''), title=f"AI Composition - {engine_result['genre']}",
        tempo_bpm=float(theory['tempo_bpm']), time_signature=TimeSignature(beats,beat_type), ppq=480,
        events=tuple(events), metadata=((('tempo_map',json.dumps(theory['tempo_map'])),) if theory.get('tempo_map') else ()) + (('genre',engine_result['genre']),('source_fingerprint',fingerprint),('handoff','OCT03_TO_SEP27_OUTPUT_CORE'),('midi_routing',json.dumps(routing)),('orchestral_player_count',str(orchestra_players)),('classical_expression_enabled', 'true' if chamber_expression else 'false'),('classical_instrument_envelopes_enabled', 'true' if chamber_expression else 'false'))
    )


def execute_output_handoff(engine_result):
    if engine_result.get('status') != 'READY_FOR_OUTPUT_HANDOFF':
        return {'status':'OUTPUT_BLOCKED','reason':engine_result.get('status'),'audio_rendered':False}
    package=build_execution_package(engine_result)
    request_id='REQ__'+hashlib.sha256(package.package_id.encode()).hexdigest()[:16]
    output=OutputManager().execute(package,RenderRequest(request_id=request_id,requested_outputs=(OutputType.MIDI,)))
    paths=write_output_package(output,OUT/package.package_id)
    return {'status':'OUTPUT_HANDOFF_PASS','source_package_id':package.package_id,
            'midi_path':str(paths['MIDI']),'manifest_path':str(paths['MANIFEST']),
            'source_mutation_detected':output.source_mutation_detected,'audio_rendered':False,
            'next_stage':'AUDIO_RENDER_RESOURCE_RESOLUTION'}


def preflight_audio_resources(engine_result):
    """Every active part must have a real executable resource before final audio."""
    from sfz_renderer_adapter import preflight, SFZRendererError
    reports=[]; missing=[]
    target=engine_result.get('modules',{}).get('target',{})
    for item in target.get('resolved_resources',[]):
        resource=item.get('resource',{})
        if resource.get('resource_type')!='SFZ_SAMPLE_LIBRARY':
            missing.append({'track_id':item.get('track_id'),'instrument_id':item.get('instrument_id'),
                            'reason':'EXECUTABLE_SAMPLE_RESOURCE_REQUIRED'})
            continue
        try:
            reports.append({'track_id':item.get('track_id'),'instrument_id':item.get('instrument_id'),**preflight(resource)})
        except SFZRendererError as exc:
            missing.append({'track_id':item.get('track_id'),'instrument_id':item.get('instrument_id'),'reason':str(exc)})
    if not target.get('resolved_resources'):
        missing.append({'reason':'NO_RESOLVED_AUDIO_RESOURCES'})
    return {'status':'AUDIO_RENDER_RESOURCE_REQUIRED' if missing else 'AUDIO_RENDER_RESOURCES_READY',
            'audio_rendered':False,'resources':reports,'missing':missing,
            'reason':missing[0]['reason'] if missing else None,'fallback_policy':'NO_SYNTHETIC_SUBSTITUTION'}


def execute_audio_render(engine_result, output_handoff):
    """Render each resource from its own event subset; never send a mix to one voice."""
    from sfz_renderer_adapter import render_midi, SFZRendererError
    if output_handoff.get('status') != 'OUTPUT_HANDOFF_PASS':
        return {'status':'AUDIO_RENDER_BLOCKED','audio_rendered':False,'reason':'OUTPUT_HANDOFF_NOT_READY'}
    ready=preflight_audio_resources(engine_result)
    if ready['status']!='AUDIO_RENDER_RESOURCES_READY': return ready
    package=build_execution_package(engine_result)
    stems=[]
    try:
        for item in engine_result['modules']['target']['resolved_resources']:
            track=str(item['track_id'])
            events=tuple(e for e in package.events if e.track_id==track)
            if not events: raise SFZRendererError('RESOURCE_TRACK_HAS_NO_EVENTS:'+track)
            suffix=hashlib.sha256((track+item['instrument_id']).encode()).hexdigest()[:12]
            stem_package=replace(package,package_id=package.package_id+'__'+suffix,events=events)
            request=RenderRequest(request_id='STEM__'+suffix,requested_outputs=(OutputType.MIDI,))
            output=OutputManager().execute(stem_package,request)
            paths=write_output_package(output,OUT/package.package_id/'stems'/suffix)
            wav=Path(paths['MIDI']).with_suffix('.wav')
            report=render_midi(item['resource'],paths['MIDI'],wav)
            stems.append({**report,'track_id':track,'instrument_id':item['instrument_id'],'note_count':len(events)})
    except SFZRendererError as exc:
        return {'status':'AUDIO_RENDER_FAILED','audio_rendered':False,'reason':str(exc),'completed_stems':stems}
    # Verify the entire stem set before handing it to the existing 3D mixer.
    from stem_delivery_manifest import build_manifest, StemDeliveryError
    try:
        manifest = build_manifest(stems,
            [str(item['track_id']) for item in engine_result['modules']['target']['resolved_resources']],
            OUT/package.package_id/'stems'/'delivery_manifest.json')
    except StemDeliveryError as exc:
        return {'status':'AUDIO_STEM_DELIVERY_BLOCKED','audio_rendered':False,
                'reason':str(exc),'completed_stems':stems}
    return {'status':'AUDIO_STEMS_READY_MASTER_REQUIRED','audio_rendered':False,
            'source_audio_rendered':True,'stems':stems,'delivery_manifest':manifest,
            'reason':'SPATIAL_MASTER_HANDOFF_REQUIRED',
            'next_stage':'EXTERNAL_3D_MASTER','fallback_policy':'NO_SYNTHETIC_SUBSTITUTION'}