"""Adapter only: existing Composer rendered stems -> untouched original 3D mixer."""
from pathlib import Path
import copy, json, hashlib, subprocess, sys
HERE=Path(__file__).resolve().parent
MIXER=HERE/'original_3d_mixer'/'standalone_3d_mixer.py'
def mix(manifest_path, output_dir, genre='ROCK', engine_result=None):
    manifest_path=Path(manifest_path); output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    tracks=json.loads(manifest_path.read_text())['tracks']
    if engine_result is None:
        engine_result={'genre':genre,'modules':{'instrument':{'profiles':[]},'target':{'resolved_resources':[]},'performance':{'events':[]},'theory':{'composition_fingerprint':hashlib.sha256(manifest_path.read_bytes()).hexdigest()}}}
    engine_result=copy.deepcopy(engine_result)
    profiles=engine_result['modules']['instrument']['profiles']
    existing={str(p['track_id']) for p in profiles}
    for t in tracks:
        tid=str(t['track_id'])
        if tid not in existing:profiles.append({'track_id':tid,'instrument_id':t['instrument_id'],'role':t['instrument_id']})
    bindings=engine_result['modules']['target']['resolved_resources'];existing={str(b['track_id']) for b in bindings}
    for t in tracks:
        if str(t['track_id']) not in existing:bindings.append({'track_id':str(t['track_id']),'resource':{'target_gain_db':0.0}})
    job={'engine_result':engine_result,'stems':[{'track_id':str(t['track_id']),'wav_path':t['wav_path']} for t in tracks]}
    job_path=output_dir/'original_mixer_job.json';job_path.write_text(json.dumps(job,indent=2))
    p=subprocess.run([sys.executable,str(MIXER),str(job_path),str(output_dir)],capture_output=True,text=True)
    (output_dir/'original_mixer_execution.log').write_text(p.stdout+'\n'+p.stderr)
    if p.returncode:raise RuntimeError('ORIGINAL_MIXER_FAILED:'+p.stdout[-2000:]+p.stderr[-2000:])
    result=json.loads(p.stdout)
    if result.get('status')!='AUDIO_RENDER_PASS':raise RuntimeError(str(result))
    return result