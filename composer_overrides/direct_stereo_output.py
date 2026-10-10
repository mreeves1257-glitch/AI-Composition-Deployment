"""Direct finished stereo from real instrument stems — NO 3D mixer.

A transparent playback/file-output stage.  It reads the original renderer's
individual WAV stems, applies their already approved resource gains, sums
them into ordinary stereo and peak-scales once to prevent clipping.  It does
not compose, select instruments, spatialize, equalize or synthesize audio.

No source WAV, SFZ, note or instrument assignment is modified.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import wave

import numpy as np

CHUNK=65536
PEAK_TARGET=10.0**(-1.0/20.0)

def _sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def _decode(raw,width,channels):
    if width==1:
        pcm=(np.frombuffer(raw,dtype=np.uint8).astype(np.float64)-128.)/128.
    elif width==2:
        pcm=np.frombuffer(raw,dtype="<i2").astype(np.float64)/32768.
    elif width==4:
        pcm=np.frombuffer(raw,dtype="<i4").astype(np.float64)/2147483648.
    else:
        raise ValueError("UNSUPPORTED_REAL_RECORDED_WAV_FORMAT")
    if len(pcm)%channels:
        raise ValueError("INCOMPLETE_WAV_FRAME")
    pcm=pcm.reshape(-1,channels)
    # Preserve the native left and right channels from a stereo source.
    return np.repeat(pcm,2,axis=1) if channels==1 else pcm

def _mix_pass(entries,frames,peak_only,scale=1.0,output=None,sr=None):
    readers=[]
    writer=None
    maximum=0.0
    try:
        readers=[wave.open(str(e["path"]),"rb") for e in entries]
        if output is not None:
            writer=wave.open(str(output),"wb")
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(sr)
        for start in range(0,frames,CHUNK):
            n=min(CHUNK,frames-start)
            mix=np.zeros((n,2),dtype=np.float64)
            for e,r in zip(entries,readers):
                audio=_decode(r.readframes(n),e["width"],e["channels"])
                mix[:len(audio)]+=audio*e["gain"]
            if not np.all(np.isfinite(mix)):
                raise ValueError("NONFINITE_IN_RECORDED_STEM_MIX")
            if peak_only:
                if mix.size:
                    maximum=max(maximum,float(np.max(np.abs(mix))))
            else:
                pcm=np.clip(mix*scale,-1.0,1.0)
                writer.writeframes((pcm*32767.0).astype("<i2").tobytes())
    finally:
        for reader in readers:
            reader.close()
        if writer is not None:
            writer.close()
    return maximum

def finish_recorded_stems(engine_result,stems,output_root):
    if not stems:
        raise ValueError("NO_REAL_RECORDED_STEMS_TO_FINISH")
    target=engine_result["modules"]["target"]["resolved_resources"]
    source_map={str(x["track_id"]):x["resource"] for x in target}
    if len(source_map)!=len(target):
        raise ValueError("DUPLICATED_INSTRUMENT_TARGET_RESOURCE")

    entries=[]
    sample_rate=None
    max_frames=0
    source_hashes={}
    for stem in stems:
        track=str(stem["track_id"])
        if track not in source_map:
            raise ValueError("STEM_HAS_NO_APPROVED_INSTRUMENT_BINDING:"+track)
        if track in source_hashes:
            raise ValueError("DUPLICATED_RECORDED_STEM:"+track)
        path=Path(stem["wav_path"]).resolve()
        if not path.is_file():
            raise ValueError("REAL_STEM_WAV_MISSING:"+track)
        with wave.open(str(path),"rb") as f:
            channels,width,sr,frames=(f.getnchannels(),f.getsampwidth(),
                                      f.getframerate(),f.getnframes())
        if channels not in (1,2) or width not in (1,2,4):
            raise ValueError("STEM_WAV_FORMAT_UNSUPPORTED:"+track)
        if sample_rate is None:
            sample_rate=sr
        if sr!=sample_rate:
            raise ValueError("RECORDED_STEM_SAMPLE_RATE_MISMATCH")
        gain_db=float(source_map[track].get("target_gain_db",0.0))
        if not math.isfinite(gain_db):
            raise ValueError("INVALID_TARGET_GAIN:"+track)
        gain=10.0**(gain_db/20)
        entries.append({"track":track,"path":path,"channels":channels,
                        "width":width,"frames":frames,"gain":gain,
                        "target_gain_db":gain_db})
        max_frames=max(max_frames,frames)
        source_hashes[track]=_sha(path)
    if max_frames==0:
        raise ValueError("ALL_RECORDED_STEMS_EMPTY")
    root=Path(output_root).resolve()
    root.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(prefix="composition_",dir=root))
    output=folder/"stereo_derivative.wav"  # Preserve the existing phone/audio URL.
    peak=_mix_pass(entries,max_frames,peak_only=True)
    if not math.isfinite(peak) or peak<=0:
        raise ValueError("NO_AUDIBLE_AUDIO_IN_RECORDED_STEMS")
    scale=PEAK_TARGET/peak
    _mix_pass(entries,max_frames,peak_only=False,scale=scale,output=output,
              sr=sample_rate)
    manifest={
        "output_kind":"audible_final",
        "renderer_source":"EXISTING_RECORDED_SFZ_STEMS",
        "output_method":"DIRECT_STEREO_SUM_NO_3D",
        "has_3d_master":False,
        "spatial_effects_applied":False,
        "no_composition_or_instrument_changes":True,
        "sample_rate":sample_rate,
        "channels":2,
        "source_count":len(entries),
        "source_wav_sha256":source_hashes,
        "duration_seconds":max_frames/sample_rate,
        "peak_scale":scale,
        "wav_sha256":_sha(output)
    }
    (folder/"output_manifest.json").write_text(json.dumps(manifest,indent=2))
    return {
        "status":"AUDIO_RENDER_PASS",
        "audio_rendered":True,
        "source_audio_rendered":True,
        "stems":stems,
        "wav_path":str(output),
        "output_manifest_path":str(folder/"output_manifest.json"),
        "output_stage":"DIRECT_STEREO_SUM_NO_3D",
        "resource_quality":"REAL_SFZ_RESOURCES"
    }
