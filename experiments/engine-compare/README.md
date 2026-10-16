# STEP 4: Python / Remotion 動画エンジン比較

比較の目的は、一般的な図解アニメーションを無料の範囲で作る際の見栄え、修正容易性、出力負荷を比較することです。

## 公平な条件

- 両実装は同じ自作の `spec.json` を使用し、12秒・640×360・15fps・H.264 CRF23。
- タイトル・図形・色・字幕・登場時刻・フェード／移動／強調のカーブを共通にします。
- **今回比較するのは動的な映像のみです。** VOICEVOX、BGM、音声同期、外部素材は使いません。音声付き完成動画の品質が同じと主張しないでください。
- 本番の `src/build.py`、VOICEVOXコード、既存Actionsには変更しません。

## Python（ローカルで実行可能）

```bash
pip install -r requirements.txt
python experiments/engine-compare/python/render.py --spec experiments/engine-compare/spec.json --output build/engine-compare/python.mp4
```

## Remotion（ライセンス条件の確認が必要）

```bash
cd experiments/engine-compare/remotion
npm install --no-audit --no-fund
npm run typecheck
npx remotion render src/index.ts Demo ../../build/engine-compare/remotion.mp4 --codec=h264 --crf=23 --concurrency=1
```

Remotionの無料利用対象は個人、従業員3人以下の組織等です。配布・再販売や商用利用の条件を各自で確認してください。参照：https://www.remotion.dev/docs/license/pricing

## GitHubで比較

PRの専用CIは**同一リポジトリ内の比較ブランチ**からのPRでのみ実行します。実行時間は最大10分、標準CPUランナー、成果物保持1日、追加料金のかかるAPI・GPUなしです。以後の大量実行やフル解像度版は承認まで行いません。初回のパッケージ導入時間と実描画時間は分けて報告します。

合格の条件は、両方式が12秒・640×360・15fpsのMP4を出力できること、動画の見切れがないこと、処理時間と成果物容量を比較できることです。