"""
AI Composition — Internal Production Render 005 — RESTORED COMPONENT
Date: 2026-10-03

Purpose
-------
Restore the missing downstream Renderer 005 component from the protected
September 26/27 specification WITHOUT modifying the Control Panel or the
AI Composition engine.

This module is deliberately downstream-only. It accepts an already-created
performance/output handoff plus verified SFZ/WAV resource bindings.

Protected rules retained:
- Never reinterpret composition/theory.
- Never silently substitute GM resources in production/fidelity mode.
- Preserve independent stems.
- Preserve source event identity and CC7/CC11 intent.
- Do not normalize stems independently.
- Use only a single global headroom scale for the listening derivative.
- Ordinary sustain samples must not be labeled true sampled legato.
- Missing/unverified resources return RESOURCE_REQUIRED.
- Stereo is a derivative, not the protected 3D/object master.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import re
import random
import struct
import wave
from typing import Any, Dict, Iterable, List, Optional, Tuple


RENDERER_ID = "AI_COMP_INTERNAL_PRODUCTION_RENDER_005_RESTORED"
QUALITY_MODE = "FIDELITY_PRODUCTION"
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_HEADROOM_PEAK = 0.82


class Renderer005Error(RuntimeError):
    pass


@dataclass(frozen=True)
class SFZRegion:
    sample: Path
    pitch_keycenter: int
    lokey: int
    hikey: int
    lovel: int = 1
    hivel: int = 127
    lorand: float = 0.0
    hirand: float = 1.0
    ampeg_release: float = 0.025

    def accepts(self, note: int, velocity: int) -> bool:
        return self.lokey <= note <= self.hikey and self.lovel <= velocity <= self.hivel


_OPCODE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=')


def _tokenize_opcodes(text: str) -> Dict[str, str]:
    """Parse SFZ opcodes while preserving quoted paths containing spaces.

    This explicitly restores the documented Renderer 005 parser correction:
    quoted sample=/default_path= values stop at the closing quote and do not
    swallow following opcodes on the same line.
    """
    result: Dict[str, str] = {}
    matches = list(_OPCODE.finditer(text))
    for i, m in enumerate(matches):
        key = m.group(1).lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = text[start:end].strip()
        if raw.startswith('"'):
            q = raw.find('"', 1)
            if q < 0:
                raise Renderer005Error(f"UNTERMINATED_QUOTED_SFZ_VALUE:{key}")
            value = raw[1:q]
        else:
            # Unquoted SFZ values end at whitespace/comment boundaries.
            value = raw.strip().split()[0] if raw.strip() else ""
        result[key] = value
    return result


def parse_sfz(sfz_path: Path) -> List[SFZRegion]:
    sfz_path = Path(sfz_path).resolve()
    if not sfz_path.is_file():
        raise Renderer005Error(f"RESOURCE_REQUIRED:SFZ_NOT_FOUND:{sfz_path}")

    text = re.sub(r"(?m)//.*$", "", sfz_path.read_text(encoding="utf-8", errors="replace"))
    default_path = Path(".")
    regions: List[SFZRegion] = []
    global_ops: Dict[str, str] = {}
    group_ops: Dict[str, str] = {}

    # Keep headers as boundaries while allowing multiple opcodes per line.
    chunks = re.split(r'(?=<(?:global|group|region)>)', text)
    for chunk in chunks:
        stripped = chunk.strip()
        if not stripped:
            continue
        if stripped.startswith("<global>"):
            global_ops.update(_tokenize_opcodes(stripped[len("<global>"):]))
            if "default_path" in global_ops:
                default_path = Path(global_ops["default_path"].replace("\\", "/"))
        elif stripped.startswith("<group>"):
            group_ops = dict(global_ops)
            group_ops.update(_tokenize_opcodes(stripped[len("<group>"):]))
        elif stripped.startswith("<region>"):
            ops = dict(global_ops)
            ops.update(group_ops)
            ops.update(_tokenize_opcodes(stripped[len("<region>"):]))
            if "sample" not in ops:
                continue
            sample = (sfz_path.parent / default_path / ops["sample"].replace("\\", "/")).resolve()
            if not sample.is_file():
                raise Renderer005Error(f"RESOURCE_REQUIRED:SAMPLE_NOT_FOUND:{sample}")
            key = int(ops.get("pitch_keycenter", ops.get("key", 60)))
            lo = int(ops.get("lokey", ops.get("key", key)))
            hi = int(ops.get("hikey", ops.get("key", key)))
            lovel = int(ops.get("lovel", 1))
            hivel = int(ops.get("hivel", 127))
            lorand = float(ops.get("lorand", 0.0))
            hirand = float(ops.get("hirand", 1.0))
            release_seconds = float(ops.get("ampeg_release", 0.025))
            if not (0 <= lorand < hirand <= 1) or not (0 <= release_seconds <= 30):
                raise Renderer005Error("INVALID_EXPRESSIVE_SFZ_RANGE")
            regions.append(SFZRegion(sample, key, lo, hi, lovel, hivel, lorand, hirand, release_seconds))

    if not regions:
        raise Renderer005Error(f"RESOURCE_REQUIRED:NO_SFZ_REGIONS:{sfz_path}")
    return regions


def _read_pcm16_mono(path: Path) -> Tuple[int, List[float]]:
    # Historical function name retained for compatibility. WAV keeps the
    # dependency-free decoder proven against Growlybass. FLAC and other
    # libsndfile-supported lossless files use soundfile when available.
    suffix = path.suffix.lower()
    if suffix != ".wav":
        try:
            import soundfile as sf
            data, rate = sf.read(str(path), dtype="float32", always_2d=True)
        except Exception as exc:
            raise Renderer005Error(f"UNSUPPORTED_OR_UNREADABLE_SAMPLE:{path}:{exc}") from exc
        channels = int(data.shape[1])
        if channels == 1:
            mono = data[:, 0]
        elif channels == 2:
            mono = data.mean(axis=1)
        else:
            raise Renderer005Error(f"UNSUPPORTED_CHANNEL_COUNT:{path}:{channels}")
        return int(rate), [float(x) for x in mono]

    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if width == 2:
        vals = struct.unpack("<" + "h" * (len(frames) // 2), frames)
        scale = 32768.0
    elif width == 3:
        vals = []
        for i in range(0, len(frames), 3):
            v = frames[i] | (frames[i+1] << 8) | (frames[i+2] << 16)
            if v & 0x800000:
                v -= 0x1000000
            vals.append(v)
        scale = 8388608.0
    elif width == 4:
        vals = struct.unpack("<" + "i" * (len(frames) // 4), frames)
        scale = 2147483648.0
    else:
        raise Renderer005Error(f"UNSUPPORTED_SAMPLE_WIDTH:{path}:{width}")
    if channels == 1:
        mono = [v / scale for v in vals]
    elif channels == 2:
        mono = [((vals[i] + vals[i + 1]) * 0.5) / scale for i in range(0, len(vals), 2)]
    else:
        raise Renderer005Error(f"UNSUPPORTED_CHANNEL_COUNT:{path}:{channels}")
    return rate, mono


def _linear_resample(samples: List[float], ratio: float, wanted: int) -> List[float]:
    if not samples or wanted <= 0:
        return []
    out: List[float] = []
    for i in range(wanted):
        src = i * ratio
        j = int(src)
        frac = src - j
        if j >= len(samples) - 1:
            out.append(samples[-1])
        else:
            out.append(samples[j] * (1.0 - frac) + samples[j + 1] * frac)
    return out


def _write_pcm16_mono(path: Path, samples: Iterable[float], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = [max(-1.0, min(1.0, float(x))) for x in samples]
    ints = [int(round(x * 32767.0)) for x in clipped]
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * len(ints), *ints))


def _write_pcm16_stereo(path: Path, left: Iterable[float], right: Iterable[float], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    interleaved: List[int] = []
    for l, r in zip(left, right):
        interleaved.extend((
            int(round(max(-1.0, min(1.0, l)) * 32767.0)),
            int(round(max(-1.0, min(1.0, r)) * 32767.0)),
        ))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * len(interleaved), *interleaved))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _event_value(event: Dict[str, Any], *keys: str, default=None):
    for k in keys:
        if k in event and event[k] is not None:
            return event[k]
    return default


def _select_region(regions: List[SFZRegion], note: int, velocity: int, random_value: float = 0.5) -> SFZRegion:
    eligible = [r for r in regions if r.accepts(note, velocity) and r.lorand <= random_value < r.hirand]
    if not eligible:
        raise Renderer005Error(f"RESOURCE_REQUIRED:NO_REGION_FOR_NOTE:{note}:{velocity}")
    return min(eligible, key=lambda r: abs(r.pitch_keycenter - note))


def render_output_handoff(
    handoff: Dict[str, Any],
    resource_bindings: Dict[str, Dict[str, Any]],
    output_dir: Path,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    global_headroom_peak: float = DEFAULT_HEADROOM_PEAK,
    tuning_reference_hz: float = 440,
) -> Dict[str, Any]:
    """Render an existing AI Composition output handoff.

    resource_bindings format:
      {
        "instrument_id": {
          "sfz": "/absolute/or/relative/path/instrument.sfz",
          "verified": True,
          "license": "...",
          "provider": "...",
          "status": "VERIFIED_OPEN_RESOURCE"
        }
      }

    No resource is invented. Missing/unverified bindings return RESOURCE_REQUIRED.
    """
    modules = handoff.get("modules") or {}
    performance = modules.get("performance") or handoff.get("performance")
    if not isinstance(performance, dict):
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005", "reason": "PERFORMANCE_PACKAGE_REQUIRED"}

    events = performance.get("events")
    if not isinstance(events, list) or not events:
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005", "reason": "PERFORMANCE_EVENTS_REQUIRED"}

    # Validate the full performance package before allocating audio buffers or
    # opening resources. Invalid events must not crash or silently disappear.
    if any(not isinstance(e, dict) or not e.get("instrument_id") for e in events):
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "INVALID_INSTRUMENT_EVENT", "audio_rendered": False}
    # Instrument identifiers are used as stem filenames. Refuse traversal and
    # platform-special names rather than writing outside the designated folder.
    import re
    for e in events:
        iid = e["instrument_id"]
        if not isinstance(iid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", iid) or iid in (".", ".."):
            return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                    "reason": "INVALID_INSTRUMENT_ID", "audio_rendered": False}
    if not isinstance(resource_bindings, dict):
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "INVALID_RESOURCE_BINDINGS", "audio_rendered": False}
    instruments = sorted({str(e["instrument_id"]) for e in events})
    missing = []
    parsed: Dict[str, List[SFZRegion]] = {}
    provenance: Dict[str, Dict[str, Any]] = {}

    for instrument_id in instruments:
        binding = resource_bindings.get(instrument_id)
        if not binding:
            missing.append({"instrument_id": instrument_id, "reason": "NO_RESOURCE_BINDING"})
            continue
        if not binding.get("verified") or binding.get("status") != "VERIFIED_OPEN_RESOURCE":
            missing.append({"instrument_id": instrument_id, "reason": "UNVERIFIED_RESOURCE"})
            continue
        sfz = binding.get("sfz")
        if not sfz:
            missing.append({"instrument_id": instrument_id, "reason": "SFZ_PATH_REQUIRED"})
            continue
        try:
            parsed[instrument_id] = parse_sfz(Path(sfz))
        except Renderer005Error as exc:
            missing.append({"instrument_id": instrument_id, "reason": str(exc)})
            continue
        provenance[instrument_id] = {
            "provider": binding.get("provider"),
            "license": binding.get("license"),
            "status": binding.get("status"),
            "sfz": str(Path(sfz)),
        }

    if missing:
        return {
            "status": "RESOURCE_REQUIRED",
            "stage": "OUTPUT_RENDER_005",
            "missing": missing,
            "audio_rendered": False,
        }

    # Accept seconds directly when available. Otherwise preserve already-resolved
    # performance timing; Renderer 005 does not reinterpret theory.
    def start_seconds(e: Dict[str, Any]) -> float:
        v = _event_value(e, "start_seconds", "start_sec", "time_seconds")
        if v is None:
            raise Renderer005Error("RESOLVED_START_SECONDS_REQUIRED")
        return float(v)

    def duration_seconds(e: Dict[str, Any]) -> float:
        v = _event_value(e, "duration_seconds", "duration_sec")
        if v is None:
            raise Renderer005Error("RESOLVED_DURATION_SECONDS_REQUIRED")
        return max(0.001, float(v))

    def midi_integer(value: Any, label: str) -> int:
        # MIDI note and velocity are discrete values; truncating a fractional
        # number would silently change the intended performance.
        if isinstance(value, bool):
            raise Renderer005Error(f"INVALID_MIDI_{label}")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            raise Renderer005Error(f"INVALID_MIDI_{label}") from None
        if not math.isfinite(number) or not number.is_integer():
            raise Renderer005Error(f"INVALID_MIDI_{label}")
        return int(number)

    try:
        event_ends = []
        for e in events:
            start, duration = start_seconds(e), duration_seconds(e)
            note = midi_integer(_event_value(e, "midi_note", "note", default=60), "NOTE")
            velocity = midi_integer(_event_value(e, "velocity", default=96), "VELOCITY")
            if not (math.isfinite(start) and math.isfinite(duration)) or start < 0 or duration <= 0:
                raise Renderer005Error("INVALID_EVENT_TIMING")
            if not (0 <= note <= 127 and 1 <= velocity <= 127):
                raise Renderer005Error("INVALID_MIDI_NOTE_OR_VELOCITY")
            for control, aliases, fallback in (("cc7", ("cc7", "part_volume"), 100),
                                               ("cc11", ("cc11", "expression"), 127)):
                value = float(_event_value(e, *aliases, default=fallback))
                if not math.isfinite(value) or not (0 <= value <= 127):
                    raise Renderer005Error(f"INVALID_MIDI_CONTROL:{control}")
            event_ends.append(start + duration)
        end_time = max(event_ends)
        if not math.isfinite(end_time) or end_time > 3600:
            raise Renderer005Error("RENDER_DURATION_LIMIT_EXCEEDED")
    except (Renderer005Error, ValueError, TypeError, OverflowError) as exc:
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": str(exc), "audio_rendered": False}

    if not isinstance(sample_rate, int) or not (8000 <= sample_rate <= 192000):
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "INVALID_SAMPLE_RATE", "audio_rendered": False}
    if not isinstance(global_headroom_peak, (int, float)) or not math.isfinite(global_headroom_peak) or not (0 < global_headroom_peak <= 1):
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "INVALID_HEADROOM_PEAK", "audio_rendered": False}
    max_release = max((r.ampeg_release for rs in parsed.values() for r in rs), default=0.025)
    from musical_tuning import validate_reference
    tuning_reference_hz = validate_reference(tuning_reference_hz)
    total_frames = int(math.ceil((end_time + max_release + 0.05) * sample_rate))
    # Python float-list stems and mix are large; refuse requests likely to exhaust RAM.
    if total_frames * (len(instruments) + 2) > 20_000_000:
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "RENDER_MEMORY_BUDGET_EXCEEDED", "audio_rendered": False}
    stems: Dict[str, List[float]] = {iid: [0.0] * total_frames for iid in instruments}
    rendered_notes = 0
    rng = random.Random(0)  # Reproducible sample selection for testable renders.

    for event in events:
        iid = str(event["instrument_id"])
        note = midi_integer(_event_value(event, "midi_note", "note", default=60), "NOTE")
        velocity = midi_integer(_event_value(event, "velocity", default=96), "VELOCITY")
        cc7 = float(_event_value(event, "cc7", "part_volume", default=100.0)) / 127.0
        cc11 = float(_event_value(event, "cc11", "expression", default=127.0)) / 127.0
        region = _select_region(parsed[iid], note, velocity, rng.random())

        try:
            src_rate, src = _read_pcm16_mono(region.sample)
        except (Renderer005Error, OSError, EOFError, ValueError, wave.Error, struct.error) as exc:
            return {"status": "RESOURCE_REQUIRED", "stage": "OUTPUT_RENDER_005",
                    "audio_rendered": False,
                    "missing": [{"instrument_id": iid, "reason": "SAMPLE_DECODE_FAILED",
                                 "sample": str(region.sample), "detail": str(exc)}]}
        if src_rate <= 0 or len(src) < 2 or not all(math.isfinite(x) for x in src):
            return {"status": "RESOURCE_REQUIRED", "stage": "OUTPUT_RENDER_005",
                    "audio_rendered": False,
                    "missing": [{"instrument_id": iid, "reason": "INVALID_SAMPLE_AUDIO",
                                 "sample": str(region.sample)}]}
        dur = duration_seconds(event)
        release_frames = int(round(region.ampeg_release * sample_rate))
        note_frames = max(1, int(round(dur * sample_rate)))
        wanted = note_frames + release_frames
        pitch_ratio = (2.0 ** ((note - region.pitch_keycenter) / 12.0)) * (src_rate / sample_rate) * (tuning_reference_hz / 440)
        # A one-shot sample cannot be stretched into a sustained performance by
        # repeating its final frame. Reject unsupported note lengths explicitly.
        available_frames = int(math.floor((len(src) - 1) / pitch_ratio)) if pitch_ratio > 0 else 0
        # A sample must cover the held note, but its natural recorded decay may
        # end during the release envelope. Do not fabricate a sustained tail.
        if available_frames < note_frames:
            return {
                "status": "RESOURCE_REQUIRED",
                "stage": "OUTPUT_RENDER_005",
                "audio_rendered": False,
                "missing": [{"instrument_id": iid,
                             "reason": f"SAMPLE_TOO_SHORT_FOR_NOTE:{note}:available={available_frames}:required={note_frames}",
                             "sample": str(region.sample)}],
            }
        rendered_frames = min(wanted, available_frames)
        rendered = _linear_resample(src, pitch_ratio, rendered_frames)

        # Short anti-click envelope; event remains note-bounded.
        attack = min(len(rendered), int(0.008 * sample_rate))
        release = release_frames
        gain = max(0.0, min(1.0, velocity / 127.0)) * max(0.0, min(1.0, cc7)) * max(0.0, min(1.0, cc11))
        start = int(round(start_seconds(event) * sample_rate))
        stem = stems[iid]
        for i, s in enumerate(rendered):
            env = 1.0
            if attack and i < attack:
                env *= i / attack
            if release and i >= note_frames:
                env *= max(0.0, (wanted - i - 1) / release)
            pos = start + i
            if pos < len(stem):
                stem[pos] += s * gain * env
        rendered_notes += 1

    # Protected stems must never be silently clipped by the PCM16 writer.
    # A global listening-derivative scale cannot repair already-clipped stems.
    stem_peaks = {iid: max((abs(x) for x in samples), default=0.0)
                  for iid, samples in stems.items()}
    overloaded = {iid: peak for iid, peak in stem_peaks.items() if peak > 1.0}
    if overloaded:
        return {"status": "BLOCKED", "stage": "OUTPUT_RENDER_005",
                "reason": "STEM_PCM16_HEADROOM_EXCEEDED",
                "stem_peaks": overloaded, "audio_rendered": False}

    output_dir = Path(output_dir)
    stems_dir = output_dir / "stems"
    stem_records = []
    for iid, samples in stems.items():
        path = stems_dir / f"{iid}.wav"
        _write_pcm16_mono(path, samples, sample_rate)
        stem_records.append({
            "instrument_id": iid,
            "path": str(path),
            "sha256": _sha256(path),
            "event_count": sum(1 for e in events if str(e.get("instrument_id")) == iid),
        })

    # Single global scale only. No independent per-stem normalization.
    mono_mix = [0.0] * total_frames
    for stem in stems.values():
        for i, s in enumerate(stem):
            mono_mix[i] += s
    peak = max((abs(x) for x in mono_mix), default=0.0)
    global_scale = 1.0 if peak <= global_headroom_peak or peak == 0 else global_headroom_peak / peak
    derivative = [x * global_scale for x in mono_mix]

    # Renderer 005 supplies source/stem audio and a neutral listening derivative.
    # Spatial Scene Resolver 006 / Object Master 006 remains a separate downstream
    # authority and is intentionally NOT reimplemented here.
    left = derivative
    right = derivative
    stereo_path = output_dir / "derivatives" / "renderer005_stereo_listening_derivative.wav"
    _write_pcm16_stereo(stereo_path, left, right, sample_rate)

    manifest = {
        "renderer_id": RENDERER_ID,
        "status": "PASS_RENDER_005_AWAITING_006",
        "quality_mode": QUALITY_MODE,
        "audio_rendered": True,
        "event_count_input": len(events),
        "event_count_rendered": rendered_notes,
        "independent_stems": stem_records,
        "source_resource_provenance": provenance,
        "per_stem_normalization": False,
        "global_headroom_scale": global_scale,
        "global_peak_before_scale": peak,
        "stereo_derivative": {
            "path": str(stereo_path),
            "sha256": _sha256(stereo_path),
            "authoritative_master": False,
        },
        "next_required_stage": "SPATIAL_SCENE_RESOLVER_006_AND_OBJECT_BASED_3D_MASTER_006",
        "protected_rule": "STEREO_DERIVATIVE_IS_NOT_THE_AUTHORITATIVE_3D_MASTER",
    }
    manifest_path = output_dir / "AI_Comp_Internal_Production_Render_005_RESTORED_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Restored downstream Renderer 005. Does not modify AI Composition or Control Panel."
    )
    parser.add_argument("handoff_json", help="Existing AI Composition output-handoff JSON")
    parser.add_argument("resource_bindings_json", help="Verified resource binding JSON")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    handoff = json.loads(Path(args.handoff_json).read_text(encoding="utf-8"))
    bindings = json.loads(Path(args.resource_bindings_json).read_text(encoding="utf-8"))
    result = render_output_handoff(handoff, bindings, Path(args.output_dir))
    print(json.dumps(result, indent=2))
