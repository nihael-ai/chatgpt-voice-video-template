import unittest
from pathlib import Path

from src.production_state import load, guidance
from src.validate import validate


ROOT = Path(__file__).parents[1]
PROJECT = ROOT / "projects" / "moon-distance-30"


class MoonExampleTests(unittest.TestCase):
    def test_example_project_is_valid(self):
        self.assertEqual(validate(str(PROJECT / "project.json")), [])

    def test_review_state_has_real_preview(self):
        state = load(PROJECT)
        self.assertEqual(state["stage"], "awaiting_review")
        self.assertIsNone(state["approval_reference"])
        self.assertEqual(state["revision_count"], 0)
        self.assertIn("WAIT", guidance(state))
        evidence = ROOT / state["evidence"]
        self.assertTrue(evidence.is_file())
        self.assertGreater(evidence.stat().st_size, 0)
        self.assertTrue((PROJECT / "storyboard.md").is_file())


if __name__ == "__main__":
    unittest.main()
