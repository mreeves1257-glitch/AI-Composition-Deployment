"""No-render safeguards for the opt-in Rock BASS note-off policy."""
from __future__ import annotations
import copy
import os
import unittest
from unittest.mock import patch

from rock_bass_sustain_policy_v1 import SWITCH, adapt_rock_bass


def n(beat=0, dur=0.48, midi=43, *, track="BASS", instrument="electric_bass_guitar", articulation="genre_bass"):
    return {"track_id":track,"instrument_id":instrument,"midi":midi,
            "velocity":80,"start_beat":beat,"duration_beats":dur,
            "articulation":articulation}


class RockBassSustainPolicyV1Tests(unittest.TestCase):
    def setUp(self):
        self.score=[n(0,0.62),n(2,0.62,48),n(4,0.48,41),
                    n(6,0.48,53),n(8,0.48,45)]

    def test_no_default_activation(self):
        with patch.dict(os.environ,{SWITCH:"0"}):
            self.assertEqual(adapt_rock_bass(self.score,"ROCK"),self.score)
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(adapt_rock_bass(self.score,"ROCK"),self.score)

    def test_only_literal_1(self):
        for value in ("true","yes","2","on","True",""):
            with self.subTest(value=value),patch.dict(os.environ,{SWITCH:value}):
                self.assertEqual(adapt_rock_bass(self.score,"ROCK"),self.score)
        with patch.dict(os.environ,{SWITCH:"1"}):
            out=adapt_rock_bass(self.score,"ROCK")
        self.assertEqual([e["duration_beats"] for e in out],
                         [1.5,1.5,1.5,1.5,0.48])

    def test_explicit_disabled_takes_precedence_over_environment(self):
        with patch.dict(os.environ,{SWITCH:"1"}):
            self.assertEqual(adapt_rock_bass(self.score,"ROCK",enabled=False),self.score)

    def test_ineligible_genres_remain_identical(self):
        for genre in ("Jazz Ballad","FUNK","Country","swing",""):
            with self.subTest(genre=genre):
                self.assertEqual(adapt_rock_bass(self.score,genre,enabled=True),self.score)

    def test_non_bass_tracks_and_wrong_sources_remain_identical(self):
        events=[n(0),n(2,midi=48),
                n(0,track="LEAD",instrument="lead_guitar"),
                n(0,track="HARMONY",instrument="electric_guitar"),
                n(0,track="BASS",instrument="double_bass")]
        changed=adapt_rock_bass(events,"ROCK",enabled=True)
        self.assertEqual([changed[i] for i in (2,3,4)],events[2:])
        self.assertEqual(changed[0]["duration_beats"],1.5)

    def test_no_notes_added_or_other_musical_fields_edited(self):
        snapshot=copy.deepcopy(self.score)
        out=adapt_rock_bass(self.score,"ROCK",enabled=True)
        self.assertEqual(self.score,snapshot)
        self.assertEqual(len(out),len(snapshot))
        for old,new in zip(snapshot,out):
            self.assertEqual({k:v for k,v in old.items() if k!="duration_beats"},
                             {k:v for k,v in new.items() if k!="duration_beats"})

    def test_rapid_passage_unchanged(self):
        events=[n(0,0.2),n(0.5,0.18),n(1.0,0.2),n(2.0,0.2)]
        out=adapt_rock_bass(events,"ROCK",enabled=True)
        self.assertEqual([x["duration_beats"] for x in out[:2]],[0.2,0.18])
        self.assertGreater(out[2]["duration_beats"],0.2)

    def test_large_phrase_gap_not_filled(self):
        events=[n(0,0.48),n(4,0.48),n(6,0.48)]
        out=adapt_rock_bass(events,"ROCK",enabled=True)
        self.assertEqual(out[0]["duration_beats"],0.48)
        self.assertEqual(out[1]["duration_beats"],1.5)

    def test_explicit_short_mutes_not_extended(self):
        for tag in ("palm_mute","staccato","short","pizz","dead","ghost","stop","chop"):
            with self.subTest(tag=tag):
                out=adapt_rock_bass([n(0,articulation=tag),n(2)],"ROCK",enabled=True)
                self.assertEqual(out[0]["duration_beats"],0.48)

    def test_last_note_keeps_original_phrase_release(self):
        out=adapt_rock_bass([n(0),n(2)],"ROCK",enabled=True)
        self.assertEqual(out[-1]["duration_beats"],0.48)

    def test_already_long_note_not_shortened(self):
        events=[n(0,1.6),n(2,0.5)]
        self.assertEqual(adapt_rock_bass(events,"ROCK",enabled=True)[0]["duration_beats"],1.6)

    def test_repeated_onsets_use_next_distinct_attack(self):
        events=[n(0,0.48,40),n(0,0.48,45),n(2,0.48,47)]
        out=adapt_rock_bass(events,"ROCK",enabled=True)
        self.assertEqual([x["duration_beats"] for x in out],[1.5,1.5,0.48])

    def test_recorded_bass_alias_supported(self):
        score=[n(0,instrument="electric_bass"),n(2,instrument="electric_bass")]
        out=adapt_rock_bass(score,"ROCK",enabled=True)
        self.assertEqual(out[0]["duration_beats"],1.5)

    def test_no_in_place_mutations(self):
        events=copy.deepcopy(self.score)
        changed=adapt_rock_bass(events,"ROCK",enabled=True)
        changed[0]["midi"]=10
        self.assertEqual(events[0]["midi"],43)


if __name__=="__main__":
    unittest.main(verbosity=2)
