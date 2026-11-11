from orchestra_trial_assembly import run_orchestra_trial, OrchestraTrialError
profile={"genre":"Classical","attachments":{"expressive_strings":{"enabled":True}}}
plan={"instrument_roles":[{"part_id":"violins_1","instrument_id":"violin","role":"melody","players":8}],
      "events":[{"track_id":"violins_1","instrument_id":"violin","start_beat":0,"duration_beats":2,"midi":72,"velocity":70,
                 "expression":{"legato":True,"crescendo":True}}],
      "enhancers":{"humanization":True},"sections":["A"],"tempo":90}
def interpreter(p,*,creation_seed):
    assert p is profile
    return {"musical_plan":plan}
def renderer(events,*,musical_plan,genre_profile,creation_seed):
    assert musical_plan is plan and genre_profile is profile
    assert events[0]["expression"]["crescendo"] is True
    assert musical_plan["instrument_roles"][0]["players"]==8
    return "TRIAL_HANDOFF_OK"
assert run_orchestra_trial(profile,interpreter,renderer,{"violin"},creation_seed=42)=="TRIAL_HANDOFF_OK"
try:
    run_orchestra_trial({"genre":"Jazz"},interpreter,renderer,{"violin"},creation_seed=42)
    raise AssertionError("Non-Classical trial allowed")
except OrchestraTrialError: pass
print("ORCHESTRA_TRIAL_HANDOFF_TESTS_PASS")
