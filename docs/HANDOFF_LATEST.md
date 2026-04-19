# 最新の引き継ぎ状態

作業セッションをまたいでも Claude Code が状況を把握できるようにする。
___各作業セッション終了時に必ず更新する___。

___

## 最終更新日

2026-04-19

## 更新者

Claude（Web版・設計フェーズ）

___

## 現在のフェーズ

Phase 1a 開始前（事前調査の待ち状態）

___

## 前回までの作業内容

計画書作成フェーズが完了。以下のドキュメントが揃った状態。

- `CLAUDE.md`（ルール・絶対条件・確定判断のサマリー）
- `docs/MASTER_PLAN.md`（全Phase詳細）
- `docs/DECISIONS.md`（確定した設計判断）
- `docs/PROGRESS.md`（Phase進捗管理）
- `docs/HANDOFF_LATEST.md`（このファイル）

___

## 次に Claude Code がやるべきこと

1. まず `CLAUDE.md` を読む
2. `docs/MASTER_PLAN.md` を読む
3. `docs/DECISIONS.md` を読む
4. `docs/PROGRESS.md` で現在の進捗を確認
5. Phase 1a（事前調査）を開始
   - 既存コードベース調査（index.html, admin.html, sw.js）
   - Supabase側の既存スキーマ調査
   - インフラ調査（APIキー、ドメイン）
6. 調査結果を `docs/reports/phase-1a-investigation.md` に出力
7. ユーザー（えふかず）に確認を取ってから次のPhaseへ

___

## 未解決の課題

なし（計画段階完了のため）

___

## 特記事項

### 認証導入にあたっての注意

- 既存の device_id ベースのロジックを並行運用する必要あり
- 既存 user_events 等のログは破壊せず残す
- device_id → auth.uid のマッピング戦略は Phase 1a で提案する

### 既存の admin.html について

- すでに Google OAuth + admin_users による保護が実装済み
- is_admin RPC関数が稼働中
- Kill Switch（system_flags）タブも実装済み
- 壊さないように注意

### Google Maps APIキーについて

- ソース上に露出している（AIzaSyBXlAvPbRMehbFLaBeckPctko2cHnPq_n0）
- ドメイン制限の設定状況を Phase 1a で確認
- 制限が甘ければ強化が必要

___

## セッションをまたぐための情報

### 共通の挨拶

Claude Code にタスク開始を伝える時の例。

```
これから Phase X の作業を行う。
CLAUDE.md と docs/MASTER_PLAN.md と docs/DECISIONS.md を読んで、
前回の HANDOFF_LATEST.md の状況を踏まえて進めて。
```

### よくある間違い

- 過去の議論を忘れて同じ選択肢を何度も聞く
- CLAUDE.md を読まずに作業を始める
- DECISIONS.md に記載された判断を再議論する

これらを防ぐため、___毎回のセッション開始時に docs/ 配下を読む___ことを徹底する。
