---
name: video-quality-check
description: Audit a general-purpose narrated video project for structural correctness, readability, rights, and verified output quality. Use before approving final rendering or reviewing generated MP4 artifacts.
---

# 映像・字幕・音声の品質監査

## Scope

現在利用できる自動検査と、未実装の品質検査を区別する。GitHub Actionsの緑色のチェックはレンダリングの技術的成功を示すのみで、映像の見栄え・伝わりやすさの合格ではない。

## Stage A: cheap automatic checks (default)

1. `AGENTS.md` と `VIDEO_STYLE.md` を確認する。
2. `python -m src.validate projects/<name>/project.json` を実行する。
3. `python -m unittest discover -s tests -v` を実行する。
4. 台本の文字量、素材の存在・権利、字幕・話者クレジット、解像度・fps設定を点検する。
5. 未実装の自動視覚検査・字幕同期がある場合、状態を `NOT IMPLEMENTED` とする。

## Stage B: visual preview (when requested or needed)

- `video-preview` Skillを使ってタイトルと図解の静止画を取得する。
- フレーム外への見切れ、被写体crop、文字同士の重なり、コントラスト、余白を目視する。
- 写真やクリップは別途メディア確認が必要。生成していないものを「確認済み」と言わない。

## Stage C: final video (only after explicit approval)

- VOICEVOX／FFmpegの環境と無料枠消費見込みを確認してから必要な作品だけレンダリング。
- `ffprobe` で長さ、縦横、fps、映像・音声ストリームを検査し、無音や不自然な空白を試聴で確認する。
- 実際の動画から代表フレームを抽出し、字幕、画面構図、急な切替、重大な見切れをチェックする。
- ナレーションの誤読・抑揚・字幕同期・意味の通りやすさは人間の視聴確認も必要。
- 成果物の保存期間・ファイル名・クレジットとActions使用時間を記録する。

## Output format

```text
Project:
Structural validation: PASS / FAIL / NOT RUN
Unit tests: PASS / FAIL / NOT RUN
Static layout review: PASS / FAIL / NEEDS HUMAN REVIEW / NOT RUN
Audio and timing: PASS / FAIL / NEEDS HUMAN REVIEW / NOT RUN
Final MP4 verification: PASS / FAIL / NOT RUN
Rights and credits: PASS / FAIL / NEEDS HUMAN REVIEW
Actions usage: 0 / measured minutes
Blockers:
Next decision:
```

## Completion gate

根拠のある項目だけPASSとする。致命的な欠陥がある場合は本番書き出しを止める。動画の生成・再実行・mainへのマージはユーザーの明示承認がある場合だけ。
