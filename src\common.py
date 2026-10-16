from __future__ import annotations

import json
from pathlib import Path


def load_project(path: str | Path) -> tuple[Path, dict]:
    project_file = Path(path).resolve()
    with project_file.open(encoding="utf-8") as handle:
        return project_file, json.load(handle)


def safe_asset(project_file: Path, value: str) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"素材パスはプロジェクト内の相対パスにしてください: {value}")
    root = project_file.parent.resolve()
    candidate = (root / raw).resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError(f"素材パスがプロジェクト外です: {value}")
    return candidate


def ts(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

