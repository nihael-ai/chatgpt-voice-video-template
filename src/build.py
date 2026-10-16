from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image

from .common import load_project, safe_asset, ts
from .render import render_scene
from .validate import validate
from .voicevox import VoicevoxClient


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, check=True, cwd=cwd)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def write_srt(items: list[tuple[float, float, str]], output: Path) -> None:
    chunks = [f"{i}\n{ts(start)} --> {ts(end)}\n{text}\n" for i, (start, end, text) in enumerate(items, 1)]
    output.write_text("\n".join(chunks), encoding="utf-8-sig")


def visual_for(scene: dict, project_file: Path, video: dict, work: Path, index: int) -> Path:
    if scene["type"] in {"title", "diagram"}:
        path = work / f"scene-{index:02}.png"
        render_scene(scene, video, path)
        return path
    return safe_asset(project_file, scene["path"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--output", default="build")
    args = parser.parse_args()
    errors = validate(args.project)
    if errors:
        raise SystemExit("\n".join(errors))
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg が必要です")

    project_file, data = load_project(args.project)
    output = Path(args.output).resolve()
    work = output / "work"
    work.mkdir(parents=True, exist_ok=True)
    voice = VoicevoxClient()
    voice.wait()
    speaker = data["voicevox"]["speaker"]
    speed = data["voicevox"].get("speed_scale", 1.0)
    concat_lines: list[str] = []
    subtitles: list[tuple[float, float, str]] = []
    cursor = 0.0

    for index, scene in enumerate(data["scenes"], 1):
        audio = work / f"scene-{index:02}.wav"
        voice.synthesize(scene["narration"], speaker, audio, speed)
        requested = scene.get("duration", "auto")
        requested_seconds = 0.0 if requested == "auto" else float(requested)
        duration = max(requested_seconds, wav_duration(audio) + 0.35)
        source = visual_for(scene, project_file, data["video"], work, index)
        segment = work / f"scene-{index:02}.mp4"
        common = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        if scene["type"] == "clip":
            cmd = common + ["-ss", str(scene.get("trim_start", 0)), "-i", str(source), "-i", str(audio)]
        else:
            if source.suffix.lower() != ".png":
                normalized = work / f"scene-{index:02}-image.png"
                Image.open(source).convert("RGB").save(normalized)
                source = normalized
            cmd = common + ["-loop", "1", "-i", str(source), "-i", str(audio)]
        width, height, fps = data["video"]["width"], data["video"]["height"], data["video"]["fps"]
        fit = scene.get("fit", "contain")
        scale = f"scale={width}:{height}:force_original_aspect_ratio={'increase' if fit == 'cover' else 'decrease'}"
        crop_pad = f",crop={width}:{height}" if fit == "cover" else f",pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={data['video'].get('background', '#10182b')}"
        cmd += ["-t", f"{duration:.3f}", "-vf", scale + crop_pad + ",format=yuv420p", "-r", str(fps), "-c:v", "libx264", "-c:a", "aac", "-shortest", str(segment)]
        run(*cmd)
        concat_lines.append(f"file '{segment.as_posix()}'")
        subtitles.append((cursor, cursor + duration, scene["narration"]))
        cursor += duration

    concat_file = work / "concat.txt"
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
    raw_video = work / "joined.mp4"
    run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(raw_video))
    srt = output / "video.srt"
    write_srt(subtitles, srt)
    captioned = work / "captioned.mp4"
    if data.get("subtitles", {}).get("burn_in", False):
        run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_video), "-vf", "subtitles=video.srt:force_style='FontName=Noto Sans CJK JP,FontSize=22,Outline=2,Shadow=1,MarginV=34'", "-c:v", "libx264", "-c:a", "copy", str(captioned), cwd=output)
    else:
        shutil.copy2(raw_video, captioned)
    final = output / "video.mp4"
    bgm = data.get("bgm", {}).get("path")
    if bgm:
        bgm_path = safe_asset(project_file, bgm)
        volume = data["bgm"].get("volume", 0.12)
        run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(captioned), "-stream_loop", "-1", "-i", str(bgm_path), "-filter_complex", f"[1:a]volume={volume}[music];[0:a][music]amix=inputs=2:duration=first", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final))
    else:
        shutil.copy2(captioned, final)
    credits = output / "CREDITS.txt"
    credits.write_text("\n".join(data.get("credits", [])) + "\n", encoding="utf-8")
    manifest = {"title": data["title"], "duration_seconds": round(cursor, 3), "scenes": len(data["scenes"]), "speaker": data["voicevox"]["speaker_name"]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

