"""Opt-in, genre-neutral interpreter arrangement handoff.

Does not select instruments, set an ensemble size, synthesize audio, or
modify any of the 55 genre profiles. Requires an explicit interpreter plan.
"""
from dataclasses import dataclass

class ArrangementHandoffError(ValueError):
    pass

@dataclass(frozen=True)
class ValidatedArrangement:
    genre: str
    instrument_roles: tuple
    musical_plan: dict

def validate_interpreter_arrangement(genre, musical_plan, available_instruments):
    if not isinstance(genre, str) or not genre.strip():
        raise ArrangementHandoffError("GENRE_REQUIRED")
    if not isinstance(musical_plan, dict):
        raise ArrangementHandoffError("INTERPRETER_PLAN_REQUIRED")
    roles = musical_plan.get("instrument_roles")
    if not isinstance(roles, (list, tuple)) or not roles:
        raise ArrangementHandoffError("INTERPRETER_INSTRUMENT_ROLES_REQUIRED")
    verified = set(available_instruments)
    normalized = []
    seen = set()
    for part in roles:
        if not isinstance(part, dict):
            raise ArrangementHandoffError("INSTRUMENT_ROLE_MUST_BE_OBJECT")
        part_id, instrument, role = part.get("part_id"), part.get("instrument_id"), part.get("role")
        if not all(isinstance(x, str) and x.strip() for x in (part_id, instrument, role)):
            raise ArrangementHandoffError("PART_ID_INSTRUMENT_AND_ROLE_REQUIRED")
        if part_id in seen:
            raise ArrangementHandoffError("DUPLICATE_PART_ID")
        if instrument not in verified:
            raise ArrangementHandoffError("UNAVAILABLE_INSTRUMENT: " + instrument)
        seen.add(part_id)
        normalized.append(dict(part))
    # Multiple parts may use the same instrument (e.g., divided strings).
    return ValidatedArrangement(genre, tuple(normalized), dict(musical_plan))

def handoff_interpreter_arrangement(genre, musical_plan, available_instruments, composer, *, creation_seed):
    validated = validate_interpreter_arrangement(genre, musical_plan, available_instruments)
    if not callable(composer):
        raise ArrangementHandoffError("COMPOSER_REQUIRED")
    return composer(validated.musical_plan, creation_seed=creation_seed)
