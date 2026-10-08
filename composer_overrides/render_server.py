"""Composer HTTP entrypoint: unchanged compose POST plus read-only Jazz preview.

Only two explicitly designated, generated preview WAV files can be served.
No arbitrary files, instrument bank data, control-panel or mixer APIs exposed.
"""
from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import re
import html
import os
import shutil

from input_gateway import Handler

HERE = Path(__file__).resolve().parent
PREVIEWS = {
    "/jazz-ballad-expressive.wav": (
        "jazz-ballad-eight-bars-generated-piano.wav"),
    "/jazz-ballad-flat.wav": (
        "jazz-ballad-eight-bars-flat-dynamics.wav"),
}
PREVIEW_DIR = HERE / "output" / "jazz_recorded_chord_probe"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jazz Ballad — Eight-Bar Listening Comparison</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:640px;
margin:36px auto;padding:0 20px;line-height:1.55;
color:#18242a;background:#f7f8f6}
section{background:#fff;border:1px solid #dbe2df;border-radius:12px;
padding:18px 22px;margin:18px 0}
audio{display:block;width:100%;margin:12px 0}
h1{font-size:1.6rem}h2{font-size:1.12rem}
small{color:#475d62}a{color:#125774}
</style></head><body>
<h1>Jazz Ballad: Listen to the Human Element</h1>
<p>One eight-bar phrase, composed by the AI Composer and played through
real recorded Wurlitzer EP200 piano samples. Both versions use the
same notes and rhythms. Only their note intensity differs.</p>
<section><h2>A — Expressive phrase</h2>
<p>The Composer's existing Jazz phrase dynamics are preserved.</p>
<audio controls preload="metadata" src="/jazz-ballad-expressive.wav"></audio>
<a href="/jazz-ballad-expressive.wav">Open audio A directly</a></section>
<section><h2>B — Constant-intensity comparison</h2>
<p>A listening control using the very same notes, timing and instrument
recordings, with identical MIDI velocity on every note.</p>
<audio controls preload="metadata" src="/jazz-ballad-flat.wav"></audio>
<a href="/jazz-ballad-flat.wav">Open audio B directly</a></section>
<p><strong>Listen for:</strong> changing emphasis between chord attacks,
a sense of phrase shape, natural breathing room, and whether the music
feels less mechanical in A.</p>
<small>These are piano-only diagnostics, not completed Jazz ensemble
recordings or the 3D-mixed final master.</small>
<p><small>Recorded piano samples: Greg Sullivan, Wurlitzer EP200,
CC BY 3.0. <a href="https://github.com/sfzinstruments/GregSullivan.E-Pianos">
Sample source and attribution</a>.</small></p>
</body></html>""".encode("utf-8")


class ComposerWithJazzPreview(Handler):
    """Preserve original POST /compose and OPTIONS; add GET preview only."""

    def do_GET(self):
        self._serve_preview(send_body=True)

    def do_HEAD(self):
        self._serve_preview(send_body=False)

    def _serve_preview(self, send_body: bool):
        path = urlsplit(self.path).path
        if path.startswith("/audio/"):
            return self._serve_finished_audio(path, send_body)
        if path == "/jazz-ballad-listen":
            content = PAGE
            mime = "text/html; charset=utf-8"
            file_path = None
        elif path in PREVIEWS:
            file_path = PREVIEW_DIR / PREVIEWS[path]
            if not file_path.is_file():
                return self._reply(503, b"Preview unavailable until audio validation completes.",
                                   "text/plain; charset=utf-8", send_body)
            content = None
            mime = "audio/wav"
        else:
            return self._reply(404, b"Not found.", "text/plain; charset=utf-8", send_body)

        if file_path is None:
            return self._reply(200, content, mime, send_body)
        try:
            with file_path.open("rb") as stream:
                size = file_path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                if send_body:
                    shutil.copyfileobj(stream, self.wfile)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_finished_audio(self, path: str, send_body: bool):
        """Serve only the finished stereo derivative made by the separate 3D mixer.

        Composer emits /audio/final_audio/composition_.../stereo_derivative.wav.
        Do not expose private stems, instrument banks, or filesystem paths.
        The output root comes from the SAME output_handoff.OUT used to render.
        """
        match = re.fullmatch(
            r"/audio/final_audio/(composition_[A-Za-z0-9_-]+)/stereo_derivative\\.wav",
            path,
        )
        if match is None:
            return self._reply(404, b"Unknown audio file.", "text/plain; charset=utf-8", send_body)
        from output_handoff import OUT
        target = (OUT / "final_audio" / match.group(1) / "stereo_derivative.wav").resolve()
        root = (OUT / "final_audio").resolve()
        if root not in target.parents or not target.is_file():
            return self._reply(404, b"Final audio not found.", "text/plain; charset=utf-8", send_body)

        try:
            size = target.stat().st_size
            if size < 44:
                return self._reply(503, b"Final audio incomplete.", "text/plain; charset=utf-8", send_body)
            start, end, status = 0, size - 1, 200
            range_header = self.headers.get("Range", "")
            if range_header:
                requested = re.fullmatch(r"bytes=(\\d*)-(\\d*)", range_header.strip())
                if requested is None or not any(requested.groups()):
                    return self._audio_range_error(size, send_body)
                first, last = requested.groups()
                if first:
                    start = int(first)
                    end = min(int(last), end) if last else end
                else:
                    suffix = int(last)
                    if suffix <= 0:
                        return self._audio_range_error(size, send_body)
                    start = max(0, size - suffix)
                if start >= size or end < start:
                    return self._audio_range_error(size, send_body)
                status = 206

            self.send_response(status)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if send_body:
                with target.open("rb") as source:
                    source.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        packet = source.read(min(256 * 1024, remaining))
                        if not packet:
                            break
                        self.wfile.write(packet)
                        remaining -= len(packet)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _audio_range_error(self, size: int, send_body: bool):
        self.send_response(416)
        self.send_header("Content-Range", f"bytes */{size}")
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _reply(self, status, body, mime, send_body):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if send_body:
            self.wfile.write(body)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "10000"))
    print(f"CURRENT_COMPOSER_START host={host} port={port}", flush=True)
    ThreadingHTTPServer((host, port), ComposerWithJazzPreview).serve_forever()
