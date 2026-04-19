# Phase 1a 事前調査レポート

調査日: 2026-04-19
調査者: Claude Code

___

## 1. コードベース調査

### device_id 生成処理

- 場所: `index.html:1783` `getDeviceId()`
- 保存先: `localStorage` キー名 `jdm-device-id`
- 生成方法: `crypto.randomUUID()` または手動UUID生成（フォールバック）
- 注意: ITPで7日後に消える。auth.uid移行後も並行運用期間中は継続利用

### お気に入り（isFavorite / getFavorites / toggleFavorite）

- 場所: `index.html:1796〜1825`
- 保存先: `localStorage` キー名 `jdm-favorites`（JSON配列）
- キャッシュ: `_favoritesCache` 変数でメモリキャッシュ済み
- 移行対象: Phase 2a で `spot_favorites` テーブルに移行する

### 🐾行ったよ（handleHelpful）

- 場所: `index.html:1850`
- DB: `sb.rpc('toggle_helpful', { p_spot_id, p_device_id })` 経由
- LocalStorage: `jdm-helpfuls`（楽観的UI用、キー名 `HELPFUL_KEY`）
- ロールバック実装済み（DB失敗時にLocalStorageとUIを戻す）
- 移行内容: `p_device_id` を `p_user_id` に変更

### スポット投稿（submitSpot）

- 場所: `index.html:1743`
- DB: `sb.rpc('submit_spot', { p_name, p_category, p_address, p_lat, p_lng, p_comment })` 経由
- テーブル名: `user_submissions`（MASTERPLANの `submissions` と異なる、注意）
- 移行内容: RPC に `p_user_id` パラメータを追加

### 口コミ投稿（submitReview）

- 場所: `index.html:1970`
- DB: `sb.from('spot_reviews').insert([{ spot_id, rating, comment, device_id, status:'pending' }])`
- `device_id` は NOT NULL、直接INSERT
- 移行内容: `user_id` カラムをINSERTに追加（nullable）

### 問題報告（submitReport）

- 場所: `index.html:2017`
- DB: `sb.from('deletion_requests').insert([{ spot_id, spot_name, reason, contact_email }])`
- `device_id` カラムなし（もともと不要設計）
- 移行内容: `user_id` カラム追加（nullable）

### チュートリアル完了フラグ

- 場所: `index.html:2056`
- 保存先: `localStorage` キー名 `jdm-tutorial-date`（Unixミリ秒）
- 仕様: 30日間隔で再表示（`TUTORIAL_INTERVAL_DAYS = 30`）
- 移行対象: Phase 4b で `user_preferences.tutorial_completed_at` に移行

### 初回注意モーダル

- 場所: `index.html:1474〜1487`
- 保存先: `localStorage` キー名 `caution_skip_date`（YYYY-MM-DD文字列）
- 仕様: 「本日は表示しない」チェック時に当日スキップ
- 移行対象: Phase 4c で `user_preferences.caution_modal_hidden_until` に移行

### PWAプロンプト表示制御

- 場所: `index.html:940〜985`（`checkAndShowPwaPrompt`）
- 保存先: `localStorage` キー名 `pwa_prompt_count`（整数）
- 仕様: 15回に1回表示、チュートリアル終了後に必ず1回表示
- 移行対象: Phase 4b で `user_preferences.pwa_prompt_last_shown_at` に移行

### Service Worker キャッシュ対象

- ファイル: `sw.js`
- プリキャッシュ: `/`、`/index.html`、`/news.json`、`/favicon.ico`
- キャッシュ除外: `supabase.co`、`googleapis.com`、`unpkg.com`、`jsdelivr.net`
- 戦略: ネットワークファースト（失敗時にキャッシュフォールバック）
- キャッシュバージョン: `v1`（デプロイ時に手動更新が必要）

___

## 2. Supabase 既存スキーマ調査

### 既存テーブル一覧

| テーブル名 | 備考 |
|---|---|
| admin_config | 管理者設定 |
| admin_users | 管理者UUID管理 |
| deletion_requests | 削除依頼 |
| places | スポットデータ（静的） |
| spot_helpfuls | 行ったよ記録 |
| spot_overrides | スポット上書き設定 |
| spot_reviews | 口コミ |
| system_flags | Kill Switch |
| user_events | 行動ログ |
| user_submissions | スポット投稿 |

注意: `submissions` というテーブルは存在しない。実際は `user_submissions`。MASTERPLANの記載と異なる。

### device_id カラムの有無

| テーブル | device_id | user_id | 備考 |
|---|---|---|---|
| spot_reviews | あり（NOT NULL） | なし | 移行要 |
| user_events | あり（NOT NULL） | なし | 移行要 |
| spot_helpfuls | あり（NOT NULL） | なし | 移行要 |
| user_submissions | なし | なし | delete_key方式 |
| deletion_requests | なし | なし | 元々不要設計 |

### spot_favorites テーブル

存在しない。Phase 2a で新規作成が必要。

### RLSポリシー現状

| テーブル | INSERT | SELECT | UPDATE | DELETE |
|---|---|---|---|---|
| user_submissions | なし（RPC経由） | approved_select | なし | なし |
| spot_reviews | reviews_insert（全員可） | reviews_select_approved（全員可） | なし | なし |
| spot_helpfuls | helpfuls_insert（全員可） | helpfuls_select（全員可） | なし | なし |
| deletion_requests | requests_insert（全員可） | なし | なし | なし |
| user_events | events_insert（全員可） | なし | なし | なし |
| admin_users | なし | admin_users_select_self | なし | なし |
| system_flags | なし | flags_select_all | flags_update_admin_only | なし |

課題:
- `spot_reviews` のINSERTは全員可（device_id必須）→ user_id追加後にRLS強化が必要
- `spot_helpfuls` のDELETEポリシーなし → toggle_helpfulはRPCで処理しているため問題なし
- `user_submissions` のINSERTポリシーなし → submit_spot RPCで処理しているため問題なし

### Anonymous Sign-Ins 設定状況

Supabase Dashboard で手動確認が必要。未設定の場合は Phase 1b で有効化する。

___

## 3. インフラ調査

### Google Maps APIキー

- 場所: `index.html:856`（ソース上に露出）
- ドメイン制限: 設定済み（Vercelドメインに制限）
- 推奨: Google Cloud Console で使用量アラートを設定（月$180で通知、$200で停止）

### 独自ドメイン

- 現状: 未取得（`japan-dog-map.vercel.app` のみ）
- 影響: AdSense申請には独自ドメインが必要（Phase 6a）

### Cloudflare アカウント

- 現状: 不明（えふかずに確認が必要）
- 用途: Turnstile（Invisible Captcha）に必要
- アカウント作成は無料

### manifest.json

- 存在: あり（`manifest.json`）
- `display: standalone` 設定済み
- アイコン: 192px・512px 設定済み
- `start_url: /` → Vercel運用と一致

### vercel.json

- 全パスを `/index.html` にリライト（SPA構成）

___

## 4. 認証導入による影響範囲

| 機能 | 変更内容 |
|---|---|
| お気に入り（★） | LocalStorage → DB。初回タップで Anonymous Auth 発動 |
| 行ったよ（🐾） | `p_device_id` → `p_user_id`。toggle_helpful RPC改修が必要 |
| 口コミ（★口コミ） | `device_id` → `user_id` 追加。初回タップで Anonymous Auth 発動 |
| スポット投稿 | `submit_spot` RPC に `p_user_id` 追加 |
| 問題報告（🚩） | `user_id` カラム追加（nullable）。認証は任意 |
| チュートリアル | LocalStorage → DB（Phase 4b） |
| 注意モーダル | LocalStorage → DB（Phase 4c） |
| PWAプロンプト | LocalStorage → DB（Phase 4b） |
| logEvent | `device_id` 継続＋`user_id` 追加 |

___

## 5. MASTERPLANとの差異・注意事項

| 項目 | MASTERPLAN記載 | 実際 | 対応 |
|---|---|---|---|
| テーブル名 | `submissions` | `user_submissions` | 全SQLを `user_submissions` に変更 |
| submitSpot | `sb.from('submissions').insert()` | `sb.rpc('submit_spot', ...)` | RPC方式のまま user_id を追加 |
| spot_helpfuls | 未記載 | 存在（device_id ベース） | Phase 2d で user_id 追加対象に含める |

___

## 6. マイグレーション戦略（device_id → auth.uid）

- 既存レコードの device_id は残す（変更・削除しない）
- user_id カラムを nullable で追加し、新規投稿から記録開始
- device_id → auth.uid のマッピングは技術的に不可能（LocalStorageが既に消えている可能性）
- 移行フラグ `jdm-favorites-migrated` を使い、LocalStorageからDBへの移行を1回だけ実行

___

## 7. Phase 1b 着手前の確認事項（えふかず向け）

以下は手動操作または確認が必要。

1. Supabase Dashboard で Anonymous Sign-Ins が有効かどうか確認
   - Authentication → Providers → Anonymous
2. Cloudflare アカウントを持っているか確認
   - なければ無料で作成（cloudflare.com）
3. 独自ドメインを取得する予定があるか確認
   - AdSense申請に必要（Phase 6a）

___

## 8. 既実装済み（計画より先行）

以下は今セッションまでに既に実装済み。正式なDB管理版はPhase 4で差し替える。

- manifest.json（Phase 4e 相当）
- PWAインストールバナー（Phase 4f 相当、LocalStorage版）
- system_flags Kill Switch フロント組み込み（Phase 1c 相当）
- admin.html Google OAuth保護（Phase 1c 相当）
