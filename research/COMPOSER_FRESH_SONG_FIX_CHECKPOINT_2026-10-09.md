# Composer — Always Fresh Song Default (October 9, 2026)
**Status:** Implemented and validated on an isolated development branch. Not deployed.

## Cause verified from original archived Composer
The original `GenreExecutionAdapter.create_new(...)` starts with `start_seed = len(prior)` when no explicit seed is given. When the composition history is empty or unavailable, a fresh request can start again from seed zero. The original `AICompositionEngine.run` calls `create_new` without supplying any seed, and the Control Panel sends new request IDs but not a creation seed.

## Small repair
`composer_overrides/enable_fresh_song_seed.py` patches **only** the original default seed selection as the original Composer runtime is assembled by `build_current_composer.sh`: replace the implicit history count with `secrets.randbits(63)`. Keep all existing fingerprint-based duplicate rejection, creation logic, genre theory, track assignments, instrument libraries, output chain, and protected original `runtime.b64` unchanged.

The default applies to both `normal` and `quick` (test) modes. Explicit `.resolve(..., creation_seed=N)` continues to permit intentional deterministic comparisons, but ordinary new requests never select a fixed test seed by default.

## Evidence
Successful GitHub Actions workflow run: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/38023577988

- Rock **normal mode**: 3 out of 3 distinct score hashes, even with a *new empty history file* for each request.
- Rock **quick/test mode**: 3 out of 3 distinct score hashes, also with empty histories.
- Same-session successive normal requests without saved history: distinct scores.
- Explicitly pinned `creation_seed=0` gives identical scores only when deliberately requested.
- These are real original Composer generated scores, **not completed SFZ instrument audio renders**. Quality of melody/arrangement is a separate open issue.

**Live production Composer not changed**, no Plug or Control Panel updates, and no 3D mixer/genre interpreter changes. The saved optional-last-3D layout is retained in the parent branch. Before claiming the app itself is fixed, the repaired Composer build must be validated in full and deployed in the authorized release path.
