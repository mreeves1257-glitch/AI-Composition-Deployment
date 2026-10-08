"""Rock lead octave-regression tests for the existing genre development layer.

Only the unintended Rock octave flip is removed. The lead gain, chord guitar,
timing, notes in other genres, real sample banks and 3D mixer are unchanged.
"""
import unittest
from genre_development_patch import develop_full_length


def original_events():
    # One normal melodic note in each 16-bar section; avoid intentional gaps.
    events = [
        {"track_id":"LEAD", "instrument_id":"lead_guitar",
         "start_beat":bar * 4.0 + 0.5, "duration_beats":0.5,
         "midi":74, "velocity":95, "articulation":"genre_lead"}
        for bar in (9, 25, 42, 57)
    ]
    # Ensure every section exists in the timeline; no new musical event for
    # the test's selected lead part.
    events.append({"track_id":"BASS","instrument_id":"electric_bass_guitar",
                   "start_beat":63*4.0,"duration_beats":0.4,
                   "midi":42,"velocity":80})
    return events


def output_leads(style, seed=0):
    original=original_events()
    ctx={"meter":{"numerator":4,"denominator":4}}
    output=develop_full_length(original,ctx,style,seed)
    return original, sorted(
        [x for x in output if x.get("track_id")=="LEAD"],
        key=lambda x:float(x["start_beat"])
    ), output


class RockLeadRegisterTest(unittest.TestCase):
    def test_rock_does_not_randomly_raise_or_lower_octave(self):
        original,lead,_=output_leads("rock")
        self.assertEqual(len(lead),4)
        self.assertEqual([x["midi"] for x in lead],[74]*4)
        self.assertEqual([x["midi"] for x in original if x["track_id"]=="LEAD"],[74]*4)

    def test_rock_keeps_original_pitch_for_several_seeds(self):
        for seed in range(4):
            with self.subTest(seed=seed):
                original,lead,_=output_leads("rock",seed)
                self.assertEqual([x["midi"] for x in lead],[74]*4)

    def test_nonrock_legacy_octave_variation_unchanged(self):
        _,lead,_=output_leads("swing")
        self.assertEqual([x["midi"] for x in lead],[74,86,74,62])

    def test_rock_preserves_lead_onsets(self):
        original,lead,_=output_leads("rock")
        expected=[float(x["start_beat"]) for x in original if x["track_id"]=="LEAD"]
        self.assertEqual([float(x["start_beat"]) for x in lead],expected)

    def test_no_sound_or_mix_engine_called_in_register_test(self):
        _,lead,out=output_leads("rock")
        self.assertTrue(all("audio" not in e for e in lead))
        self.assertTrue(any(e["track_id"]=="BASS" for e in out))


if __name__=="__main__":
    unittest.main(verbosity=2)
