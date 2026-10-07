"""Preserved Scene 009 -> Object Master 006 handoff for real SFZ stems."""
from pathlib import Path
import hashlib, json, math, tempfile, wave, importlib.util
import numpy as np
from global_3d_output_gate import validate_final_audio_output
ROOT=Path(__file__).resolve().parent
def _load(filename,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/filename)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
SCENE=_load('AI_Comp_3D_Spatialization_Scene_Engine_009_RESTORED_2026-10-03.py','scene009')
MASTER=_load('AI_Comp_Object_Based_3D_Master_006_RESTORED_2026-10-03.py','master006')
def _read_pcm_wav(path):
    with wave.open(str(path),'rb') as w:
        ch=w.getnchannels(); width=w.getsampwidth(); sr=w.getframerate(); frames=w.getnframes(); raw=w.readframes(frames)
    if width==1:
        a=np.frombuffer(raw,dtype=np.uint8).astype(np.float64); a=(a-128.0)/128.0
    elif width==2: a=np.frombuffer(raw,dtype='<i2').astype(np.float64)/32768.0
    elif width==4: a=np.frombuffer(raw,dtype='<i4').astype(np.float64)/2147483648.0
    else: raise ValueError('UNSUPPORTED_WAV_SAMPLE_WIDTH')
    return a.reshape(-1,ch),sr
def _write_stereo(path,samples,sr):
    samples=np.asarray(samples,dtype=np.float64)
    if samples.ndim!=2 or samples.shape[1]!=2 or not np.isfinite(samples).all(): raise ValueError('INVALID_STEREO_AUDIO')
    peak=float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak<=0: raise ValueError('SILENT_OR_INVALID_DERIVATIVE')
    if peak>=1: samples=samples*(0.98/peak)
    pcm=np.clip(samples,-.999969,.999969)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((pcm*32767).astype('<i2').tobytes())
def finalize_real_stems(engine_result,stems,output_root):
    if not stems: raise ValueError('NO_SOURCE_STEMS')
    output_root=Path(output_root).resolve(); output_root.mkdir(parents=True,exist_ok=True)
    directory=Path(tempfile.mkdtemp(prefix='composition_',dir=output_root))
    profiles={str(p['track_id']):p for p in engine_result['modules']['instrument']['profiles']}
    bindings={str(x['track_id']):x['resource'] for x in engine_result['modules']['target']['resolved_resources']}
    rock_pan={'BASS':0.0,'KICK':0.0,'SNARE':.02,'RHYTHM_GUITAR':-.28,'LEAD_GUITAR':.24,'HI_HAT':.34}
    sources=[]; audio=[]; sample_rate=None; max_frames=0
    for stem in stems:
        track=str(stem['track_id']); path=Path(stem['wav_path']).resolve(); arr,sr=_read_pcm_wav(path)
        if sample_rate is None: sample_rate=sr
        if sr!=sample_rate: raise ValueError('STEM_SAMPLE_RATE_MISMATCH')
        mono=arr.mean(axis=1) if arr.shape[1]>1 else arr[:,0]
        audio.append((track,mono)); max_frames=max(max_frames,len(mono))
        profile=profiles[track]; iid=profile['instrument_id']; role=profile.get('role')
        source=SCENE.sources_from_renderer005_manifest({'independent_stems':[{'instrument_id':iid,'path':str(path),'sha256':MASTER.sha256_file(path)}]})[0]
        source.update(source_id=track,role=role)
        source['provenance']={'audio_sha256':MASTER.sha256_file(path),'renderer':'SFIZZ_REAL_SAMPLE_RENDERER','resource':bindings[track],'production_resource_ready':True,'placement_basis':'EXISTING_009_NEUTRAL_STAGING'}
        key={'electric_bass_guitar':'BASS','kick_drum_rock':'KICK','snare_drum':'SNARE','hi_hat':'HI_HAT'}.get(iid)
        if iid=='electric_guitar': key={'RHYTHM_POWER_CHORDS':'RHYTHM_GUITAR','LEAD_MELODY':'LEAD_GUITAR'}.get(role)
        if engine_result.get('genre','').upper()=='ROCK' and key:
            az=rock_pan[key]*math.pi/2
            source['position']={'x':math.sin(az),'y':math.cos(az),'z':0.0}
            source['provenance']['placement_basis']='SEPT27_ROCK_PAN_ON_NEUTRAL_UNIT_STAGE'
        sources.append(source)
    scene=SCENE.compile_scene(sources,{'position':{'x':0.0,'y':0.0,'z':0.0}},scene_id=directory.name,derivatives=('stereo',))
    master=MASTER.build_object_master(scene,represented_note_events=len(engine_result['modules']['performance']['events']),production_resource_ready=True)
    master['master_id']='AI_COMP_3D_OBJECT_MASTER_006__'+directory.name
    master['source_composition_fingerprint']=engine_result['modules']['theory']['composition_fingerprint']
    master_path=directory/'object_master.json'; master_path.write_text(json.dumps(master,indent=2))
    (directory/'scene.json').write_text(json.dumps(scene,indent=2))
    stereo=np.zeros((max_frames,2),dtype=np.float64); objects=[]; by_track={o['source_id']:o for o in master['audio_objects']}
    for track,mono in audio:
        obj=by_track[track]; p=obj['position']; az=math.atan2(p['x'],p['y']); pan=max(-1.0,min(1.0,az/(math.pi/2)))
        angle=(pan+1)*math.pi/4; n=len(mono); stereo[:n,0]+=mono*math.cos(angle); stereo[:n,1]+=mono*math.sin(angle)
        objects.append({'source_identity':track,'azimuth':math.degrees(az),'elevation':math.degrees(math.atan2(p['z'],math.hypot(p['x'],p['y']))),'distance':math.sqrt(sum(v*v for v in p.values()))})
    stereo-=np.mean(stereo,axis=0,keepdims=True)
    peak=float(np.max(np.abs(stereo)))
    if peak<=0 or not math.isfinite(peak): raise ValueError('SILENT_OR_INVALID_DERIVATIVE')
    stereo*=10**(-1/20)/peak
    derivative=directory/'stereo_derivative.wav'; _write_stereo(derivative,stereo,sample_rate)
    manifest={'output_kind':'audible_final','has_3d_master':True,'master_type':'object_scene','spatial_objects':objects,'derivative_type':'stereo','parent_3d_master_id':master['master_id'],'authoritative_master':False,'master_path':str(master_path),'resource_quality':'REAL_SFZ_RESOURCES','decoder':'SEPT27_EQUAL_POWER_STEREO','events':master['represented_note_events'],'source_count':len(stems),'channels':2,'sample_rate':sample_rate,'duration_seconds':max_frames/sample_rate}
    manifest['global_3d_gate']=validate_final_audio_output(manifest)
    if not manifest['global_3d_gate']['compliant']: raise ValueError('GLOBAL_3D_GATE_FAILED')
    manifest['derivative_sha256']=hashlib.sha256(derivative.read_bytes()).hexdigest()
    (directory/'output_manifest.json').write_text(json.dumps(manifest,indent=2))
    return {'status':'AUDIO_RENDER_PASS','audio_rendered':True,'source_audio_rendered':True,'stems':stems,'wav_path':str(derivative),'master_path':str(master_path),'parent_3d_master_id':master['master_id'],'resource_quality':'REAL_SFZ_RESOURCES'}
