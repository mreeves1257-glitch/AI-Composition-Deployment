#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
import copy, hashlib, json

class PerformanceExecutionError(RuntimeError): pass
FORBIDDEN_LOCAL_DECISIONS={'LOCAL_THEORY_DEFAULTS','LOCAL_INSTRUMENT_DEFAULTS','LOCAL_TARGET_DEFAULTS','LOCAL_SOUND_SHAPING'}

class PerformanceExecutor:
    """Pass through resolved domain instructions without inventing sound shaping."""
    def execute(self,theory_package:dict[str,Any],instrument_package:dict[str,Any],target_package:dict[str,Any],events:list[dict[str,Any]]|None=None)->dict[str,Any]:
        if theory_package.get('authority')!='THEORY_ONLY':
            raise PerformanceExecutionError('THEORY_AUTHORITY_INVALID')
        if instrument_package.get('authority')!='INSTRUMENT_BEHAVIOR_ONLY':
            raise PerformanceExecutionError('INSTRUMENT_AUTHORITY_INVALID')
        if target_package.get('authority')!='MANUFACTURER_OR_INTERNAL_TARGET_ONLY':
            raise PerformanceExecutionError('TARGET_AUTHORITY_INVALID')
        source_events=events or []
        schedule=instrument_package.get('articulation_event_schedule',[])
        if schedule and len(schedule)!=len(source_events):
            raise PerformanceExecutionError('ARTICULATION_SCHEDULE_EVENT_COUNT_MISMATCH')
        for i, item in enumerate(schedule):
            if item.get('event_index')!=i:
                raise PerformanceExecutionError('ARTICULATION_SCHEDULE_ORDER_MISMATCH')
            event=source_events[i]
            if any(item.get(k)!=event.get(k) for k in ('track_id','articulation','start_beat','duration_beats','velocity','dynamic')):
                raise PerformanceExecutionError('ARTICULATION_SCHEDULE_SOURCE_MISMATCH')
        return {
          'program':'PERFORMANCE_EXECUTION', 'authority':'EXECUTE_RESOLVED_INSTRUCTIONS_ONLY',
          'genre_name':theory_package.get('genre_name'),
          'theory_package':copy.deepcopy(theory_package),
          'instrument_package':copy.deepcopy(instrument_package),
          'target_package':copy.deepcopy(target_package),
          'events':copy.deepcopy(source_events),
          'articulation_event_schedule':copy.deepcopy(schedule),
          'manipulation_performed':False,
          'local_musical_defaults_used':False,
          'local_instrument_defaults_used':False,
          'local_target_defaults_used':False,
          'status':'READY_FOR_ASSEMBLY'
        }

def canonical_sha256(obj:dict[str,Any])->str:
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()