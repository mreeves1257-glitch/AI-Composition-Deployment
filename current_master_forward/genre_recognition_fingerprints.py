"""Fine-tooth genre-recognition fingerprints for the 55-profile Composer.

This layer does not choose a genre. The user-selected genre remains authoritative.
It tells downstream stages what features must remain recognizable and what nearby
profiles must not be silently collapsed together.

The musical-detail anchors are read directly from each profile, so there is one
source of truth for tempo, groove, harmony, bass, percussion, instrumentation,
phrasing, articulation, humanization, mix and production.  This module adds the
recognition/disambiguation layer that the performance registry previously lacked.
"""
from __future__ import annotations

import copy
import hashlib
import json

SCHEMA_ID = 'AI_COMPOSER_GENRE_RECOGNITION_FINGERPRINT_V1'

ANCHOR_FIELDS = (
    'tempo_bpm_range','meter_options','form_tendencies','groove_behavior',
    'phrase_behavior','harmony_behavior','bass_behavior',
    'percussion_behavior_if_applicable','instrument_role_behavior',
    'ensemble_player_behavior','arrangement_transformation','dynamic_behavior',
    'articulation_behavior','timing_humanization_behavior',
    'continuous_performance_control','mix_prominence_intent','sound_effects_intent',
    'production_mastering_intent','manufacturer_adapter_requirements',
)

UNIVERSAL_GATES = (
    'DO_NOT_RECOGNIZE_FROM_TEMPO_ALONE',
    'DO_NOT_RECOGNIZE_FROM_ONE_INSTRUMENT_ALONE',
    'DO_NOT_RECOGNIZE_FROM_ONE_DRUM_PATTERN_ALONE',
    'PRESERVE_ALL_REQUESTED_PART_IDENTITIES_THROUGH_SEPARATOR',
    'PRESERVE_GENRE_SPECIFIC_GROOVE_HARMONY_PHRASING_AND_ARTICULATION_TOGETHER',
    'NEAREST_NEIGHBOR_DISAMBIGUATION_REQUIRED',
)

# Research/source IDs are intentionally family-level.  They support recognition
# architecture and genre traits without pretending that any one reference is a
# universal definition of a living genre.
SOURCES = {
    'BERKLEE_BIG_BAND': 'https://college.berklee.edu/courses/cw-311',
    'BERKLEE_JAZZ_ARRANGING': 'https://online.berklee.edu/courses/jazz-arranging',
    'SMITHSONIAN_SWING': 'https://www.americanhistory.si.edu/explore/projects/smithsonian-jazz/education/bennys-music-class',
    'SMITHSONIAN_JAZZ_ANTHOLOGY': 'https://folkways-media.si.edu/docs/folkways/artwork/SFW40820.pdf',
    'BERKLEE_FUNK': 'https://college.berklee.edu/courses/ilbs-247',
    'BERKLEE_RNB': 'https://college.berklee.edu/courses/encf-122',
    'BERKLEE_NEO_SOUL': 'https://college.berklee.edu/courses/enjz-418',
    'LOC_BLUEGRASS': 'https://www.loc.gov/collections/dolly-parton-and-the-roots-of-country-music/articles-and-essays/bluegrass-music/',
    'BERKLEE_COUNTRY_GUITAR': 'https://online.berklee.edu/courses/country-guitar',
    'BERKLEE_SALSA': 'https://college.berklee.edu/courses/cw-225',
    'BERKLEE_CLAVE': 'https://pulse.berklee.edu/?id=4&lesson=14',
    'BERKLEE_LATIN_ENSEMBLE': 'https://college.berklee.edu/courses/enlt-220',
    'NI_HOUSE': 'https://blog.native-instruments.com/house-music-101/',
    'ABLETON_TECHNO': 'https://learningmusic.ableton.com/make-melodies/ride.html',
    'ABLETON_MAKING_MUSIC': 'https://cdn-resources.ableton.com/resources/uploads/makingmusic/MakingMusic_DennisDeSantis.pdf',
    'NI_AFRO_HOUSE': 'https://blog.native-instruments.com/afro-house-production-101/',
    'NI_AFROBEATS': 'https://www.native-instruments.com/products/afrobeats',
    'BERKLEE_DEMBOW': 'https://www.berklee.edu/berklee-now/news/what-is-dembow-tracing-the-roots-of-a-global-phenomenon',
    'BERKLEE_TRIP_HOP': 'https://online.berklee.edu/courses/composing-and-producing-electronic-music-2',
    'LOC_SPIRITUALS': 'https://www.loc.gov/collections/songs-of-america/articles-and-essays/musical-styles/ritual-and-worship/spirituals/',
    'BERKLEE_SOLO_PIANO': 'https://www.berklee.edu/berklee-today/berklee-today-fall-2017/woodshed',
    'MIXMAG_CHUGG': 'https://mixmagmena.com/assets/uploads/images/MUSIC-INTELLIGENCE-REPORT-Internal-Use-Only.pdf',
}

# Nearest-neighbor rules are project recognition guards, not claims that these
# genres have one immutable definition.
DETAIL = {
    'ROCK': dict(neighbors=['Country Rock','Jazz Fusion'], discriminators=[
        'rock backbeat plus electric-guitar/bass/drum hierarchy must remain primary',
        'do not infer Country Rock without country articulation/timbre evidence; do not infer Fusion from electric instruments alone'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'New Age': dict(neighbors=['Ambient Electronic','Spiritual'], discriminators=[
        'spacious melodic/harmonic foreground may be acoustic or electronic and need not have a beat',
        'do not collapse into Ambient Electronic when melody/acoustic performance is structurally foregrounded; do not infer sacred tradition'], sources=['ABLETON_MAKING_MUSIC']),
    'Classical': dict(neighbors=['WALTZ','New Age'], discriminators=[
        'score-like voice leading, phrase hierarchy, dynamics and articulation must survive with independent orchestral/chamber identities',
        'meter such as 3/4 is insufficient: Classical must not become generic Waltz, and orchestral timbre alone is insufficient'], sources=[]),
    'Swing': dict(neighbors=['Big Band','Bebop','Cool Jazz'], discriminators=[
        'swing pocket requires coordinated ride/time feel, bass motion and responsive comping',
        'small/medium swing is not Big Band unless sectional horn orchestration is present'], sources=['SMITHSONIAN_SWING','SMITHSONIAN_JAZZ_ANTHOLOGY']),
    'Jazz Ballad': dict(neighbors=['Cool Jazz','Country Ballad'], discriminators=[
        'slow jazz harmony plus intimate lead, sparse bass and brush/light accompaniment form the fingerprint',
        'slow tempo alone must never classify a ballad as Jazz Ballad'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'Big Band': dict(neighbors=['Swing','Mambo'], discriminators=[
        'saxophone, trumpet and trombone sections must remain independently registered alongside rhythm section',
        'sectional voicing, call-response, backgrounds, soli and ensemble hits distinguish large-ensemble behavior from combo swing'], sources=['BERKLEE_BIG_BAND','SMITHSONIAN_SWING']),
    'Jazz Waltz': dict(neighbors=['WALTZ','Jazz Ballad'], discriminators=[
        'triple meter must retain jazz comping/harmony and swing-or-straight jazz subdivision',
        'explicitly reject generic oom-pah-pah as an automatic substitute for jazz 3/4'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'Bebop': dict(neighbors=['Swing','Cool Jazz'], discriminators=[
        'fast interactive small-combo language, walking bass, ride time and harmonically dense/chromatic melodic behavior are joint anchors',
        'tempo alone does not create bebop'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'Cool Jazz': dict(neighbors=['Bebop','Jazz Ballad'], discriminators=[
        'space, lighter attack, transparent texture and restrained ensemble interaction must remain audible',
        'extended harmony alone must not collapse Cool Jazz into Bebop'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'Dixieland': dict(neighbors=['Swing','Big Band'], discriminators=[
        'front-line identities must remain differentiated: trumpet/cornet lead, clarinet obbligato/counterline and trombone support/counterline',
        'collective improvisatory texture must not be replaced by later swing-section block writing'], sources=['SMITHSONIAN_JAZZ_ANTHOLOGY']),
    'Jazz Fusion': dict(neighbors=['ROCK','Funk'], discriminators=[
        'electric rhythm section plus jazz harmonic/improvisational behavior and funk/rock-derived precision must coexist',
        'electric guitar or synthesizer alone does not identify Fusion'], sources=['BERKLEE_JAZZ_ARRANGING']),
    'Rhythm and Blues': dict(neighbors=['Soul','Contemporary R&B'], discriminators=[
        'groove, 4/4 or 12/8 feel, call-response/vocal texture and blues/gospel-derived language must be evaluated together',
        'retain live-ensemble groove identity rather than automatically modernizing into Contemporary R&B'], sources=['BERKLEE_RNB']),
    'Soul': dict(neighbors=['Rhythm and Blues','Funk'], discriminators=[
        'gospel-derived phrasing/harmony and expressive lead with rhythm-section support remain central',
        'horn/organ color may support identity but cannot replace expressive phrasing and groove evidence'], sources=['BERKLEE_RNB']),
    'Funk': dict(neighbors=['Soul','Jazz Fusion','DISCO'], discriminators=[
        'interlocking syncopated drums, bass, clipped guitar/keys and optional horns are recognized as one groove system',
        'four-on-floor alone is not Funk and must not collapse Funk into Disco'], sources=['BERKLEE_FUNK']),
    'Contemporary R&B': dict(neighbors=['Rhythm and Blues','Neo-Soul-related'], discriminators=[
        'modern programmed/live hybrid groove, low-end design and sparse layered production must coexist with R&B phrasing',
        'do not force classic live-band instrumentation when the production profile is intentionally modern'], sources=['BERKLEE_RNB']),
    'Neo-Soul-related': dict(neighbors=['Contemporary R&B','Soul'], discriminators=[
        'deep pocket, harmonically sophisticated keys/guitar, bass/drums interaction and expressive human timing must remain linked',
        'do not quantize away the laid-back pocket or reduce identity to extended chords alone'], sources=['BERKLEE_NEO_SOUL']),
    'Traditional Country': dict(neighbors=['Country Rock','Two-Step','Bluegrass-related'], discriminators=[
        'country guitar/bass phrasing with fiddle/steel/piano colors must remain distinguishable when selected',
        'do not make rock backbeat dominant and do not replace country ensemble with bluegrass break-exchange behavior'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Country Rock': dict(neighbors=['ROCK','Traditional Country'], discriminators=[
        'rock rhythm-section weight and country articulation/timbre must both be present',
        'country color alone must not override the rock backbeat foundation'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Country Ballad': dict(neighbors=['Traditional Country','Jazz Ballad'], discriminators=[
        'country timbre/phrasing with slow sparse accompaniment and restrained fills must survive',
        'slow tempo and extended harmony must not redirect it to Jazz Ballad'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Country Shuffle': dict(neighbors=['Two-Step','Traditional Country'], discriminators=[
        'triplet/shuffle subdivision must be shared by drums, bass and accompaniment',
        'do not substitute straight two-beat drive for shuffle feel'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Two-Step': dict(neighbors=['Country Shuffle','Traditional Country'], discriminators=[
        'steady dance pulse with alternating-bass/two-beat drive is structural',
        'do not introduce shuffle subdivision unless the selected piece explicitly requests it'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Country Waltz': dict(neighbors=['WALTZ','Country Ballad'], discriminators=[
        '3/4 beat-one hierarchy must retain country guitar/fiddle/steel/piano language',
        'triple meter by itself is not enough to classify a generic Waltz as Country Waltz'], sources=['BERKLEE_COUNTRY_GUITAR']),
    'Bluegrass-related': dict(neighbors=['Traditional Country','Country Rock'], discriminators=[
        'acoustic string-band identities and break/lead exchanges must remain separate: guitar, bass, fiddle, banjo/mandolin/dobro when available',
        'traditional texture must not automatically gain a rock drum kit'], sources=['LOC_BLUEGRASS']),
    'Bossa Nova': dict(neighbors=['Samba','Jazz Ballad'], discriminators=[
        'understated Brazilian syncopation, soft guitar/piano comping and jazz-influenced harmony must remain integrated',
        'do not replace bossa restraint with full samba percussion density'], sources=['BERKLEE_LATIN_ENSEMBLE']),
    'Samba': dict(neighbors=['Bossa Nova','Salsa'], discriminators=[
        'layered Brazilian percussion roles and continuous forward syncopation must remain independent',
        'do not impose Afro-Cuban clave/tumbao architecture as a generic Latin substitute'], sources=['BERKLEE_LATIN_ENSEMBLE']),
    'Salsa': dict(neighbors=['Mambo','Cha-Cha','Rumba'], discriminators=[
        'clave orientation, piano montuno role, bass tumbao role and differentiated percussion must agree',
        '2-3 versus 3-2 orientation is composition-specific and must not be silently flipped'], sources=['BERKLEE_SALSA','BERKLEE_CLAVE']),
    'Mambo': dict(neighbors=['Salsa','Big Band'], discriminators=[
        'clave-organized Afro-Cuban rhythm with strong arranged brass/reed figures and percussion setup must remain linked',
        'large horn section alone is not Mambo; rhythmic architecture must remain Afro-Cuban'], sources=['BERKLEE_SALSA','BERKLEE_LATIN_ENSEMBLE']),
    'Rumba': dict(neighbors=['Salsa','Cha-Cha'], discriminators=[
        'rumba-clave/percussion-led identity must remain distinct from salsa montuno/big-band assumptions',
        'do not infer one universal rumba pattern across all variants; preserve selected project baseline'], sources=['BERKLEE_CLAVE','BERKLEE_LATIN_ENSEMBLE']),
    'Cha-Cha': dict(neighbors=['Mambo','Salsa'], discriminators=[
        'moderate dance pulse, cha-cha rhythmic identity and Afro-Cuban ensemble roles must remain stable',
        'do not accelerate/reshape into Mambo simply because brass and clave are present'], sources=['BERKLEE_LATIN_ENSEMBLE']),
    'Bolero': dict(neighbors=['Jazz Ballad','Rumba'], discriminators=[
        'slow lyrical Latin/Cuban phrase and accompaniment behavior must remain primary',
        'slow tempo alone is insufficient; preserve source-specific percussion/accompaniment instead of generic ballad drums'], sources=['BERKLEE_LATIN_ENSEMBLE']),
    'House': dict(neighbors=['Techno','DISCO','Afro House'], discriminators=[
        'four-on-floor kick, offbeat/propulsive hats, dance bass and loop-evolving arrangement form the core fingerprint',
        'house must not be identified from kick pattern alone; harmonic/groove/production context separates it from Techno and Disco'], sources=['NI_HOUSE','ABLETON_MAKING_MUSIC']),
    'Techno': dict(neighbors=['House','Trance'], discriminators=[
        'repetitive machine pulse, evolving timbre/automation and percussion/synth sequencing may carry more identity than chord progression',
        'do not force house-style soulful harmony or trance-style euphoric lead behavior'], sources=['ABLETON_TECHNO']),
    'Trance': dict(neighbors=['House','Techno'], discriminators=[
        'driving dance pulse plus sustained/evolving harmony, arpeggiated/lead synth language and long tension-release arcs must coexist',
        'four-on-floor alone is insufficient'], sources=['ABLETON_MAKING_MUSIC']),
    'Ambient Electronic': dict(neighbors=['New Age','Downtempo'], discriminators=[
        'texture, space, drones/pads and gradual timbral evolution may outweigh conventional beat or melody',
        'do not invent a beat merely to make the genre easier to classify'], sources=['ABLETON_MAKING_MUSIC']),
    'Downtempo': dict(neighbors=['Trip-Hop','Ambient Electronic'], discriminators=[
        'slow-to-moderate beat, spacious production and melodic/harmonic atmosphere must coexist without requiring Trip-Hop break/sample grammar',
        'do not erase the beat into pure ambient unless the profile says so'], sources=['ABLETON_MAKING_MUSIC']),
    'Breakbeat-related': dict(neighbors=['Garage-related','Trip-Hop'], discriminators=[
        'broken/syncopated drum pattern is structural and must remain separate from bass and melodic layers',
        'do not straighten the rhythm into four-on-floor during rendering'], sources=['ABLETON_MAKING_MUSIC']),
    'Garage-related': dict(neighbors=['House','Breakbeat-related'], discriminators=[
        'garage swing/shuffle and syncopated drum/bass relationship must survive quantization',
        'do not reduce Garage-related to straight House simply because both may use dance tempos'], sources=['ABLETON_MAKING_MUSIC']),
    'Experimental Electronic': dict(neighbors=['Genre-Breaking / Borderless','Ambient Electronic'], discriminators=[
        'component/provenance rules are the fingerprint; no default beat, harmony or instrumentation may be invented',
        'recognition succeeds only when user-selected components and transformation rules remain traceable'], sources=['ABLETON_MAKING_MUSIC']),
    'Eclectic New Indie': dict(neighbors=['ROCK','Genre-Breaking / Borderless'], discriminators=[
        'indie-oriented song identity may combine guitars, synths, acoustic/electronic rhythm and unusual texture without one mandatory grammar',
        'keep profile broad and do not pretend a single production trope universally defines current indie'], sources=[]),
    'Mexican Reggaeton': dict(neighbors=['Chugg / #chugg','Afro-Latin / Afrobeats Fusion'], discriminators=[
        'reggaeton/dembow-derived rhythmic identity and contemporary Mexican scene production choices must remain jointly represented',
        'do not substitute Dominican dembow, generic Latin percussion or Afrobeats simply because related rhythmic ancestry exists'], sources=['BERKLEE_DEMBOW']),
    'Chugg / #chugg': dict(neighbors=['Mexican Reggaeton','Experimental Electronic'], discriminators=[
        'treat #chugg as an emerging scene-specific plugg evolution rather than a timeless fixed genre grammar',
        'sparse plugg/trap-derived texture and local scene profile must remain; no universal chugg swing may be invented'], sources=['MIXMAG_CHUGG']),
    'Afrobeats': dict(neighbors=['Afro House','Afro-Latin / Afrobeats Fusion'], discriminators=[
        'layered syncopated groove, percussion/bass interlock, rhythmic guitar/keys and hook-oriented production are evaluated together',
        'do not collapse Afrobeats into Afrobeat, generic house or generic world-music percussion'], sources=['NI_AFROBEATS']),
    'Afro-Latin / Afrobeats Fusion': dict(neighbors=['Afrobeats','Salsa','Afro House'], discriminators=[
        'recognition is component-driven: explicitly named Afrobeats and Afro-Latin source behaviors must both remain traceable',
        'never stack every percussion vocabulary at once or erase provenance'], sources=['BERKLEE_CLAVE','NI_AFROBEATS']),
    'Afro House': dict(neighbors=['House','Afrobeats'], discriminators=[
        'stable house four-on-floor foundation plus organic/polyrhythmic percussion and deep atmospheric/bass behavior must coexist',
        'do not classify as Afrobeats merely because African-derived percussion/guitar colors are present'], sources=['NI_AFRO_HOUSE']),
    'Trip-Hop': dict(neighbors=['Downtempo','Breakbeat-related'], discriminators=[
        'downtempo broken/sample-like drums, heavy bass and atmospheric/soul/jazz-derived texture must work as one system',
        'slow breakbeat alone is insufficient'], sources=['BERKLEE_TRIP_HOP']),
    'Contemporary Trip-Hop / Trip-Hop Revival': dict(neighbors=['Trip-Hop','Downtempo'], discriminators=[
        'base Trip-Hop looseness and atmosphere must survive beneath modern sub-bass/digital layers',
        'the modern overlay must not erase the underlying breakbeat/space identity'], sources=['BERKLEE_TRIP_HOP']),
    'Regional Electronic Hybrids': dict(neighbors=['Genre-Breaking / Borderless','Custom Hybrid'], discriminators=[
        'regional source identity and electronic component must be named and provenance-preserved',
        'never infer regional instruments, scales or rhythms from geography labels alone'], sources=[]),
    'Genre-Breaking / Borderless': dict(neighbors=['Experimental Electronic','Custom Hybrid'], discriminators=[
        'component assignment and transformation rules are authoritative; there is intentionally no fixed genre fingerprint',
        'retain source identity for each imported component through every section'], sources=[]),
    'Custom Hybrid': dict(neighbors=['Genre-Breaking / Borderless','Custom Style'], discriminators=[
        'user-selected component genres and conflict-resolution map define recognition',
        'no automatic default fingerprint may replace missing user components'], sources=[]),
    'Custom Style': dict(neighbors=['Custom Hybrid','Controlled Custom Style Profile'], discriminators=[
        'all recognition dimensions are user-defined and must remain explicit',
        'do not borrow the nearest automatic genre as a hidden fallback'], sources=[]),
    'Controlled Custom Style Profile': dict(neighbors=['Custom Style','Custom Hybrid'], discriminators=[
        'saved profile identity and its stored recognition data are authoritative',
        'block if saved profile is unavailable rather than guessing'], sources=[]),
    'DISCO': dict(neighbors=['House','Funk'], discriminators=[
        'four-on-floor dance pulse, syncopated melodic bass, rhythmic guitar and orchestral/keyboard hook colors must remain independently audible',
        'distinguish from House by disco ensemble/arrangement language and from Funk by persistent dance-floor pulse'], sources=['NI_HOUSE']),
    'WALTZ': dict(neighbors=['Country Waltz','Jazz Waltz','Classical'], discriminators=[
        '3/4 beat-one hierarchy is necessary but substyle/context must control harmony, articulation and instrumentation',
        'never classify all triple-meter music as the same Waltz'], sources=[]),
    'PIANIST': dict(neighbors=['Jazz Ballad','Classical'], discriminators=[
        'single-performer coherence and independent left/right-hand roles are the fingerprint, not a backing-band genre',
        'do not manufacture separate bass/drum/guitar players unless explicitly requested'], sources=['BERKLEE_SOLO_PIANO']),
    'Spiritual': dict(neighbors=['New Age','Rhythm and Blues'], discriminators=[
        'this project profile is deliberately nonsectarian and must not silently map to Gospel, African American spirituals, meditation or an Indigenous/religious tradition',
        'if a historical spiritual subprofile is explicitly chosen, call-response and source-specific performance practice require separate provenance'], sources=['LOC_SPIRITUALS']),
}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def _mode(profile):
    policy = profile.get('resolution_policy')
    status = profile.get('status')
    if policy in ('CONTROLLED_RESOLVER','USER_COMPONENTS_REQUIRED','SAVED_PROFILE_REQUIRED'):
        return 'COMPONENT_OR_PROFILE_DRIVEN'
    if status in ('CONTROLLED_BROAD_PROFILE','CONTROLLED_EMERGING_PROFILE','CONTROLLED_OVERLAY'):
        return 'BOUNDED_BROAD_BASELINE'
    if status == 'CONTROLLED_INSTRUMENTAL_STYLE':
        return 'INSTRUMENTAL_STYLE'
    return 'FIXED_PROJECT_BASELINE'


def build(name, profile, requested_parts):
    if not profile or not profile.get('profile_id'):
        raise ValueError('GENRE_RECOGNITION_PROFILE_MISSING')
    if not requested_parts or len(requested_parts) != len(set(requested_parts)):
        raise ValueError('GENRE_RECOGNITION_PARTS_INVALID')
    detail = copy.deepcopy(DETAIL.get(name, {
        'neighbors': [],
        'discriminators': ['unregistered/test profile: rely on supplied profile anchors without neighbor substitution'],
        'sources': [],
    }))
    anchors = {field: copy.deepcopy(profile.get(field)) for field in ANCHOR_FIELDS if field in profile}
    missing = [field for field in ANCHOR_FIELDS if field not in profile]
    # Synthetic test fixtures used by regression tests may omit optional musical
    # fields, but every registered Composer profile must be complete.
    if name in DETAIL and missing:
        raise ValueError('GENRE_RECOGNITION_ANCHOR_MISSING::' + ','.join(missing))
    fp = {
        'schema_id': SCHEMA_ID,
        'genre': name,
        'profile_id': profile['profile_id'],
        'recognition_mode': _mode(profile),
        'profile_anchor_fields': anchors,
        'required_part_identities': list(requested_parts),
        'separator_requirement': 'EVERY_REQUESTED_PART_IDENTITY_SURVIVES_TO_INSTRUMENT_RESOLUTION',
        'nearest_neighbors': detail['neighbors'],
        'disambiguation_rules': detail['discriminators'],
        'universal_recognition_gates': list(UNIVERSAL_GATES),
        'source_ids': detail['sources'],
        'source_urls': {sid: SOURCES[sid] for sid in detail['sources']},
        'scope_rule': 'PROJECT_CONTROLLED_RECOGNITION_BASELINE_NOT_UNIVERSAL_GENRE_DEFINITION',
    }
    fp['fingerprint_sha256'] = _hash(fp)
    return fp


def validate(fingerprint, *, genre=None, profile_id=None, requested_parts=None):
    if not isinstance(fingerprint, dict) or fingerprint.get('schema_id') != SCHEMA_ID:
        raise ValueError('GENRE_RECOGNITION_FINGERPRINT_MISSING_OR_INVALID')
    claimed = fingerprint.get('fingerprint_sha256')
    body = dict(fingerprint)
    body.pop('fingerprint_sha256', None)
    if _hash(body) != claimed:
        raise ValueError('GENRE_RECOGNITION_FINGERPRINT_HASH_MISMATCH')
    if genre is not None and fingerprint.get('genre') != genre:
        raise ValueError('GENRE_RECOGNITION_FINGERPRINT_GENRE_MISMATCH')
    if profile_id is not None and fingerprint.get('profile_id') != profile_id:
        raise ValueError('GENRE_RECOGNITION_FINGERPRINT_PROFILE_MISMATCH')
    if requested_parts is not None and list(fingerprint.get('required_part_identities', [])) != list(requested_parts):
        raise ValueError('GENRE_RECOGNITION_FINGERPRINT_PARTS_MISMATCH')
    if not fingerprint.get('disambiguation_rules'):
        raise ValueError('GENRE_RECOGNITION_DISAMBIGUATION_MISSING')
    return fingerprint