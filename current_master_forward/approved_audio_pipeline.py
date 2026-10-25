"""Explicit SoundFont instrument mapping -> preserved object mixer -> playable audio."""
from pathlib import Path
import copy, hashlib, importlib.util, json, shutil, sys, wave
import mido
from render_substitute_universal import render_track
from original_mixer_adapter import mix
from output_handoff import OUT
ROOT=Path(__file__).resolve().parent
PROGRAMS={'electric_bass_guitar':33,'electric_guitar':30,'electric_piano':4,'strings':48,'synth_pad':88,'concert_flute':73,'oboe':68,'bassoon':70,'double_bass':43,'clarinet_bb':71,'violin':40,'viola':41,'cello':42,'horn_f':60,'trumpet_c':56,'tenor_trombone':57,'bass_tuba':58,'timpani':47,'alto_sax':65,'tenor_sax':66,'baritone_sax':67,'synth_lead':80,'clav':7,'synth_bass':38,'acoustic_guitar':24,'marimba':12,'synth_chord':81,'noise_fx':122,'synth_pulse':80,'synth_arp':81,'piano':0,'choir':52}
DRUMS={'crash_cymbal','hi_hat','kick_drum_rock','snare_drum','tom_tom','ride_cymbal','conga_family','bongo_family','timbales','claves','cowbell','shaker','surdo','caixa','repinique','tamborim','agogo_bells','electronic_kick','electronic_hat','electronic_snare'}
EXPECTED_SF2='c5378b62028c920cb11e4803327983fee2f2cdff5dc89c708e39da417e51c854'

# Recovered 2026-10-17 Classical Divisimate 14-section listening reference.
# Section identity intentionally overrides generic instrument identity for Classical only.
CLASSICAL_GOLDEN_SECTION_PROGRAMS={
    'VIOLIN_I':48,'VIOLIN_II':49,'VIOLA':41,'CELLO':42,'DOUBLE_BASS':43,
    'FLUTE':73,'OBOE':68,'CLARINET':71,'BASSOON':70,'HORN':60,
    'TRUMPET':56,'TROMBONE':57,'TUBA':58,'TIMPANI':47,
}
CLASSICAL_GOLDEN_SECTION_CONTROLS={
    'VIOLIN_I':{'pan':38,'expression':92,'reverb':60},
    'VIOLIN_II':{'pan':48,'expression':86,'reverb':62},
    'VIOLA':{'pan':56,'expression':88,'reverb':58},
    'CELLO':{'pan':76,'expression':94,'reverb':56},
    'DOUBLE_BASS':{'pan':84,'expression':98,'reverb':50},
    'FLUTE':{'pan':50,'expression':67,'reverb':66},
    'OBOE':{'pan':58,'expression':76,'reverb':64},
    'CLARINET':{'pan':70,'expression':70,'reverb':64},
    'BASSOON':{'pan':78,'expression':88,'reverb':60},
    'HORN':{'pan':88,'expression':90,'reverb':62},
    'TRUMPET':{'pan':80,'expression':76,'reverb':58},
    'TROMBONE':{'pan':92,'expression':84,'reverb':56},
    'TUBA':{'pan':98,'expression':92,'reverb':52},
    'TIMPANI':{'pan':64,'expression':82,'reverb':54},
}


# User-approved 2026-10-19 Big Band golden listening recipe.
# Preserve the 17-player / 22-registration V3 arrangement while giving each
# chair/role a deterministic downstream sound, control and gain identity.
BIG_BAND_GOLDEN_PROGRAMS={
    'ALTO_SAX_1':65,'ALTO_SAX_2':65,'TENOR_SAX_1':66,'TENOR_SAX_2':66,
    'BARITONE_SAX':67,'TRUMPET_1':56,'TRUMPET_2':56,'TRUMPET_3':56,
    'TRUMPET_4':56,'TROMBONE_1':57,'TROMBONE_2':57,'TROMBONE_3':57,
    'TROMBONE_4':57,'PIANO':0,'GUITAR':26,'BASS':43,
}
BIG_BAND_GOLDEN_CONTROLS={
    'ALTO_SAX_1':{'pan':38,'expression':98,'reverb':44},
    'ALTO_SAX_2':{'pan':44,'expression':82,'reverb':40},
    'TENOR_SAX_1':{'pan':50,'expression':96,'reverb':44},
    'TENOR_SAX_2':{'pan':56,'expression':80,'reverb':40},
    'BARITONE_SAX':{'pan':62,'expression':84,'reverb':36},
    'TRUMPET_1':{'pan':82,'expression':100,'reverb':38},
    'TRUMPET_2':{'pan':86,'expression':84,'reverb':34},
    'TRUMPET_3':{'pan':90,'expression':78,'reverb':32},
    'TRUMPET_4':{'pan':94,'expression':74,'reverb':30},
    'TROMBONE_1':{'pan':70,'expression':84,'reverb':38},
    'TROMBONE_2':{'pan':74,'expression':78,'reverb':36},
    'TROMBONE_3':{'pan':78,'expression':74,'reverb':34},
    'TROMBONE_4':{'pan':82,'expression':72,'reverb':32},
    'PIANO':{'pan':58,'expression':76,'reverb':34},
    'GUITAR':{'pan':46,'expression':66,'reverb':28},
    'BASS':{'pan':64,'expression':92,'reverb':24},
    'RIDE':{'pan':70,'expression':70,'reverb':22},
    'HIHAT_FOOT':{'pan':74,'expression':62,'reverb':18},
    'KICK':{'pan':64,'expression':64,'reverb':18},
    'SNARE_COMP':{'pan':68,'expression':66,'reverb':20},
    'SNARE_SETUP':{'pan':68,'expression':70,'reverb':20},
    'CRASH':{'pan':72,'expression':66,'reverb':24},
}
BIG_BAND_GOLDEN_GAIN_DB={
    'ALTO_SAX_1':0.0,'ALTO_SAX_2':-3.5,'TENOR_SAX_1':-0.5,'TENOR_SAX_2':-3.5,
    'BARITONE_SAX':-4.0,'TRUMPET_1':0.0,'TRUMPET_2':-3.0,'TRUMPET_3':-4.0,
    'TRUMPET_4':-5.0,'TROMBONE_1':-3.0,'TROMBONE_2':-4.0,'TROMBONE_3':-5.0,
    'TROMBONE_4':-5.5,'PIANO':-5.0,'GUITAR':-8.0,'BASS':-1.0,'RIDE':-6.0,
    'HIHAT_FOOT':-10.0,'KICK':-8.0,'SNARE_COMP':-8.0,'SNARE_SETUP':-6.0,'CRASH':-7.0,
}
BIG_BAND_DRUM_ROLES={'RIDE','HIHAT_FOOT','KICK','SNARE_COMP','SNARE_SETUP','CRASH'}

def _normalized_track_key(track_name):
    return str(track_name or '').upper().replace(' ','_').replace('-','_')

def _big_band_role(track_name):
    role=_normalized_track_key(track_name)
    return role if role in BIG_BAND_GOLDEN_CONTROLS else None

def _apply_genre_initial_controls(mid, genre):
    if str(genre).strip().lower()!='big band':
        return mid
    out=copy.deepcopy(mid)
    for track in out.tracks:
        name=next((m.name for m in track if m.type=='track_name'),None)
        role=_big_band_role(name)
        if not role: continue
        c=BIG_BAND_GOLDEN_CONTROLS[role]
        rebuilt=[]; inserted=False
        for msg in track:
            if msg.type=='control_change' and msg.time==0 and msg.control in (10,11,91):
                continue
            rebuilt.append(msg)
            if not inserted and msg.type=='track_name':
                rebuilt.extend([
                    mido.Message('control_change',control=10,value=c['pan'],channel=0,time=0),
                    mido.Message('control_change',control=11,value=c['expression'],channel=0,time=0),
                    mido.Message('control_change',control=91,value=c['reverb'],channel=0,time=0),
                ])
                inserted=True
        if not inserted:
            rebuilt[:0]=[
                mido.Message('control_change',control=10,value=c['pan'],channel=0,time=0),
                mido.Message('control_change',control=11,value=c['expression'],channel=0,time=0),
                mido.Message('control_change',control=91,value=c['reverb'],channel=0,time=0),
            ]
        track[:] = rebuilt
    return out

def _classical_section_key(track_name):
    n=str(track_name or '').upper().replace(' ','_').replace('-','_')
    aliases={'FRENCH_HORN':'HORN','HORN_F':'HORN','TRUMPET_C':'TRUMPET',
             'TENOR_TROMBONE':'TROMBONE','BASS_TUBA':'TUBA','CLARINET_BB':'CLARINET'}
    return aliases.get(n,n)

def _resolved_program(genre, track_name, instrument_id):
    g=str(genre).strip().lower()
    if g in {'classical','orchestra','orchestral'}:
        section=_classical_section_key(track_name)
        if section in CLASSICAL_GOLDEN_SECTION_PROGRAMS:
            return CLASSICAL_GOLDEN_SECTION_PROGRAMS[section], section, None
    if g=='big band':
        role=_big_band_role(track_name)
        if role:
            return BIG_BAND_GOLDEN_PROGRAMS.get(role,PROGRAMS.get(instrument_id,0)), None, role
    return PROGRAMS.get(instrument_id,0), None, None


def render(result):
    tuning_reference_hz=result.get('tuning_reference_hz',440)
    sf=ROOT/'replacement_instruments/TimGM6mb.sf2'
    if hashlib.sha256(sf.read_bytes()).hexdigest()!=EXPECTED_SF2:raise ValueError('SOUNDFONT_HASH_MISMATCH')
    handoff=result['output_handoff'];out=Path(handoff['midi_path']).parent/'approved_audio';out.mkdir(exist_ok=True)
    mid=_apply_genre_initial_controls(mido.MidiFile(handoff['midi_path']),result.get('genre'))
    profiles={str(p['track_id']):p for p in result['modules']['instrument']['profiles']}
    expected={str(e['track_id']) for e in result['modules']['performance']['events']}
    stems=[]; mappings=[]; bindings=[]
    for index,track in enumerate(mid.tracks):
        name=next((m.name for m in track if m.type=='track_name'),None)
        if name not in expected:continue
        profile=profiles[name];iid=profile['instrument_id'];big_band_role=_big_band_role(name) if str(result.get('genre')).strip().lower()=='big band' else None;drum=iid in DRUMS or big_band_role in BIG_BAND_DRUM_ROLES
        if not drum and iid not in PROGRAMS:raise ValueError('NO_EXPLICIT_SOUNDFONT_MAPPING:'+iid)
        program,classical_section,big_band_role=_resolved_program(result.get('genre'),name,iid);wav=out/f'stem_{index:02d}.wav'
        recorded = iid == 'electric_bass_guitar'
        if recorded:
            spec=importlib.util.spec_from_file_location('approved_recorded_renderer',ROOT/'AI_Comp_Internal_Production_Render_005.py')
            renderer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=renderer;spec.loader.exec_module(renderer)
            sfz=ROOT/'sound_resources/KARORYFER_GROWLYBASS_V1_002/growlybass_vicious.sfz'
            events=[e for e in result['modules']['performance']['events'] if str(e['track_id'])==name]
            bpm=result['modules']['theory']['tempo_bpm']
            formatted=[{'instrument_id':'electric_bass','midi_note':e['midi'],'velocity':e['velocity'],'start_seconds':e['start_beat']*60/bpm,'duration_seconds':e['duration_beats']*60/bpm} for e in events]
            binding={'electric_bass':{'sfz':str(sfz),'verified':True,'status':'VERIFIED_OPEN_RESOURCE','provider':'Karoryfer','license':'CC0'}}
            bass=renderer.render_output_handoff({'performance':{'events':formatted}},binding,out/f'recorded_{index}',sample_rate=22050,tuning_reference_hz=tuning_reference_hz)
            if bass.get('audio_rendered'):
                shutil.copyfile(bass['stereo_derivative']['path'],wav)
                import numpy as np
                with wave.open(str(wav),'rb') as w:samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
                proof={'notes':len(events),'peak':float(np.max(np.abs(samples.astype(float))))/32768,'renderer':'RECORDED_GROWLYBASS_SFZ'}
            else:
                recorded=False
                proof=render_track(mid,index,sf,wav,'program',program=program,tuning_reference_hz=tuning_reference_hz)
                proof['preferred_recorded_resource_unavailable']=bass
        else:
            proof=render_track(mid,index,sf,wav,'drums' if drum else 'program',program=program,tuning_reference_hz=tuning_reference_hz)
        if not proof['notes'] or proof['peak']<=0:raise ValueError('EMPTY_OR_SILENT_STEM:'+name)
        with wave.open(str(wav),'rb') as w:
            frames=w.getnframes();rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth()
        digest=hashlib.sha256(wav.read_bytes()).hexdigest()
        stems.append({'track_id':name,'instrument_id':iid,'wav_path':str(wav),'sample_rate':rate,'channels':channels,'sample_width_bytes':width,'frames':frames,'sha256':digest,**proof})
        resource={'resource_type':'APPROVED_SF2_SAMPLE_LIBRARY','renderer':'FLUIDSYNTH','sf2':str(sf),'sf2_sha256':EXPECTED_SF2,'program_zero_based':program,'percussion':drum,'substitute':True,'target_gain_db':BIG_BAND_GOLDEN_GAIN_DB.get(big_band_role,0.0) if big_band_role else 0.0,'classical_golden_section':classical_section,'classical_golden_controls':CLASSICAL_GOLDEN_SECTION_CONTROLS.get(classical_section) if classical_section else None,'big_band_golden_role':big_band_role,'big_band_golden_controls':BIG_BAND_GOLDEN_CONTROLS.get(big_band_role) if big_band_role else None}
        if recorded:resource={'resource_type':'SFZ_SAMPLE_LIBRARY','sfz':str(sfz),'renderer':'RECORDED_GROWLYBASS_SFZ','substitute':False,'target_gain_db':BIG_BAND_GOLDEN_GAIN_DB.get(big_band_role,0.0) if big_band_role else 0.0,'classical_golden_section':classical_section,'classical_golden_controls':CLASSICAL_GOLDEN_SECTION_CONTROLS.get(classical_section) if classical_section else None,'big_band_golden_role':big_band_role,'big_band_golden_controls':BIG_BAND_GOLDEN_CONTROLS.get(big_band_role) if big_band_role else None}
        if proof.get('preferred_recorded_resource_unavailable'):resource['preferred_recorded_resource_unavailable']=proof['preferred_recorded_resource_unavailable']
        bindings.append({'track_id':name,'instrument_id':iid,'resource':resource})
        mappings.append({'track_id':name,'instrument_id':iid,**resource})
    if {s['track_id'] for s in stems}!=expected:raise ValueError('INCOMPLETE_RENDERED_TRACK_SET')
    manifest=out/'stems_manifest.json';manifest.write_text(json.dumps({'tracks':stems},indent=2))
    mix_result=copy.deepcopy(result)
    mix_result['modules']['target']['resolved_resources']=bindings
    final=mix(manifest,out/'finished_music',result['genre'],mix_result)
    report={**final,'status':'AUDIO_RENDER_PASS','audio_rendered':True,'stems':stems,'track_count':len(stems),'resource_quality':'APPROVED_SF2_SUBSTITUTE','instrument_mappings':mappings,'finished_audio_sha256':hashlib.sha256(Path(final['wav_path']).read_bytes()).hexdigest(),'original_sample_libraries_certified':False,'certification_scope':'FULL_COMPOSER_TO_PRESERVED_OBJECT_MASTER_WITH_EXPLICIT_SF2_RESOURCES'}
    (out/'AUDIO_VERIFICATION.json').write_text(json.dumps(report,indent=2));return report
