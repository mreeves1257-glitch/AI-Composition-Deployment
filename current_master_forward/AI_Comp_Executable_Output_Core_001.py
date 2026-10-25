#!/usr/bin/env python3
"""AI Composition — Executable Output Core 001

First executable vertical slice for the AI Comp Executable Theory Engine.

Responsibilities:
- Accept an immutable CompositionExecutionPackage.
- Compute a deterministic source fingerprint.
- Build a RenderRequest / RenderPlan.
- Route the same source package to MIDI and MusicXML adapters.
- Preserve source immutability and provenance.

Non-responsibilities:
- No composition or recomposition.
- No theory decisions.
- No genre selection.
- No instrument substitution.
- No audio rendering, stems, DAW packaging, or 3D spatial rendering yet.

This module is intentionally standalone so it does not overwrite the existing
Composition Sandbox, Theory Engine, Instrument Bridge, or Output/Render Interface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from fractions import Fraction
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence
import xml.etree.ElementTree as ET


ENGINE_ID = "AI_COMP_EXECUTABLE_OUTPUT_CORE_001"
SCHEMA_VERSION = "1.0.0"


class OutputCoreError(Exception):
    """Base exception for executable output-core failures."""


class ValidationError(OutputCoreError):
    pass


class SourceMutationError(OutputCoreError):
    pass


class UnsupportedOutputError(OutputCoreError):
    pass


class OutputType(str, Enum):
    MIDI = "MIDI"
    MUSICXML = "MUSICXML"


class RouteStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class TimeSignature:
    beats: int = 4
    beat_type: int = 4

    def validate(self) -> None:
        if self.beats <= 0:
            raise ValidationError("time signature beats must be > 0")
        if self.beat_type <= 0 or self.beat_type & (self.beat_type - 1):
            raise ValidationError("beat_type must be a positive power of two")

    def measure_quarter_beats(self) -> Fraction:
        return Fraction(self.beats * 4, self.beat_type)


@dataclass(frozen=True)
class MusicalEvent:
    event_id: str
    track_id: str
    instrument_id: str
    start_beats: Fraction
    duration_beats: Fraction
    midi_note: Optional[int] = None
    velocity: int = 80
    articulation: Optional[str] = None
    dynamic: Optional[str] = None

    def validate(self) -> None:
        if not self.event_id:
            raise ValidationError("event_id is required")
        if not self.track_id:
            raise ValidationError("track_id is required")
        if not self.instrument_id:
            raise ValidationError("instrument_id is required")
        if self.start_beats < 0:
            raise ValidationError(f"{self.event_id}: start_beats must be >= 0")
        if self.duration_beats <= 0:
            raise ValidationError(f"{self.event_id}: duration_beats must be > 0")
        if self.midi_note is not None and not (0 <= self.midi_note <= 127):
            raise ValidationError(f"{self.event_id}: midi_note must be 0..127")
        if not (1 <= self.velocity <= 127):
            raise ValidationError(f"{self.event_id}: velocity must be 1..127")


@dataclass(frozen=True)
class CompositionExecutionPackage:
    package_id: str
    title: str
    tempo_bpm: float
    time_signature: TimeSignature
    ppq: int
    events: tuple[MusicalEvent, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not self.package_id:
            raise ValidationError("package_id is required")
        if not self.title:
            raise ValidationError("title is required")
        if not math.isfinite(self.tempo_bpm) or self.tempo_bpm <= 0:
            raise ValidationError("tempo_bpm must be finite and > 0")
        if self.ppq <= 0:
            raise ValidationError("ppq must be > 0")
        self.time_signature.validate()
        if not self.events:
            raise ValidationError("at least one event is required")
        seen = set()
        for event in self.events:
            event.validate()
            if event.event_id in seen:
                raise ValidationError(f"duplicate event_id: {event.event_id}")
            seen.add(event.event_id)

    def track_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(event.track_id for event in self.events))


@dataclass(frozen=True)
class SourceExecutionFingerprint:
    algorithm: str
    digest: str
    schema_version: str


@dataclass(frozen=True)
class RenderRequest:
    request_id: str
    requested_outputs: tuple[OutputType, ...]

    def validate(self) -> None:
        if not self.request_id:
            raise ValidationError("request_id is required")
        if not self.requested_outputs:
            raise ValidationError("requested_outputs cannot be empty")
        if len(set(self.requested_outputs)) != len(self.requested_outputs):
            raise ValidationError("duplicate output types are not allowed")


@dataclass(frozen=True)
class OutputRoute:
    output_type: OutputType
    status: RouteStatus
    adapter_id: str


@dataclass(frozen=True)
class RenderPlan:
    plan_id: str
    source_package_id: str
    source_fingerprint: SourceExecutionFingerprint
    routes: tuple[OutputRoute, ...]


@dataclass(frozen=True)
class RenderArtifact:
    artifact_id: str
    output_type: OutputType
    source_fingerprint: SourceExecutionFingerprint
    media_type: str
    payload: bytes
    adapter_id: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


@dataclass(frozen=True)
class OutputPackage:
    output_package_id: str
    source_package_id: str
    source_fingerprint: SourceExecutionFingerprint
    render_plan: RenderPlan
    artifacts: tuple[RenderArtifact, ...]
    source_mutation_detected: bool


# ----------------------------- Canonical source -----------------------------


def _fraction_string(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _canonical_source_dict(package: CompositionExecutionPackage) -> dict[str, Any]:
    """Serialize only authoritative musical source state in deterministic order."""
    events = []
    for event in sorted(package.events, key=lambda e: (e.track_id, e.start_beats, e.event_id)):
        events.append(
            {
                "event_id": event.event_id,
                "track_id": event.track_id,
                "instrument_id": event.instrument_id,
                "start_beats": _fraction_string(event.start_beats),
                "duration_beats": _fraction_string(event.duration_beats),
                "midi_note": event.midi_note,
                "velocity": event.velocity,
                "articulation": event.articulation,
                "dynamic": event.dynamic,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": package.package_id,
        "title": package.title,
        "tempo_bpm": package.tempo_bpm,
        "time_signature": {
            "beats": package.time_signature.beats,
            "beat_type": package.time_signature.beat_type,
        },
        "ppq": package.ppq,
        "events": events,
        "metadata": list(package.metadata),
    }


def compute_source_fingerprint(package: CompositionExecutionPackage) -> SourceExecutionFingerprint:
    package.validate()
    canonical = json.dumps(
        _canonical_source_dict(package),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return SourceExecutionFingerprint(
        algorithm="sha256",
        digest=hashlib.sha256(canonical).hexdigest(),
        schema_version=SCHEMA_VERSION,
    )


# --------------------------------- MIDI ------------------------------------


def _u16be(value: int) -> bytes:
    return value.to_bytes(2, "big")


def _u32be(value: int) -> bytes:
    return value.to_bytes(4, "big")


def _vlq(value: int) -> bytes:
    if value < 0:
        raise ValueError("VLQ cannot encode a negative value")
    buffer = value & 0x7F
    out = bytearray([buffer])
    value >>= 7
    while value:
        buffer = (value & 0x7F) | 0x80
        out.insert(0, buffer)
        value >>= 7
    return bytes(out)


def _meta_text(meta_type: int, text: str) -> bytes:
    data = text.encode("utf-8")
    return bytes([0xFF, meta_type]) + _vlq(len(data)) + data


def _midi_pitch_events(events: Iterable[MusicalEvent], ppq: int, channel: int = 0) -> list[tuple[int, int, bytes]]:
    absolute: list[tuple[int, int, bytes]] = []
    for event in events:
        if event.midi_note is None:
            continue
        start = round(float(event.start_beats * ppq))
        end = round(float((event.start_beats + event.duration_beats) * ppq))
        if end <= start:
            end = start + 1
        # order: note-off (0) before note-on (1) at same tick
        absolute.append((start, 1, bytes([0x90 | channel, event.midi_note, event.velocity])))
        absolute.append((end, 0, bytes([0x80 | channel, event.midi_note, 0])))
    return sorted(absolute, key=lambda x: (x[0], x[1]))


class MidiAdapter:
    adapter_id = "MIDI_ADAPTER_001"

    def render(self, package: CompositionExecutionPackage, fingerprint: SourceExecutionFingerprint) -> RenderArtifact:
        tracks = package.track_ids()

        # Conductor track: tempo + time signature.
        conductor = bytearray()
        conductor += _vlq(0) + _meta_text(0x03, "Conductor")
        tempo_us = round(60_000_000 / package.tempo_bpm)
        if dict(package.metadata).get('tempo_map', '[]') != '[]':
            dd = int(math.log2(package.time_signature.beat_type))
            conductor += _vlq(0) + bytes([
                0xFF,
                0x58,
                0x04,
                package.time_signature.beats,
                dd,
                24,
                8,
            ])
        tempo_map = json.loads(dict(package.metadata).get('tempo_map', '[]'))
        if not tempo_map:
            conductor += _vlq(0) + bytes([0xFF, 0x51, 0x03]) + tempo_us.to_bytes(3, "big")
        else:
            previous_tick = 0
            previous_beat = -1
            for index, point in enumerate(tempo_map):
                beat, bpm = float(point['start_beat']), float(point['bpm'])
                if not math.isfinite(beat) or not math.isfinite(bpm) or beat < 0 or bpm <= 0:
                    raise ValidationError('TEMPO_MAP_INVALID')
                if (index == 0 and beat != 0) or beat <= previous_beat:
                    raise ValidationError('TEMPO_MAP_ORDER_INVALID')
                tick = round(beat * package.ppq)
                us = round(60_000_000 / bpm)
                if not 1 <= us <= 0xFFFFFF:
                    raise ValidationError('TEMPO_MAP_RANGE_INVALID')
                conductor += _vlq(tick-previous_tick) + bytes([0xFF,0x51,0x03]) + us.to_bytes(3,'big')
                previous_tick, previous_beat = tick, beat
        if not tempo_map:
            dd = int(math.log2(package.time_signature.beat_type))
            conductor += _vlq(0) + bytes([
                0xFF,
                0x58,
                0x04,
                package.time_signature.beats,
                dd,
                24,
                8,
            ])
        conductor += _vlq(0) + bytes([0xFF, 0x2F, 0x00])
        chunks = [b"MTrk" + _u32be(len(conductor)) + bytes(conductor)]

        routing = json.loads(dict(package.metadata).get('midi_routing', '{}'))
        expression_enabled = dict(package.metadata).get('classical_expression_enabled') == 'true'
        curves_enabled = dict(package.metadata).get('classical_expression_curves_enabled') == 'true'
        if curves_enabled and not expression_enabled:
            raise ValidationError('CLASSICAL_CURVES_REQUIRES_EXPRESSION')
        vibrato_enabled = dict(package.metadata).get('classical_midi_vibrato_enabled') == 'true'
        if vibrato_enabled and not expression_enabled:
            raise ValidationError('CLASSICAL_VIBRATO_REQUIRES_EXPRESSION')
        envelopes_enabled = dict(package.metadata).get('classical_instrument_envelopes_enabled') == 'true'
        if envelopes_enabled and not expression_enabled:
            raise ValidationError('CLASSICAL_ENVELOPES_REQUIRES_EXPRESSION')
        if envelopes_enabled and curves_enabled:
            raise ValidationError('CLASSICAL_ENVELOPES_CONFLICT_WITH_GENERIC_CURVES')
        melodic_pool = [c for c in range(16) if c != 9]
        channels = {}
        polyphonic_messages = {}
        track_channels = {}
        # Allocate globally, not independently per track: channel-wide CC11 must
        # never leak into another instrument's voice.
        if expression_enabled:
            from classical_polyphony import allocate_polyphonic_expression
            for track_id in tracks:
                route = routing.get(track_id, {})
                if route.get('percussion'):
                    channels[track_id] = 9
                    track_channels[track_id] = (9,)
                    continue
                track_events = [e for e in package.events if e.track_id == track_id]
                try:
                    profile = track_events[0].instrument_id if envelopes_enabled and track_events else None
                    profile = {'flute':'concert_flute','clarinet':'clarinet_bb'}.get(profile,profile)
                    if envelopes_enabled:
                        from classical_instrument_envelopes import PROFILES
                        if profile not in PROFILES:
                            raise ValueError('UNSUPPORTED_INSTRUMENT_PROFILE: ' + str(profile))
                    messages, used = allocate_polyphonic_expression(track_events, package.ppq, tuple(melodic_pool), use_curves=curves_enabled, use_vibrato=vibrato_enabled, tempo_bpm=package.tempo_bpm, instrument_profile=profile)
                except ValueError as exc:
                    raise ValidationError('CLASSICAL_EXPRESSION_UNSAFE: ' + str(exc)) from exc
                if not used:
                    raise ValidationError('CLASSICAL_EXPRESSION_NO_MELODIC_CHANNEL')
                polyphonic_messages[track_id] = messages
                track_channels[track_id] = used
                channels[track_id] = used[0]
                melodic_pool = [c for c in melodic_pool if c not in used]
        else:
            # Large ensembles routinely contain more than 15 logical tracks.
            # MIDI channels are channel-wide sound/control identities, not a
            # one-track-per-chair limit. Safely share a melodic channel only when
            # tracks use the same instrument and identical initial routing.
            # Percussion continues to share channel 10 (zero-based channel 9).
            available_channels = iter(melodic_pool)
            shared_channels = {}
            for track_id in tracks:
                route = routing.get(track_id, {})
                if route.get('percussion'):
                    channels[track_id] = 9
                else:
                    track_events = [e for e in package.events if e.track_id == track_id]
                    instrument_ids = tuple(dict.fromkeys(e.instrument_id for e in track_events))
                    if len(instrument_ids) != 1:
                        raise ValidationError(
                            f"track {track_id} contains multiple instrument IDs; "
                            "split instruments into separate logical tracks before MIDI routing"
                        )
                    initial_cc = tuple(sorted((int(k), int(v)) for k,v in route.get('initial_cc', {}).items()))
                    share_key = (instrument_ids[0], route.get('bank_msb'), route.get('bank_lsb'), route.get('program'), initial_cc)
                    if share_key not in shared_channels:
                        try:
                            shared_channels[share_key] = next(available_channels)
                        except StopIteration:
                            raise ValidationError('MIDI_MELODIC_CHANNEL_CAPACITY_EXCEEDED')
                    channels[track_id] = shared_channels[share_key]
                track_channels[track_id] = (channels[track_id],)
        for track_id in tracks:
            track_events = [e for e in package.events if e.track_id == track_id]
            instrument_ids = tuple(dict.fromkeys(e.instrument_id for e in track_events))
            if len(instrument_ids) != 1:
                raise ValidationError(
                    f"track {track_id} contains multiple instrument IDs; "
                    "split instruments into separate logical tracks before MIDI routing"
                )
            instrument_id = instrument_ids[0]
            body = bytearray()
            body += _vlq(0) + _meta_text(0x03, track_id)
            body += _vlq(0) + _meta_text(0x04, instrument_id)
            route = routing.get(track_id, {})
            channel = channels[track_id]
            for voice_channel in track_channels[track_id]:
                for key, controller in (('bank_msb', 0), ('bank_lsb', 32)):
                    if key in route:
                        value = int(route[key])
                        if not 0 <= value <= 127: raise ValidationError('MIDI_BANK_INVALID')
                        body += _vlq(0) + bytes([0xB0 | voice_channel, controller, value])
                for controller, value in route.get('initial_cc', {}).items():
                    controller = int(controller); value = int(value)
                    if not 0 <= controller <= 127 or not 0 <= value <= 127:
                        raise ValidationError('MIDI_CC_INVALID')
                    body += _vlq(0) + bytes([0xB0 | voice_channel, controller, value])
                if 'program' in route:
                    value = int(route['program'])
                    if not 0 <= value <= 127: raise ValidationError('MIDI_PROGRAM_INVALID')
                    body += _vlq(0) + bytes([0xC0 | voice_channel, value])
            if expression_enabled and channel != 9:
                absolute = polyphonic_messages[track_id]
            else:
                absolute = _midi_pitch_events(track_events, package.ppq, channel)
            last_tick = 0
            for tick, _, msg in absolute:
                body += _vlq(tick - last_tick) + msg
                last_tick = tick
            body += _vlq(0) + bytes([0xFF, 0x2F, 0x00])
            chunks.append(b"MTrk" + _u32be(len(body)) + bytes(body))

        header = b"MThd" + _u32be(6) + _u16be(1) + _u16be(len(chunks)) + _u16be(package.ppq)
        payload = header + b"".join(chunks)
        return RenderArtifact(
            artifact_id=f"{package.package_id}__midi",
            output_type=OutputType.MIDI,
            source_fingerprint=fingerprint,
            media_type="audio/midi",
            payload=payload,
            adapter_id=self.adapter_id,
        )


# ------------------------------- MusicXML ----------------------------------


_NOTE_NAMES = [
    ("C", 0),
    ("C", 1),
    ("D", 0),
    ("D", 1),
    ("E", 0),
    ("F", 0),
    ("F", 1),
    ("G", 0),
    ("G", 1),
    ("A", 0),
    ("A", 1),
    ("B", 0),
]


def _midi_to_pitch(note: int) -> tuple[str, int, int]:
    octave = note // 12 - 1
    step, alter = _NOTE_NAMES[note % 12]
    return step, alter, octave


def _duration_ticks(beats: Fraction, ppq: int) -> int:
    ticks = round(float(beats * ppq))
    if ticks <= 0:
        raise ValidationError("event duration quantizes to zero ticks")
    return ticks


def _measure_ticks(package: CompositionExecutionPackage) -> int:
    beats = package.time_signature.measure_quarter_beats()
    ticks = round(float(beats * package.ppq))
    if ticks <= 0:
        raise ValidationError("invalid measure length")
    return ticks


def _append_note(parent: ET.Element, note_number: int, duration: int, tie_start: bool, tie_stop: bool) -> None:
    note = ET.SubElement(parent, "note")
    pitch = ET.SubElement(note, "pitch")
    step, alter, octave = _midi_to_pitch(note_number)
    ET.SubElement(pitch, "step").text = step
    if alter:
        ET.SubElement(pitch, "alter").text = str(alter)
    ET.SubElement(pitch, "octave").text = str(octave)
    ET.SubElement(note, "duration").text = str(duration)
    if tie_stop:
        ET.SubElement(note, "tie", {"type": "stop"})
    if tie_start:
        ET.SubElement(note, "tie", {"type": "start"})
    if tie_start or tie_stop:
        notations = ET.SubElement(note, "notations")
        if tie_stop:
            ET.SubElement(notations, "tied", {"type": "stop"})
        if tie_start:
            ET.SubElement(notations, "tied", {"type": "start"})


def _append_rest(parent: ET.Element, duration: int) -> None:
    if duration <= 0:
        return
    note = ET.SubElement(parent, "note")
    ET.SubElement(note, "rest")
    ET.SubElement(note, "duration").text = str(duration)


class MusicXMLAdapter:
    adapter_id = "MUSICXML_ADAPTER_001"

    def render(self, package: CompositionExecutionPackage, fingerprint: SourceExecutionFingerprint) -> RenderArtifact:
        root = ET.Element("score-partwise", {"version": "4.0"})
        work = ET.SubElement(root, "work")
        ET.SubElement(work, "work-title").text = package.title
        identification = ET.SubElement(root, "identification")
        encoding = ET.SubElement(identification, "encoding")
        ET.SubElement(encoding, "software").text = ENGINE_ID

        part_list = ET.SubElement(root, "part-list")
        track_ids = package.track_ids()
        part_ids = {track_id: f"P{i+1}" for i, track_id in enumerate(track_ids)}
        for track_id in track_ids:
            track_events = [e for e in package.events if e.track_id == track_id]
            instruments = tuple(dict.fromkeys(e.instrument_id for e in track_events))
            if len(instruments) != 1:
                raise ValidationError(
                    f"track {track_id} contains multiple instrument IDs; "
                    "split instruments into separate logical tracks before MusicXML routing"
                )
            score_part = ET.SubElement(part_list, "score-part", {"id": part_ids[track_id]})
            ET.SubElement(score_part, "part-name").text = instruments[0]

        measure_ticks = _measure_ticks(package)
        max_end = max(
            round(float((e.start_beats + e.duration_beats) * package.ppq))
            for e in package.events
        )
        measure_count = max(1, math.ceil(max_end / measure_ticks))

        for track_id in track_ids:
            part = ET.SubElement(root, "part", {"id": part_ids[track_id]})
            events = sorted(
                [e for e in package.events if e.track_id == track_id],
                key=lambda e: (e.start_beats, e.event_id),
            )
            # First slice intentionally requires monophonic logical tracks.
            cursor_end = 0
            for e in events:
                start = round(float(e.start_beats * package.ppq))
                if start < cursor_end:
                    raise ValidationError(
                        f"track {track_id} contains overlapping events; "
                        "polyphonic MusicXML voices are not part of the first executable slice"
                    )
                cursor_end = start + _duration_ticks(e.duration_beats, package.ppq)

            # Create measures first.
            measures = []
            for index in range(measure_count):
                measure = ET.SubElement(part, "measure", {"number": str(index + 1)})
                measures.append(measure)
                if index == 0:
                    attrs = ET.SubElement(measure, "attributes")
                    ET.SubElement(attrs, "divisions").text = str(package.ppq)
                    time = ET.SubElement(attrs, "time")
                    ET.SubElement(time, "beats").text = str(package.time_signature.beats)
                    ET.SubElement(time, "beat-type").text = str(package.time_signature.beat_type)
                    sound = ET.SubElement(measure, "sound")
                    sound.set("tempo", f"{package.tempo_bpm:g}")

            # Fill each measure sequentially with rests + notes.
            by_measure: dict[int, list[tuple[int, MusicalEvent, int, int]]] = {i: [] for i in range(measure_count)}
            for event in events:
                if event.midi_note is None:
                    continue
                start_tick = round(float(event.start_beats * package.ppq))
                total_duration = _duration_ticks(event.duration_beats, package.ppq)
                remaining = total_duration
                segment_start = start_tick
                segment_index = 0
                while remaining > 0:
                    measure_index = segment_start // measure_ticks
                    within = segment_start % measure_ticks
                    available = measure_ticks - within
                    seg_duration = min(remaining, available)
                    by_measure.setdefault(measure_index, []).append(
                        (within, event, seg_duration, segment_index)
                    )
                    remaining -= seg_duration
                    segment_start += seg_duration
                    segment_index += 1

            for measure_index, measure in enumerate(measures):
                cursor = 0
                segments = sorted(by_measure.get(measure_index, []), key=lambda x: (x[0], x[1].event_id, x[3]))
                for within, event, seg_duration, seg_index in segments:
                    if within < cursor:
                        raise ValidationError(f"overlap detected in MusicXML measure {measure_index + 1}")
                    _append_rest(measure, within - cursor)
                    total_ticks = _duration_ticks(event.duration_beats, package.ppq)
                    start_tick = round(float(event.start_beats * package.ppq))
                    first_measure = start_tick // measure_ticks
                    final_tick_exclusive = start_tick + total_ticks
                    last_measure = (final_tick_exclusive - 1) // measure_ticks
                    tie_stop = measure_index > first_measure
                    tie_start = measure_index < last_measure
                    _append_note(measure, event.midi_note, seg_duration, tie_start, tie_stop)
                    cursor = within + seg_duration
                _append_rest(measure, measure_ticks - cursor)

        payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return RenderArtifact(
            artifact_id=f"{package.package_id}__musicxml",
            output_type=OutputType.MUSICXML,
            source_fingerprint=fingerprint,
            media_type="application/vnd.recordare.musicxml+xml",
            payload=payload,
            adapter_id=self.adapter_id,
        )


# ------------------------------ OutputManager -------------------------------


class OutputManager:
    def __init__(self) -> None:
        self._adapters = {
            OutputType.MIDI: MidiAdapter(),
            OutputType.MUSICXML: MusicXMLAdapter(),
        }

    def capability_matrix(self) -> dict[OutputType, RouteStatus]:
        return {output_type: RouteStatus.SUPPORTED for output_type in self._adapters}

    def build_render_plan(
        self,
        package: CompositionExecutionPackage,
        request: RenderRequest,
    ) -> RenderPlan:
        package.validate()
        request.validate()
        fingerprint = compute_source_fingerprint(package)
        routes = []
        for output_type in request.requested_outputs:
            adapter = self._adapters.get(output_type)
            if adapter is None:
                routes.append(OutputRoute(output_type, RouteStatus.UNSUPPORTED, ""))
            else:
                routes.append(OutputRoute(output_type, RouteStatus.SUPPORTED, adapter.adapter_id))
        unsupported = [r.output_type.value for r in routes if r.status is RouteStatus.UNSUPPORTED]
        if unsupported:
            raise UnsupportedOutputError(f"unsupported outputs: {', '.join(unsupported)}")
        return RenderPlan(
            plan_id=f"{request.request_id}__plan",
            source_package_id=package.package_id,
            source_fingerprint=fingerprint,
            routes=tuple(routes),
        )

    def execute(
        self,
        package: CompositionExecutionPackage,
        request: RenderRequest,
    ) -> OutputPackage:
        package.validate()
        # Deep-copy comparison is intentional: it catches accidental object mutation
        # even before the canonical fingerprint check.
        before_object = copy.deepcopy(package)
        before_fp = compute_source_fingerprint(package)
        plan = self.build_render_plan(package, request)
        if plan.source_fingerprint != before_fp:
            raise SourceMutationError("render plan source fingerprint mismatch")

        artifacts: list[RenderArtifact] = []
        for route in plan.routes:
            adapter = self._adapters[route.output_type]
            artifact = adapter.render(package, before_fp)
            if artifact.source_fingerprint != before_fp:
                raise SourceMutationError(f"{route.output_type.value} artifact fingerprint mismatch")
            artifacts.append(artifact)

        after_fp = compute_source_fingerprint(package)
        mutation = before_fp != after_fp or before_object != package
        if mutation:
            raise SourceMutationError("source package changed during output execution")

        return OutputPackage(
            output_package_id=f"{request.request_id}__output",
            source_package_id=package.package_id,
            source_fingerprint=before_fp,
            render_plan=plan,
            artifacts=tuple(artifacts),
            source_mutation_detected=False,
        )


# ---------------------------- File serialization ----------------------------


def write_output_package(output: OutputPackage, directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact in output.artifacts:
        if artifact.output_type is OutputType.MIDI:
            suffix = ".mid"
        elif artifact.output_type is OutputType.MUSICXML:
            suffix = ".musicxml"
        else:
            raise UnsupportedOutputError(artifact.output_type.value)
        path = directory / f"{artifact.artifact_id}{suffix}"
        path.write_bytes(artifact.payload)
        paths[artifact.output_type.value] = path

    manifest = {
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "output_package_id": output.output_package_id,
        "source_package_id": output.source_package_id,
        "source_fingerprint": asdict(output.source_fingerprint),
        "render_plan": {
            "plan_id": output.render_plan.plan_id,
            "routes": [
                {
                    "output_type": route.output_type.value,
                    "status": route.status.value,
                    "adapter_id": route.adapter_id,
                }
                for route in output.render_plan.routes
            ],
        },
        "source_mutation_detected": output.source_mutation_detected,
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "output_type": artifact.output_type.value,
                "adapter_id": artifact.adapter_id,
                "media_type": artifact.media_type,
                "sha256": artifact.sha256,
                "source_fingerprint": artifact.source_fingerprint.digest,
            }
            for artifact in output.artifacts
        ],
    }
    manifest_path = directory / f"{output.output_package_id}__manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    paths["MANIFEST"] = manifest_path
    return paths


# --------------------------- Canonical test fixture -------------------------


def build_first_slice_fixture() -> CompositionExecutionPackage:
    """A deterministic 3/4 fixture aligned with the project's earlier proof chain.

    Tracks are monophonic because polyphonic MusicXML voices are intentionally not
    part of the first executable output-routing slice.
    """
    return CompositionExecutionPackage(
        package_id="OUTPUT_CORE_FIXTURE_001",
        title="Executable Output Core — First Slice",
        tempo_bpm=72.0,
        time_signature=TimeSignature(3, 4),
        ppq=480,
        events=(
            MusicalEvent(
                event_id="E001",
                track_id="clarinet_track",
                instrument_id="Clarinet in Bb",
                start_beats=Fraction(0),
                duration_beats=Fraction(1),
                midi_note=52,  # E3 sounding reference for routing proof
                velocity=76,
                dynamic="mp",
            ),
            MusicalEvent(
                event_id="E002",
                track_id="clarinet_track",
                instrument_id="Clarinet in Bb",
                start_beats=Fraction(1),
                duration_beats=Fraction(2),
                midi_note=55,
                velocity=82,
                dynamic="mf",
            ),
            MusicalEvent(
                event_id="E003",
                track_id="bass_track",
                instrument_id="Double Bass",
                start_beats=Fraction(0),
                duration_beats=Fraction(3),
                midi_note=38,  # D2 sounding reference
                velocity=72,
                dynamic="mp",
            ),
            MusicalEvent(
                event_id="E004",
                track_id="bass_track",
                instrument_id="Double Bass",
                start_beats=Fraction(3),
                duration_beats=Fraction(3),
                midi_note=41,
                velocity=74,
                dynamic="mp",
            ),
        ),
        metadata=(("fixture", "first_executable_output_slice"),),
    )


def run_self_test(output_dir: Path) -> dict[str, Any]:
    package = build_first_slice_fixture()
    manager = OutputManager()
    request = RenderRequest(
        request_id="OUTPUT_CORE_RENDER_001",
        requested_outputs=(OutputType.MIDI, OutputType.MUSICXML),
    )

    original_fp = compute_source_fingerprint(package)
    output = manager.execute(package, request)
    final_fp = compute_source_fingerprint(package)
    paths = write_output_package(output, output_dir)

    midi_artifact = next(a for a in output.artifacts if a.output_type is OutputType.MIDI)
    xml_artifact = next(a for a in output.artifacts if a.output_type is OutputType.MUSICXML)

    tests: list[tuple[str, bool]] = []
    tests.append(("package validates", True))
    tests.append(("fingerprint deterministic", original_fp == final_fp))
    tests.append(("render plan uses source fingerprint", output.render_plan.source_fingerprint == original_fp))
    tests.append(("two output routes", len(output.render_plan.routes) == 2))
    tests.append(("MIDI route supported", any(r.output_type is OutputType.MIDI and r.status is RouteStatus.SUPPORTED for r in output.render_plan.routes)))
    tests.append(("MusicXML route supported", any(r.output_type is OutputType.MUSICXML and r.status is RouteStatus.SUPPORTED for r in output.render_plan.routes)))
    tests.append(("MIDI header valid", midi_artifact.payload.startswith(b"MThd")))
    tests.append(("MusicXML parses", ET.fromstring(xml_artifact.payload).tag == "score-partwise"))
    tests.append(("MIDI fingerprint matches", midi_artifact.source_fingerprint == original_fp))
    tests.append(("MusicXML fingerprint matches", xml_artifact.source_fingerprint == original_fp))
    tests.append(("source not mutated", not output.source_mutation_detected and original_fp == final_fp))
    tests.append(("manifest written", paths["MANIFEST"].exists()))
    tests.append(("MIDI file written", paths["MIDI"].exists() and paths["MIDI"].stat().st_size > 0))
    tests.append(("MusicXML file written", paths["MUSICXML"].exists() and paths["MUSICXML"].stat().st_size > 0))

    failures = [name for name, passed in tests if not passed]
    return {
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not failures else "FAIL",
        "tests_total": len(tests),
        "tests_passed": len(tests) - len(failures),
        "failures": failures,
        "source_fingerprint": original_fp.digest,
        "artifacts": {k: str(v) for k, v in paths.items()},
        "checks": [{"name": name, "passed": passed} for name, passed in tests],
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="AI Comp Executable Output Core 001")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the canonical first-slice executable test",
    )
    parser.add_argument(
        "--output-dir",
        default="./output_core_001_artifacts",
        help="artifact directory for --self-test",
    )
    args = parser.parse_args()

    if args.self_test:
        result = run_self_test(Path(args.output_dir))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())