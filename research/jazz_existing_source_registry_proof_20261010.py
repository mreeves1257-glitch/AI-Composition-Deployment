"""Read-only evidence of original Jazz recorded instrument availability."""
import json
from pathlib import Path
root=Path('composer/runtime')
registry=json.loads((root/'target_registry.json').read_text())['targets']['INTERNAL']['instrument_bindings']
names=['double_bass','kick_drum_rock:brush_drums','snare_drum:brush_drums','clarinet_bb','electric_piano']
report={}
for name in names:
 entry=registry.get(name)
 if entry is None:
  report[name]={'installed':False}
  continue
 path=root/'sound_resources'/entry['resource_id']/entry['preferred_mapping']
 report[name]={'installed':path.is_file(),'source':entry['resource_id'],'program':entry['preferred_mapping'],'original_samples':entry.get('resource_type')=='SFZ_SAMPLE_LIBRARY'}
out=Path('jazz-existing-sources-report')
out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
