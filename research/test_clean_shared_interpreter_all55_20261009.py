"""Verify all 55 genres use exactly one structurally identical interpreter route.

The shared router MUST NOT invoke Rock-only sound or MIDI compilers, and
archived experiments must not be copied into the live genre package.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.shared_interpreter_router import connect_all_genres,route_to_shared_interpreter
routes=connect_all_genres()
assert len(routes)==55
schema={name:tuple(sorted(payload)) for name,payload in routes.items()}
assert len(set(schema.values()))==1,"SHARED_SCHEMA_NOT_UNIFORM"
r=routes["ROCK"]
j=routes["Jazz Ballad"]
assert r["stage_3_to_4"]==j["stage_3_to_4"]=="MUSICAL_INTERPRETER_AND_SOURCE_SPECIFIC_BRIDGE"
assert r["arranger_backend_state"]==j["arranger_backend_state"]=="MUSICAL_EVENT_GENERATOR_NOT_ENABLED_OR_VERIFIED"
assert r["musical_notes_authorized"] is j["musical_notes_authorized"] is False
assert r["live_genre_enabled"] is j["live_genre_enabled"] is False
source=(ROOT/"composer_overrides"/"genre_styles"/"shared_interpreter_router.py").read_text()
assert "def compile_selected_musical_interpreter(" not in source
assert "rock_pinned_mma_interpreter" not in source
assert "from .Rock." not in source
for name in ("rock_pinned_mma_interpreter.py","rock_strum_phrase_performance.py","ROCK_ARRANGER_INTERPRETER_PLACEMENT_R1.json"):
    assert not (ROOT/"composer_overrides"/"genre_styles"/"Rock"/name).exists(),name
    assert (ROOT/"research"/"archived_rock_20261009"/"original"/name).is_file(),name
assert (ROOT/"research"/"archived_rock_20261009"/"original"/"research"/"test_pinned_mma_shared_interpreter_execution_20261009.py").is_file()
assert set(routes)==set(schema)
print("ALL_55_SAME_SHARED_INTERPRETER_CONNECTION_PASS",len(routes),"ROCK_HAS_NO_LOCAL_COMPILER","OLD_RESEARCH_PRESERVED")
