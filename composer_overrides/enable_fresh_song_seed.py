"""Enable a genuinely new song by default in the preserved Composer.

The original GenreExecutionAdapter.create_new used len(history) as its seed.
A new runtime with empty/missing history therefore regenerated seed zero.  This
tiny source patch changes only the *default* start seed to OS cryptographic
entropy. The existing score-fingerprint exclusion + bounded retry still apply.

Explicit seed replay via .resolve(..., creation_seed=N) remains possible for
a controlled comparison, but neither ordinary use nor an ordinary test run
will replay seed zero by accident. This installer does NOT edit runtime.b64.
"""
from __future__ import annotations
import argparse
from pathlib import Path

OLD = "if start_seed is None: start_seed = len(prior)"
NEW = """if start_seed is None:
            import secrets
            start_seed = secrets.randbits(63)"""

def patch_source(source: str) -> str:
    if OLD not in source:
        if NEW in source:
            raise ValueError("FRESH_SONG_SEED_PATCH_ALREADY_INSTALLED")
        raise ValueError("ORIGINAL_CREATE_NEW_SEED_LINE_NOT_FOUND")
    if source.count(OLD) != 1:
        raise ValueError("AMBIGUOUS_ORIGINAL_COMPOSER_SEED_LOCATION")
    result=source.replace(OLD,NEW)
    if result.count(NEW)!=1:
        raise ValueError("FRESH_SONG_SEED_PATCH_INSTALL_FAILED")
    return result

def install(adapter: str | Path) -> None:
    path=Path(adapter)
    source=path.read_text(encoding="utf-8")
    updated=patch_source(source)
    path.write_text(updated,encoding="utf-8")
    print("FRESH_COMPOSITION_SEED_DEFAULT_INSTALLED",str(path))

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--adapter",required=True)
    args=p.parse_args()
    install(args.adapter)

if __name__=="__main__":
    main()
