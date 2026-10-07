"""Preserved Scene 009 -> Object Master 006 handoff for real SFZ stems.

This version performs the stereo derivative in bounded streaming passes so a
normal 3-4 minute composition does not require all stems in RAM at once.
"""
from pathlib import Path
import hashlib, json, math, tempfile, wave, importlib.util
import numpy as np
from global_3d_output_gate import validate_final_audio_output

ROOT=Path(__file__).resolve().parent
CHUNK_FRAMES=65536

def _load(filename,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/filename)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def _sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

SCENE=_load('AI_Comp_3D_Spatialization_Scene_Engine_009_RESTORED_2026-10-03.py','scene009')
MASTER=_load('AI_Comp_Object_Based_3D_Master_006_RESTORED_2026-10-03.py','master006')

def _decode_mono(raw,width,channels):
    if not raw:
        return np.empty((0,),dtype=np.float32)
    if width==1:
        a=np.frombuffer(raw,dtype=np.uint8).astype(np.float32)
        a=(a-128.0)/128.0
    elif width==2:
        a=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0
    elif width==4:
        a=np.frombuffer(raw,dtype='<i4').astype(np.float32)/2147483648.0
    else:
        raise ValueError('UNSUPPORTED_WAV_SAMPLE_WIDTH')
    if len(a)%channels:
        raise ValueError('INVALID_WAV_FRAME_ALIGNMENT')
    a=a.reshape(-1,channels)
    return a.mean(axis=1,dtype=np.float32) if channels>1 else a[:,0]

def _stream_mix(entries,max_frames,mean=None,peak_only=False,write_path=None,sample_rate=None):
    readers=[]
    writer=None
    total=np.zeros(2,dtype=np.float64)
    count=0
    peak=0.0
    try:
        for e in entries:
            readers.append(wave.open(str(e['path']),'rb'))
        if write_path is not None:
            writer=wave.open(str(write_path),'wb')
            writer.setnchannels(2); writer.setsampwidth(2); writer.setframerate(sample_rate)
        for start in range(0,max_frames,CHUNK_FRAMES):
            n=min(CHUNK_FRAMES,max_frames-start)
            mix=np.zeros((n,2),dtype=np.float32)
            for e,w in zip(entries,readers):
                mono=_decode_mono(w.readframes(n),e['width'],e['channels'])
                k=len(mono)
                if not k:
                    continue
                mix[:k,0]+=mono*e['left_gain']
                mix[:k,1]+=mono*e['right_gain']
            if mean is None:
                total+=mix.sum(axis=0,dtype=np.float64)
                count+=n
                continue
            mix[:,0]-=mean[0]; mix[:,1]-=mean[1]
            if peak_only:
                if mix.size:
                    peak=max(peak,float(np.max(np.abs(mix))))
                continue
            scale=e_scale=entries[0].get('_normalization_scale',1.0)
            mix*=scale
            pcm=np.clip(mix,-.999969,.999969)
            writer.writeframes((pcm*32767.0).astype('<i2').tobytes())
    finally:
        for w in readers:
            try: w.close()
            except Exception: pass
        if writer is not None:
            writer.close()
    if mean is None:
        if count<=0:
            raise ValueError('EMPTY_STEREO_DERIVATIVE')
        return (float(total[0]/count),float(total[1]/count))
    if peak_only:
        return peak
    return None

def finalize_real_stems(engine_result,stems,output_root):
    if not stems:
        raise ValueError('NO_SOURCE_STEMS')
    output_root=Path(output_root).resolve(); output_root.mkdir(parents=True,exist_ok=True)
    directory=Path(tempfile.mkdtemp(prefix='composition_',dir=output_root))
    profiles={str(p['track_id']):p for p in engine_result['modules']['instrument']['profiles']}
    bindings={str(x['track_id']):x['resource'] for x in engine_result['modules']['target']['resolved_resources']}
    rock_pan={'BASS':0.0,'KICK':0.0,'SNARE':.02,'RHYTHM_GUITAR':-.28,'LEAD_GUITAR':.24,'HI_HAT':.34}

    sources=[]; entries=[]; sample_rate=None; max_frames=0
    for stem in stems:
        track=str(stem['track_id'])
        path=Path(stem['wav_path']).resolve()
        with wave.open(str(path),'rb') as w:
            channels=w.getnchannels(); width=w.getsampwidth(); sr=w.getframerate(); frames=w.getnframes()
        if sample_rate is None:
            sample_rate=sr
        if sr!=sample_rate:
            raise ValueError('STEM_SAMPLE_RATE_MISMATCH')
        if channels not in (1,2):
            raise ValueError('UNSUPPORTED_STEM_CHANNEL_COUNT')
        if width not in (1,2,4):
            raise ValueError('UNSUPPORTED_WAV_SAMPLE_WIDTH')
        max_frames=max(max_frames,frames)

        profile=profiles[track]; iid=profile['instrument_id']; role=profile.get('role')
        binding=bindings[track]
        target_gain_db=float(binding.get('target_gain_db',0.0))
        target_gain=10.0**(target_gain_db/20.0)
        source=SCENE.sources_from_renderer005_manifest({'independent_stems':[{
            'instrument_id':iid,'path':str(path),'sha256':MASTER.sha256_file(path)
        }]})[0]
        source.update(source_id=track,role=role)
        source['provenance']={
            'audio_sha256':MASTER.sha256_file(path),
            'renderer':'SFIZZ_REAL_SAMPLE_RENDERER',
            'resource':binding,
            'target_gain_db':target_gain_db,
            'production_resource_ready':True,
            'placement_basis':'EXISTING_009_NEUTRAL_STAGING'
        }
        key={'electric_bass_guitar':'BASS','kick_drum_rock':'KICK','snare_drum':'SNARE','hi_hat':'HI_HAT'}.get(iid)
        if iid=='electric_guitar':
            key={'RHYTHM_POWER_CHORDS':'RHYTHM_GUITAR','LEAD_MELODY':'LEAD_GUITAR'}.get(role)
        if engine_result.get('genre','').upper()=='ROCK' and key:
            az=rock_pan[key]*math.pi/2
            source['position']={'x':math.sin(az),'y':math.cos(az),'z':0.0}
            source['provenance']['placement_basis']='SEPT27_ROCK_PAN_ON_NEUTRAL_UNIT_STAGE'
        sources.append(source)

        p=source['position']; az=math.atan2(p['x'],p['y'])
        pan=max(-1.0,min(1.0,az/(math.pi/2)))
        angle=(pan+1)*math.pi/4
        entries.append({
            'track':track,'path':path,'channels':channels,'width':width,'frames':frames,
            'left_gain':float(math.cos(angle))*target_gain,
            'right_gain':float(math.sin(angle))*target_gain,
            'target_gain_db':target_gain_db
        })

    if not max_frames:
        raise ValueError('EMPTY_SOURCE_STEMS')

    scene=SCENE.compile_scene(sources,{'position':{'x':0.0,'y':0.0,'z':0.0}},
                              scene_id=directory.name,derivatives=('stereo',))
    master=MASTER.build_object_master(
        scene,
        represented_note_events=len(engine_result['modules']['performance']['events']),
        production_resource_ready=True
    )
    master['master_id']='AI_COMP_3D_OBJECT_MASTER_006__'+directory.name
    master['source_composition_fingerprint']=engine_result['modules']['theory']['composition_fingerprint']
    master_path=directory/'object_master.json'; master_path.write_text(json.dumps(master,indent=2))
    (directory/'scene.json').write_text(json.dumps(scene,indent=2))

    by_track={o['source_id']:o for o in master['audio_objects']}
    objects=[]
    for e in entries:
        obj=by_track[e['track']]; p=obj['position']; az=math.atan2(p['x'],p['y'])
        objects.append({
            'source_identity':e['track'],
            'azimuth':math.degrees(az),
            'elevation':math.degrees(math.atan2(p['z'],math.hypot(p['x'],p['y']))),
            'distance':math.sqrt(sum(v*v for v in p.values()))
        })

    # Three bounded passes: DC mean, post-DC peak, then normalized write.
    mean=_stream_mix(entries,max_frames)
    peak=_stream_mix(entries,max_frames,mean=mean,peak_only=True)
    if peak<=0 or not math.isfinite(peak):
        raise ValueError('SILENT_OR_INVALID_DERIVATIVE')
    normalization=10**(-1/20)/peak
    for e in entries:
        e['_normalization_scale']=normalization

    derivative=directory/'stereo_derivative.wav'
    _stream_mix(entries,max_frames,mean=mean,write_path=derivative,sample_rate=sample_rate)

    manifest={
        'output_kind':'audible_final',
        'has_3d_master':True,
        'master_type':'object_scene',
        'spatial_objects':objects,
        'derivative_type':'stereo',
        'parent_3d_master_id':master['master_id'],
        'authoritative_master':False,
        'master_path':str(master_path),
        'resource_quality':'REAL_SFZ_RESOURCES',
        'decoder':'SEPT27_EQUAL_POWER_STEREO_STREAMING',
        'events':master['represented_note_events'],
        'source_count':len(stems),
        'channels':2,
        'sample_rate':sample_rate,
        'duration_seconds':max_frames/sample_rate
    }
    manifest['global_3d_gate']=validate_final_audio_output(manifest)
    if not manifest['global_3d_gate']['compliant']:
        raise ValueError('GLOBAL_3D_GATE_FAILED')
    manifest['derivative_sha256']=_sha256_file(derivative)
    (directory/'output_manifest.json').write_text(json.dumps(manifest,indent=2))
    return {
        'status':'AUDIO_RENDER_PASS',
        'audio_rendered':True,
        'source_audio_rendered':True,
        'stems':stems,
        'wav_path':str(derivative),
        'master_path':str(master_path),
        'parent_3d_master_id':master['master_id'],
        'resource_quality':'REAL_SFZ_RESOURCES'
    }
