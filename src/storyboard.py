"""Cheap, offline storyboard preview: Pillow only, no audio or video rendering.

Usage: python -m src.storyboard projects/demo/project.json --output build/storyboard
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from .common import load_project, safe_asset
from .render import font, render_scene
from .validate import validate


SUPPORTED_STILL = {'title', 'diagram', 'image'}


def _fits(bounds: tuple[int, int, int, int], width: int, height: int, margin: float) -> bool:
    x0, y0, x1, y1 = bounds
    return x0 >= width * margin and y0 >= height * margin and x1 <= width * (1 - margin) and y1 <= height * (1 - margin)


def inspect_static_layout(scene: dict, video: dict, *, margin: float = 0.05) -> list[str]:
    """Inspect draw coordinates and title bounding boxes for the *current* static renderer.

    These are estimates based on text metrics; this is not a video-frame audit.
    """
    if scene['type'] not in {'title', 'diagram'}:
        return []
    w, h = int(video['width']), int(video['height'])
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    issues: list[str] = []

    def check_text(name: str, text: str, xy: tuple[int, int], size: int, bold: bool) -> None:
        if not text:
            return
        bbox = draw.textbbox(xy, text, font=font(size, bold), anchor='mm')
        if not _fits(bbox, w, h, margin):
            issues.append(f'{name}: text may cross the {margin:.0%} safe margin ({bbox})')

    if scene['type'] == 'title':
        check_text('title', scene.get('title', ''), (w // 2, h // 2 - 55), 64, True)
        check_text('subtitle', scene.get('subtitle', ''), (w // 2, h // 2 + 55), 34, False)
    else:
        check_text('title', scene.get('title', ''), (w // 2, 86), 50, True)
        for index, shape in enumerate(scene.get('shapes', []), 1):
            x, y, size = shape['x'], shape['y'], shape['size']
            half = size // 2
            bbox = (x - half, y - half, x + half, y + half)
            if not _fits(bbox, w, h, margin):
                issues.append(f'shape {index}: shape may cross the {margin:.0%} safe margin ({bbox})')
            check_text(f'shape {index} label', shape.get('label', ''), (x, y), 31, True)
    return issues


def _image_preview(scene: dict, project_file: Path, video: dict, dst: Path) -> None:
    w, h = int(video['width']), int(video['height'])
    source = safe_asset(project_file, scene['path'])
    with Image.open(source) as im:
        rgb = im.convert('RGB')
        if scene.get('fit', 'contain') == 'cover':
            result = ImageOps.fit(rgb, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        else:
            fitted = ImageOps.contain(rgb, (w, h), method=Image.Resampling.LANCZOS)
            result = Image.new('RGB', (w, h), video.get('background', '#10182b'))
            result.paste(fitted, ((w - fitted.width) // 2, (h - fitted.height) // 2))
        result.save(dst)


def _clip_placeholder(video: dict, dst: Path) -> None:
    w, h = int(video['width']), int(video['height'])
    img = Image.new('RGB', (w, h), '#263246')
    d = ImageDraw.Draw(img)
    d.text((w//2, h//2 - 16), 'CLIP — NOT PREVIEWED', font=font(max(16, min(28, w//25)), True), fill='white', anchor='mm')
    d.text((w//2, h//2 + 23), 'Requires a separate media review', font=font(max(12, min(20,w//40))), fill='#cdd9ea', anchor='mm')
    img.save(dst)


def _contact_sheet(records: list[dict], output: Path, columns: int = 2, thumb_width: int = 440) -> None:
    if not records:
        return
    # Adapt to portrait or landscape without stretching source images.
    with Image.open(output / records[0]['file']) as sample:
        aspect = sample.height / sample.width
    size = (thumb_width, min(660, max(245, int(thumb_width * aspect))))
    label_height = 38
    rows = (len(records) + columns - 1) // columns
    gap = 16
    sheet = Image.new('RGB', (columns * (size[0]+gap) + gap, rows*(size[1]+label_height+gap)+gap), '#e7eaf0')
    d = ImageDraw.Draw(sheet)
    for idx, record in enumerate(records):
        x = gap + (idx%columns)*(size[0]+gap)
        y = gap + (idx//columns)*(size[1]+label_height+gap)
        with Image.open(output / record['file']) as im:
            tile = ImageOps.contain(im.convert('RGB'), size, method=Image.Resampling.LANCZOS)
        sx = x + (size[0]-tile.width)//2
        sy = y + (size[1]-tile.height)//2
        sheet.paste(tile, (sx, sy))
        status = 'REVIEW' if record['warnings'] else 'STATIC'
        d.text((x+4,y+size[1]+6), f"{record['index']:02d} / {record['type']} / {status}", fill='#162233',font=font(16,True))
    sheet.save(output / 'contact-sheet.jpg', quality=85, optimize=True)


def build_storyboard(project: str | Path, output: str | Path, *, strict: bool = False) -> dict:
    errors = validate(str(project))
    if errors:
        raise ValueError('Project validation failed: ' + '; '.join(errors))
    project_file, data = load_project(project)
    target = Path(output).resolve()
    target.mkdir(parents=True, exist_ok=True)
    video = data['video']
    records = []
    for index, scene in enumerate(data['scenes'], 1):
        kind = scene['type']
        dst = target / f'scene-{index:02}.png'
        warnings = inspect_static_layout(scene, video)
        status = 'static-preview'
        if kind in {'title', 'diagram'}:
            render_scene(scene, video, dst)
        elif kind == 'image':
            _image_preview(scene, project_file, video, dst)
            if scene.get('fit', 'contain') == 'cover':
                warnings.append('cover may crop important image content; inspect manually')
        elif kind == 'clip':
            _clip_placeholder(video, dst)
            warnings.append('clip content and timing were not previewed (placeholder only)')
            status = 'placeholder'
        else:
            raise ValueError(f'Unsupported scene type: {kind}')
        if len(scene.get('narration', '')) > 55:
            warnings.append('long scene narration: current subtitle rendering shows whole scene text at once')
        records.append({'index': index, 'type': kind, 'file': dst.name, 'status': status, 'warnings': warnings})
    _contact_sheet(records, target)
    result = {
        'project': str(project_file), 'scenes': records, 'scene_count': len(records),
        'warning_count': sum(len(record['warnings']) for record in records),
        'limits': [
            'No VOICEVOX, FFmpeg, audio, or MP4 rendering was performed',
            'Static stills do not represent final burned-in subtitle style or timing',
            'Clip scenes are placeholders, not actual extracted frames',
            'Geometry checks use estimated bounding boxes, not semantic overlap detection'
        ],
    }
    (target / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if strict and result['warning_count']:
        raise RuntimeError(f"Storyboard has {result['warning_count']} warnings; see {target / 'report.json'}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Produce a free offline storyboard; no TTS/video build.')
    parser.add_argument('project', help='Path to project.json')
    parser.add_argument('--output', default='build/storyboard')
    parser.add_argument('--strict', action='store_true', help='Fail when there are warnings')
    args = parser.parse_args()
    try:
        result = build_storyboard(args.project, args.output, strict=args.strict)
    except (ValueError, RuntimeError, OSError) as err:
        parser.exit(1, f'ERROR: {err}\n')
    print(f"storyboard: {result['scene_count']} scenes, {result['warning_count']} warnings; {Path(args.output).resolve()}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
