#!/usr/bin/env python3
import json
from pathlib import Path
from engine import AICompositionEngine
ROOT=Path(__file__).resolve().parent
HISTORY=ROOT/'separator_test_history.json'
OUT=ROOT/'ALL_55_INSTRUMENT_SEPARATOR_VERIFICATION_2026-10-17.json'

def specs_for(e):
    out={}
    for n,p in e.theory_module_profiles.items():
        if p['resolution_policy']=='AUTOMATIC_BASELINE_ALLOWED': continue
        s={'verification_fixture_only':True,'sections':[{'genre':'House','duration_seconds':10},{'genre':'Techno','duration_seconds':10}]}
        if n=='Afro-Latin / Afrobeats Fusion': s['sections']=[{'genre':'Afrobeats','duration_seconds':10},{'genre':'Salsa','duration_seconds':10}]
        if n=='Regional Electronic Hybrids':
            s.update(region='Afrobeats component as registered in the preserved project',source_provenance='AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json:Afrobeats')
            s['sections']=[{'genre':'Afrobeats','duration_seconds':10},{'genre':'House','duration_seconds':10}]
        if p['resolution_policy']=='SAVED_PROFILE_REQUIRED': s['saved_profile_id']='VERIFICATION_FIXTURE_HOUSE_TECHNO_V1'
        out[n]=s
    return out

def main():
    if HISTORY.exists(): HISTORY.unlink()
    e=AICompositionEngine(history_path=HISTORY); specs=specs_for(e); rows=[]
    for i,n in enumerate(e.genre.numbered_choices(),1):
        err=None
        try:
            r=e.run(n,mode='quick',controlled_input=specs.get(n))
            th=r['modules']['theory']; inst=r['modules']['instrument']
            man=th.get('instrument_separator') or {}
            resolution=inst.get('instrument_separator_resolution') or {}
            if man.get('status')!='PASS': raise AssertionError('separator manifest not PASS')
            if resolution.get('status')!='PASS': raise AssertionError('resolution not PASS')
            regs=man.get('registrations') or []
            reg_iids={x.get('instrument_id') for x in regs if x.get('instrument_id')}
            event_iids={x.get('instrument_id') for x in th.get('events',[]) if x.get('instrument_id')}
            if not event_iids.issubset(reg_iids): raise AssertionError('event identity missing registration')
            st='PASS'
        except Exception as ex:
            st='FAIL'; err=repr(ex); r={}; regs=[]; reg_iids=set(); event_iids=set(); resolution={}
        rows.append({'index':i,'genre':n,'status':st,'engine_status':r.get('status'),'registration_count':len(regs),'registered_instrument_ids':sorted(reg_iids),'event_instrument_ids':sorted(event_iids),'resolution_status':resolution.get('status'),'error':err})
    failed=[x for x in rows if x['status']!='PASS']
    out={'schema':'AI_COMPOSER_ALL_55_INSTRUMENT_SEPARATOR_VERIFICATION_V2','genre_count':len(rows),'passed':len(rows)-len(failed),'failed':failed,'controlled_fixture_count':len(specs),'results':rows}
    OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('genre_count','passed','failed','controlled_fixture_count')},indent=2))
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())