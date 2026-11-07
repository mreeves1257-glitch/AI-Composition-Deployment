"""Validate original recorded stems before the existing external 3D mixer.

No mixing, synthesis, control-panel changes, or modification of source audio.
"""
import hashlib
import json
from pathlib import Path
import wave


class StemDeliveryError(ValueError):
    pass


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(stems, expected_tracks, destination=None):
    expected = [str(x) for x in expected_tracks]
    if not expected or len(set(expected)) != len(expected):
        raise StemDeliveryError('INVALID_EXPECTED_TRACKS')
    if len(stems) != len(expected):
        raise StemDeliveryError('INCOMPLETE_STEM_SET')
    found = [str(x.get('track_id')) for x in stems]
    if len(set(found)) != len(found) or set(found) != set(expected):
        raise StemDeliveryError('STEM_TRACK_MISMATCH')
    checked = []
    used_paths = set()
    common_format = None
    for item in stems:
        if not item.get('instrument_id'):
            raise StemDeliveryError('STEM_INSTRUMENT_MISSING')
        path = Path(item.get('wav_path', ''))
        if not path.is_file():
            raise StemDeliveryError('STEM_AUDIO_MISSING')
        resolved = path.resolve()
        if resolved in used_paths:
            raise StemDeliveryError('DUPLICATE_STEM_AUDIO')
        used_paths.add(resolved)
        try:
            with wave.open(str(path), 'rb') as f:
                frames, rate, channels = f.getnframes(), f.getframerate(), f.getnchannels()
                width, compression = f.getsampwidth(), f.getcomptype()
                if frames <= 0 or rate <= 0 or channels not in (1, 2) or width not in (1, 2, 3, 4) or compression != 'NONE':
                    raise StemDeliveryError('STEM_AUDIO_INVALID')
                # Read the entire declared PCM stream to reject truncated files.
                pcm = f.readframes(frames)
                if len(pcm) != frames * channels * width:
                    raise StemDeliveryError('STEM_AUDIO_TRUNCATED')
                # 8-bit PCM silence is 0x80; other PCM widths use zero.
                silence = b'\x80' if width == 1 else b'\x00'
                if all(byte == silence[0] for byte in pcm):
                    raise StemDeliveryError('STEM_AUDIO_SILENT')
        except (wave.Error, EOFError, OSError) as exc:
            raise StemDeliveryError('STEM_AUDIO_INVALID') from exc
        fmt = (rate, width)
        if common_format is not None and fmt != common_format:
            raise StemDeliveryError('STEM_FORMAT_MISMATCH')
        common_format = fmt
        checked.append({'track_id': str(item['track_id']),
                        'instrument_id': str(item['instrument_id']),
                        'wav_path': str(resolved), 'sample_rate': rate,
                        'channels': channels, 'sample_width_bytes': width,
                        'frames': frames, 'sha256': _hash_file(path)})
    result = {'status': 'STEMS_VALIDATED_FOR_EXISTING_3D_MIXER',
              'finished_music': False, 'mixer_executed': False,
              'tracks': sorted(checked, key=lambda x: x['track_id'])}
    if destination is not None:
        output = Path(destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + '\n')
    return result
