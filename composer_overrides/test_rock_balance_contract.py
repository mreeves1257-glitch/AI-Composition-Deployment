"""Non-audio regression tests for composer-side Rock mix handoff."""
import unittest
from rock_balance_contract import apply_rock_balance, ROCK_GAIN_TRIMS_DB, CONTRACT_VERSION

INSTRUMENTS={
    'HARMONY':'electric_guitar',
    'LEAD':'electric_guitar',
    'BASS':'electric_bass_guitar',
    'KICK':'kick_drum_rock',
    'SNARE':'snare_drum',
    'HAT':'hi_hat',
    'TOMS':'tom_tom',
    'CRASH':'crash_cymbal',
    'RIDE':'ride_cymbal',
}
GAINS={
    'HARMONY':-7.0, 'LEAD':-8.0, 'BASS':0.0, 'KICK':10.0,
    'SNARE':9.0, 'HAT':4.0, 'TOMS':9.0, 'CRASH':6.0, 'RIDE':5.0,
}
def composition(genre="ROCK"):
    return {'genre':genre,'tempo_bpm':145,
        'modules':{
            'instrument':{'profiles':[{'track_id':t,'instrument_id':iid} for t,iid in INSTRUMENTS.items()]},
            'target':{'resolved_resources':[{'track_id':t,'resource':{
                'instrument_id':iid, 'resource_type':'SFZ_SAMPLE_LIBRARY',
                'target_gain_db':GAINS[t], 'preferred_mapping':str(t)+'.sfz'
            }} for t,iid in INSTRUMENTS.items()]},
            'performance':{'events':[{'track_id':'LEAD','midi':70,'start_beat':0.5,'duration_beats':2.5}]}
        }, 'audio_rendered':True}
def resource(result,track):
    return next(x['resource'] for x in result['modules']['target']['resolved_resources'] if x['track_id']==track)

class RockBalanceContractTest(unittest.TestCase):
    def test_all_expected_rock_roles_adjusted(self):
        src=composition()
        out=apply_rock_balance(src)
        self.assertEqual(set(out['composer_mix_instruction']['adjusted_tracks']),set(ROCK_GAIN_TRIMS_DB))
        for t in INSTRUMENTS:
            self.assertEqual(resource(out,t)['target_gain_db'], GAINS[t]+ROCK_GAIN_TRIMS_DB[t])
        self.assertEqual(out['composer_mix_instruction']['name'],CONTRACT_VERSION)
    def test_lead_foreground_and_chords_support(self):
        out=apply_rock_balance(composition())
        self.assertGreater(resource(out,'LEAD')['target_gain_db'],resource(out,'HARMONY')['target_gain_db'])
        self.assertLess(resource(out,'HARMONY')['target_gain_db'],GAINS['HARMONY'])
    def test_drums_not_flattened(self):
        out=apply_rock_balance(composition())
        for role in ['SNARE','HAT','TOMS','CRASH','RIDE']:
            self.assertGreater(resource(out,role)['target_gain_db'],GAINS[role])
        self.assertLessEqual(ROCK_GAIN_TRIMS_DB['KICK'],1.0)
    def test_other_genres_untouched(self):
        for genre in ['FUNK','Bossa Nova','HOUSE','Jazz Ballad','COUNTRY ROCK','OTHER']:
            obj=composition(genre)
            self.assertIs(apply_rock_balance(obj),obj)
    def test_no_midi_or_timing_changes(self):
        obj=composition()
        out=apply_rock_balance(obj)
        self.assertIs(out['modules']['performance'],obj['modules']['performance'])
        self.assertEqual(out['tempo_bpm'],obj['tempo_bpm'])
    def test_unmodified_original_resources(self):
        obj=composition()
        out=apply_rock_balance(obj)
        self.assertEqual(resource(obj,'LEAD')['target_gain_db'],-8.0)
        self.assertEqual(resource(obj,'KICK')['target_gain_db'],10.0)
        self.assertIsNot(resource(out,'LEAD'),resource(obj,'LEAD'))
    def test_only_matching_instrument_receives_trim(self):
        obj=composition()
        for p in obj['modules']['instrument']['profiles']:
            if p['track_id']=='HAT':
                p['instrument_id']='piano'
        out=apply_rock_balance(obj)
        self.assertEqual(resource(out,'HAT')['target_gain_db'],GAINS['HAT'])
        self.assertEqual(resource(out,'SNARE')['target_gain_db'],GAINS['SNARE']+ROCK_GAIN_TRIMS_DB['SNARE'])
    def test_no_deep_kick_claim(self):
        out=apply_rock_balance(composition())
        self.assertIn('NO_SUBKICK',out['composer_mix_instruction']['kick_depth_note'])
    def test_invalid_structure_fails_open_unchanged(self):
        for obj in [{'genre':'ROCK'}, {'genre':'ROCK','modules':{}}, {'genre':'ROCK','modules':{'instrument':{},'target':{}}}]:
            self.assertIs(apply_rock_balance(obj),obj)

if __name__=='__main__': unittest.main(verbosity=2)
