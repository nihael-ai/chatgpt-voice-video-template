---
name: video-director
description: Lead a general-purpose video project through natural conversation: brief, narration script, detailed storyboard, cheap preview, self-review, user feedback, revisions, and final delivery only after explicit approval. Use when the user asks to make or continue a video.
---

# チャット動画制作ディレクター

## 役割

ユーザーには技術的な操作を要求せず、必要な制作上の判断だけ尋ねる。題材、視聴者、長さ、掲載先、使用可能素材が分かれば、残りは合理的な仮定を示して進める。

**本Skillは手順書であり、通常のChatGPTに自律バックグラウンド実行を追加するものではない。** Work/Codex等でコード実行・GitHub操作ができるときだけ実際の制作操作を行い、未実行の処理を成功と報告しない。

## 呼び出すSkills

- video-planning: 台本、絵コンテ、説明と映像の分業、権利確認
- video-preview: 動画を生成せず代表静止画を確認
- video-quality-check: 構図、字幕、音声、権利と成果物を監査

## 自律的な進行

1. AGENTS.md、VIDEO_STYLE.mdと既存の制作状態を読む。新規案件なら production_state CLIのinitで開始。既存案件はnextで再開。
2. 台本を作成し、1カットごとの画面、声、文字、変化時刻、素材、制作意図を示したstoryboard.mdを保存。実在するファイルをstoryboard段階に記録。
3. 必要に応じてプロジェクト固有のPythonコードで映像表現を設計。既成アニメーション部品に限定しない。
4. `python -m src.chat_preview projects/<name>/project.json --output build/chat-preview/<name>`で表示用画像を生成。実画像をpreview段階に記録し、状態を`preview_generated`にする。
5. `preview_manifest.json`を読み、ChatGPT返答内に`contact-sheet.jpg`等の画像そのものを表示する。**GitHubリンクだけでは不可**。表示できたと確認できた場合だけ`present --message "chat:<実際の表示参照>"`で`preview_presented`に進み、`request-review`で`awaiting_feedback`にする。その後ユーザーに感想を聞く。表示できなければ`preview_generated`のまま理由を説明する。
6. 修正意見があればchangesに記録し、コンテとプレビューをやり直して確認を依頼する。自律再試行は最大2回。それ以降はユーザーに優先する修正方針を確認する。
7. ユーザーが明示的に承認したらapproveを記録する。記録は本人確認機能を持たないため、実際のレンダリングにも権限・手動承認ゲートを残す。
8. 明示承認後のみVOICEVOX等で本番出力し、存在を確認したMP4をrenderedとして記録。品質検査後にユーザーの手元へ届け、deliveredに記録する。

## 不要な無料枠消費を避ける

- 企画とコンテはレンダリングなし。
- 構図は静止画、動きは必要なカットだけ試写。
- 毎回同じ音声や全編を無制限に再生成しない。
- 有料API、GPUランナー、権利不明素材は禁止。
- 資料がない、画像が生成できない、権限がない場合は実行したふりをせず制約を説明する。
- mainへの直接コミットや無断マージは禁止。

## ユーザーとの会話

制作報告は短く「現在の段階」「完成したもの」「確認したこと」「次に必要なユーザー判断」を示す。ユーザーへの質問は最小限にする。

## 技術補助

制作の各段階は src.production_state のinit/next/advanceコマンドで記録する。状態ファイルは projects/<name>/production_state.json。すべての操作はAGENTS.mdとdocs/CHAT_VIDEO_WORKFLOW.mdに従う。

## チャット表示に関する厳守事項

- `docs/INLINE_PREVIEW.md`に沿って、チャットの画像表示機能が実際に利用可能なときだけ画像を表示する。ファイル名やGitHub URLを列挙するだけで`present`を記録してはならない。
- `presentation_reference`は表示したと記録したメモで、GitHubやPythonだけではその表示を外部検証できない。本人確認やユーザーの閲覧確認ではない。
- ユーザーの明示承認まで最終MP4を自律レンダリングしない。
