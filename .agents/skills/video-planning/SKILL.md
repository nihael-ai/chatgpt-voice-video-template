---
name: video-planning
description: Design short or long general-purpose narrated videos with a script, storyboard, credits, and project.json that matches the repository's supported scene types. Use before any rendering or when revising a concept.
---

# 動画の企画・台本・絵コンテ

## When to use

- 新しい解説・観光・商品・教育・ニュース動画を企画するとき
- 原稿の修正、構成変更、字幕・画面情報の整理が必要なとき
- 不要なフルレンダリングを避けて設計だけを固めるとき

## Read first

`AGENTS.md` / `VIDEO_STYLE.md` / `README.md` / 対象 `project.json` / `project.schema.json`。

## Workflow

1. 利用者から題材、狙い、対象視聴者、掲載先、尺、言語、画面比、権利確認済み素材、音声話者を確認する。未指定値は「仮定」として明記する。
2. 冒頭の導入、要点の順序、最後の回収を設計する。1シーン1目的とする。
3. シーンごとに、映像、読み上げ原稿、字幕表示文、切替条件、素材・出典を表にする。
4. 文字を増やして解決せず、音声と図・写真の分担を検討する。見切れが予想される長文は短くする。
5. テンプレート現行実装の `title` / `diagram` / `image` / `clip` に落とし込む。未対応の動き・フレーズ単位字幕・場面転換は絵コンテの「将来の実装要件」に残し、`project.json` に未実装キーを追加しない。
6. VOICEVOX話者IDと表示名、必要なクレジット、追加素材の権利を確認する。不明素材は使用しない。
7. `python -m src.validate projects/<name>/project.json` で構造チェックする。動画生成はしない。
8. 視認性に不安がある場合は `video-preview` を使う。最終判断はユーザーの確認後。

## Deliverables

- 目的／対象視聴者／尺／画面サイズ
- シーン表（目的、ナレーション、画像・図形、字幕、想定秒数）
- バリデーション済みの `project.json`（対象を作成・編集した場合）
- 素材の権利とクレジットの確認状況
- 現行エンジンで実現できない演出と代替案
- 実行済み検証／未実行のテストを分離した報告

## Completion gate

無断の有料APIやフルレンダリングを使わず、構造を検証でき、内容がレビュー可能であること。制作意図の未確定部分を黙って決定しない。
