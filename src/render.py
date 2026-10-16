from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        os.getenv("VIDEO_FONT"),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/meiryob.ttc" if bold else "C:/Windows/Fonts/meiryo.ttc",
    ]
    for item in candidates:
        if item and Path(item).is_file():
            return ImageFont.truetype(item, size=size)
    return ImageFont.load_default(size=size)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill: str) -> None:
    draw.text(xy, text, font=fnt, fill=fill, anchor="mm", align="center")


def render_scene(scene: dict, video: dict, output: Path) -> None:
    width, height = video["width"], video["height"]
    image = Image.new("RGB", (width, height), video.get("background", "#10182b"))
    draw = ImageDraw.Draw(image)
    title = scene.get("title", "")
    if scene["type"] == "title":
        centered(draw, (width // 2, height // 2 - 55), title, font(64, True), "white")
        centered(draw, (width // 2, height // 2 + 55), scene.get("subtitle", ""), font(34), "#b9c8e8")
    elif scene["type"] == "diagram":
        centered(draw, (width // 2, 86), title, font(50, True), "white")
        for shape in scene.get("shapes", []):
            x, y, size = shape["x"], shape["y"], shape["size"]
            half = size // 2
            bounds = (x - half, y - half, x + half, y + half)
            if shape["shape"] == "circle":
                draw.ellipse(bounds, fill=shape["color"])
            elif shape["shape"] == "triangle":
                draw.polygon([(x, y-half), (x-half, y+half), (x+half, y+half)], fill=shape["color"])
            else:
                draw.rounded_rectangle(bounds, radius=28, fill=shape["color"])
            centered(draw, (x, y), shape.get("label", ""), font(31, True), "#102038")
    image.save(output)

