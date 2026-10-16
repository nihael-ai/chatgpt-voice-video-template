import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.storyboard import build_storyboard, inspect_static_layout


class StoryboardTests(unittest.TestCase):
    def _write_project(self, root, scenes):
        data = {'title': 'Preview test', 'video': {'width': 800, 'height': 450, 'fps': 30}, 'voicevox': {'speaker': 3, 'speaker_name': 'ずんだもん'}, 'scenes': scenes}
        path = root / 'project.json'
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def test_static_scenes_make_images_without_video_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = self._write_project(root,[{'type': 'title', 'title': 'Hello', 'subtitle': 'World', 'narration':'Hello world'}, {'type':'diagram','title':'Shape','shapes':[{'shape':'circle','x':400,'y':250,'size':90,'color':'#ff0000','label':'A'}],'narration':'Here is a circle'}])
            result = build_storyboard(p, root/'out')
            self.assertEqual(result['scene_count'], 2)
            self.assertTrue((root/'out'/'scene-01.png').is_file())
            self.assertTrue((root/'out'/'contact-sheet.jpg').is_file())
            self.assertTrue((root/'out'/'report.json').is_file())
            self.assertEqual(result['warning_count'],0)
            self.assertFalse(any(root.rglob('*.mp4')))
            self.assertFalse(any(root.rglob('*.wav')))

    def test_overflow_reports_warning(self):
        v = {'width':640,'height':360}
        issues=inspect_static_layout({'type':'title','title':'This is a super extra long title that does not fit in one screen','subtitle':'','narration':'x'},v)
        self.assertTrue(any('safe margin' in x for x in issues))

    def test_image_contain_and_cover(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            Image.new('RGB',(100,300),'red').save(root/'portrait.jpg')
            p=self._write_project(root,[{'type':'image','path':'portrait.jpg','fit':'contain','narration':'x'},{'type':'image','path':'portrait.jpg','fit':'cover','narration':'x'}])
            result=build_storyboard(p,root/'out')
            self.assertEqual(result['scene_count'],2)
            self.assertTrue(any('cover' in x for x in result['scenes'][1]['warnings']))
            with Image.open(root/'out'/'scene-01.png') as first:
                self.assertEqual(first.size,(800,450))

    def test_clip_placeholder_is_marked_unreviewed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'clip.mp4').write_bytes(b'video is a placeholder; do not parse')
            p=self._write_project(root,[{'type':'clip','path':'clip.mp4','narration':'clip content'}])
            result=build_storyboard(p,root/'out')
            self.assertEqual(result['scenes'][0]['status'],'placeholder')
            self.assertIn('clip content',result['scenes'][0]['warnings'][0])

    def test_invalid_input_no_render(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            p=self._write_project(root,[])
            with self.assertRaises(ValueError):
                build_storyboard(p,root/'out')


if __name__ == '__main__':
    unittest.main()
