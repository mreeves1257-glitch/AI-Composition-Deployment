"""Opt-in resource recognition for approved SF2 substitute; never claims rendered audio."""
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parent
EXPECTED='c5378b62028c920cb11e4803327983fee2f2cdff5dc89c708e39da417e51c854'

def preflight_substitute(engine_result, root=ROOT):
    sf=Path(root)/'replacement_instruments'/'TimGM6mb.sf2'
    if not sf.is_file():
        return {'status':'AUDIO_RENDER_RESOURCE_REQUIRED','reason':'APPROVED_SOUNDFONT_MISSING','audio_rendered':False}
    digest=hashlib.sha256(sf.read_bytes()).hexdigest()
    if digest != EXPECTED:
        return {'status':'AUDIO_RENDER_RESOURCE_REQUIRED','reason':'APPROVED_SOUNDFONT_HASH_MISMATCH','audio_rendered':False}
    mapping=json.loads((Path(root)/'replacement_instruments'/'REPLACEMENT_MAPPING_WORKING.json').read_text())
    if not {'KARORYFER_SHINYGUITAR','KARORYFER_BIG_RUSTY_DRUMS'} <= set(mapping.get('replaces',{})):
        return {'status':'AUDIO_RENDER_RESOURCE_REQUIRED','reason':'SUBSTITUTE_MAPPING_INCOMPLETE','audio_rendered':False}
    return {'status':'SUBSTITUTE_RESOURCE_RECOGNIZED','audio_rendered':False,'resource':str(sf),'sha256':digest,'scope':'RESOURCE_RECOGNITION_ONLY','next_stage':'SUBSTITUTE_AUDIO_HANDOFF_REQUIRED'}