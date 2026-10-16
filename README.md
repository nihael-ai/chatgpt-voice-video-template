# ChatGPT Video Starter

ChatGPTやCodexに原稿・素材・指示を渡し、`project.json` を更新するだけで、VOICEVOXナレーション、字幕、画像、図解、動画クリップ、任意BGMを組み合わせたMP4を生成する汎用テンプレートです。サンプルは数学に依存せず、文章と図形はすべて本リポジトリ用の自作です。

生成時に有料AI APIは呼びません。VOICEVOX Engine、Python、FFmpeg、GitHub Actionsの標準runnerだけを使います。ただしGitHub Actionsにはアカウント／リポジトリ種別ごとの無料枠があり、超過時の課金設定は利用者のGitHub設定に依存します。

## チャットから制作を進める（video-director 試作）

動画を作成・再開する際には、[video-director Skill](.agents/skills/video-director/SKILL.md)と[会話型制作の進行手順](docs/CHAT_VIDEO_WORKFLOW.md)を使用できます。制作状態を `projects/<name>/production_state.json` に保存し、台本 → 絵コンテ → 静止画プレビュー → ユーザー確認 → 明示承認 → MP4 の順序で進めます。

コマンド一覧：`python -m src.production_state --help`。この状態CLIは**動画そのものを作りません**。コード実行可能なWork/Codex等の環境と適切な権限が必要です。追加料金のかかるAPIは使用しません。

## できること

- `title`: 見出しと副見出し
- `diagram`: 丸・三角・四角による自作図解
- `image`: 手元のPNG/JPEGを `contain` または `cover` で配置
- `clip`: MP4等のクリップをトリミングして利用
- VOICEVOXによるシーン単位の日本語音声
- SRT字幕の出力と字幕焼き込み
- BGMのループ、音量調整
- MP4、SRT、クレジット、manifestをActions artifactとして3日間保存

## まずデモを作る（GitHubだけで実行）

1. このリポジトリから新しいリポジトリを作るか、Forkします。
2. GitHubの **Actions** タブを開き、初回だけActionsを有効にします。
3. 左側の **Build video** を選び、**Run workflow** を押します。
4. `project` は `demo` のまま実行します。
5. 完了したrunの下部にある **Artifacts** からZIPを取得します。`video.mp4`、`video.srt`、`CREDITS.txt`、`manifest.json` が入ります。

手動実行に限定しているため、第三者がPRを送っただけではVOICEVOXイメージの取得や動画ビルドは走りません。PRでは軽い検証だけを行い、権限は `contents: read`、checkout時の認証情報も保持しません。

## ChatGPT / Codexから作る手順

リポジトリをGitHub-connected coding agentまたはCodexで開き、次のように依頼します。

> AGENTS.mdとREADME.mdを読み、projects/demoをprojects/my-videoへ複製してください。テーマは「○○」、45秒前後、4シーン、VOICEVOX:ずんだもん。権利不明の外部素材は使わず、自作図形だけでproject.jsonを作成し、validatorとテストを実行してください。変更を小さなコミットまたはPRにし、Build videoを手動実行できる状態で止めてください。

エージェントがPRを作ったら、差分と素材の権利を人が確認してmergeします。その後 **Build video** を手動実行し、artifactを視聴します。字幕・読み・間・音量を直す場合は、同じチャットで `project.json` の修正を依頼します。

`AGENTS.md` はCodexが認識するリポジトリ常設指示です。GitHub接続、リポジトリへの書込権限、PR作成はChatGPT/Codex側で一度ユーザー承認が必要です。これはGitHub Actions内にOpenAIキーを置く仕組みではありません。

## project.json の要点

```json
{
  "video": {"width": 1280, "height": 720, "fps": 30, "background": "#10182b"},
  "voicevox": {"speaker": 3, "speaker_name": "ずんだもん", "speed_scale": 1.08},
  "subtitles": {"enabled": true, "burn_in": true},
  "bgm": {"path": "assets/bgm.wav", "volume": 0.12, "loop": true},
  "credits": ["VOICEVOX:ずんだもん", "BGM: 作者名 / ライセンス"],
  "scenes": [
    {"type": "image", "path": "assets/photo.jpg", "fit": "cover", "duration": "auto", "narration": "..."},
    {"type": "clip", "path": "assets/clip.mp4", "trim_start": 2.5, "duration": 6, "narration": "..."}
  ]
}
```

`duration: "auto"` は音声長に合わせます。秒数を指定した場合も、音声が切れないよう必要なら自動延長します。素材パスは `project.json` があるフォルダ内の相対パスだけが許可されます。


## 音声・MP4を生成しない静止画レビュー

Pillowだけで構図を確認します。**VOICEVOX・FFmpeg・Docker・GitHub Actionsは起動しません**。まずproject.jsonを検証し、タイトル・図解の静止画、写真素材のcontain/cover配置例、動画クリップの未確認プレースホルダーを生成します。

```bash
python -m src.storyboard projects/demo/project.json --output build/storyboard
```

出力は各シーンのPNG、一覧の \`contact-sheet.jpg\`、検査レポート \`report.json\` です。安全余白の推定警告、長いナレーション、画像トリミングの注意、動画クリップの未確認情報を記録します。警告を終了コード1として扱う場合は \`--strict\` を指定します（レポートは保存されます）。

**制限**：動画クリップの実フレーム、最終字幕の見え方と同期、ナレーション音声、アニメーションは未検査です。代表静止画のレイアウト検査は推定値であり、全ての文字の重なりや読みやすさを自動保証するものではありません。完成MP4は内容承認後に \`Build video\` で生成してください。

## ローカル実行

Python 3.12、FFmpeg、Docker Desktopを用意します。PowerShellの例:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker run --rm -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
python -m src.validate projects/demo/project.json --check-tools
python -m src.build projects/demo/project.json --output build
```

VOICEVOX Engineを既に起動している場合はDocker行を省略できます。別URLなら `VOICEVOX_URL` を設定します。

## 話者・素材・ライセンス

VOICEVOXはソフトウェア本体の規約に加えて、各音声ライブラリ／キャラクターの規約を確認してください。`speaker` IDと `speaker_name` は、利用中のVOICEVOX Engineの `/speakers` で確認できます。クレジット例は `VOICEVOX:ずんだもん` です。

写真、動画、BGMは「ネットにあったから」では使えません。自作、明示的に許諾された素材、または条件を確認済みのライセンス素材だけを `assets/` に置き、`credits` に記録してください。このテンプレートには第三者素材を同梱していません。

## 無料枠とセキュリティ

- 動画生成は `workflow_dispatch` のみ。pushや外部PRでは重い処理を自動実行しません。
- PRで走る検証は5分、動画ビルドは15分で打ち切ります。
- 同一ブランチの古いrunはキャンセルし、artifactは3日で削除します。
- workflow権限は読み取りだけで、secretsは不要です。
- DockerイメージとActionsは将来変わり得ます。安定運用では検証済みdigest／commit SHAへの固定を検討してください。
- 公開リポジトリの標準runner利用条件、非公開リポジトリの無料分、保存容量はGitHubの現行料金ページで確認してください。

## 現在の制約

- トランジション、話者の途中変更、テキストの自動折返し、高度なレイアウト編集UIは未実装です。
- BGMはファイルを同梱した場合だけ使います。デモは権利上の曖昧さをなくすためBGMなしです。
- `project.schema.json` はエディタ補助用の概要です。実際の安全検証は `src.validate` が担当します。
- GitHub側でテンプレートリポジトリ設定にする操作、Actions有効化、ChatGPT/CodexのGitHub接続はリポジトリ所有者の承認が必要です。

## ライセンス

コードと自作サンプルはMIT Licenseです。VOICEVOX、各話者、利用者が追加する素材にはそれぞれ別の規約が適用されます。

