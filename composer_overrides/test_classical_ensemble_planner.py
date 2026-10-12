from classical_ensemble_planner import plan_classical_ensemble, EnsembleError, CLASSICAL_ROLES
available=[name for name,_ in CLASSICAL_ROLES]
for intent,low,high in (("chamber",3,6),("expanded_chamber",5,9),
                        ("small_orchestra",9,15),("orchestra",16,len(available))):
    plans=[plan_classical_ensemble(musical_intent=intent,composition_seed=i,available_instruments=available) for i in range(12)]
    assert all(low<=len(p.instruments)<=high for p in plans)
    assert len({p.instruments for p in plans})>1
    assert all(len(set(p.instruments))==len(p.instruments) for p in plans)
try:
    plan_classical_ensemble(musical_intent="orchestra",composition_seed=0,available_instruments=["violin","flute"])
    raise AssertionError("Accepted unsupported orchestra")
except EnsembleError: pass
try:
    plan_classical_ensemble(musical_intent="unknown",composition_seed=0,available_instruments=available)
    raise AssertionError("Accepted unspecified intent")
except EnsembleError: pass
assert any(len(plan_classical_ensemble(musical_intent="orchestra",composition_seed=i,available_instruments=available).instruments)>20 for i in range(100)), "Orchestra still capped at 20"\nprint("CLASSICAL_ENSEMBLE_PLANNER_TESTS_PASS")
