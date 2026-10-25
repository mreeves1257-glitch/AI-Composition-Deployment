"""Execute explicit component sections without replacing the 55 registered profiles."""
import copy, hashlib, json, math


def create_controlled(adapter, genre, profile, specification, mode):
    if profile['resolution_policy']=='AUTOMATIC_BASELINE_ALLOWED':raise ValueError('CONTROLLED_INPUT_ONLY_FOR_CONTROLLED_GENRES')
    if not isinstance(specification, dict):
        return {'status':'CONTROLLED_INPUT_REQUIRED','genre_name':genre,'events':[]}
    if profile['resolution_policy']=='SAVED_PROFILE_REQUIRED' and not specification.get('saved_profile_id'):
        raise ValueError('SAVED_PROFILE_ID_REQUIRED')
    if genre=='Regional Electronic Hybrids' and not all(specification.get(k) for k in ('region','source_provenance')):
        raise ValueError('REGIONAL_SOURCE_PROVENANCE_REQUIRED')
    sections=specification.get('sections')
    if not isinstance(sections,list) or not sections or len(sections)>8:
        raise ValueError('CONTROLLED_SECTIONS_REQUIRED_MAX_8')
    seed=len(adapter._history()); resolved=[]; provenance=[]; meter=None; tempo=None
    for number, section in enumerate(sections):
        if not isinstance(section,dict):raise ValueError('CONTROLLED_SECTION_INVALID')
        source=section.get('genre')
        if source==genre:raise ValueError('CONTROLLED_COMPONENT_RECURSION')
        setup=adapter.resolve(source,mode,seed+number)
        if setup.get('status')!='PASS':raise ValueError('COMPONENT_MUST_BE_AUTOMATIC_PROFILE:'+str(source))
        # Realize each controlled component under its own source-genre profile
        # before it is time-scaled and combined. This preserves component identity
        # instead of applying a generic hybrid dynamic contour afterward.
        from genre_performance_realization import realize as realize_genre_performance
        registry=json.loads((__import__('pathlib').Path(__file__).parent/'AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json').read_text())['profiles']
        component_realization=realize_genre_performance(
            source, registry[source], setup['events'],
            generation_plan=setup.get('pre_generation_genre_plan',{}),
            meter=setup.get('meter','4/4'), bars=setup.get('bars'))
        setup=copy.deepcopy(setup)
        setup['events']=component_realization['events']
        setup['component_performance_realization']=component_realization['manifest']
        seconds=section.get('duration_seconds')
        if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 1<=seconds<=setup['duration_seconds']:
            raise ValueError('SECTION_DURATION_OUT_OF_RANGE')
        if meter is None:meter=setup['meter'];tempo=setup['tempo_bpm']
        if setup['meter']!=meter:raise ValueError('COMPONENT_METER_CONFLICT_REQUIRES_EXPLICIT_TRANSFORMATION')
        resolved.append((number,section,source,setup,seconds))
    palette=sorted({part for _,_,_,setup,_ in resolved for part in setup.get('palette',[])})
    if not palette:raise ValueError('CONTROLLED_COMPONENT_PARTS_MISSING')
    from genre_interpreter_linkage import interpret_genre
    interpreted=interpret_genre(genre,profile,palette)
    controlled_plan={'source':'EXPLICIT_COMPONENT_SECTIONS','meter':meter,'tempo_bpm':tempo,
                     'sections':[{'genre':source,'profile_id':setup['profile_id'],'duration_seconds':seconds}
                                 for _,_,source,setup,seconds in resolved]}
    from genre_communication_blueprint import build as build_communication_blueprint
    communication_blueprint=build_communication_blueprint(genre,profile,palette,interpreted,controlled_plan,controlled_input=specification)
    events=[]; elapsed=0.
    for number, section, source, setup, seconds in resolved:
        ratio=tempo/setup['tempo_bpm']; boundary=seconds*setup['tempo_bpm']/60
        count=0
        for original in setup['events']:
            if original['start_beat']>=boundary:continue
            event=copy.deepcopy(original)
            event['track_id']=f"S{number+1}_"+str(event['track_id'])
            event['duration_beats']=min(event['duration_beats'],boundary-event['start_beat'])*ratio
            event['start_beat']=elapsed*tempo/60+event['start_beat']*ratio
            event['component_genre']=source
            events.append(event);count+=1
        provenance.append({'section':number+1,'genre':source,'profile_id':setup['profile_id'],'start_seconds':elapsed,'duration_seconds':seconds,'source_tempo_bpm':setup['tempo_bpm'],'event_count':count,'performance_realization':copy.deepcopy(setup.get('component_performance_realization'))})
        elapsed+=seconds
    if not events:raise ValueError('CONTROLLED_NO_EVENTS')
    first=copy.deepcopy(resolved[0][3])
    first.update(genre_name=genre,profile_id=profile['profile_id'],resolution_policy=profile['resolution_policy'],events=events,palette=palette,tempo_bpm=tempo,meter=meter,duration_seconds=elapsed,execution_template='EXPLICIT_COMPONENT_SECTIONS',component_provenance=provenance,controlled_input=copy.deepcopy(specification),communication_blueprint=communication_blueprint,pre_generation_genre_plan=controlled_plan)
    first['profile_required_fields_sha256']=hashlib.sha256(json.dumps({k:profile[k] for k in json.loads((__import__('pathlib').Path(__file__).parent/'AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json').read_text())['universal_required_fields']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    first['composition_fingerprint']=hashlib.sha256(json.dumps({'genre':genre,'events':events,'components':provenance},sort_keys=True).encode()).hexdigest()
    first['duplicate_guard']='PASS_UNIQUE'
    from genre_interpreter_linkage import link_genre
    first['genre_interpreter_linkage']=link_genre(genre,profile,palette,events,interpreted=interpreted)
    return first