"""Run isolated Classical recognition -> interpreter -> execution contract test.

Usage from repository root:
  python composer_overrides/run_classical_trial.py

This is not a live composer/audio integration test.
"""
import json
from pathlib import Path
from genre_pipeline import recognize_genre, execute_genre, GenrePipelineError

ROOT = Path(__file__).resolve().parent / "genre_styles"
genre = recognize_genre("Classical", ROOT)
assert genre.profile_id == "CLASSICAL_COMMON_PRACTICE_TONAL_CHAMBER_V2"
assert set(genre.source_profile["original_composer_instrument_palette"]) == {"violin","flute","clarinet","double_bass"}

def simulated_interpreter(definition, source_profile):
    """Contract stub; must be replaced by existing runtime interpreter after inspection."""
    return {"musical_plan": {
        "tempo": definition["tempo_bpm_range"][0],
        "meter": definition["meter_options"][0],
        "sections": ["A","B","A"],
        "instrument_roles": {"violin":"melody","flute":"countermelody","clarinet":"inner_voice","double_bass":"bass"}
    }}

def simulated_composer(plan, *, creation_seed):
    """Contract stub; does not produce notes or audio."""
    return {"seed": creation_seed, "plan": plan}

result = execute_genre(genre, simulated_interpreter, simulated_composer, creation_seed=1011)
assert result["plan"]["instrument_roles"]["violin"] == "melody"
assert len(result["plan"]["instrument_roles"]) == 4
for blocked in ("Swing","ROCK","WALTZ"):
    try:
        recognize_genre(blocked,ROOT)
    except GenrePipelineError:
        continue
    raise AssertionError(f"Non-Classical trial incorrectly enabled: {blocked}")
print(json.dumps({"status":"PASS_CONTRACT_ONLY","genre":genre.name,"profile_id":genre.profile_id,"instrument_roles":result["plan"]["instrument_roles"],"runtime_connected":False,"midi_tested":False,"audio_tested":False},indent=2))
