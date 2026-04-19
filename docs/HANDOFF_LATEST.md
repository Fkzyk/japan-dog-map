# 最新の引き継ぎ状態

作業セッションをまたいでも Claude Code が状況を把握できるようにする。
___各作業セッション終了時に必ず更新する___。

___

## 最終更新日

2026-04-19

## 更新者

Claude Code

___

## 現在のフェーズ

Phase 1〜5・7c・7d 完了。えふかず手動作業（7a・7b）待ち。

___

## 前回までの作業内容

- Phase 1〜5 全完了（認証基盤・既存機能認証紐付け・ゲーミフィケーション・LocalStorage全廃・運用強化）
- Phase 7c 完了：「別端末でも使う」アカウント昇格モーダル実装
- Phase 7d 完了：linkWithGoogle() / linkWithEmail() 実装
  - 発動条件：お気に入り20件超過（toggleFavorite成功後）または口コミ3件投稿時（submitReview成功後）
  - 匿名ユーザーのみ対象（user.is_anonymous チェック）
  - セッション中1回限り表示（_upgradePromptShown フラグ）
  - 「あとで」で7日間非表示（localStorage: jdm-upgrade-dismissed）

___

## 次に Claude Code がやるべきこと

### えふかずの手動作業完了後
- Phase 7a（Google OAuth有効化）完了 → linkWithGoogle() が動作可能になる
- Phase 7b（マジックリンク設定）完了 → linkWithEmail() が動作可能になる
- 動作確認後に Phase 7a・7b を PROGRESS.md で [x] に更新

### Phase 6（広告導入）
- 独自ドメイン取得後に着手（えふかず手動が先決）
- 6a: 独自ドメイン取得 → 6b: プライバシーポリシー等 → 6c: Cookie同意バナー → 6d: AdSense申請

___

## えふかずへの手動作業依頼

### Phase 7a：Google OAuth設定
1. Supabase Dashboard → Authentication → Providers → Google → Enable
2. Google Cloud Console で OAuth 2.0 クライアントID を作成
3. Supabase に Client ID・Client Secret を登録
4. 承認済みリダイレクトURIに `https://rfcfilhqkkjmkecxzijw.supabase.co/auth/v1/callback` を追加

### Phase 7b：メール（マジックリンク）設定
1. Supabase Dashboard → Authentication → Providers → Email → Enable
2. 「Confirm email」を ON にする
3. メールテンプレートの文言を日本語に調整（任意）

### Phase 5a：GitHubシークレット登録（バックアップ）
- GitHub リポジトリ → Settings → Secrets → Actions → New repository secret
- 名前: `SUPABASE_DB_PASSWORD`
- 値: Supabase Dashboard → Settings → Database → Database password

### Phase 5c：UptimeRobot登録
- https://uptimerobot.com で監視追加
- URL: https://japan-dog-map.vercel.app/
- 種別: HTTP(s)、チェック間隔: 5分

___

## 未解決の課題

- Phase 7a・7b：Supabase側の手動設定が必要（フロントエンドは実装済み）
- Phase 5a：GitHub Secretsへの DB パスワード登録（バックアップWorkflowが未稼働）
- Phase 5c：UptimeRobot登録（えふかず手動）
- Phase 6：独自ドメイン取得待ち

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
