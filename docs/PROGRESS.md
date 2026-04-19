# Phase 進捗管理

各 Phase の進捗をここで追跡する。
___作業完了時は必ずチェックボックスを更新する___。

最終更新日: 2026-04-19

___

## Phase 1: 認証基盤

- [x] Phase 1a: 事前調査（既存コード・DB・インフラ）✅ 2026-04-19
- [x] Phase 1b: Supabase Dashboard設定（Anonymous Sign-Ins ON）✅ 2026-04-19
- [x] Phase 1c: Cloudflare Turnstile設定（Managed mode・Site Key設定・Supabase Secret Key登録完了）✅ 2026-04-19
- [x] Phase 1d: auth.js 実装 ✅ 2026-04-19
- [x] Phase 1e: turnstile.js 実装 ✅ 2026-04-19（TURNSTILE_SITE_KEYはプレースホルダー・1c完了後に差し替え）

## Phase 2: 既存機能の認証紐付け

- [x] Phase 2a: お気に入りのSupabase化（新規テーブル + LocalStorage移行）✅ 2026-04-19
- [x] Phase 2b: user_submissions.user_id追加 + submitSpot改修（submit_spot_v2）✅ 2026-04-19
- [x] Phase 2c: spot_reviews.user_id追加 + submitReview改修 ✅ 2026-04-19
- [x] Phase 2d: spot_helpfuls.user_id追加 + handleHelpful改修（toggle_helpful_v2）✅ 2026-04-19
- [x] Phase 2e: deletion_requests.user_id追加 + submitReport改修 ✅ 2026-04-19

## Phase 3: ゲーミフィケーション

- [x] Phase 3a: achievementsテーブル + user_achievementsテーブル作成 ✅ 2026-04-19
- [x] Phase 3a-2: 初期バッジ18件投入 ✅ 2026-04-19
- [x] Phase 3b: RPC関数4本実装（get_my_achievements, check_and_unlock_achievements, confirm, revoke）✅ 2026-04-19
- [x] Phase 3c: バッジ獲得モーダル + 紙吹雪 + SNSシェア ✅ 2026-04-19
- [x] Phase 3d: 既存フックへの差し込み（submitSpot, handleHelpful, submitReview）✅ 2026-04-19
- [x] Phase 3e: プロフィールモーダル実装 ✅ 2026-04-19
- [ ] Phase 3f: admin.html 承認・却下連動

## Phase 4: UX強化（LocalStorage全廃）

- [ ] Phase 4a: user_preferences テーブル作成
- [ ] Phase 4b: チュートリアル表示状態のDB化
- [ ] Phase 4c: PWAプロンプト表示制御のDB化
- [ ] Phase 4d: 初回注意モーダル表示日のDB化
- [ ] Phase 4e: manifest.json 整備
- [ ] Phase 4f: ホーム画面追加バナー実装

## Phase 5: 運用強化

- [ ] Phase 5a: GitHub Actions 日次バックアップ
- [ ] Phase 5b: GitHub Actions keep-alive Ping
- [ ] Phase 5c: UptimeRobot登録
- [ ] Phase 5d: 信頼スコア自動承認トリガー（口コミ）
- [ ] Phase 5e: 投稿レート制限トリガー

## Phase 6: 広告導入

- [ ] Phase 6a: 独自ドメイン取得
- [ ] Phase 6b: プライバシーポリシー・利用規約・お問い合わせページ作成
- [ ] Phase 6c: Cookie同意バナー実装
- [ ] Phase 6d: AdSense申請
- [ ] Phase 6e: 広告枠実装（4箇所）
- [ ] Phase 6f: アフィリエイトプログラム登録

## Phase 7: アカウント昇格導線

- [ ] Phase 7a: Google OAuth設定
- [ ] Phase 7b: マジックリンク設定
- [ ] Phase 7c: 「別端末でも使う」モーダル実装
- [ ] Phase 7d: linkIdentity実装

___

## 進捗更新ルール

- Phase 完了時にチェックボックスを [x] に変更
- 作業開始時に 🚧 Phase X 作業中 とメモ
- 完了日を横に追記（例: Phase 1a ✅ 2026-04-20）
- 問題発生時は - 問題: xxx と下に追記
