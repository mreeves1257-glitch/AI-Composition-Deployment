"""Pre-render instrument/section registration separator.

Preserves independently arranged musical identities before instrument/resource
resolution.  It never invents instruments or notes.  Classical/Orchestra uses
explicit orchestral section identities; other genres preserve each existing
track/instrument identity and split only when a legacy track contains multiple
instrument identities.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict

SEPARATOR_ID = 'GENRE_INSTRUMENT_SEPARATOR_V1'


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def _safe(value):
    out=[]
    for ch in str(value).upper():
        out.append(ch if ch.isalnum() else '_')
    return ''.join(out).strip('_') or 'PART'


def _classical_section(player_id, instrument_id):
    pid=str(player_id or '').upper()
    prefixes=(
        ('VIOLIN_I_', 'VIOLIN_I'), ('VIOLIN_II_', 'VIOLIN_II'),
        ('VIOLA_', 'VIOLA'), ('CELLO_', 'CELLO'),
        ('DOUBLE_BASS_', 'DOUBLE_BASS'), ('FLUTE_', 'FLUTE'),
        ('OBOE_', 'OBOE'), ('CLARINET_', 'CLARINET'),
        ('BASSOON_', 'BASSOON'), ('HORN_', 'FRENCH_HORN'),
        ('TRUMPET_', 'TRUMPET'), ('TROMBONE_', 'TROMBONE'),
        ('TUBA_', 'TUBA'), ('TIMPANI_', 'TIMPANI'),
    )
    for prefix,section in prefixes:
        if pid.startswith(prefix):
            return section
    return _safe(instrument_id)


def separate_events(genre, events):
    """Return a non-destructive separated event list plus registration manifest."""
    if not events:
        raise ValueError('INSTRUMENT_SEPARATOR_NO_EVENTS')
    source=copy.deepcopy(list(events))
    out=[]

    # Detect legacy tracks carrying more than one instrument/drum identity.  Those
    # must be split; otherwise keep the original track name for compatibility.
    track_identities=defaultdict(set)
    for e in source:
        identity=(str(e.get('instrument_id')), str(e.get('drum') or ''))
        track_identities[str(e.get('track_id'))].add(identity)

    registrations={}
    counts=Counter()
    for e in source:
        original_track=str(e.get('track_id'))
        instrument=str(e.get('instrument_id'))
        drum=e.get('drum')
        item=copy.deepcopy(e)
        item['pre_separator_track_id']=original_track

        if genre == 'Classical':
            section=_classical_section(item.get('player_id'), instrument)
            registration_id='CLASSICAL__'+section
            separated_track=section
            registration_role=section
        else:
            if len(track_identities[original_track]) > 1:
                suffix=_safe(instrument + ('_'+str(drum) if drum else ''))
                separated_track=original_track+'__'+suffix
            else:
                separated_track=original_track
            registration_id=f"{_safe(genre)}__{_safe(separated_track)}__{_safe(instrument)}"
            if drum:
                registration_id += '__'+_safe(drum)
            registration_role=original_track

        item['track_id']=separated_track
        item['registration_id']=registration_id
        item['registration_role']=registration_role
        item['separator_id']=SEPARATOR_ID
        out.append(item)
        counts[registration_id]+=1
        if registration_id not in registrations:
            registrations[registration_id]={
                'registration_id':registration_id,
                'track_id':separated_track,
                'instrument_id':instrument,
                'role':registration_role,
                'player_ids':[],
                'drum_member':drum,
            }
        pid=item.get('player_id')
        if pid is not None and pid not in registrations[registration_id]['player_ids']:
            registrations[registration_id]['player_ids'].append(pid)

    # One registration may contain many players, but never conflicting instrument IDs.
    conflicts=[]
    by_reg=defaultdict(set)
    for e in out:
        by_reg[e['registration_id']].add(e['instrument_id'])
    for rid,iids in by_reg.items():
        if len(iids)>1:
            conflicts.append({'registration_id':rid,'instrument_ids':sorted(iids)})
    if conflicts:
        raise ValueError('INSTRUMENT_SEPARATOR_IDENTITY_COLLISION:'+json.dumps(conflicts,sort_keys=True))

    manifest={
        'status':'PASS',
        'separator_id':SEPARATOR_ID,
        'genre':genre,
        'source_event_count':len(source),
        'separated_event_count':len(out),
        'registration_count':len(registrations),
        'registrations':list(registrations.values()),
        'event_counts':dict(counts),
        'source_events_sha256':_sha(source),
        'separated_events_sha256':_sha(out),
        'rule':'DECLARED_INSTRUMENT_IDENTITIES_MUST_REMAIN_DISTINCT_UNTIL_RENDER_AND_MIX',
    }
    if genre=='Classical':
        manifest['section_policy']='ORCHESTRAL_SECTION_IDENTITY'
        manifest['expected_section_count']=14
    else:
        manifest['section_policy']='GENRE_NATIVE_TRACK_AND_INSTRUMENT_IDENTITY'
    return {'status':'PASS','events':out,'manifest':manifest}


def verify_instrument_resolution(manifest, instrument_package):
    expected={r['registration_id'] for r in manifest.get('registrations',[])}
    bindings=instrument_package.get('event_bindings',[])
    actual={b.get('registration_id') for b in bindings if b.get('registration_id')}
    missing=sorted(expected-actual)
    extra=sorted(actual-expected)
    if missing or extra:
        raise ValueError('INSTRUMENT_SEPARATOR_RESOLVER_MISMATCH:'+json.dumps({'missing':missing,'extra':extra},sort_keys=True))
    return {'status':'PASS','expected_registration_count':len(expected),
            'resolved_registration_count':len(actual),'missing_registrations':[],
            'extra_registrations':[]}