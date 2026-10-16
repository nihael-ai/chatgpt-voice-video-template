import json
import tempfile
import unittest
from pathlib import Path

from src.common import safe_asset, ts
from src.validate import validate


ROOT = Path(__file__).parents[1]


class ProjectTests(unittest.TestCase):
    def test_demo_is_valid(self):
        self.assertEqual(validate(str(ROOT / "projects/demo/project.json")), [])

    def test_timestamp(self):
        self.assertEqual(ts(61.234), "00:01:01,234")

    def test_path_traversal_is_rejected(self):
        project = ROOT / "projects/demo/project.json"
        with self.assertRaises(ValueError):
            safe_asset(project, "../secret.png")

    def test_missing_narration_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.json"
            path.write_text(json.dumps({"title": "x", "video": {}, "voicevox": {}, "scenes": [{"type": "title"}]}), encoding="utf-8")
            self.assertTrue(any("narration" in item for item in validate(str(path))))


if __name__ == "__main__":
    unittest.main()

