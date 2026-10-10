# AI Composer — Agreed Working Signal Path

**Status:** User-approved working layout. Documentation only; not a claim of live deployment or full audio verification.

```text
AI COMPOSER
  Genre Selection
  Musical Theory
  Musical Structure / Blueprint
  Instrument Library and Track Assignments
  Composition Generation
        |
        v
MIDI
        |
        v
INDIVIDUAL GENRE INTERPRETER
  (genre-specific musical behavior; no shared genre interpreter)
        |
        v
ORIGINAL INSTRUMENT RENDERER
        |
        v
STANDARD AUDIO MIX
  (must produce complete playable music without 3D)
        |
        v
OPTIONAL 3D MIXER
  (if used, strictly the last audio-processing component)
        |
        v
FINISHED MUSIC
```

## Preserve these rules
- Keep all original Composer functions: genre selection, theory, structure, instrument library, track assignments, composition, MIDI execution package.
- MIDI proceeds into the selected genre's own interpreter, never a shared genre interpreter.
- Keep original recorded sound sources and independent instrument parts.
- Standard stereo audio must work independently; the 3D mixer is optional and inactive by default.
- Any optional 3D processing, if ever enabled, is the final processing step before finished music.
- Do not modify protected hard copies, the live deployment, or upstream components simply to enable 3D.
- The present historical standalone 3D module consumes stems; a future post-mix input/output interface is not yet verified. This is an approved *layout*, not a claim that optional 3D processing is wired up.

**Development state:** Direct-stereo output passed an isolated WAV-format test, not yet a complete live audio end-to-end demonstration. No optional 3D activation has been made.
