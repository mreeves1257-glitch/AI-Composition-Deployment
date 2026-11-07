#!/usr/bin/env python3
"""External SFZ renderer boundary for AI Composition - Sandbox.
Resolves approved sample resources and never synthesizes/substitutes timbre.
"""
from __future__ import annotations
from pathlib import Path
import os, re, shutil, subprocess, wave, math
import numpy as np

class SFZRendererError(RuntimeError): pass

RESOURCE_ENV = 'AI_COMP_RESOURCE_BANK'
RENDERER_ENV = 'AI_COMP_SFZ_RENDERER'


def _candidate_roots():
    seen=set()
    for raw in (os.environ.get(RESOURCE_ENV), str(Path(__file__).resolve().parent/'sound_resources'), str(Path(__file__).resolve().parent/'resources'), str(Path(__file__).resolve().parent.parent/'Sound Resource Bank')):
        if not raw: continue
        p=Path(raw).expanduser().resolve()
        if p not in seen:
            seen.add(p); yield p


def resolve_sfz(resource: dict) -> Path:
    mapping=resource.get('preferred_mapping')
    if resource.get('resource_type')!='SFZ_SAMPLE_LIBRARY' or not mapping:
        raise SFZRendererError('SFZ_RESOURCE_DECLARATION_INVALID')
    for root in _candidate_roots():
        direct=root/mapping
        if direct.is_file(): return direct
        rid=resource.get('resource_id','')
        for rel in (rid, 'Growlybass', 'Karoryfer.Growlybass.v1.002', 'Karoryfer Growlybass'):
            p=root/rel/mapping
            if p.is_file(): return p
    raise SFZRendererError(f"SFZ_RESOURCE_NOT_INSTALLED:{resource.get('resource_id')}:{mapping}")


def validate_sfz_samples(sfz_path: Path, allowed_root: Path|None=None) -> dict:
    """Validate SFZ sample references with nested includes, default_path and #define macros.

    This remains read-only. Macro expansion is required for real SFZ programs such as
    Karoryfer Shinyguitar, whose wrapper defines $sample_dir and whose included main
    program uses that variable in default_path.
    """
    visited=set(); refs=[]; missing=[]
    allowed=Path(allowed_root).resolve() if allowed_root is not None else None

    def expand(raw: str, macros: dict[str,str]) -> str:
        value=raw.strip().strip('"').replace('\\','/')
        for _ in range(16):
            before=value
            for key,replacement in macros.items():
                value=value.replace(key,replacement)
            if value==before:
                break
        unresolved=re.findall(r'\$[A-Za-z_][A-Za-z0-9_]*',value)
        if unresolved:
            raise SFZRendererError('SFZ_UNRESOLVED_MACRO:'+','.join(sorted(set(unresolved))))
        return value

    def within_allowed(path: Path) -> bool:
        if allowed is None:
            return True
        try:
            path.resolve().relative_to(allowed)
            return True
        except ValueError:
            return False

    def walk(path: Path, inherited_default: Path|None=None,
             inherited_macros: dict[str,str]|None=None):
        path=path.resolve()
        if path in visited:
            return
        if not path.is_file():
            missing.append('INCLUDE:'+str(path)); return
        if not within_allowed(path):
            missing.append('INCLUDE_OUTSIDE_ALLOWED_ROOT:'+str(path)); return
        visited.add(path)
        text=path.read_text(errors='strict')
        text=re.sub(r'//[^\n]*', '', text)
        macros=dict(inherited_macros or {})

        for name,value in re.findall(
            r'(?m)^\s*#define\s+(\$[A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$',
            text,
        ):
            macros[name]=expand(value,macros)

        default=inherited_default
        dm=re.search(r'(?:^|\s)default_path=([^\s<]+)', text)
        if dm:
            raw_default=expand(dm.group(1),macros)
            default=(path.parent/raw_default).resolve()
            if not within_allowed(default):
                missing.append('DEFAULT_PATH_OUTSIDE_ALLOWED_ROOT:'+str(default))

        for inc in re.findall(r'#include\s+["<]([^">]+)[">]', text):
            rel=expand(inc,macros)
            walk((path.parent/rel).resolve(), default, macros)

        for match in re.finditer(r'(?:^|\s)sample=(.*?)(?=\s+\w+=|\s*<|$)', text, re.S):
            ref=expand(match.group(1),macros)
            refs.append(ref)
            base=default if default is not None else path.parent
            candidate=(base/ref).resolve()
            if not within_allowed(candidate) or not candidate.is_file():
                missing.append(ref)

    walk(Path(sfz_path))
    if not refs:
        raise SFZRendererError('SFZ_NO_SAMPLE_REFERENCES')
    if missing:
        raise SFZRendererError(f'SFZ_SAMPLE_SET_INCOMPLETE:{len(missing)}_MISSING')
    return {'sample_references':len(refs),'unique_samples':len(set(refs)),
            'sfz_files_validated':len(visited)}

def resolve_renderer() -> str:
    explicit=os.environ.get(RENDERER_ENV)
    if explicit:
        p=shutil.which(explicit) or (explicit if Path(explicit).is_file() else None)
        if p: return str(p)
    for name in ('sfizz_render','sfizz-render'):
        p=shutil.which(name)
        if p: return p
    raise SFZRendererError('SFZ_RENDERER_NOT_INSTALLED')


def preflight(resource: dict) -> dict:
    sfz=resolve_sfz(resource)
    samples=validate_sfz_samples(sfz)
    renderer=resolve_renderer()
    try:
        help_result=subprocess.run([renderer,'--help'],capture_output=True,text=True,timeout=10)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise SFZRendererError('SFZ_RENDERER_UNAVAILABLE:'+str(exc))
    help_text=help_result.stdout+help_result.stderr
    if not all(flag in help_text for flag in ('--sfz','--midi','--wav','--samplerate')):
        raise SFZRendererError('SFZ_RENDERER_COMMAND_CONTRACT_UNSUPPORTED')
    # CLI flag support alone cannot establish faithful playback of complex SFZ programs.
    from official_sfz_compatibility import assess_production_mapping
    assessment = assess_production_mapping(resource.get('resource_id', ''),
                                            resource.get('preferred_mapping', ''),
                                            backend='external_sfz')
    if assessment['status'] == 'BACKEND_COMPATIBILITY_NOT_YET_VERIFIED':
        raise SFZRendererError('SFZ_BACKEND_COMPATIBILITY_UNVERIFIED:' + str(resource.get('resource_id')))
    return {'status':'SFZ_RENDER_READY','resource_id':resource.get('resource_id'),
            'sfz_path':str(sfz),'renderer':renderer,**samples,
            'fallback_policy':'NO_SYNTHETIC_SUBSTITUTION'}



def probe_original_sfz(resource: dict, midi_path: str|Path, wav_path: str|Path,
                       sample_rate: int=44100) -> dict:
    """Diagnostic-only audio probe; never grants production certification.

    Uses the declared original SFZ, complete samples, and actual external renderer.
    The normal production preflight remains fail-closed until separately certified.
    """
    from official_sfz_compatibility import assess_production_mapping
    assessment = assess_production_mapping(resource.get('resource_id', ''),
                                           resource.get('preferred_mapping', ''),
                                           backend='external_sfz')
    if assessment['status'] != 'BACKEND_COMPATIBILITY_NOT_YET_VERIFIED':
        raise SFZRendererError('SFZ_PROBE_NOT_APPLICABLE')
    sfz = resolve_sfz(resource)
    samples = validate_sfz_samples(sfz)
    renderer = resolve_renderer()
    help_result = subprocess.run([renderer, '--help'], capture_output=True,
                                 text=True, timeout=10)
    if help_result.returncode != 0 or not all(
        flag in (help_result.stdout + help_result.stderr)
        for flag in ('--sfz', '--midi', '--wav', '--samplerate')
    ):
        raise SFZRendererError('SFZ_RENDERER_COMMAND_CONTRACT_UNSUPPORTED')
    midi = Path(midi_path).resolve()
    wav = Path(wav_path).resolve()
    if not midi.is_file():
        raise SFZRendererError('MIDI_INPUT_MISSING')
    wav.parent.mkdir(parents=True, exist_ok=True)
    wav.unlink(missing_ok=True)
    try:
        cp = subprocess.run(
            [renderer, '--sfz', str(sfz), '--midi', str(midi),
             '--wav', str(wav), '--samplerate', str(sample_rate)],
            capture_output=True, text=True, timeout=120
        )
        if cp.returncode != 0 or not wav.is_file():
            raise SFZRendererError('SFZ_PROBE_RENDER_FAILED')
        with wave.open(str(wav), 'rb') as stream:
            if (stream.getcomptype() != 'NONE' or stream.getframerate() != sample_rate
                or stream.getnchannels() not in (1, 2) or stream.getnframes() == 0
                or stream.getsampwidth() not in (1, 2, 3, 4)):
                raise SFZRendererError('SFZ_PROBE_WAVEFORM_INVALID')
            data = stream.readframes(stream.getnframes())
            width = stream.getsampwidth()
            if width == 1:
                audible = any(x != 128 for x in data)
            else:
                audible = any(data[i:i+width] != bytes(width)
                              for i in range(0, len(data), width))
            if not audible:
                raise SFZRendererError('SFZ_PROBE_SILENT')
            frames = stream.getnframes()
    except Exception:
        wav.unlink(missing_ok=True)
        raise
    return {'status': 'DIAGNOSTIC_AUDIO_ONLY_NOT_CERTIFIED',
            'resource_id': resource['resource_id'], 'sfz_path': str(sfz),
            'renderer': renderer, 'wav_path': str(wav), 'frames': frames,
            'samples': samples, 'production_gate': 'UNCHANGED_BLOCKED'}

def render_midi(resource: dict, midi_path: str|Path, wav_path: str|Path, sample_rate: int=44100) -> dict:
    """Render MIDI through an approved SFZ backend.

    Command contract is adapter-driven. Set AI_COMP_SFZ_RENDERER to a compatible
    command-line backend when auto-detection is not sufficient. No synthetic fallback is allowed.
    """
    ready=preflight(resource)
    midi=Path(midi_path).resolve(); wav=Path(wav_path).resolve()
    if not midi.is_file(): raise SFZRendererError('MIDI_INPUT_MISSING')
    wav.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ready['renderer'],'--sfz',ready['sfz_path'],'--midi',str(midi),'--wav',str(wav),'--samplerate',str(sample_rate)]
    # Remove an old output so a failed process cannot be mistaken for success.
    if wav.exists(): wav.unlink()
    try:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise SFZRendererError('SFZ_RENDER_FAILED:'+str(exc))
    if cp.returncode!=0 or not wav.is_file():
        wav.unlink(missing_ok=True)
        raise SFZRendererError('SFZ_RENDER_FAILED:'+((cp.stderr or cp.stdout or '').strip()[:400]))
    try:
        try:
            with wave.open(str(wav),'rb') as stream:
                frames=stream.getnframes(); channels=stream.getnchannels(); rate=stream.getframerate()
                width=stream.getsampwidth(); audible=False
                if width not in (1,2,3,4) or stream.getcomptype() != 'NONE':
                    raise SFZRendererError('SFZ_WAVEFORM_UNSUPPORTED_FORMAT')
                while True:
                    chunk=stream.readframes(8192)
                    if not chunk: break
                    if width == 1:
                        values=np.frombuffer(chunk,dtype=np.uint8).astype(np.int16)-128
                    elif width == 2:
                        values=np.frombuffer(chunk,dtype='<i2')
                    elif width == 4:
                        values=np.frombuffer(chunk,dtype='<i4')
                    else:
                        raw=np.frombuffer(chunk,dtype=np.uint8).reshape(-1,3).astype(np.int32)
                        values=raw[:,0] | (raw[:,1]<<8) | (raw[:,2]<<16)
                        values=np.where(values & 0x800000, values-0x1000000, values)
                    if np.any(values != 0):
                        audible=True
                        break
            if not frames or not audible or rate!=sample_rate or channels not in (1,2):
                raise SFZRendererError('SFZ_WAVEFORM_INVALID_OR_SILENT')
        except (wave.Error, EOFError, OSError) as exc:
            raise SFZRendererError('SFZ_WAVEFORM_UNREADABLE:'+str(exc))
    except Exception:
        # Invalid or silent output must never survive as a purported finished stem.
        wav.unlink(missing_ok=True)
        raise
    return {**ready,'frames':frames,'channels':channels,'sample_rate':rate,'status':'AUDIO_RENDER_PASS','wav_path':str(wav),'audio_rendered':True}
