# AI Composer — Performance Language Research Checkpoint
Date: 2026-10-08 America/Chicago
Branch: performance-language-research-20261008
Status: NOT CONNECTED / RESEARCH ONLY

This branch is reserved for adding instrument-aware performance interpretation safely and does not change the deployed Composer, plug, control panel, genre-family routes, recorded sample libraries, or standalone 3D mixer.

Existing relevant implementation:
- composer_overrides/instrument_performance_contract.py: Rock guitar phrase-duration rules.
- composer_overrides/phrase_expression_decisions.py and automatic_phrase_handoff.py: phrase-end vibrato is experimental and OFF in ordinary production.
- composer_overrides/musical_gesture_author.py, expressive_gesture_bridge.py, performance_capabilities.json: real recorded Shinyguitar lead CC1 vibrato response verified for an exact mono SFZ program; full human-like music NOT verified.
- genre_styles/README.md: 13 genre families / 55 reserved genres; none approved as fully working.

The missing component is a layer separating (A) MUSICAL INTENT such as sustain, connection, natural phrase release, articulations, dynamics, and (B) ACTUAL CAPABILITY of the exact selected recorded instrument. Never emit controls for articulations whose recorded sample or SFZ program does not support them. Original recordings and historical files must be preserved.

A dated standalone research package, ai-composer-performance-language-2026-10-08.zip, was constructed and tested outside deployment in the October 8, 2026 ChatGPT session. It contains a 16-intent vocabulary, evidence-audited sample program inventory, a read-only preliminary interpreter and its independent Python safety tests. That ZIP is a separate conversation artifact; its code is NOT deployed or included in this branch checkpoint.

Technical references:
Yamaha https://usa.yamaha.com/files/download/other_assets/4/2318564/Genos2_owners_manual_En_D0.pdf
Korg https://www.korg.com/us/products/synthesizers/pa5x/index.php
MIDI https://midi.org/midi-ci-profile-for-note-on-selection-of-orchestral-articulation
SFZ https://sfzformat.com/opcodes/trigger/
SFZ https://sfzformat.com/opcodes/seq_position/

Next: audit the exact Shinyguitar lead and rhythm programs and Growlybass SFZ mappings for sample length, one-shot/looping, note release, controller semantics, and available articulation alternates. Do not assume lengthening a MIDI event can sustain a one-shot sample. Only after source-level and audible verification should additional mappings be added to the active capability manifest. No genre-stage linking or control-panel revisions yet.
