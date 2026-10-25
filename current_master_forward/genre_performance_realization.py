"""Profile-authoritative musical performance realization before instrument separation.

This stage closes a specific gap: non-Classical profiles already describe dynamics,
articulation and ensemble behavior, but their generated events previously carried
almost no dynamic markings.  V1 deliberately changes only velocity/dynamic contour.
It does NOT change pitch, onset, duration, track, instrument, drum identity, or the
approved Classical path.  Timing/articulation/CC realization remain separate future
gates so unsupported behavior is never fabricated.
"""
from __future__ import annotations
import copy, hashlib, json, math

REALIZER_ID='GENRE_PERFORMANCE_REALIZATION_V1'

DYNAMIC_LEVELS=((40,'pp'),(55,'p'),(70,'mp'),(88,'mf'),(104,'f'),(127,'ff'))
ELECTRONIC_PREFIXES=('synth_','electronic_','noise_')


def _sha(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def _dynamic(v):
    for ceiling,name in DYNAMIC_LEVELS:
        if v<=ceiling:return name
    return 'ff'

def _deterministic_variation(genre,event,index,amount):
    if amount<=0:return 0
    key=f"{genre}|{index}|{event.get('track_id')}|{event.get('instrument_id')}|{event.get('midi')}|{event.get('start_beat')}"
    raw=hashlib.sha256(key.encode()).digest()[0]
    return (raw%(amount*2+1))-amount

def realize(genre, profile, events, generation_plan=None, meter=4, bars=None):
    source=copy.deepcopy(list(events))
    if not source: raise ValueError('PERFORMANCE_REALIZATION_NO_EVENTS')
    # Controlled/hybrid top-level profiles are assembled from explicit component
    # genres. Their component events are realized under each source profile before
    # combination; never impose a generic top-level contour afterward.
    if profile.get('resolution_policy')!='AUTOMATIC_BASELINE_ALLOWED':
        return {'status':'PASS','events':source,'manifest':{
            'status':'PASS','realizer_id':REALIZER_ID,'genre':genre,
            'policy':'CONTROLLED_COMPONENT_REALIZATION_PRESERVED',
            'source_event_count':len(source),'realized_event_count':len(source),
            'velocity_changed_events':0,'dynamic_labeled_events':sum(e.get('dynamic') is not None for e in source),
            'pitch_timing_identity_preserved':True,'source_sha256':_sha(source),'realized_sha256':_sha(source)}}

    # Classical is already the approved specialized expressive path. Do not touch it.
    if genre=='Classical':
        return {'status':'PASS','events':source,'manifest':{
            'status':'PASS','realizer_id':REALIZER_ID,'genre':genre,'policy':'CLASSICAL_SPECIALIZED_PATH_UNCHANGED',
            'source_event_count':len(source),'realized_event_count':len(source),'velocity_changed_events':0,
            'dynamic_labeled_events':sum(e.get('dynamic') is not None for e in source),
            'pitch_timing_identity_preserved':True,'source_sha256':_sha(source),'realized_sha256':_sha(source)}}

    tags=set((generation_plan or {}).get('semantic_tags',[]))
    phrase=max(1,int((generation_plan or {}).get('phrase_bars',4) or 4))
    try: meter_beats=float(meter.split('/')[0]) if isinstance(meter,str) else float(meter)
    except Exception: meter_beats=4.0
    if meter_beats<=0: meter_beats=4.0
    if bars is None:
        bars=max(1,math.ceil(max(float(e.get('start_beat',0)) for e in source)/meter_beats))
    bars=max(1,int(bars))

    # Profile-driven global feel, kept intentionally small. The generator already
    # supplies role velocities; this stage adds musical contour rather than replacing them.
    base_shift=0
    if 'light_attack' in tags: base_shift-=3
    if 'laidback' in tags: base_shift-=1
    if 'space' in tags: base_shift-=1
    if 'strong_one' in tags or 'horn_stab' in tags: base_shift+=1

    realized=[]; changed=0; labeled=0; max_delta=0
    for i,e in enumerate(source):
        item=copy.deepcopy(e)
        original=max(1,min(127,int(item.get('velocity',80))))
        bar=int(float(item.get('start_beat',0))//meter_beats)
        within=bar%phrase
        contour=0
        # Shared phrase contour: opening is settled; cadential/fill bar receives a
        # small lift. Wide-dynamic profiles get a larger but still bounded arc.
        if phrase>1:
            if within==0: contour-=1
            if within==phrase-1: contour+=3
        if 'wide_dynamic' in tags:
            phase=(bar/max(1,bars-1))*2-1
            contour+=round(5*phase)
        elif 'long_build' in tags:
            contour+=round(-3 + 6*(bar/max(1,bars-1)))
        if 'breaks' in tags and within==0 and bar>0:
            contour-=2

        iid=str(item.get('instrument_id',''))
        electronic=iid.startswith(ELECTRONIC_PREFIXES) or iid in ('synth_bass','synth_chord','synth_lead','synth_pad','synth_pulse','synth_arp','noise_fx')
        # Acoustic performers get tiny deterministic velocity variation. Electronic
        # parts stay tighter; this is velocity nuance, never timing jitter.
        variation=_deterministic_variation(genre,item,i,1 if electronic else 2)
        # Keep kick/strong structural hits stable; repeated hats/percussion may breathe.
        if item.get('drum')=='kick': variation=0
        new=max(1,min(127,original+base_shift+contour+variation))
        item['pre_performance_velocity']=original
        item['velocity']=new
        item['dynamic']=_dynamic(new)
        item['performance_realization_id']=REALIZER_ID
        item['performance_dynamic_source']='PROFILE_SEMANTIC_CONTOUR'
        if new!=original: changed+=1
        labeled+=1
        max_delta=max(max_delta,abs(new-original))
        realized.append(item)

    # Invariant: this V1 is forbidden from changing the musical identity/timeline.
    identity_fields=('track_id','instrument_id','start_beat','duration_beats','midi','drum')
    for before,after in zip(source,realized):
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise ValueError('PERFORMANCE_REALIZATION_IDENTITY_MUTATION::'+field)
    manifest={
        'status':'PASS','realizer_id':REALIZER_ID,'genre':genre,'policy':'PROFILE_DYNAMIC_CONTOUR_ONLY_V1',
        'source_event_count':len(source),'realized_event_count':len(realized),
        'velocity_changed_events':changed,'dynamic_labeled_events':labeled,'max_velocity_delta':max_delta,
        'pitch_timing_identity_preserved':True,'timing_humanization_status':'NOT_YET_EXECUTED',
        'target_articulation_switching_status':'NOT_YET_EXECUTED','continuous_cc_status':'NOT_YET_EXECUTED',
        'source_sha256':_sha(source),'realized_sha256':_sha(realized),
        'semantic_tags_used':sorted(tags),
    }
    return {'status':'PASS','events':realized,'manifest':manifest}