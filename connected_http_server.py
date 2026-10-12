"""HTTP delivery adapter for the saved October 11 composer; no musical edits."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import hashlib, json, os, re, subprocess, sys, threading, time, uuid, wave

HERE = Path(__file__).resolve().parent
COMPOSER = HERE if (HERE/'engine.py').is_file() else HERE/'composer'/'runtime'
ROOT = COMPOSER.parent.parent
native = str(COMPOSER/'runtime_linux'/'lib')
if os.environ.get('AI_COMP_NATIVE_BOOTSTRAPPED') != native:
    os.environ['AI_COMP_NATIVE_BOOTSTRAPPED'] = native
    os.environ['LD_LIBRARY_PATH'] = native + (':' + os.environ['LD_LIBRARY_PATH'] if os.environ.get('LD_LIBRARY_PATH') else '')
    os.environ['AI_COMP_FLUIDSYNTH_LIBRARY'] = native + '/libfluidsynth.so.3'
    os.execv(sys.executable, [sys.executable, *sys.argv])
OUTPUT = ROOT / 'connected_outputs'
LOCK = threading.Lock()
GENRES = json.loads((COMPOSER / 'AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json').read_text())['profiles']

def worker(genre, destination, mode, tuning_reference_hz="440"):
    sys.path.insert(0, str(COMPOSER))
    from musical_tuning import validate_reference
    tuning_reference_hz=validate_reference(float(tuning_reference_hz))
    from engine import AICompositionEngine
    import output_handoff
    output_handoff.OUT = Path(destination)
    result = AICompositionEngine(history_path=OUTPUT/'composition_history.json').run(
        genre, mode=mode, analyze_audio=False,tuning_reference_hz=tuning_reference_hz)
    result.pop('modules', None)
    result['analysis'] = {'status':'AVAILABLE_OFFLINE', 'reason':'Advisory analysis is separate from the memory-bounded HTTP audio delivery worker.'}
    Path(destination, 'result.json').write_text(json.dumps(result))
    return 0 if result.get('audio_rendered') else 2

class Handler(BaseHTTPRequestHandler):
    def send_headers(self, code, mime, size):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(size))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, HEAD, OPTIONS')
        self.send_header('Cache-Control', 'no-store')

    def json(self, code, value):
        data = json.dumps(value).encode()
        self.send_headers(code, 'application/json', len(data)); self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_headers(204, 'text/plain', 0); self.end_headers()

    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/health':
            return self.json(200, {'status':'BRIDGE_READY', 'audio_ready':True,
                'resource_ready':True, 'genre_count':len(GENRES),
                'deployment':'OCT12_TUNING_REPAIR', 'supported_tuning_references_hz':[440,432], 'verification':'All genre resource preflights checked at build; each returned WAV verified separately.'})
        match = re.fullmatch(r'/audio/([a-f0-9]{32})/finished.wav', path)
        if not match: return self.json(404, {'status':'NOT_FOUND'})
        file = OUTPUT/match.group(1)/'finished.wav'
        if not file.is_file(): return self.json(404, {'status':'AUDIO_NOT_FOUND'})
        size = file.stat().st_size; start = 0; end = size-1; code = 200
        requested = self.headers.get('Range')
        if requested:
            m = re.fullmatch(r'bytes=(\d*)-(\d*)', requested.strip())
            if not m or not any(m.groups()): return self.json(416, {'status':'INVALID_RANGE'})
            a,b = m.groups()
            if a: start = int(a); end = min(int(b),end) if b else end
            else:
                if int(b)<=0: return self.json(416, {'status':'INVALID_RANGE'})
                start = max(0,size-int(b))
            if start>end or start>=size: return self.json(416, {'status':'INVALID_RANGE'})
            code = 206
        self.send_response(code)
        self.send_header('Content-Type','audio/wav')
        self.send_header('Content-Length',str(end-start+1))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','no-store')
        if code==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        if self.command=='HEAD': return
        try:
            with file.open('rb') as source:
                source.seek(start); remaining=end-start+1
                while remaining:
                    block=source.read(min(65536,remaining))
                    if not block: break
                    self.wfile.write(block); remaining-=len(block)
        except (BrokenPipeError,ConnectionResetError): pass

    def do_POST(self):
        if urlsplit(self.path).path != '/compose': return self.json(404, {'status':'NOT_FOUND'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=65536: raise ValueError('INVALID_REQUEST_SIZE')
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict): raise ValueError('INPUT_PAYLOAD_MUST_BE_OBJECT')
            genre=payload.get('genre'); mode=payload.get('mode','normal')
            if genre not in GENRES: raise ValueError('UNKNOWN_GENRE')
            if mode not in ('normal','quick'): raise ValueError('INPUT_MODE_INVALID')
            if payload.get('target','INTERNAL')!='INTERNAL': raise ValueError('INTERNAL_TARGET_REQUIRED')
            from musical_tuning import validate_reference
            tuning=validate_reference(payload.get('tuning_reference_hz',440))
            if not LOCK.acquire(timeout=10): return self.json(503, {'status':'COMPOSER_BUSY','reason':'Another composition is rendering; retry when it finishes.'})
            try:
                job=uuid.uuid4().hex; destination=OUTPUT/job; destination.mkdir(parents=True)
                p=subprocess.run([sys.executable,__file__,'--worker',genre,str(destination),mode,str(tuning)],
                    capture_output=True,text=True,timeout=350)
                (destination/'worker.log').write_text(p.stdout+'\n'+p.stderr)
                report_file=destination/'result.json'
                if not report_file.is_file(): raise RuntimeError('COMPOSER_WORKER_FAILED: '+p.stderr[-1200:])
                result=json.loads(report_file.read_text())
                if p.returncode or not result.get('audio_rendered'):
                    return self.json(409, result)
                audio=result['audio_render']; source=Path(audio['wav_path']).resolve()
                source.relative_to(destination.resolve())
                import shutil
                final=destination/'finished.wav'; shutil.copyfile(source,final)
                with wave.open(str(final),'rb') as wav:
                    frames=wav.getnframes(); rate=wav.getframerate()
                    if not frames or len(wav.readframes(frames))!=frames*wav.getnchannels()*wav.getsampwidth(): raise ValueError('INCOMPLETE_FINISHED_AUDIO')
                result['audio_url']=f'/audio/{job}/finished.wav'
                result['audio_sha256']=hashlib.sha256(final.read_bytes()).hexdigest()
                result['duration_seconds']=frames/rate
                result['genre']=genre; result['delivery_status']='VERIFIED_FINISHED_WAV'
                print('CONNECTED_AUDIO_PASS',genre,job,frames/rate,flush=True)
                self.json(200,result)
                # Completed master remains available; working stems and duplicate masters
                # are temporary delivery material, preventing unbounded disk growth.
                for child in destination.iterdir():
                    if child.is_dir(): shutil.rmtree(child)
                completed=sorted(OUTPUT.glob('*/finished.wav'),key=lambda x:x.stat().st_mtime)
                for old in completed[:-8]: shutil.rmtree(old.parent)
            finally: LOCK.release()
        except Exception as exc:
            print('CONNECTED_AUDIO_ERROR',type(exc).__name__,str(exc),flush=True)
            self.json(503,{'status':'AUDIO_RENDER_FAILED','reason':str(exc),'audio_rendered':False})

    def log_message(self,*args): pass

if __name__=='__main__':
    OUTPUT.mkdir(exist_ok=True)
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        raise SystemExit(worker(*sys.argv[2:]))
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','10000'))),Handler).serve_forever()
