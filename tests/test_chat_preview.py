import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from src.production_state import StateError, advance, init, load
from src.chat_preview import prepare_chat_preview


class ChatPresentationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.project = self.repo / "projects" / "trial"
        self.project.mkdir(parents=True)
        (self.project / "storyboard.md").write_text("# A storyboard", encoding="utf-8")
        self.project_json = self.project / "project.json"
        self.project_json.write_text(json.dumps({
            "title": "Coffee facts",
            "video": {"width": 640, "height": 360, "fps": 15, "background": "#10182b"},
            "voicevox": {"speaker": 3, "speaker_name": "ずんだもん"},
            "scenes": [{"type": "title", "title": "Coffee", "subtitle": "Trivia", "narration": "Short fact."},
                       {"type": "diagram", "title": "Why?", "narration": "A diagram.", "shapes": [
                           {"shape": "circle", "x": 310, "y": 220, "size": 60, "color": "#3ab", "label": "A"}]}]
        }, ensure_ascii=False), encoding="utf-8")

    def _generated(self):
        result = prepare_chat_preview(self.project_json, self.repo / "build/chat-preview/trial")
        init(self.project, "Coffee")
        advance(self.project, "storyboard", evidence="storyboard.md")
        advance(self.project, "preview", evidence="../../build/chat-preview/trial/contact-sheet.jpg")
        return result

    def test_chat_manifest_local_images_no_url_or_video(self):
        result = self._generated()
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "generated_not_presented")
        self.assertEqual(manifest["media"][0]["role"], "contact_sheet")
        self.assertEqual(manifest["scene_count"], 2)
        for media in manifest["media"]:
            self.assertNotIn("url", media)
            self.assertNotIn("sandbox", media["path"])
            p = Path(result["output"]) / media["path"]
            self.assertTrue(p.is_file())
            with Image.open(p) as img:
                self.assertGreater(img.width, 0)
            self.assertEqual(media["bytes"], p.stat().st_size)
            self.assertEqual(len(media["sha256"]), 64)
        self.assertFalse(any(self.repo.rglob("*.mp4")))
        self.assertFalse(any(self.repo.rglob("*.wav")))

    def test_approval_without_visible_presentation_is_blocked(self):
        self._generated()
        self.assertEqual(load(self.project)["stage"], "preview_generated")
        with self.assertRaises(StateError):
            advance(self.project, "request-review")
        with self.assertRaises(StateError):
            advance(self.project, "approve", message="user:ok")
        with self.assertRaises(StateError):
            advance(self.project, "present", message="not actually displayed")
        self.assertEqual(load(self.project)["stage"], "preview_generated")

    def test_present_feedback_then_user_approval(self):
        self._generated()
        state = advance(self.project, "present", message="chat:preview shown as an inline image in reply")
        self.assertEqual(state["stage"], "preview_presented")
        state = advance(self.project, "request-review")
        self.assertEqual(state["stage"], "awaiting_feedback")
        approved = advance(self.project, "approve", message="user:please finish the video")
        self.assertEqual(approved["stage"], "approved")

    def test_v1_state_requires_representing_in_chat(self):
        self._generated()
        path = self.project / "production_state.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["version"] = 1
        obj["stage"] = "awaiting_review"
        obj.pop("presentation_reference", None)
        path.write_text(json.dumps(obj), encoding="utf-8")
        migrated = load(self.project)
        self.assertEqual(migrated["stage"], "preview_generated")
        self.assertIsNone(migrated["presentation_reference"])
        with self.assertRaises(StateError):
            advance(self.project, "approve", message="user:approve")


if __name__ == "__main__":
    unittest.main()
