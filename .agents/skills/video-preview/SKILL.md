---
name: video-preview
description: Inspect layouts and static representative frames before paid or lengthy audio/video renders. Use for cheap storyboard previews, layout review, or deciding whether a full render is necessary.
---

# 低コストプレビュー

## Purpose and current limits

動画全体を書き出す前に画面デザインを確認する。**現在自動化されているのは静的なtitle/diagram画像の生成だけ**。動画の部分レンダリング、タイムラインプレビュー、差分キャッシュは未実装なので、利用可能と約束しない。

## Prerequisites

`AGENTS.md` と `VIDEO_STYLE.md` を読み、対象 `project.json` を確認する。PythonとPillowがある環境を使用。VOICEVOX・FFmpeg・GitHub Actionsは不要。

## Static preview procedure

1. `python -m src.validate projects/demo/project.json` を実行する（対象に合わせパスを変更）。
2. `title` / `diagram` について既存 `src.render.render_scene` を直接呼び、1シーン1枚のPNGを一時領域へ保存する。
3. `image` と `clip` は元ファイルを安全に確認する。現行の静止画描画関数が対応していないので、生成済みと誤報告しない。
4. 代表画面を一覧にして、文字切れ、コントラスト、余白、図の重なり、権利情報を検査する。
5. 不合格なら `project.json` または設計を修正する。まだ動画は書き出さない。

### Example: render supported static scenes without audio

```bash
python -m src.validate projects/demo/project.json
python - <<'PY'
from pathlib import Path
from src.common import load_project
from src.render import render_scene

path, data = load_project("projects/demo/project.json")
output = Path("/tmp/video-storyboard")
output.mkdir(parents=True, exist_ok=True)
for index, scene in enumerate(data["scenes"], 1):
    if scene["type"] in ("title", "diagram"):
        dst = output / f"scene-{index:02d}.png"
        render_scene(scene, data["video"], dst)
        print(dst)
    else:
        print(f"scene {index}: {scene['type']} は素材の目視確認が必要")
PY
```

## Future capability (not yet implemented)

将来は `storyboard` コマンド、部分時間範囲指定、低解像度動画、音声フレーズとの同期、フレーム比較、キャッシュを追加する。実装までは既存 `src.build` を「安いプレビュー」と偽装して呼ばない。

## Report

- 何枚の静止画を作ったかと保存先
- 構図・文字・素材上の問題
- 確認できない動き・音声・動画クリップ部分
- フルレンダリングが必要な理由（ある場合）
- 今回使用したActions実行回数（通常0回）

## Done criteria

VOICEVOXやフルMP4を起動せずに、実装済みシーンの構図が確認でき、未確認点が明示されていること。
