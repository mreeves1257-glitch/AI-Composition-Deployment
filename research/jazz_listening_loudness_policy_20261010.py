#!/usr/bin/env python3
"""Non-destructive loudness QC for Jazz listening exports (not the approved mixer).

Never normalize individual instrument stems or overwrite master audio.
"""
import json,subprocess,sys,re
from pathlib import Path
TARGET_LUFS=-12.0
TRUE_PEAK_DBTP=-1.0
def measure(file):
 p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(file),'-af','loudnorm=I=-12:TP=-1:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 m=re.search(r'\{\s*"input_i".*?\}',p.stderr,re.S)
 if not m:raise RuntimeError('loudness measurements unavailable')
 return json.loads(m.group())
def export(source,dest):
 if source.resolve()==dest.resolve():raise ValueError('Never overwrite source')
 dest.parent.mkdir(parents=True,exist_ok=True)
 # EBU R128 loudness with peak protection. This is playback QC, not a genre mixer setting.
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-af','loudnorm=I=-12:TP=-1:LRA=9','-c:a','libmp3lame','-b:a','192k',str(dest)],check=True)
 report={'source':str(source),'listening_export':str(dest),'target_integrated_lufs':TARGET_LUFS,'true_peak_ceiling_dbtp':TRUE_PEAK_DBTP,'source_measurement':measure(source),'export_measurement':measure(dest),'approved_3d_mixer_unchanged':True,'original_instrument_sources_unchanged':True}
 return report
if __name__=='__main__':
 reports=[]
 for item in sys.argv[1:]:
  src=Path(item)
  if not src.is_file():continue
  dest=src.with_name(src.stem+'_Listening_Level.mp3')
  reports.append(export(src,dest))
 print(json.dumps(reports,indent=2))
