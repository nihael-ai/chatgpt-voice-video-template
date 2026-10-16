from __future__ import annotations

import argparse
import shutil
import sys

from .common import load_project, safe_asset


ALLOWED_SCENES = {"title", "diagram", "image", "clip"}


def validate(path: str) -> list[str]:
    project_file, data = load_project(path)
    errors: list[str] = []
    for key in ("title", "video", "voicevox", "scenes"):
        if key not in data:
            errors.append(f"必須項目がありません: {key}")
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes は1件以上必要です")
        return errors
    for index, scene in enumerate(scenes, 1):
        if scene.get("type") not in ALLOWED_SCENES:
            errors.append(f"scene {index}: 未対応typeです")
        if not str(scene.get("narration", "")).strip():
            errors.append(f"scene {index}: narration が必要です")
        if scene.get("type") in {"image", "clip"}:
            if not scene.get("path"):
                errors.append(f"scene {index}: path が必要です")
            else:
                try:
                    asset = safe_asset(project_file, scene["path"])
                    if not asset.is_file():
                        errors.append(f"scene {index}: 素材がありません: {scene['path']}")
                except ValueError as exc:
                    errors.append(f"scene {index}: {exc}")
    bgm = data.get("bgm", {}).get("path")
    if bgm:
        try:
            if not safe_asset(project_file, bgm).is_file():
                errors.append(f"BGMがありません: {bgm}")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--check-tools", action="store_true")
    args = parser.parse_args()
    errors = validate(args.project)
    if args.check_tools and shutil.which("ffmpeg") is None:
        errors.append("ffmpeg が見つかりません")
    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors), file=sys.stderr)
        return 1
    print("project.json: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

