#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

class InstrumentProgramError(RuntimeError): pass

class InstrumentProgram:
    def __init__(self, library_path: str | Path):
        self.library_path=Path(library_path)
        self.library=json.loads(self.library_path.read_text())
        self.by_id={x['id']:x for x in self.library.get('instruments',[])}

    def _resolve_single(self, req: dict[str,Any]) -> list[dict[str,Any]]:
        iid=req.get('instrument_id')
        if iid not in self.by_id:
            raise InstrumentProgramError(f'INSTRUMENT_PROFILE_MISSING::{iid}')
        profile=self.by_id[iid]
        base={
            'track_id':req.get('track_id'),
            'registration_id':req.get('registration_id'),
            'source_track_id':req.get('source_track_id'),
            'role':req.get('role'),
            'instrument_id':iid,
            'instrument_profile':profile,
            'requested_articulations':req.get('articulations',[]),
            'requested_register':req.get('register_request'),
            'behavior_authority':'INSTRUMENT_LIBRARY',
        }
        if not profile.get('composite'):
            return [base]

        kit_intent=req.get('kit_intent',{})
        member_map=dict(profile.get('member_role_defaults',{}))
        member_map.update(kit_intent.get('member_overrides',{}))
        required_roles=kit_intent.get('required_roles') or profile.get('required_core_roles',[])
        extended_roles=kit_intent.get('extended_roles',[])
        roles=[]
        for role in list(required_roles)+list(extended_roles):
            if role not in roles:
                roles.append(role)

        member_profiles=[]
        for role in roles:
            member_id=member_map.get(role)
            if not member_id:
                raise InstrumentProgramError(f'DRUM_KIT_MEMBER_MAPPING_MISSING::{role}')
            member=self.by_id.get(member_id)
            if not member:
                raise InstrumentProgramError(f'DRUM_KIT_MEMBER_PROFILE_MISSING::{role}::{member_id}')
            member_profiles.append({
                'track_id':role,
                'parent_track_id':req.get('track_id'),
                'role':f'DRUM_KIT_MEMBER::{role}',
                'kit_member_role':role,
                'kit_profile_id':iid,
                'instrument_id':member_id,
                'instrument_profile':member,
                'behavior_authority':'INSTRUMENT_LIBRARY',
                'composite_member':True,
            })
        base['kit_intent']=kit_intent
        base['resolved_member_ids']=[x['instrument_id'] for x in member_profiles]
        base['composite_profile']=True
        return [base]+member_profiles

    def resolve_events(self, events):
        aliases = {'electric_bass': 'electric_bass_guitar', 'lead_guitar': 'electric_guitar',
                   'flute': 'concert_flute', 'clarinet': 'clarinet_bb',
                   'trumpet': 'trumpet_c', 'trombone': 'tenor_trombone', 'conga': 'conga_family'}
        requests = {}; missing = []; bindings = []; event_schedule = []
        for event in events:
            original = event['instrument_id']
            instrument = aliases.get(original, original)
            drum = event.get('drum')
            if drum and original in ('drums', 'drums_four', 'drums_soft', 'drums_ride', 'brush_drums', 'drums_shuffle', 'drums_latin', 'drums_afro'):
                instrument = {'kick':'kick_drum_rock', 'snare':'snare_drum', 'hat':'hi_hat', 'ride':'ride_cymbal', 'crash':'crash_cymbal', 'tom':'tom_tom'}.get(drum, original)
            elif drum and original in ('drums_electronic', 'drums_dembow', 'break_drums'):
                instrument = {'kick':'electronic_kick', 'snare':'electronic_snare', 'hat':'electronic_hat'}.get(drum, original)
            if original == 'drums_ride' and drum == 'hat': instrument = 'ride_cymbal'
            if instrument not in self.by_id:
                if original not in missing: missing.append(original)
                continue
            track = event['track_id']
            source_track = event.get('pre_separator_track_id', track)
            registration_id = event.get('registration_id', str(track))
            role_source = event.get('registration_role', source_track)
            role = ('LEAD_MELODY' if role_source == 'LEAD' else
                    'RHYTHM_POWER_CHORDS' if original == 'electric_guitar' and role_source == 'HARMONY' else role_source)
            key = (registration_id, track, instrument, role)
            if key not in requests:
                requests[key] = {'track_id': track, 'registration_id':registration_id,
                                 'source_track_id':source_track, 'instrument_id': instrument,
                                 'role': role, 'articulations':[], 'source_instrument_id':original}
            articulation = event.get('articulation')
            if articulation and articulation not in requests[key]['articulations']:
                requests[key]['articulations'].append(articulation)
            event_schedule.append({'event_index':len(event_schedule), 'track_id':track,
                'registration_id':registration_id, 'source_track_id':source_track,
                'instrument_id':instrument, 'role':role, 'articulation':articulation,
                'start_beat':event.get('start_beat'), 'duration_beats':event.get('duration_beats'),
                'velocity':event.get('velocity'), 'dynamic':event.get('dynamic')})
            binding = {'track_id': track, 'registration_id':registration_id,
                       'source_track_id':source_track, 'source_instrument_id': original,
                       'instrument_id': instrument, 'role': role}
            if binding not in bindings: bindings.append(binding)
        if missing:
            return {'status': 'BLOCKED', 'missing': missing, 'authority': 'INSTRUMENT_BEHAVIOR_ONLY'}
        result = self.resolve(list(requests.values()))
        result['event_bindings'] = bindings
        result['articulation_event_schedule'] = event_schedule
        result['source_requests'] = list(requests.values())
        result['status'] = 'PASS'
        return result

    def resolve(self, requests: list[dict[str,Any]]) -> dict[str,Any]:
        resolved=[]
        for req in requests:
            resolved.extend(self._resolve_single(req))
        return {
            'program':'INSTRUMENT',
            'authority':'INSTRUMENT_BEHAVIOR_ONLY',
            'profiles':resolved,
            'drum_kit_system_id':self.library.get('drum_kit_system',{}).get('system_id'),
            'no_engine_override':True,
        }