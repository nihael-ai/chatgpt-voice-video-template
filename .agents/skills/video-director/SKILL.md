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
4. 低コストな静止画プレビューを生成。VOICEVOXやフルMP4を使わず、文字切れと構図をまず検証する。CLIのpreview段階に実在ファイルを記録。
5. プレビューを自身で確認し、危険な誤字や見切れがあれば修正。request-review後、ユーザーに実物画像とコンテ要約を示し、「修正箇所はありますか」と尋ねる。承認を先取りしない。
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
