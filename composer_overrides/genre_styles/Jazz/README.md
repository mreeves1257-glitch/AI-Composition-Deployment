# Jazz — one shared instrument library, Jazz Ballad first

This folder is the parent of the Jazz family. It contains one shared catalog
of recorded instruments, but **only Jazz Ballad is in development now**.
The other seven style files and role manifests are deliberately empty placeholders.
Do not populate them, copy Jazz Ballad into them, or treat them as operational
arrangements until the finished Ballad has been approved as a reusable template.

## File structure

- `instrument_library.json`: canonical existing Jazz sample references. The WAV/SFZ
  audio files remain in the shared `sound_resources` bank; there are no copies here.
- `harmony.py`: bounded common Jazz harmonic mechanics. A placeholder style is
  not activated by this shared helper.
- `jazz_ballad.py`: **the only active new Jazz framework**; owns its composition,
  progression, ensemble arrangement, and instrument role decisions.
- `instrument_packages/jazz_ballad.json`: working Ballad roles referencing the
  verified sources in `instrument_library.json`. Its Wurlitzer piano stays
  unchanged. The double bass, clarinet, kick, brush snare and hat use existing
  recorded samples.
- `swing.py`, `big_band.py`, `jazz_waltz.py`, `bebop.py`,
  `cool_jazz.py`, `dixieland.py`, `jazz_fusion.py`: reserved names only,
  with `DEVELOPMENT_STATUS = "NOT_STARTED"`, no chord progressions,
  no arrangement algorithms and no instrument assignments. Their manifests
  under `instrument_packages/` have empty `roles` objects.

## Sequence

1. **Finish Jazz Ballad completely:** hear all instruments, develop the melody
   and chords, balance the ensemble, remove distracting brush noise/static,
   and confirm stable playable final audio.
2. Keep that verified implementation as the reference template.
3. Only then create the other Jazz subgenres individually by copying that
   proven structure and changing *their own* music rules and instrument
   selections. Sharing samples does not mean all styles must sound the same.

## Shared infrastructure and other genres

`genre_styles/registry.py` routes named styles while preventing undeveloped
Jazz placeholder modules from being loaded as finished arrangements.
The Composer, control panel, plug, sample renderer and standalone 3D mixer
are shared utilities, not music genre folders.

**Rock stays independent** under `genre_styles/rock.py`; its working audio,
instrument mix, tempo and performance controls are not modified by Jazz work.
Other multistyle genres can later use similar family folders when needed.

## Preserve earlier work

Older file versions remain in Git history; the hardcopy references include
`protected-composer-before-jazz-audibility-2026-10-08` and
`jazz-pre-consolidation-hardcopy-20261008`.
Do not overwrite the protected history or claim that resource links alone
prove a finished audible Jazz performance.
