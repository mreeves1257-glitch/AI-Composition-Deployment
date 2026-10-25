#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json
class TargetProgramError(RuntimeError): pass
class TargetProgram:
    def __init__(self, registry_path: str|Path):
        self.registry=json.loads(Path(registry_path).read_text())
    def resolve(self,target_id:str,instrument_package:dict[str,Any])->dict[str,Any]:
        target=self.registry.get('targets',{}).get(target_id)
        if not target: raise TargetProgramError('TARGET_PROFILE_MISSING')
        bindings = target.get('instrument_bindings', {})
        mix_plan = instrument_package.get('genre_mix_prominence_plan') or {}
        mix_by_track = {str(x.get('track_id')): x for x in mix_plan.get('entries', [])}
        cap_plan = instrument_package.get('performance_capability_requirements') or {}
        cap_by_track = {str(x.get('track_id')): x for x in cap_plan.get('entries', [])}
        resolved = []; missing = []
        for item in instrument_package.get('profiles', []):
            iid = item['instrument_id']; role = item.get('role', '')
            source = next((r.get('source_instrument_id') for r in instrument_package.get('source_requests',[]) if r['track_id']==item['track_id'] and r['instrument_id']==iid), iid)
            style_specific = source in ('drums_soft','drums_ride','brush_drums','drums_shuffle','drums_latin','drums_afro','drums_electronic','drums_dembow','break_drums')
            resource = bindings.get(iid + ':' + source) if style_specific else bindings.get(iid + ':' + role, bindings.get(iid))
            if resource is None:
                missing.append({'track_id': item['track_id'], 'instrument_id':iid, 'role':role, 'source_instrument_id':source, 'mix_control':mix_by_track.get(str(item['track_id'])), 'performance_capability_requirements':cap_by_track.get(str(item['track_id'])), 'proof_option':self.registry.get('recovered_proof_resource_options',{}).get('instruments',{}).get(iid,{}).get('proof_fallback')})
            else:
                # Real-resource integrity gate: a canonical acoustic/electric instrument may not
                # silently degrade to a synthetic fixture when a real sample resource is required.
                fallback_policy = resource.get('fallback_policy') if isinstance(resource, dict) else None
                render_model = resource.get('render_model') if isinstance(resource, dict) else None
                if fallback_policy == 'NO_SYNTHETIC_SUBSTITUTION' and render_model:
                    missing.append({'track_id': item['track_id'], 'instrument_id': iid, 'role': role, 'source_instrument_id': source,
                                    'mix_control':mix_by_track.get(str(item['track_id'])),
                                    'performance_capability_requirements':cap_by_track.get(str(item['track_id'])),
                                    'reason': 'SYNTHETIC_FALLBACK_FORBIDDEN'})
                    continue
                resolved.append({'track_id': item['track_id'], 'instrument_id': iid,
                                 'mix_control':mix_by_track.get(str(item['track_id'])),
                                 'performance_capability_requirements':cap_by_track.get(str(item['track_id'])),
                                 'resource': resource})
        if missing:
            return {'status':'RESOURCE_REQUIRED', 'reason':'TARGET_RESOURCE_BINDING_MISSING',
                    'target_id':target_id, 'target_profile':target, 'resolved_resources':resolved,
                    'missing':missing, 'render_allowed':False,
                    'authority':'MANUFACTURER_OR_INTERNAL_TARGET_ONLY'}
        return {
          'status':'PASS', 'render_allowed':False, 'audio_backend_verified':False, 'resolved_resources':resolved, 'program':'TARGET', 'target_id':target_id, 'target_profile':target,
          'instrument_profile_refs':[x['instrument_id'] for x in instrument_package.get('profiles',[])],
          'authority':'MANUFACTURER_OR_INTERNAL_TARGET_ONLY',
          'numeric_parameter_policy':'TARGET_AUTHORITY_ONLY_NO_ENGINE_DEFAULTS'
        }