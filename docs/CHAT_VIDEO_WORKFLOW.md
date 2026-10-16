# 知人向け：ChatGPTで話しながら動画を作る試作

## ユーザーの最初の指示

「video-director Skillに従って、テーマ『初めてのコーヒー豆の選び方』の60秒動画を作って。企画、原稿、コンテ、低コストのプレビューまで自分で進めて、感想を聞いてください。最終動画は私が明示的に承認するまで作らないでください。」

AIは適切なSkillsと制作状態を読み、必要な質問だけ行います。

## 実行環境

GitHubが接続されたChatGPT WorkやCodexなど、リポジトリの内容を読み書きし、Pythonを実行できる環境が前提です。Skillsだけでは普通のチャットが常駐エージェントになったり、実行環境に直接アクセスできるわけではありません。

## 動画ディレクターが実行するコマンド例

新規案件：

~~~bash
python -m src.production_state init projects/my-video --topic "コーヒーの選び方"
python -m src.production_state next projects/my-video
~~~

AIはprojects/my-video/storyboard.mdに絵コンテを書きます。

~~~bash
python -m src.production_state advance projects/my-video storyboard --evidence storyboard.md
python -m src.chat_preview projects/my-video/project.json --output build/chat-preview/my-video
python -m src.production_state advance projects/my-video preview --evidence ../../build/chat-preview/my-video/contact-sheet.jpg
# ChatGPTが実際の画像を会話内に表示できたと確認できた場合のみ：
python -m src.production_state advance projects/my-video present --message "chat:実際に表示したメッセージの参照"
python -m src.production_state advance projects/my-video request-review
~~~

作品のproject.jsonは別途AIが作る必要があります。自由なPython表現のプレビューには別の書き出し処理が必要な場合があります。静止画の自動プレビューは今のところtitle/diagram/image等に限定されます。

ここでユーザーにプレビューを提示し、返答を待ちます。明示的な修正意見はchangesで記録し、修正後に再び確認を依頼します。明示承認後にのみapproveへ進めます。

~~~bash
python -m src.production_state advance projects/my-video changes --message "字幕を短くして"
# または人間の明示的な承認後に限り：
python -m src.production_state advance projects/my-video approve --message "user:このプレビューで完成版を生成してよい"
~~~

**重要**：これは制作進行の記録です。approveにuser:と書くだけでは本人確認になりません。GitHub Actionsのworkflow_dispatchなど、実際の権限・確認ゲートも残します。コマンドを順番に一括実行してユーザーの確認を飛ばしてはいけません。

## 費用と守る条件

まず台本・コンテ・静止画。明示承認なしにフル動画やVOICEVOXの長時間生成を実行しない。同じ問題の自律修正を2回までに制限。無料API・ソフトウェアを使い、外部有料サービスと権利未確認の素材を使わない。GitHubではmainへの無断マージを避ける。

本試作ではChatGPTから新規動画の完全自動納品までの動作はまだ検証していません。

## チャット表示の最重要条件

実際の表示工程は `docs/INLINE_PREVIEW.md` を参照。GitHub Actionsやリポジトリ単体から会話内へ画像を挿入することはできません。画像がまだユーザーに表示されていない場合は`preview_generated`に留めてください。
