"""Read-only SFZ preprocessing and sample graph checks for the full SFZ backend.

sfizz resolves include and sample paths from the original SFZ directory, not
the directory of each nested include. Definitions/default_path follow stream order.
This checks bytes and paths, not opcode support or audible playback.
"""
from pathlib import Path
import re

class SampleGraphError(RuntimeError):
    pass

def validate_graph(sfz_path, allowed_root=None):
    primary = Path(sfz_path).resolve()
    base = primary.parent
    boundary = Path(allowed_root).resolve() if allowed_root is not None else None
    definitions = {}
    default_path = ''
    files, samples = set(), []
    missing = []
    silent_regions = []

    def expand(value):
        seen = set()
        while '$' in value:
            if value in seen:
                raise SampleGraphError('SFZ_MACRO_CYCLE')
            seen.add(value)
            def replace(match):
                name = match.group(0)
                if name not in definitions:
                    raise SampleGraphError('SFZ_UNDEFINED_MACRO:' + name)
                return definitions[name]
            updated = re.sub(r'\$[A-Za-z_][A-Za-z_0-9]*', replace, value)
            if updated == value:
                raise SampleGraphError('SFZ_UNRESOLVED_MACRO:' + value)
            value = updated
        return value.replace('\\', '/')

    def resolve(value):
        path = Path(value)
        result = (path if path.is_absolute() else base / path).resolve()
        if boundary is not None and not result.is_relative_to(boundary):
            raise SampleGraphError('SFZ_RESOURCE_PATH_ESCAPE:' + value)
        return result

    def walk(path, active):
        nonlocal default_path
        if len(active) >= 64 or path in active:
            raise SampleGraphError('SFZ_INCLUDE_CYCLE_OR_DEPTH')
        if not path.is_file():
            missing.append('INCLUDE:' + str(path)); return
        files.add(path)
        text = path.read_text(encoding='utf-8-sig')
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        text = re.sub(r'//[^\n]*', '', text)
        # Directives are expanded inline, preserving controller/path state.
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.fullmatch(r'#define\s+(\$[A-Za-z_][A-Za-z_0-9]*)\s+(.+)', line)
            if match:
                definitions[match[1]] = match[2].strip(); continue
            match = re.fullmatch(r'#include\s+["<]([^">]+)[">]', line)
            if match:
                walk(resolve(expand(match[1])), active + [path]); continue
            if line.startswith('#'):
                raise SampleGraphError('SFZ_UNSUPPORTED_DIRECTIVE:' + line)
            for opcode, raw in re.findall(
                r'(?:^|\s)(default_path|sample)\s*=\s*(.*?)(?=\s+[A-Za-z_][\w]*\s*=|\s*<|$)', line
            ):
                value = expand(raw.strip().strip('"'))
                if opcode == 'default_path':
                    default_path = value
                elif value.startswith('*'):
                    # Original drum libraries use silence for choke/mute groups.
                    # Count it separately; never substitute generated oscillators.
                    if value != '*silence':
                        raise SampleGraphError('SFZ_NON_RECORDED_SAMPLE:' + value)
                    silent_regions.append(path)
                else:
                    sample = resolve(default_path + value)
                    samples.append(sample)
                    if not sample.is_file():
                        missing.append(str(sample))

    if boundary is not None and not primary.is_relative_to(boundary):
        raise SampleGraphError('SFZ_RESOURCE_PATH_ESCAPE:' + str(primary))
    walk(primary, [])
    if missing:
        raise SampleGraphError('SFZ_SAMPLE_SET_INCOMPLETE:' + str(len(missing)) + '_MISSING')
    if not samples:
        raise SampleGraphError('SFZ_NO_SAMPLE_REFERENCES')
    result = {'sample_references': len(samples), 'unique_samples': len(set(samples)),
              'sfz_files_validated': len(files)}
    if silent_regions:
        result['silent_choke_regions'] = len(silent_regions)
    return result
