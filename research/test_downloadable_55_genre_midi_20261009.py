"""Validate downloaded MIDI preview archive is complete and musically separated."""
import sys,unittest,tempfile,zipfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from export_55_original_genre_midi_previews_20261009 import export_all
import mido

class GenrePreviewDownload(unittest.TestCase):
 def test_production_is_unchanged_and_55_type1_midi_tracks_roundtrip(self):
    with tempfile.TemporaryDirectory() as tmp:
        result=export_all(Path(tmp))
        self.assertEqual(result["genre_count"],55)
        self.assertGreater(result["total_note_events"],1000)
        self.assertFalse(result["audio_included"])
        self.assertTrue(result["all_roles_independent"])
        files=list((Path(tmp)/"midi").glob("*.mid"))
        self.assertEqual(len(files),55)
        profiles={r["genre"] for r in result["genres"]}
        self.assertEqual(len(profiles),55)
        self.assertTrue({"ROCK","Swing","Salsa","WALTZ","PIANIST"}.issubset(profiles))
        for record in result["genres"]:
            with self.subTest(genre=record["genre"]):
                midi=mido.MidiFile(str(Path(tmp)/"midi"/record["midi_file"]))
                self.assertEqual(midi.type,1)
                self.assertEqual(len(midi.tracks),record["role_count"]+1)
                self.assertEqual(len({v["midi_channel"] for v in record["source_roles"].values()}),
                                 record["role_count"])
                self.assertEqual(sum(sum(e.type=="note_on" and e.velocity>0 for e in t)
                        for t in midi.tracks),record["note_event_count"])
                self.assertFalse(any(e.type=="program_change" for t in midi.tracks for e in t))
        with zipfile.ZipFile(Path(tmp)/result["archive"]) as z:
            self.assertEqual(len([x for x in z.namelist() if x.endswith(".mid")]),55)
            self.assertIn("MANIFEST.json",z.namelist())
            self.assertIn("README.txt",z.namelist())
        print("55_GENRE_DOWNLOADABLE_MIDI_TYPE1_MULTI_TRACK_PASS",
              {"genre_count":55,"note_events":result["total_note_events"],
               "archive_bytes":result["archive_bytes"],"audio_claim":False})
if __name__=="__main__":unittest.main(verbosity=2)
