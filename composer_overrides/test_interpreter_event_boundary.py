from interpreter_event_boundary import validate_interpreter_events, execute_interpreter_events, InterpreterEventError
roles=[{"part_id":"v1","instrument_id":"violin","role":"melody"},{"part_id":"v2","instrument_id":"violin","role":"counterline"},{"part_id":"b1","instrument_id":"double_bass","role":"bass"}]
events=[{"track_id":p["part_id"],"instrument_id":p["instrument_id"],"start_beat":0,"duration_beats":1,"midi":60,"velocity":75} for p in roles]
plan={"instrument_roles":roles,"events":events}
for genre in ("Classical","Jazz","Country"):
    assert len(validate_interpreter_events(genre,plan,{"violin","double_bass"}))==3
    result=execute_interpreter_events(genre,plan,{"violin","double_bass"},lambda ev,**kwargs: (len(ev),kwargs["creation_seed"]),creation_seed=11)
    assert result==(3,11)
for invalid in (dict(plan,events=events[:-1]),dict(plan,events=[dict(events[0],instrument_id="flute")]+events[1:])):
    try:
        validate_interpreter_events("Classical",invalid,{"violin","double_bass"})
        raise AssertionError("Invalid event plan accepted")
    except InterpreterEventError: pass
print("INTERPRETER_EVENT_BOUNDARY_TESTS_PASS")
