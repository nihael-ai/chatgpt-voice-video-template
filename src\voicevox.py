from __future__ import annotations

import os
from pathlib import Path

import requests


class VoicevoxClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")).rstrip("/")

    def wait(self, timeout: int = 90) -> None:
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                response = requests.get(f"{self.base_url}/version", timeout=3)
                response.raise_for_status()
                return
            except requests.RequestException:
                time.sleep(2)
        raise RuntimeError(f"VOICEVOX Engineに接続できません: {self.base_url}")

    def synthesize(self, text: str, speaker: int, output: Path, speed_scale: float = 1.0) -> None:
        query = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker},
            timeout=30,
        )
        query.raise_for_status()
        payload = query.json()
        payload["speedScale"] = speed_scale
        audio = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker},
            json=payload,
            timeout=120,
        )
        audio.raise_for_status()
        output.write_bytes(audio.content)

