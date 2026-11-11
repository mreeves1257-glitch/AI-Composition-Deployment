"""Classical-only audio verification for the EXISTING packaged composer.

Run from repo root after build_connected_composer.sh has extracted composer/runtime:
    python composer_overrides/verify_classical_audio.py

Does not change engine.py, control panel, or any other genre.
"""
from pathlib import Path
import hashlib, json, sys, tempfile, wave

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "composer" / "runtime"
if not (RUNTIME / "engine.py").is_file():
    raise SystemExit("NOT_RUN: composer/runtime/engine.py is not extracted; no claims about audio.")
sys.path.insert(0, str(RUNTIME))
from engine import AICompositionEngine
import output_handoff

def verify_wav(path):
    path = Path(path)
    if not path.is_file():
        raise AssertionError("Missing rendered WAV: " + str(path))
    with wave.open(str(path), "rb") as wav:
        channels, rate, frames = wav.getnchannels(), wav.getframerate(), wav.getnframes()
        pcm = wav.readframes(frames)
    assert channels == 2 and frames > 0 and any(pcm), "Silent or empty WAV"
    return {"path":str(path), "channels":channels, "sample_rate":rate,
            "frames":frames, "pcm_sha256":hashlib.sha256(pcm).hexdigest()}

with tempfile.TemporaryDirectory(prefix="classical_audio_trial_") as tmp:
    tmp = Path(tmp)
    output_handoff.OUT = tmp / "output"
    engine = AICompositionEngine(history_path=tmp / "composition_history.json")
    results = []
    for run in range(3):
        result = engine.run("Classical", mode="quick", analyze_audio=False)
        assert result.get("audio_rendered"), "Classical audio rendering failed: " + repr(result.get("reason"))
        audio = result.get("audio_render") or {}
        assert audio.get("wav_path"), "Audio result did not contain wav_path"
        results.append({"run":run+1, "audio":verify_wav(audio["wav_path"]),
                        "composition_fingerprint":result.get("composition_fingerprint")})
    hashes = [r["audio"]["pcm_sha256"] for r in results]
    assert len(set(hashes)) == len(hashes), "Duplicate PCM outputs; Classical variation test failed"
    print(json.dumps({"status":"PASS_BASIC_CLASSICAL_AUDIO","runs":results,
      "limits":"Distinct audio hashes do not prove orchestration, genre accuracy, or perceptual originality; stem and listening checks remain required."},indent=2))
