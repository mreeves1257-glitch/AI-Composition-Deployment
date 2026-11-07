#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import base64,hashlib,io,json,tarfile
from pathlib import Path
root=Path('connected_package');manifest=json.loads((root/'manifest.json').read_text())
archive=bytearray()
for part in manifest['parts']:
    data=base64.b64decode((root/part['name']).read_text(),validate=True)
    assert hashlib.sha256(data).hexdigest()==part['sha256'], 'CONNECTED_PART_HASH_MISMATCH'
    archive.extend(data)
assert hashlib.sha256(archive).hexdigest()==manifest['archive_sha256'], 'CONNECTED_ARCHIVE_HASH_MISMATCH'
dest=Path('composer/runtime');dest.mkdir(parents=True,exist_ok=True)
tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz').extractall(dest,filter='data')
print('CONNECTED_PACKAGE_EXTRACTED',manifest['source_package'],flush=True)
PY
cp tuning_runtime_overrides/*.py composer/runtime/
python - <<'FORWARDPY'
import hashlib,json,shutil
from pathlib import Path
overlay=Path('current_master_forward')
runtime=Path('composer/runtime')
manifest=json.loads((overlay/'CURRENT_MASTER_SYNC.json').read_text())
assert manifest['master_policy']=='ONE_MASTER_FORWARD_ONLY'
assert manifest['genre_count']==55
for name in manifest['runtime_files']:
    src=overlay/name
    assert src.is_file(), f'CURRENT_MASTER_FORWARD_FILE_MISSING:{name}'
    shutil.copy2(src,runtime/name)
ap=runtime/'approved_audio_pipeline.py'
assert hashlib.sha256(ap.read_bytes()).hexdigest()==manifest['approved_audio_pipeline_sha256'], 'APPROVED_AUDIO_PIPELINE_HASH_MISMATCH'
(runtime/'CURRENT_MASTER_SYNC.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print('CURRENT_MASTER_FORWARD_SYNC_APPLIED',manifest['source_checkpoint'],len(manifest['runtime_files']),flush=True)
FORWARDPY
python - <<'REASONINGFORWARDPY'
import json, shutil
from pathlib import Path

source=Path('reasoning_forward')
runtime=Path('composer/runtime')
files=[p for p in source.rglob('*') if p.is_file()]
assert len(files)==12, f'ALL55_REASONING_FORWARD_FILE_COUNT:{len(files)}'
for src in files:
    rel=src.relative_to(source)
    dst=runtime/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

required={
    'AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py':'dedicated_genre_arranger_manifest',
    'classical_composition.py':'CLASSICAL_REASONING_V0_1_USER_PREFERRED_TRIAL_BASELINE',
    'controlled_genre_input.py':'musical_reasoning_bridge',
    'approved_audio_pipeline.py':'genre_style_sound_maps.json',
    'genre_arranger_packages.py':'reasoning_bridge_active',
    'genre_reasoning_bridge.py':'GENRE_REASONING_BRIDGE_V1_ALL_55',
    'genre_v3_overlay.py':'augment_profiles',
    'genre_v3_safe_overlay.json':'Classical',
    'genre_style_sound_maps.json':'Big Band',
    'genre_selector.py':'genre_v3_overlay',
    'genre_pre_generation_compiler.py':'v3_genre_grammar',
    'experimental_reasoning/reasoning_engine_v0_1.py':'COMPOSER_MUSICAL_REASONING_ENGINE_V0_1',
}
for rel,marker in required.items():
    p=runtime/rel
    assert p.is_file(), f'ALL55_REASONING_FORWARD_MISSING:{rel}'
    assert marker in p.read_text(), f'ALL55_REASONING_FORWARD_MARKER_MISSING:{rel}:{marker}'

(runtime/'ALL55_REASONING_DEPLOYMENT.json').write_text(json.dumps({
    'status':'ALL55_REASONING_WIRED',
    'checkpoint':'2026-11-07',
    'source':'reasoning_forward',
    'file_count':len(files),
    'protected_anchors':['Classical','Big Band'],
    'reasoning_engine':'COMPOSER_MUSICAL_REASONING_ENGINE_V0_1',
    'reasoning_bridge':'GENRE_REASONING_BRIDGE_V1_ALL_55',
},indent=2)+'\n')
print('ALL55_REASONING_FORWARD_APPLIED',len(files),flush=True)
REASONINGFORWARDPY
python -m pip install --no-index --find-links composer/runtime/enhancer_wheels -r composer/runtime/enhancer_requirements.txt
python -m pip install --no-index --no-deps composer/runtime/enhancer_wheels/basic_pitch-0.4.0-py2.py3-none-any.whl
cp connected_http_server.py composer/runtime/render_server.py
# Match native dependencies to the deployment host instead of the saved workstation.
# Rootless Debian package extraction keeps the sound resources and engine intact.
NATIVE="$PWD/composer/runtime/runtime_linux/lib"
mkdir -p "$PWD/.native_debs" "$PWD/.native_root"
python - <<'NATIVEPY'
import subprocess,re
from pathlib import Path
apt_options=['-o','Dir::State::lists='+str(Path('.apt_lists').resolve())]
Path('.apt_lists/partial').mkdir(parents=True,exist_ok=True)
subprocess.run(['apt-get',*apt_options,'update'],check=True)
text=subprocess.check_output(['apt-cache',*apt_options,'depends','--recurse','--no-recommends','--no-suggests','--no-conflicts','--no-breaks','--no-replaces','--no-enhances','libfluidsynth3'],text=True)
names=sorted({line for line in text.splitlines() if re.fullmatch(r'[a-z0-9][a-z0-9+.-]*',line) and line not in {'libc6','libc-bin'}})
assert 'libfluidsynth3' in names
subprocess.run(['apt-get',*apt_options,'download',*names],cwd='.native_debs',check=True)
for deb in Path('.native_debs').glob('*.deb'):
 subprocess.run(['dpkg-deb','-x',str(deb),'.native_root'],check=True)
import shutil
native=Path('composer/runtime/runtime_linux/lib')
shutil.rmtree(native);native.mkdir(parents=True)
for file in Path('.native_root').rglob('*'):
 if file.is_file() and '.so' in file.name:
  shutil.copyfile(file,native/file.name)
assert (native/'libfluidsynth.so.3').is_file()
print('HOST_NATIVE_DEPENDENCIES_READY',flush=True)
NATIVEPY
export LD_LIBRARY_PATH="$PWD/composer/runtime/runtime_linux/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export AI_COMP_FLUIDSYNTH_LIBRARY="$PWD/composer/runtime/runtime_linux/lib/libfluidsynth.so.3"
PYTHONPATH=composer/runtime python composer/runtime/verify_genre_recognition_55.py
PYTHONPATH=composer/runtime python composer/runtime/verify_performance_realization_55.py
PYTHONPATH=composer/runtime python composer/runtime/verify_instrument_separator_55.py
echo 'CONNECTED_ALL_55_MASTER_VERIFICATIONS_PASS'
PYTHONPATH=composer/runtime python - <<'REASONINGPY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path('composer/runtime/experimental_reasoning').resolve()))
from reasoning_engine_v0_1 import ComposerState, reason, validate, ENGINE_ID
packet=reason(ComposerState(
    genre='Classical',
    profile_id='CLASSICAL_COMMON_PRACTICE_TONAL_CHAMBER_V2',
    section='Verse',
    active_instruments=('violin_1','cello','double_bass')
))
validate(packet)
assert ENGINE_ID=='COMPOSER_MUSICAL_REASONING_ENGINE_V0_1'
from genre_reasoning_bridge import BRIDGE_ID
assert 'REASONING' in BRIDGE_ID
print('ALL55_REASONING_ENGINE_SMOKE_PASS',ENGINE_ID,BRIDGE_ID,flush=True)
REASONINGPY
PYTHONPATH=composer/runtime python - <<'PY'
import tempfile,wave
from pathlib import Path
from engine import AICompositionEngine
import output_handoff
with tempfile.TemporaryDirectory() as tmp:
    engine=AICompositionEngine(history_path=Path(tmp)/'history.json')
    output_handoff.OUT=Path(tmp)/'outputs'
    for genre in ['Classical','Big Band']:
        result=engine.run(genre,mode='quick',audio_backend='APPROVED_SF2')
        assert result.get('status')=='AUDIO_RENDER_PASS' and result.get('audio_rendered'), (genre,result.get('reason'))
        with wave.open(result['audio_render']['wav_path'],'rb') as wav:
            frames=wav.getnframes()
            assert wav.getnchannels()==2 and frames>0
            samples=wav.readframes(frames)
            assert any(samples), (genre,'SILENT_WAV')
        print('CONNECTED_APPROVED_ANCHOR_AUDIO_PASS',genre,frames,flush=True)
PY
PYTHONPATH=composer/runtime python - <<'TUNINGPY'
from musical_tuning import validate_reference
assert validate_reference(432)==432 and validate_reference(440)==440
from engine import AICompositionEngine
import tempfile
from pathlib import Path
import output_handoff
with tempfile.TemporaryDirectory() as tmp:
    output_handoff.OUT=Path(tmp)/'outputs'
    engine=AICompositionEngine(history_path=Path(tmp)/'history.json')
    result=engine.run('Country Rock',mode='quick',audio_backend='APPROVED_SF2',tuning_reference_hz=432)
    assert result.get('status')=='AUDIO_RENDER_PASS' and result.get('audio_rendered') and result.get('tuning_reference_hz')==432,result
print('BUILD_432_FINISHED_AUDIO_PASS')
TUNINGPY
python -m py_compile composer/runtime/render_server.py
echo 'CONNECTED COMPOSER READY'
