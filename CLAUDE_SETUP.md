# Claude API セットアップ

このプロジェクトで Claude を呼び出すための最小手順です。

## 1) 依存関係をインストール

```bash
npm install
```

## 2) APIキーを設定

`.env.example` をコピーして `.env` を作成し、`ANTHROPIC_API_KEY` を入れてください。

```bash
cp .env.example .env
```

## 3) 呼び出し

```bash
npm run ask:claude -- "東京の犬連れ散歩スポットを3つ教えて"
```

## 補足

- この環境は Anthropic の公式 SDK で Claude API を直接呼びます。
- APIキーを Git にコミットしないでください（`.env` はローカル専用）。
