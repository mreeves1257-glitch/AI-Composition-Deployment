#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from engine import AICompositionEngine
from genre_performance_realization import realize, REALIZER_ID

ROOT=Path(__file__).resolve().parent
HISTORY=ROOT/'performance_realization_test_history.json'
OUT=ROOT/'ALL_55_PERFORMANCE_REALIZATION_VERIFICATION_2026-10-17.json'
IDENTITY_FIELDS=('track_id','instrument_id','start_beat','duration_beats','midi','drum')


def controlled_specs(engine):
    specs={}
    for name,profile in engine.theory_module_profiles.items():
        policy=profile['resolution_policy']
        if policy=='AUTOMATIC_BASELINE_ALLOWED':
            continue
        spec={'verification_fixture_only':True,
              'sections':[{'genre':'House','duration_seconds':10},{'genre':'Techno','duration_seconds':10}]}
        if name=='Afro-Latin / Afrobeats Fusion':
            spec['sections']=[{'genre':'Afrobeats','duration_seconds':10},{'genre':'Salsa','duration_seconds':10}]
        if name=='Regional Electronic Hybrids':
            spec.update(region='Afrobeats component as registered in the preserved project',
                        source_provenance='AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json:Afrobeats')
            spec['sections']=[{'genre':'Afrobeats','duration_seconds':10},{'genre':'House','duration_seconds':10}]
        if policy=='SAVED_PROFILE_REQUIRED':
            spec['saved_profile_id']='VERIFICATION_FIXTURE_HOUSE_TECHNO_V1'
        specs[name]=spec
    return specs


def same_identity(before, after):
    if len(before)!=len(after): return False, 'event_count'
    for i,(a,b) in enumerate(zip(before,after)):
        for field in IDENTITY_FIELDS:
            if a.get(field)!=b.get(field):
                return False, f'{i}:{field}'
    return True, None


def main():
    if HISTORY.exists(): HISTORY.unlink()
    e=AICompositionEngine(history_path=HISTORY)
    specs=controlled_specs(e)
    rows=[]
    for idx,name in enumerate(e.genre.numbered_choices(),1):
        profile=e.theory_module_profiles[name]
        error=None
        try:
            if profile['resolution_policy']=='AUTOMATIC_BASELINE_ALLOWED':
                raw=e.theory.resolve(name,'quick',0)
                if raw.get('status')!='PASS': raise AssertionError('raw setup not PASS')
                direct=realize(name,profile,raw['events'],raw.get('pre_generation_genre_plan',{}),raw.get('meter','4/4'),raw.get('bars'))
                manifest=direct['manifest']
                identity_ok, identity_error=same_identity(raw['events'],direct['events'])
                if not identity_ok: raise AssertionError('direct identity mutation '+str(identity_error))
                if manifest['realizer_id']!=REALIZER_ID: raise AssertionError('realizer id')
                if name=='Classical':
                    if direct['events']!=raw['events']: raise AssertionError('Classical changed')
                    if manifest['policy']!='CLASSICAL_SPECIALIZED_PATH_UNCHANGED': raise AssertionError('Classical policy')
                else:
                    if manifest['policy']!='PROFILE_DYNAMIC_CONTOUR_ONLY_V1': raise AssertionError('automatic policy')
                    if manifest['dynamic_labeled_events']!=len(raw['events']): raise AssertionError('dynamic labels incomplete')
                    if manifest.get('max_velocity_delta',999)>12: raise AssertionError('velocity delta too large')
                    for ev in direct['events']:
                        if not ev.get('dynamic'): raise AssertionError('missing dynamic')
                        if ev.get('performance_realization_id')!=REALIZER_ID: raise AssertionError('event realizer id missing')
                result=e.run(name,mode='quick')
                theory=result['modules']['theory']
                eng_manifest=theory.get('musical_performance_realization') or {}
                if eng_manifest.get('realizer_id')!=REALIZER_ID: raise AssertionError('engine manifest missing')
                if result['modules']['instrument'].get('instrument_separator_resolution',{}).get('status')!='PASS':
                    raise AssertionError('separator resolution not PASS')
                controlled_components=0
                changed=eng_manifest.get('velocity_changed_events',0)
                max_delta=eng_manifest.get('max_velocity_delta',0)
            else:
                result=e.run(name,mode='quick',controlled_input=specs[name])
                theory=result['modules']['theory']
                eng_manifest=theory.get('musical_performance_realization') or {}
                if eng_manifest.get('policy')!='CONTROLLED_COMPONENT_REALIZATION_PRESERVED':
                    raise AssertionError('controlled top-level policy')
                provenance=theory.get('component_provenance') or []
                if not provenance: raise AssertionError('controlled provenance missing')
                for p in provenance:
                    cm=p.get('performance_realization') or {}
                    if cm.get('realizer_id')!=REALIZER_ID: raise AssertionError('component realizer missing')
                    if cm.get('policy')!='PROFILE_DYNAMIC_CONTOUR_ONLY_V1': raise AssertionError('component policy wrong')
                    if cm.get('dynamic_labeled_events')!=cm.get('realized_event_count'): raise AssertionError('component dynamic labels incomplete')
                    if cm.get('max_velocity_delta',999)>12: raise AssertionError('component delta too large')
                if result['modules']['instrument'].get('instrument_separator_resolution',{}).get('status')!='PASS':
                    raise AssertionError('controlled separator resolution not PASS')
                controlled_components=len(provenance)
                changed=sum((p.get('performance_realization') or {}).get('velocity_changed_events',0) for p in provenance)
                max_delta=max((p.get('performance_realization') or {}).get('max_velocity_delta',0) for p in provenance)
            status='PASS'
        except Exception as exc:
            status='FAIL'; error=repr(exc); result={}; changed=None; max_delta=None; controlled_components=None
        rows.append({
            'index':idx,'genre':name,'profile_id':profile['profile_id'],
            'resolution_policy':profile['resolution_policy'],'status':status,
            'engine_status':result.get('status'),'velocity_changed_events':changed,
            'max_velocity_delta':max_delta,'controlled_component_count':controlled_components,
            'error':error})
    failed=[r for r in rows if r['status']!='PASS']
    out={
        'schema':'AI_COMPOSER_ALL_55_PERFORMANCE_REALIZATION_VERIFICATION_V1',
        'genre_count':len(rows),'passed':len(rows)-len(failed),'failed':failed,
        'controlled_fixture_count':len(specs),
        'invariants':{
            'pitch_onset_duration_track_instrument_drum_identity':'PRESERVED_BY_REALIZER',
            'classical_specialized_path':'UNCHANGED_BY_REALIZER',
            'velocity_delta_bound':12,
            'automatic_nonclassical_dynamic_labels':'REQUIRED_FOR_ALL_EVENTS',
            'controlled_profiles':'SOURCE_COMPONENT_REALIZATION_PRESERVED'
        },
        'results':rows
    }
    OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('genre_count','passed','failed','controlled_fixture_count')},indent=2))
    return 1 if failed else 0

if __name__=='__main__':
    raise SystemExit(main())