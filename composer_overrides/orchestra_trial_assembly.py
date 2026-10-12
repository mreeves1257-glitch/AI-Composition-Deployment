"""Isolated orchestral trial assembly: preserves interpreter plan and enhancements.

No palette selection, fixed size, synthesis, or deployment. A supplied real
interpreter and renderer are required; this module never simulates them.
"""
from universal_arrangement_handoff import validate_interpreter_arrangement
from interpreter_event_boundary import validate_interpreter_events

class OrchestraTrialError(ValueError): pass

def run_orchestra_trial(genre_profile, interpreter, renderer, available_instruments, *, creation_seed):
    if not isinstance(genre_profile, dict) or genre_profile.get("genre") != "Classical":
        raise OrchestraTrialError("CLASSICAL_TRIAL_ONLY")
    if not callable(interpreter) or not callable(renderer):
        raise OrchestraTrialError("REAL_INTERPRETER_AND_RENDERER_REQUIRED")
    # Preserve the original profile and all attachments. No filtering.
    interpreted = interpreter(genre_profile, creation_seed=creation_seed)
    if not isinstance(interpreted, dict) or not isinstance(interpreted.get("musical_plan"), dict):
        raise OrchestraTrialError("INTERPRETER_PLAN_REQUIRED")
    plan = interpreted["musical_plan"]
    validate_interpreter_arrangement("Classical",plan,available_instruments)
    events = validate_interpreter_events("Classical",plan,available_instruments)
    # The renderer receives the entire plan, not only MIDI notes; articulation,
    # dynamics, expression, sections, player counts and enhancer data survive.
    return renderer(events, musical_plan=plan, genre_profile=genre_profile, creation_seed=creation_seed)
