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

Phase 1b・1c 完了待ち（えふかず手動作業待ち）

___

## 前回までの作業内容

- Phase 1a 完了：`docs/reports/phase-1a-investigation.md` に調査結果出力済み
- Phase 1d 完了：`auth.js` 作成済み（Supabaseクライアント sb・requireAuth・ensureAuthenticated等）
- Phase 1e 完了：`turnstile.js` 作成済み（TURNSTILE_SITE_KEYはプレースホルダー）
- index.html整理：インラインのSUPABASE_URL・sb初期化を削除し auth.js に委譲済み
- index.htmlに `/turnstile.js` と `/auth.js` の script タグを追加済み

___

## 次に Claude Code がやるべきこと

えふかずの手動作業が完了したら以下を実施：

### Phase 1c 完了後の作業
1. えふかずから Cloudflare Turnstile の Site Key を受け取る
2. `turnstile.js` の `REPLACE_WITH_TURNSTILE_SITE_KEY` を実際のSite Keyに差し替える
3. PROGRESS.md の Phase 1b・1c を [x] に更新
4. コミット・プッシュ
5. Phase 2a（spot_favorites テーブル作成・お気に入りDB化）へ進む

___

## えふかずへの手動作業依頼

### Phase 1b：Supabase Anonymous Sign-Ins
- Supabase Dashboard → Authentication → Providers → Anonymous → Enable

### Phase 1c：Cloudflare Turnstile
1. Cloudflare Dashboard → Turnstile → Add widget
2. 入力：Site name: Japan Dog Map / Domain: japan-dog-map.vercel.app / Widget mode: Managed
3. Create → Site Key と Secret Key をコピー
4. Secret Key を Supabase Dashboard → Authentication → Settings → Captcha に登録
5. Site Key を Claude Code に渡す

___

## 未解決の課題

- TURNSTILE_SITE_KEY がプレースホルダーのまま（Phase 1c完了後に差し替え）
- Supabase Anonymous Sign-Ins が未設定（Phase 1b待ち）

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
