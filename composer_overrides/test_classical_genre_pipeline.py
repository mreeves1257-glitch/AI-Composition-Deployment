"""No production imports or sound dependencies."""
from pathlib import Path
import json
import tempfile
from genre_pipeline import recognize_genre, execute_genre, GenrePipelineError

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/"Classical_Acoustic").mkdir()
    (root/"index.json").write_text(json.dumps({"genre_to_family_file":{"Classical":"Classical_Acoustic/profile.json"}}))
    (root/"Classical_Acoustic/profile.json").write_text(json.dumps({"profiles":{"Classical":{
        "genre":"Classical","family_name":"Classical_Acoustic",
        "musical_definition":{"profile_id":"CLASSICAL_TEST","resolution_policy":"AUTOMATIC_BASELINE_ALLOWED"}
    }}}))
    recognized=recognize_genre("Classical",root)
    assert recognized.profile_id=="CLASSICAL_TEST"
    try:
        recognize_genre("Swing",root)
        raise AssertionError("Non-Classical genre accepted")
    except GenrePipelineError: pass
    try:
        execute_genre(recognized,lambda *_: {"musical_plan":{}},lambda *_ , **__: None,creation_seed=1)
        raise AssertionError("Incomplete plan accepted")
    except GenrePipelineError: pass
    def interpreter(definition,profile):
        return {"musical_plan":{"tempo":90,"meter":"4/4","instrument_roles":[{"part_id":"v1","instrument_id":"violin","role":"lead"},{"part_id":"f1","instrument_id":"flute","role":"counterline"},{"part_id":"c1","instrument_id":"clarinet","role":"harmony"},{"part_id":"b1","instrument_id":"double_bass","role":"bass"}],"sections":["A","B","A"]}}
    def composer(plan,*,creation_seed):
        return {"seed":creation_seed,"roles":len(plan["instrument_roles"])}
    assert execute_genre(recognized,interpreter,composer,creation_seed=123,available_instruments={"violin","flute","clarinet","double_bass"})=={"seed":123,"roles":4}
print("PASS: Classical recognition, strict handoff, reject missing plan and other genres")
