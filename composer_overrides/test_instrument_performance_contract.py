import unittest
from instrument_performance_contract import perform, CONTRACT_VERSION, GENRE_POLICIES

def note(track, onset, dur, pitch=60, articulation="genre_harmony", instrument=None):
    return {'track_id':track,'instrument_id':instrument or ('lead_guitar' if track == 'LEAD' else 'electric_guitar'),
            'start_beat':onset,'duration_beats':dur,'midi':pitch,'velocity':90,'articulation':articulation}

class PerformanceContractTest(unittest.TestCase):
    def test_ringing_chord_is_one_strummed_gesture(self):
        source=[note('HARMONY',0,.46,52),note('HARMONY',.032,.46,59),note('HARMONY',.064,.46,64),
                note('HARMONY',2,.46,52),note('HARMONY',2.032,.46,59),note('HARMONY',2.064,.46,64)]
        before=[dict(e) for e in source]
        result=perform(source,'ROCK')
        self.assertTrue(all(1.4 < e['duration_beats'] < 1.8 for e in result[:3]))
        self.assertEqual(len({round(e['start_beat'] + e['duration_beats'],4) for e in result[:3]}),1)
        self.assertEqual(source,before)
        self.assertEqual([x['midi'] for x in result],[x['midi'] for x in source])
        self.assertEqual([x['start_beat'] for x in result],[x['start_beat'] for x in source])
    def test_fast_picked_notes_not_automatically_sustained(self):
        x=[note('LEAD',0,.13,62, 'genre_lead'),note('LEAD',.25,.13,64,'genre_lead'),note('LEAD',.5,.13,65,'genre_lead')]
        self.assertEqual(perform(x,'ROCK'),x)
    def test_rock_lead_can_sustain(self):
        x=[note('LEAD',0,.34,67,'genre_lead'),note('LEAD',2,.34,69,'genre_lead')]
        self.assertGreater(perform(x,'ROCK')[0]['duration_beats'],1.5)
    def test_explicit_muting_is_respected(self):
        x=[note('HARMONY',0,.14,55,'palm_muted'),note('HARMONY',2,.5,60)]
        self.assertEqual(perform(x,'ROCK')[0]['duration_beats'],.14)
    def test_explicit_legato_rapid(self):
        x=[note('LEAD',0,.12,61,'legato'),note('LEAD',.5,.12,63,'legato')]
        self.assertGreater(perform(x,'ROCK')[0]['duration_beats'],.4)
    def test_no_synthetic_pads_at_ending(self):
        x=[note('HARMONY',0,.5),note('HARMONY',2,.32)]
        self.assertEqual(perform(x,'ROCK')[1]['duration_beats'],.32)
    def test_other_genres_untouched(self):
        x=[note('HARMONY',0,.46),note('HARMONY',2,.46)]
        for g in ['FUNK','SALSA','Jazz Ballad','Country Rock','HOUSE','Custom Hybrid']:
            self.assertEqual(perform(x,g),x)
    def test_drums_bass_keyboard_unmodified(self):
        x=[note('KICK',0,.1,36,'rock_kick','kick_drum_rock'),
           note('SNARE',1,.1,38,'rock_backbeat','snare_drum'),
           note('HAT',0,.06,42,'hat','hi_hat'),
           note('BASS',0,.5,43,'genre_bass','electric_bass_guitar'),
           note('KEYS',0,1,60,'genre_harmony','electric_piano')]
        self.assertEqual(perform(x,'ROCK'),x)
    def test_valid_contract(self):
        self.assertEqual(CONTRACT_VERSION,'INSTRUMENT_PERFORMANCE_V1')
        self.assertEqual(list(GENRE_POLICIES),['ROCK'])

if __name__=='__main__':
    unittest.main(verbosity=2)
