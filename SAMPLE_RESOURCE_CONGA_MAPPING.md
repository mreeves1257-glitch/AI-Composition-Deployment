# FreePats recorded conga sound-bank mapping

- Source repository: https://github.com/freepats/world-percussion
- Recording source: Versilian Community Sample Library (VCSL), CC0, curated into the FreePats World Percussion bank
- Recorded instrument class: actual conga percussion samples, **not synthesized imitations**
- Bank license: CC0 1.0 Universal (https://creativecommons.org/publicdomain/zero/1.0/)
- Original instrument remains unchanged. The build derives `composer-conga-five-strokes.sfz`, pointing to original samples.
- FreePats source MIDI **62 standard** -> genre MIDI **60**; **64 high** -> **61**; **63 low** -> **62**; **65 muted** -> **63**; **66 muted low** -> **64**.
- This explicit mapping matches the legacy genre generator which emits MIDI 60, 61, 62 for conga. Five distinct sampled strokes remain accessible at notes 60..64.
- Verify 38 real source sample references, 38 resolved files, and 5 non-silent 44,100 Hz output notes before Render deploys.
- Do not use FreePats' README high/low ordering as authoritative; the SFZ's actual sample-folder labels identify high vs. low congas.
- Other world percussion notes in the upstream SFZ are not automatically approved as genre instruments.
