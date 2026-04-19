# japan-dog-map 認証基盤導入 引き継ぎ資料

## 目的

既存アプリの機能を壊さずに認証基盤を後付けする。
お気に入り等のデータを Supabase に紐付けし、完全無料運用を維持しつつ広告収益化の土台を整える。

___

## プロジェクト情報

- リポジトリ: https://github.com/Fkzyk/japan-dog-map
- 公開URL: https://fkzyk.github.io/japan-dog-map/
- 技術スタック: 静的サイト + Supabase + Service Worker + Vercel + GitHub Pages
- スポット数: 10,848件
- スポットデータ配信: places_data.json を GitHub Pages で静的配信

___

## 絶対条件

- 運用費は完全無料を維持する
- Supabase無料枠厳守: DB 500MB、MAU 50,000、Egress 5GB/月
- 有料プラン提供なし（ユーザー課金なし）
- 運用費は広告収入でペイする前提
- 既存機能を壊さない、既存ユーザーのデータを失わせない

___

## 現状把握（本番稼働中）

以下は本番サイトで稼働確認済み。実装を破壊しないこと。

### UI機能

- 地図表示（クラスタリング・ポップアップ・現在地取得）
- カテゴリフィルター（すべて / ドッグラン / ペット可飲食店 / 動物病院 / ペット可宿泊施設）
- ★お気に入りタブ（フィルターの一部）
- テキスト検索・ジャンル絞り込み
- サイドパネルのスポット一覧
- 初回注意モーダル（「本日は表示しない」選択肢付き）
- お知らせ機能（ベルアイコン）
- チュートリアル（「スキップ」「次へ」付き）
- Service Worker（オフライン対応）

### ユーザー操作機能

- ★お気に入り（保存先は要調査、LocalStorage or Supabase）
- 🐾行ったよ！（訪問チェックイン、カウント表示あり、Supabaseと推定）
- ★口コミ（星1〜5、500文字以内、一覧表示、Supabaseと推定）
- 🚩問題を報告（報告内容 + 連絡先メール任意）
- スポット追加（名前・カテゴリ・住所・コメント、位置微調整可）
- 投稿完了モーダル（管理者確認後公開、通常1〜3日と明記）

### 運営機能

- 管理者ページ（/admin.html）
- 投稿承認フロー

___

## 核心方針

### 既存機能を壊さない3原則

- 既存UIはそのまま残し、背後の保存処理だけ変える
- 既存LocalStorageデータは初回アクセス時にSupabaseへ自動移行
- 認証失敗時はLocalStorageフォールバックで従来通り動作

### Lazy Anonymous Auth の発動タイミング

- 閲覧だけのユーザー: 認証なし、MAUゼロ
- ★お気に入り・🐾行ったよ・★口コミ・🚩報告・スポット追加 の初回操作時に認証発動
- 以降はセッションで認証維持

### 3層防御

- Lazy Anonymous Auth でMAU抑制
- Invisible CAPTCHA（Cloudflare Turnstile）でボット遮断
- Kill Switch で無料枠逼迫時に段階停止

___

## Phase 1a: 事前調査（実装前に必須）

Claude Code は実装開始前に以下をレポート出力すること。

### コードベース調査

- index.html の地図ライブラリ（Google Maps or Leaflet or MapLibre）
- Google Maps の場合、課金リスクを評価、Leaflet 移行計画を提示
- 既存 Supabase 接続コードの有無と場所
- 既存 お気に入り の保存先・キー名
- 🐾行ったよ! の保存先・DBスキーマ
- ★口コミ の保存先・DBスキーマ
- 🚩報告 の保存先・DBスキーマ
- スポット投稿 の保存先・DBスキーマ
- 削除キー機能の有無と生成ロジック
- sw.js のキャッシュ対象と除外パターン
- manifest.json の有無と内容
- vercel.json のルーティング設定
- admin.html の現状の保護方法（要確認の最優先事項）

### Supabase側調査

- 既存テーブル一覧と現行スキーマ
- 既存RLSポリシー
- 現在のMAU数・DB使用量・Egress使用量
- Anonymous Sign-Ins が既に有効化されているか
- Google OAuth が設定済みか

### インフラ調査

- 独自ドメイン取得済みか
- Vercelプロジェクト設定（本番URL含む）
- GitHub Pages設定

### 出力内容

- 現状レポート（上記の全項目に答える）
- 影響範囲レポート（認証導入で挙動が変わる箇所一覧）
- マイグレーション戦略（既存データの user_id バックフィル方針）

___

## Phase 1b: 認証基盤

### Supabase Dashboard設定

- Authentication > Providers > Anonymous Sign-Ins: ON
- Authentication > Rate Limits > Anonymous sign-ins: 10/hour/IP
- Authentication > CAPTCHA: Cloudflare Turnstile有効化

### Cloudflare Turnstile設定

- Managed mode（invisible）
- サイトキー + シークレットキーを Supabase に登録
- ドメイン追加: fkzyk.github.io、Vercel URL

### 新規ファイル

auth.js を新規作成。以下の関数を提供。

- supabase クライアントのエクスポート
- getCurrentUser()
- isAnonymous()
- ensureAuthenticated(captchaToken): Lazy Anonymous Auth 本体
- getSystemFlags(): Kill Switch 状態取得

turnstile.js を新規作成。以下の関数を提供。

- loadTurnstileScript()
- getTurnstileToken(): invisible モードでトークン取得

### Lazy Auth の挙動

- ★や🐾の初回タップ時に getTurnstileToken() → ensureAuthenticated() の順で呼ぶ
- 通常ユーザーには CAPTCHA が表示されない
- 疑わしい通信時のみチャレンジ表示

___

## Phase 1c: 共通インフラ

### system_flagsテーブル（Kill Switch）

```sql
CREATE TABLE system_flags (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  allow_new_anonymous_auth BOOLEAN DEFAULT true,
  allow_reviews BOOLEAN DEFAULT true,
  allow_helpfuls BOOLEAN DEFAULT true,
  allow_checkins BOOLEAN DEFAULT true,
  allow_spot_submission BOOLEAN DEFAULT true,
  allow_reports BOOLEAN DEFAULT true,
  maintenance_mode BOOLEAN DEFAULT false,
  updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO system_flags (id) VALUES (1);

ALTER TABLE system_flags ENABLE ROW LEVEL SECURITY;

CREATE POLICY "flags_select_all"
  ON system_flags FOR SELECT USING (true);

CREATE POLICY "flags_update_admin_only"
  ON system_flags FOR UPDATE
  USING (EXISTS (SELECT 1 FROM admin_users WHERE user_id = auth.uid()));
```

### admin_usersテーブル + admin.html保護（最優先）

現状 admin.html が認証なしで開ける可能性がある。これは致命的なので Phase 1 の最優先で対応する。

```sql
CREATE TABLE admin_users (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin_users_select_self"
  ON admin_users FOR SELECT
  USING (auth.uid() = user_id);
```

- admin-login.html を新規作成（Google OAuthのみ許可）
- admin.html に requireAdmin() を差し込み、未認証は admin-login.html へリダイレクト
- 管理者の auth.uid は Supabase Dashboard から手動 INSERT

### GitHub Actions バックアップ

.github/workflows/backup-supabase.yml

- 毎日18:00 UTC（JST 03:00）に pg_dump 実行
- GitHub Actions artifacts に30日分保存
- SUPABASE_DB_PASSWORD を GitHub Secrets に登録

### GitHub Actions Keep-Alive Ping

.github/workflows/keepalive.yml

- 6時間ごとに Supabase に curl で ping
- UptimeRobot と併用で 1週間 pause 対策を冗長化

___

## Phase 1d: 既存機能の認証紐付け

Phase 1a の調査結果に基づいて改修。既存データを失わないこと。

### 共通の改修パターン

1. 既存テーブルに user_id 列を追加（既存データは NULL 許容）
2. RLS ポリシーを auth.uid() ベースに変更
3. 新規投稿からは auth.uid() を紐付け
4. 既存 LocalStorage データは migration 関数で Supabase にインサート

### お気に入り

想定スキーマ（既存が LocalStorage の場合に新規作成）

```sql
CREATE TABLE IF NOT EXISTS spot_favorites (
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  spot_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, spot_id)
);

CREATE INDEX idx_favorites_user ON spot_favorites(user_id);
CREATE INDEX idx_favorites_spot ON spot_favorites(spot_id);

ALTER TABLE spot_favorites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "favorites_select_own"
  ON spot_favorites FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "favorites_insert_own"
  ON spot_favorites FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "favorites_delete_own"
  ON spot_favorites FOR DELETE
  USING (auth.uid() = user_id);
```

100件上限トリガーを追加（無料運用維持のため）。
LocalStorage からの自動移行関数を実装（jdm-favorites-migrated フラグで1回だけ実行）。

### 🐾行ったよ（訪問チェックイン）

- UNIQUE(user_id, spot_id) で1ユーザー1スポット1回に制限
- マテリアライズドビューで件数集計（Egress 節約）
- RLS: SELECT は全員可（件数表示用）、INSERT/DELETE は自分のみ

### ★口コミ

既存実装があるので user_id 列追加 + RLS 差し替え。

- 投稿者本人は status 問わず自分の口コミを閲覧可能（承認待ちバッジ表示用）
- 他人は approved のみ閲覧可能
- 削除は管理者のみ（誹謗中傷逃げ対策で必須）
- UNIQUE(user_id, spot_id) で 1ユーザー 1スポット 1件
- 投稿レート制限: 1日3件まで
- 信頼スコア自動承認: 3件承認されたら以降自動承認（管理者業務縮減）

### 🚩報告

- 認証ユーザー + 完全匿名の両方を受け付ける
- INSERT は全員可、SELECT は管理者のみ
- user_id は nullable

### スポット投稿

- 既存 spots テーブルに user_id 列追加（nullable）
- 既存データはそのまま、新規投稿のみ紐付け
- 削除キー方式は既存ユーザー保護のため並行運用継続

___

## Phase 1e: 運用強化

- 信頼スコア自動承認トリガー（スポット投稿にも適用検討）
- マテリアライズドビュー定期更新（GitHub Actions cron、10〜30分間隔）
- 匿名ユーザーの定期クリーンアップ（GitHub Actions cron、30日無アクセス + 活動履歴なしを削除）

___

## Phase 1f: 広告導入

### 必要な整備

- 独自ドメイン取得（AdSense審査必須、年1,500円程度）
- プライバシーポリシー・利用規約・お問い合わせページ作成
- Cookie同意バナー実装（個人情報保護法・GDPR対応）

### 広告枠

- 地図下部バナー（320x50相当）
- サイドパネルリスト内ネイティブ広告（5件ごとに1件、PR表記）
- スポット詳細ポップアップ下部（カテゴリ連動）
- 投稿完了モーダル（ペット関連アフィリエイト）

### 収益試算

- 月間50,000 MAU × 10 impressions = 500,000 impressions
- CPM $0.3〜$1 → 月$150〜$500
- Supabase Pro $25 を十分にペイできる水準

___

## Phase 1g: UX強化

- PWA化（manifest.json 整備、未整備なら追加）
- ホーム画面追加バナー（2回目訪問以降、iOS 7日問題緩和）
- Lazy Auth のローディング演出（オプティミスティックUI）
- トースト実装の統一

___

## Phase 2: アカウント昇格

お気に入り20件超過時または口コミ3件投稿時にモーダル提案。

- Googleで続ける（1タップ）
- メールで続ける（マジックリンク、補助）
- あとで（閉じる）

linkIdentity で auth.uid を保持したまま連携。既存データを引き継ぎ可能。

___

## 運用監視とKill Switch

### 定期監視

Supabase Dashboardで週1回確認。

- MAU: 40,000で警戒、45,000で対策開始
- DB Size: 400MBで警戒
- Egress: 4GBで警戒

### Kill Switch発動段階

MAU 45,000到達時点から。

- 段階1: allow_new_anonymous_auth = false（新規認証停止）
- 段階2: allow_reviews = false（口コミ停止）
- 段階3: allow_spot_submission = false（投稿停止）
- 段階4: maintenance_mode = true（全面停止）

既存ユーザーの閲覧は維持。翌月MAUリセットで段階復旧。

___

## セキュリティチェックリスト

### 認証

- [ ] Anonymous Sign-InにCAPTCHA必須
- [ ] Rate limit強化（10/hour/IP）
- [ ] Session duration適切に設定
- [ ] redirectUrl許可リスト設定

### RLS

- [ ] 全テーブルでRLS有効化
- [ ] 匿名ユーザーは自分のデータのみ操作可
- [ ] 公開読み取りは USING (true) で明示
- [ ] Service Role Keyをクライアントに露出させない
- [ ] 口コミ削除は管理者のみ
- [ ] 報告閲覧は管理者のみ

### 管理者

- [ ] admin.html をGoogle OAuth必須に（最優先）
- [ ] admin_users テーブルで管理者を定義
- [ ] admin 画面の操作ログ記録

### データ保護

- [ ] プライバシーポリシー整備
- [ ] 利用規約整備
- [ ] Cookie同意バナー実装
- [ ] 個人情報保護法対応
- [ ] GitHub Actions 日次バックアップ稼働

___

## 実装タスクリスト

### Phase 1a: 事前調査

- [ ] 既存コードの調査レポート出力
- [ ] 既存Supabase DBの調査レポート出力
- [ ] 影響範囲レポート出力
- [ ] マイグレーション戦略の提示

### Phase 1b: 認証基盤

- [ ] Supabase Dashboard でAnonymous Sign-Ins有効化
- [ ] Cloudflare Turnstile登録・Supabase連携
- [ ] auth.js 作成
- [ ] turnstile.js 作成

### Phase 1c: 共通インフラ

- [ ] system_flags テーブル作成・RLS設定
- [ ] admin_users テーブル作成
- [ ] admin-login.html 作成（Google OAuth）
- [ ] admin.html 保護実装（requireAdmin）
- [ ] GitHub Actions バックアップワークフロー
- [ ] GitHub Actions keep-alive ワークフロー
- [ ] UptimeRobot登録

### Phase 1d: 既存機能紐付け

- [ ] お気に入りの Supabase 化 + 移行
- [ ] 🐾行ったよ に user_id 追加 + RLS差し替え
- [ ] ★口コミ に user_id 追加 + RLS差し替え
- [ ] 承認待ちバッジ表示実装
- [ ] 🚩報告に user_id 追加 + RLS差し替え
- [ ] spots.user_id 列追加
- [ ] 新規スポット投稿の紐付け

### Phase 1e: 運用強化

- [ ] 信頼スコア自動承認トリガー
- [ ] 投稿レート制限トリガー
- [ ] マテリアライズドビュー + 定期REFRESH
- [ ] 匿名ユーザークリーンアップ

### Phase 1f: 広告

- [ ] 独自ドメイン取得（必要なら）
- [ ] プライバシーポリシー・利用規約・お問い合わせページ
- [ ] Cookie同意バナー
- [ ] AdSense申請
- [ ] 広告枠HTML・CSS設置
- [ ] アフィリエイトプログラム登録

### Phase 1g: UX強化

- [ ] manifest.json 整備
- [ ] ホーム画面追加バナー
- [ ] Lazy Auth 演出
- [ ] トースト統一

### Phase 2: 昇格導線

- [ ] Google OAuth 設定
- [ ] マジックリンク設定
- [ ] 「別端末でも使う」モーダル
- [ ] linkIdentity 実装

___

## ユーザー体験の最終形

### 見るだけユーザー（大多数）

- 認証なし、MAUゼロ
- 地図・検索・スポット詳細を普通に閲覧
- 全員に広告表示

### お気に入り利用ユーザー

- 初回★タップで invisible CAPTCHA 通過 + 匿名認証
- オプティミスティック UI で体感遅延ゼロ
- 100件まで保存可能

### 口コミ投稿ユーザー

- 投稿直後に自分だけ「承認待ち」バッジで見える
- 管理者承認後に全員に公開
- 3件承認されると以降自動承認

### iOS Safariユーザー

- 未昇格: 7日後にトークン消失時、新規匿名認証で再開（お気に入りロスト）
- 昇格済み: トークン消失しても Google 認証で即復帰
- PWA ホーム画面追加済み: ITP 影響軽減

___

## 残存リスクと許容理由

- Google Maps API課金: 既存実装次第、Leaflet移行で解消可能
- 独自ドメイン年間費用: AdSense審査に必要、年1,500円程度
- iOS未昇格ユーザーの7日問題: 技術的に完全解決不可、昇格導線と PWA化 で緩和
- 50,000MAU超過: Kill Switchで段階縮退、翌月復旧
- Supabase仕様変更: Firebase、Cloudflare D1等への移行計画を頭の片隅に
- バックアップはGitHub Actions artifacts頼み: 30日以上古いデータは保持しない

___

## まとめ

この設計の特徴。

- 既存実装を壊さずに認証を後付け
- Lazy Anonymous AuthでMAU最小化
- Invisible CAPTCHAでUX悪化なしにボット遮断
- Kill Switchで無料枠逼迫時に段階縮退
- GitHub Actionsで定期バックアップとkeep-alive
- 全員に広告表示、運用費を広告収入でペイ
- 有料プラン提供なし、ユーザー課金なし
- PWA化でiOS 7日問題を技術的に緩和
- 信頼スコア自動承認で管理者業務を段階縮減

完全無料運用を維持しつつ、既存ユーザーとデータを守り、アプリが成長しても持続可能な構造。

___

## 引き継ぎ注意事項

- Phase 1a の事前調査を飛ばさないこと
- 既存の admin.html が無防備なら Phase 1c を最優先で対応
- 既存データを絶対に失わせないこと
- LocalStorage からの移行は jdm-favorites-migrated 等のフラグで冪等性を保つこと
- 実装コードの詳細は auth.js と turnstile.js のエクスポート仕様を参考に Claude Code 側で判断してよい
