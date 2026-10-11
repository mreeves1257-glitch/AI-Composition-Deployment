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
text=subprocess.check_output(['apt-cache','depends','--recurse','--no-recommends','--no-suggests','--no-conflicts','--no-breaks','--no-replaces','--no-enhances','libfluidsynth3'],text=True)
names=sorted({line for line in text.splitlines() if re.fullmatch(r'[a-z0-9][a-z0-9+.-]*',line) and line not in {'libc6','libc-bin'}})
assert 'libfluidsynth3' in names
subprocess.run(['apt-get','download',*names],cwd='.native_debs',check=True)
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
PYTHONPATH=composer/runtime python - <<'PY'
import json,tempfile,wave
from pathlib import Path
from engine import AICompositionEngine
import output_handoff
root=Path('composer/runtime').resolve()
profiles=json.loads((root/'AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json').read_text())['profiles']
assert len(profiles)==55
with tempfile.TemporaryDirectory() as tmp:
    engine=AICompositionEngine(history_path=Path(tmp)/'history.json')
    output_handoff.OUT=Path(tmp)/'outputs'
    for genre in profiles:
        result=engine.run(genre,mode='quick',render_audio=False,analyze_audio=False)
        check=result.get('audio_resource_preflight',{})
        assert result['status']=='MIDI_READY_AUDIO_NOT_REQUESTED' and not check.get('missing'), (genre,result)
    print('CONNECTED_ALL_55_RESOURCE_PREFLIGHT_PASS',flush=True)
    for genre in ['Country Rock','Classical','Custom Hybrid']:
        result=engine.run(genre,mode='quick',analyze_audio=False)
        assert result.get('audio_rendered'), (genre,result.get('reason'))
        with wave.open(result['audio_render']['wav_path'],'rb') as wav:
            frames=wav.getnframes()
            assert wav.getnchannels()==2 and frames>0
            samples=wav.readframes(frames)
            assert any(samples), (genre,'SILENT_WAV')
        print('CONNECTED_BUILD_AUDIO_PASS',genre,frames,flush=True)
PY
python -m py_compile composer/runtime/render_server.py
echo 'CONNECTED COMPOSER READY'
