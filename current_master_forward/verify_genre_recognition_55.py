#!/usr/bin/env python3
import json
from pathlib import Path
from engine import AICompositionEngine
from genre_recognition_fingerprints import validate, ANCHOR_FIELDS

ROOT=Path(__file__).resolve().parent

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

def main():
    history=ROOT/'fingerprint_test_history.json'
    if history.exists(): history.unlink()
    e=AICompositionEngine(history_path=history)
    specs=controlled_specs(e)
    rows=[]
    for i,name in enumerate(e.genre.numbered_choices()):
        profile=e.theory_module_profiles[name]
        spec=specs.get(name)
        result=e.run(name,mode='quick',controlled_input=spec)
        theory=result.get('modules',{}).get('theory') or result.get('theory_package',{})
        linkage=theory.get('genre_interpreter_linkage',{})
        fp=(linkage.get('interpreter') or {}).get('genre_recognition_fingerprint')
        try:
            fp=validate(fp,genre=name,profile_id=profile['profile_id'],requested_parts=theory.get('palette',[]))
            anchor_missing=[f for f in ANCHOR_FIELDS if f not in fp['profile_anchor_fields']]
            assert not anchor_missing, anchor_missing
            assert fp['disambiguation_rules']
            assert fp['separator_requirement']=='EVERY_REQUESTED_PART_IDENTITY_SURVIVES_TO_INSTRUMENT_RESOLUTION'
            # If the full engine made modules, the exact fingerprint must survive as its own module.
            if result.get('modules'):
                assert result['modules']['genre_recognition_fingerprint']==fp
            status='PASS'
            error=None
        except Exception as exc:
            status='FAIL'; error=repr(exc)
        rows.append({'index':i+1,'genre':name,'profile_id':profile['profile_id'],
                     'resolution_policy':profile['resolution_policy'],
                     'engine_status':result.get('status'),'fingerprint_status':status,
                     'requested_part_count':len(theory.get('palette',[])),
                     'nearest_neighbors':(fp or {}).get('nearest_neighbors') if isinstance(fp,dict) else None,
                     'error':error})
    out={'schema':'AI_COMPOSER_ALL_55_GENRE_RECOGNITION_VERIFICATION_V1',
         'genre_count':len(rows),'passed':sum(r['fingerprint_status']=='PASS' for r in rows),
         'failed':[r for r in rows if r['fingerprint_status']!='PASS'],
         'controlled_fixture_count':len(specs),'results':rows}
    (ROOT/'ALL_55_GENRE_RECOGNITION_VERIFICATION_2026-10-17.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:out[k] for k in ('genre_count','passed','failed','controlled_fixture_count')},indent=2))
    return 1 if out['failed'] else 0

if __name__=='__main__':
    raise SystemExit(main())