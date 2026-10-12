from universal_arrangement_handoff import validate_interpreter_arrangement, handoff_interpreter_arrangement, ArrangementHandoffError
parts=[{"part_id":"first_violin","instrument_id":"violin","role":"melody"},
       {"part_id":"second_violin","instrument_id":"violin","role":"counterline"},
       {"part_id":"cello","instrument_id":"cello","role":"bass"}]
plan={"instrument_roles":parts,"tempo":90}
for genre in ("Classical","Jazz","Country","Electronic"):
    got=validate_interpreter_arrangement(genre,plan,{"violin","cello"})
    assert len(got.instrument_roles)==3 and got.musical_plan==plan
    assert handoff_interpreter_arrangement(genre,plan,{"violin","cello"},lambda p,creation_seed:(p,creation_seed),creation_seed=42)==(plan,42)
try:
    validate_interpreter_arrangement("Classical",{"instrument_roles":[{"part_id":"x","instrument_id":"missing","role":"lead"}]},{"violin"})
    raise AssertionError("Unsupported instrument accepted")
except ArrangementHandoffError: pass
try:
    validate_interpreter_arrangement("Classical",{},{"violin"})
    raise AssertionError("Missing interpreter decision accepted")
except ArrangementHandoffError: pass
print("UNIVERSAL_HANDOFF_TESTS_PASS")
