"""Render only exact approved connections and deliver all stems to original mixer."""
from pathlib import Path
import importlib.util
import json
import sys
from dataclasses import replace

ROOT=Path(__file__).resolve().parent

def preflight(engine_result):
    from resource_connections import validate_connection
    target=engine_result['modules']['target']
    missing=list(target.get('missing',[]));ready=[]
    for item in target.get('resolved_resources',[]):
        try:
            ready.append(dict(validate_connection(item['resource']),track_id=item['track_id'],instrument_id=item['instrument_id']))
        except Exception as exc:
            missing.append({'track_id':item['track_id'],'instrument_id':item['instrument_id'],'reason':str(exc)})
    return {'status':'AUDIO_RENDER_RESOURCE_REQUIRED' if missing else 'AUDIO_RENDER_RESOURCES_READY',
            'audio_rendered':False,'resources':ready,'missing':missing,
            'reason':missing[0]['reason'] if missing else None}

def render(engine_result,handoff):
    tuning_reference_hz=engine_result.get('tuning_reference_hz',440)
    check=preflight(engine_result)
    if check['missing']:return check
    from output_handoff import build_execution_package, OUT
    from AI_Comp_Executable_Output_Core_001 import OutputManager,RenderRequest,OutputType,write_output_package
    from stem_delivery_manifest import build_manifest
    from original_mixer_adapter import mix
    from resource_connections import validate_connection
    package=build_execution_package(engine_result)
    out=OUT/package.package_id/'approved_audio';out.mkdir(parents=True,exist_ok=True)
    stems=[];render_details=[]
    try:
        for item in engine_result['modules']['target']['resolved_resources']:
            track=str(item['track_id']);resource=item['resource']
            events=tuple(e for e in package.events if e.track_id==track)
            if not events:raise ValueError('RESOURCE_TRACK_HAS_NO_EVENTS:'+track)
            sub=replace(package,package_id=package.package_id+'__'+track,events=events)
            result=OutputManager().execute(sub,RenderRequest(request_id='STEM__'+track,requested_outputs=(OutputType.MIDI,)))
            paths=write_output_package(result,out/track);wav=Path(paths['MIDI']).with_suffix('.wav')
            checked=validate_connection(resource)
            if resource['resource_type']=='SF2_SAMPLE_LIBRARY':
                import mido
                from render_substitute_universal import render_track
                midi=mido.MidiFile(paths['MIDI'])
                indices=[i for i,t in enumerate(midi.tracks) if any(m.type=='note_on' and m.velocity>0 for m in t)]
                if len(indices)!=1:raise ValueError('STEM_MIDI_TRACK_COUNT_INVALID:'+track)
                route=resource['midi_mapping']
                proof=render_track(midi,indices[0],Path(checked['path']),wav,'drums' if route.get('percussion') else 'program',program=route['program'],
                    bank=route.get('soundfont_bank'),note_map=route.get('note_map'),tuning_reference_hz=tuning_reference_hz)
                if proof['peak']<=0:raise ValueError('SILENT_STEM:'+track)
            elif resource.get('renderer_backend')=='RECOVERED_RENDERER005':
                spec=importlib.util.spec_from_file_location('approved_renderer005',ROOT/'AI_Comp_Internal_Production_Render_005.py')
                module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
                iid=item['instrument_id'];bpm=package.tempo_bpm
                timed=[{'instrument_id':iid,'midi_note':e.midi_note,'velocity':e.velocity,
                        'start_seconds':float(e.start_beats)*60/bpm,'duration_seconds':float(e.duration_beats)*60/bpm} for e in events]
                proof=module.render_output_handoff({'performance':{'events':timed}},
                    {iid:{'sfz':checked['path'],'verified':True,'status':'VERIFIED_OPEN_RESOURCE','provider':'Karoryfer','license':'CC0'}},out/track/'sample_audio',sample_rate=22050,tuning_reference_hz=tuning_reference_hz)
                if not proof.get('audio_rendered'):return dict(proof,audio_rendered=False,completed_stems=stems)
                # Use the unnormalized independent source, never the listening mix.
                wav=Path(proof['independent_stems'][0]['path'])
            else:
                from sfz_renderer_adapter import render_midi
                render_midi(resource,paths['MIDI'],wav,sample_rate=22050)
            stems.append({'track_id':track,'instrument_id':item['instrument_id'],'wav_path':str(wav),'note_count':len(events)})
            render_details.append({'track_id':track,'resource_id':resource['resource_id'],
                'midi_mapping':resource.get('midi_mapping'),'renderer_proof':proof if resource['resource_type']=='SF2_SAMPLE_LIBRARY' else {'backend':resource.get('renderer_backend')}})
        delivery=out/'delivery_manifest.json'
        build_manifest(stems,[x['track_id'] for x in engine_result['modules']['target']['resolved_resources']],delivery)
        final=mix(delivery,out/'finished_music',genre=engine_result['genre'],engine_result=engine_result)
        return dict(final,audio_rendered=True,source_audio_rendered=True,mixer_executed=True,
                    resource_quality='EXPLICIT_SFZ_AND_SF2_SAMPLE_ASSIGNMENTS',
                    provenance_note='Original mixer metadata uses a fixed SFZ renderer label; actual source types are recorded in resource_connections.json and this report.',
                    delivery_manifest=str(delivery),resource_scope='EXPLICIT_APPROVED_CONNECTIONS',
                    stem_render_details=render_details,
                    temporary_replacements_used=any(x['resource'].get('temporary_replacement') for x in engine_result['modules']['target']['resolved_resources']))
    except Exception as exc:
        return {'status':'AUDIO_RENDER_FAILED','audio_rendered':False,'reason':type(exc).__name__+': '+str(exc),'completed_stems':stems}
