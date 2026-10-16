"""Prepare actual local preview images and metadata for an agent to show inline.

No network, VOICEVOX, FFmpeg or video export. This module CANNOT post into ChatGPT.
The chat runtime must attach the resulting image itself.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from .storyboard import build_storyboard


def _image_entry(root: Path, file_name: str, role: str, scene: int | None = None) -> dict:
    path = root / file_name
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing/nonempty preview image: {path}")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        width, height = image.size
    obj = {
        "role": role, "path": file_name,
        "mime": "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png",
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "width": width, "height": height,
    }
    if scene is not None:
        obj["scene"] = scene
    return obj


def prepare_chat_preview(project: str | Path, output: str | Path) -> dict:
    root = Path(output).resolve()
    report = build_storyboard(project, root)
    images = [_image_entry(root, "contact-sheet.jpg", "contact_sheet")]
    for record in report["scenes"]:
        images.append(_image_entry(root, record["file"], "scene", record["index"]))
    result = {
        "format": "chat-preview/1",
        "status": "generated_not_presented",
        "scene_count": report["scene_count"],
        "warning_count": report["warning_count"],
        "media": images,
        "display_order": [x["path"] for x in images],
        "limitations": [
            "The agent must attach the contact-sheet as a visible inline image; filenames do not display images",
            "No chat attachment or user delivery is performed by the GitHub repository or this script",
            "The contact sheet is a static layout preview, not an animation or narration preview",
            "Never invent sandbox URLs, chat message IDs or successful-delivery acknowledgments",
        ],
    }
    manifest = root / "preview_manifest.json"
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"output": str(root), "manifest": str(manifest), "images": len(images),
            "warnings": report["warning_count"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build inline-chat preview assets without producing video")
    parser.add_argument("project")
    parser.add_argument("--output", default="build/chat-preview/demo")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare_chat_preview(args.project, args.output), ensure_ascii=False))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
