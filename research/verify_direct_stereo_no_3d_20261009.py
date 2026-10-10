"""Verify ordinary stereo output without running the 3D mixer.

The small WAV fixtures are only an output-format/track-preservation check;
they are NOT presented as musical samples or proof of recorded instrument
fidelity. That needs its own real SFZ audition.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"composer_overrides"))
from direct_stereo_output import finish_recorded_stems

def check(flag,detail):
    if not flag:raise AssertionError(detail)

def wav(path,frequency,channels=1,frames=16000):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(channels);w.setframerate(8000);w.setsampwidth(2)
        out=[]
        for i in range(frames):
            v=int(9000*math.sin(2*math.pi*frequency*i/8000))
            out.extend([v] if channels==1 else [v,int(v*.65)])
        w.writeframes(struct.pack("<"+"h"*len(out),*out))

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);bass=root/"bass.wav";lead=root/"lead.wav"
        wav(bass,110,1);wav(lead,440,2)
        original={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (bass,lead)}
        engine={"genre":"ROCK","modules":{"target":{"resolved_resources":[
            {"track_id":"BASS","resource":{"target_gain_db":1.0,
                "resource_id":"KARORYFER_GROWLYBASS_V1_002"}},
            {"track_id":"LEAD","resource":{"target_gain_db":5.5,
                "resource_id":"KARORYFER_SHINYGUITAR"}},
        ]}}}
        stems=[{"track_id":"BASS","wav_path":str(bass)},
               {"track_id":"LEAD","wav_path":str(lead)}]
        result=finish_recorded_stems(engine,stems,root/"output")
        check(result["status"]=="AUDIO_RENDER_PASS" and result["audio_rendered"],
              "DIRECT_AUDIO_OUTPUT_NOT_CREATED")
        check(result["output_stage"]=="DIRECT_STEREO_SUM_NO_3D","SPATIAL_STAGE_NOT_REMOVED")
        final=Path(result["wav_path"])
        check(final.name=="stereo_derivative.wav"
              and final.parent.name.startswith("composition_")
              and final.parent.parent.name=="output",
              "EXISTING_PLAYBACK_URL_PATH_BROKEN")
        with wave.open(str(final),"rb") as f:
            check((f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())==
                  (2,2,8000,16000),"FINAL_STEREO_FILE_INVALID")
            check(any(f.readframes(100)),"FINAL_AUDIO_EMPTY")
        manifest=json.loads(Path(result["output_manifest_path"]).read_text())
        check(manifest["output_method"]=="DIRECT_STEREO_SUM_NO_3D"
              and manifest["has_3d_master"] is False
              and manifest["spatial_effects_applied"] is False,
              "3D_AUDIO_STILL_IN_OUTPUT_ROUTE")
        check(all(hashlib.sha256(p.read_bytes()).hexdigest()==original[str(p)]
                  for p in (bass,lead)),"ORIGINAL_STEMS_ALTERED")
        build=(Path(__file__).resolve().parents[1]/"build_current_composer.sh").read_text()
        check("cp composer_overrides/direct_stereo_output.py composer/runtime/" in build,
              "STEREO_OUTPUT_NOT_INSTALLED_IN_BUILD")
        check("[sys.executable, str(ROOT / 'standalone_3d_mixer.py')" not in build,
              "OLD_3D_PROCESS_STILL_ACTIVE")
        check("finish_recorded_stems(stereo_instructions, stereo_stems, final_root)" in build,
              "DIRECT_STEREO_ROUTE_NOT_ATTACHED")
        check("cp composer_overrides/standalone_3d_mixer.py composer/runtime/" not in build,
              "OLD_3D_INSTALLED_AS_ACTIVE_RUNTIME")
        print("NO_3D_DIRECT_STEREO_OUTPUT_VERIFIED",json.dumps({
            "output":"VALID_STEREO_PCM_WAV","channels":2,"sample_rate":8000,
            "test_frames":16000,"stems":2,"no_spatialization":True,
            "source_files_unchanged":True,"original_playback_url_contract_kept":True,
            "builder_wired_direct_stereo":True,"real_SFZ_music_rendered_here":False,
            "live_deployed":False
        },sort_keys=True))
if __name__=="__main__":main()
