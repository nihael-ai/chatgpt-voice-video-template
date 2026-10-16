# チャット内プレビュー表示の実装契約

## 目的と実行上の限界

ユーザーの主な確認場所はChatGPTの会話です。GitHubのPRリンクやZIPは保存先・フォールバックであり、プレビュー提示の代用にしないこと。

**GitHub ActionsやGitHubリポジトリは既存のChatGPT会話に画像を投稿できません。** 実際の画像表示は、そのターンのChatGPT / Work / Codexなどが利用可能なメディア表示機能を通じて行います。表示APIがない環境では、無理に「表示済み」と記録せず、プレビュー画像を添付できる環境へ作業を引き継ぐかフォールバックを明示してください。

## ChatGPTで実行する基本工程

1. AGENTS.md と video-director / video-preview Skillsを読み、台本・コンテを作成。
2. \`python -m src.chat_preview projects/<name>/project.json --output build/chat-preview/<name>\` を実行。Python/Pillowのみ、VOICEVOX・FFmpeg・MP4なし。
3. \`preview_manifest.json\` を読み、\`contact-sheet.jpg\` を最優先で表示。必要なら \`scene-XX.png\` を複数枚表示する。**表示するのは実ファイルそのもの**であり、スクリプトが生成したパス文字列だけを出してはならない。
4. チャットが添付を受理し実際に画像を表示した場合にのみ \`advance ... present --message "chat:<表示した発言への説明/参照>"\` を実行。この記録はホスト受理の暗号学的証拠ではない。表示に失敗した場合は \`preview_generated\` のまま。
5. \`advance ... request-review\` のあと、短い自己点検と「どこを修正しましょうか？」を提示。ユーザーの返答があるまでは\`approve\`を行わない。
6. 修正があれば \`changes\`→コンテ→新しいプレビュー→再表示→質問、明示承認があれば \`approve\`。
7. 本番レンダリングは別途ユーザーの明示承認＋GitHub Actions側の権限管理を条件とする。

この方式は**UIに画像が表示される実装が可能なホスト環境**を前提とします。単に\`presentation_reference\`欄へ文字を保存するだけでは、ChatGPTのUI表示や本人認証を保証しません。

## 制作状態

\`\`\`
brief -> storyboard -> preview_generated -> preview_presented
      -> awaiting_feedback -> revision_requested -> storyboard -> ...
      -> approved -> rendered -> delivered
\`\`\`

\`preview_generated\`: 画像と管理情報を生成したが、表示は未確認。
\`preview_presented\`: 実際にチャットが画像を表示できたことをエージェントが確認して記録。
\`awaiting_feedback\`: プレビューが提示され、質問を行った。回答待ち。

旧v1の \`preview\` と \`awaiting_review\` は、自動移行時に安全側へ倒して\`preview_generated\`とし、あらためて表示を求める。

## コストと安全

- この工程はローカルにPillowがある場合はGitHub Actions実行時間を消費しない。
- 低コストの静止画だけ生成し、制作途中のフルMP4と音声合成は起動しない。
- 実際の素材が巨大または第三者著作物の場合はリポジトリに無断コミットしない。
- 自動チェックは字幕の実際の表示タイミング・動画内の動き・音声の発音を保証しない。
- 実装はGitHubにコミットしただけでは、ChatGPT画面に新しいボタンや自動表示機能が生えるわけではない。
