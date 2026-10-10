#!/usr/bin/env python3
"""Isolated actual Jazz Ballad full engine audio proof. Never deploy."""
import json,os,sys,traceback,shutil,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
runtime=root/'composer'/'runtime'
output=root/'research'/'jazz_ballad_real_output'
output.mkdir(parents=True,exist_ok=True)
os.environ['AI_COMP_SFZ_RENDERER']=str(root/'.composer_tools/bin/sfizz_render')
sys.path.insert(0,str(runtime))
report={'genre':'Jazz Ballad','deployment':False}
try:
 from engine import AICompositionEngine
 engine=AICompositionEngine(history_path=output/'independent_history.json')
 result=engine.run('Jazz Ballad',target_id='INTERNAL',mode='normal')
 report['engine_status']=result.get('status')
 report['audio_rendered']=result.get('audio_rendered')
 report['reason']=result.get('reason')
 report['keys']=list(result)
 report['audio_render']=result.get('audio_render')
 if result.get('audio_rendered') and result.get('audio_render',{}).get('status')=='AUDIO_RENDER_PASS':
  source=Path(result['audio_render']['wav_path'])
  if not source.is_file(): raise RuntimeError('JAZZ_BALLAD_RENDERED_WAV_MISSING')
  target=output/'JAZZ_BALLAD_ORIGINAL_RECORDED_3D.wav'
  shutil.copyfile(source,target)
  report['copied_wav']=target.name
  report['wav_bytes']=target.stat().st_size
  report['wav_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
 report['audio_resource_preflight']=result.get('audio_resource_preflight')
 report['output_handoff']=result.get('output_handoff')
except Exception as exc:
 report['error']=repr(exc)
 report['traceback']=traceback.format_exc()
(output/'report.json').write_text(json.dumps(report,indent=2,default=str))
print(json.dumps({k:v for k,v in report.items() if k not in ('audio_render','audio_resource_preflight','output_handoff','traceback')},default=str))
if report.get('error') or not report.get('audio_rendered'):
 raise SystemExit(1)
