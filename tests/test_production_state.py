import tempfile
import unittest
from pathlib import Path
from src.production_state import StateError, init, load, advance, guidance, project_dir, MAX_REVISIONS

class DirectorStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.project = root / "projects" / "sample"
        self.project.mkdir(parents=True)
        (self.project / "storyboard.md").write_text("# storyboard", encoding="utf8")
        self.preview = root / "build" / "contact-sheet.png"
        self.preview.parent.mkdir()
        self.preview.write_bytes(b"nonempty-image-for-transition-testing")
        self.mp4 = root / "build" / "video.mp4"
        self.mp4.write_bytes(b"nonempty-video-for-transition-testing")

    def to_review(self):
        init(self.project, "General explainer")
        advance(self.project, "storyboard", evidence="storyboard.md")
        advance(self.project, "preview", evidence="../../build/contact-sheet.png")
        return advance(self.project, "request-review")

    def test_init_resume_no_overwrite(self):
        init(self.project, "One")
        self.assertEqual(load(self.project)["stage"], "brief")
        with self.assertRaises(StateError):
            init(self.project, "Two")

    def test_invalid_transition_no_approval_shortcut(self):
        init(self.project, "One")
        with self.assertRaises(StateError):
            advance(self.project, "approve", message="user:ok")
        self.assertEqual(load(self.project)["stage"], "brief")

    def test_review_must_follow_real_preview_evidence(self):
        init(self.project, "One")
        advance(self.project, "storyboard", evidence="storyboard.md")
        with self.assertRaises(StateError):
            advance(self.project, "preview", evidence="no.png")
        self.assertEqual(load(self.project)["stage"], "storyboard")

    def test_explicit_approval_then_delivery(self):
        self.to_review()
        with self.assertRaises(StateError):
            advance(self.project, "approve", message="assistant:approved")
        advance(self.project, "approve", message="user:explicit confirmation in conversation")
        advance(self.project, "rendered", evidence="../../build/video.mp4")
        result = advance(self.project, "delivered", message="https://example.test/artifacts/test")
        self.assertEqual(result["stage"], "delivered")
        self.assertEqual(len(result["history"]), 7)

    def test_revision_limit_stops_automatic_loop(self):
        self.to_review()
        for i in range(MAX_REVISIONS):
            state = advance(self.project, "changes", message=f"revision {i}")
            if i < MAX_REVISIONS-1:
                advance(self.project, "storyboard", evidence="storyboard.md")
                advance(self.project, "preview", evidence="../../build/contact-sheet.png")
                advance(self.project, "request-review")
        self.assertTrue(state["awaiting_user_decision"])
        with self.assertRaises(StateError):
            advance(self.project, "storyboard", evidence="storyboard.md")
        self.assertIn("Stop", guidance(state))

    def test_existing_files_and_repo_scope(self):
        init(self.project, "One")
        with self.assertRaises(StateError):
            advance(self.project, "storyboard", evidence="/etc/hosts")
        with self.assertRaises(StateError):
            advance(self.project, "storyboard", evidence="../../build/video.mp4")
        with self.assertRaises(StateError):
            project_dir(self.project.parent.parent / "outside")
        self.assertEqual(load(self.project)["stage"], "brief")

    def test_changes_require_feedback(self):
        self.to_review()
        with self.assertRaises(StateError):
            advance(self.project, "changes")
        self.assertEqual(load(self.project)["stage"], "awaiting_review")

if __name__ == "__main__":
    unittest.main()
