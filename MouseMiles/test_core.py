import tempfile
import unittest
from pathlib import Path

from capsules import get_scale_story
from storage import AtomicJsonFile


class ScaleStoryTests(unittest.TestCase):
    def test_zero_distance_gives_clear_starting_instruction(self):
        story = get_scale_story(0)
        self.assertIn("Move the mouse", story["headline"])
        self.assertEqual(story["progress"], 0.0)

    def test_scale_story_moves_to_next_landmark(self):
        story = get_scale_story(0.5)
        self.assertIn("keyboard lengths", story["headline"])
        self.assertGreater(story["progress"], 0.0)
        self.assertEqual(story["next_label"], "Doorway")

    def test_scale_story_never_reports_negative_progress(self):
        story = get_scale_story(100000000)
        self.assertGreaterEqual(story["progress"], 0.0)
        self.assertLessEqual(story["progress"], 100.0)


class StorageTests(unittest.TestCase):
    def test_atomic_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tracker.json"
            payload = {"distance_m": 12.5, "clicks": 3}
            AtomicJsonFile.save(str(path), payload)
            self.assertEqual(AtomicJsonFile.load(str(path)), payload)

    def test_backup_recovers_previous_valid_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tracker.json"
            first = {"distance_m": 10}
            second = {"distance_m": 20}
            AtomicJsonFile.save(str(path), first)
            AtomicJsonFile.save(str(path), second)
            path.write_text("{not valid json", encoding="utf-8")
            self.assertEqual(AtomicJsonFile.load(str(path)), first)


if __name__ == "__main__":
    unittest.main()