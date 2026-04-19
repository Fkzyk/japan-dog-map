# CLAUDE.md

このファイルは Claude Code がセッション開始時に自動で読み込む指示書です。

___

## 最重要ルール

作業を始める前に必ず以下のファイルを読むこと。

- `docs/MASTER_PLAN.md`（全体の実装計画書）
- `docs/DECISIONS.md`（過去の議論で確定した設計判断）
- `docs/HANDOFF_LATEST.md`（最新の引き継ぎ状態）

このルールを___一切例外なく、毎回のセッションで守ること___。

作業前にこれらを読まなければ、___過去の議論の結論を忘れて同じ議論を繰り返すことになる___。

___

## プロジェクト情報

- 公開URL: https://fkzyk.github.io/japan-dog-map/
- Supabase URL: https://rfcfilhqkkjmkecxzijw.supabase.co
- 技術: 静的サイト（index.html + admin.html）+ Supabase + Google Maps + Service Worker

___

## 絶対条件（変更不可、議論不要）

- 運用費は完全無料を維持する
- Supabase無料枠厳守: DB 500MB、MAU 50,000、Egress 5GB/月
- 有料プラン提供なし（ユーザーから料金徴収なし）
- 既存機能を壊さない、既存ユーザーのデータを失わせない

___

## 確定している設計判断（再議論禁止）

以下は過去の議論で結論が出ている。___再度議論せずこれを前提に進める___。

### 認証基盤

- Supabase Anonymous Sign-Ins を採用
- Lazy Anonymous Auth（書き込み操作の初回のみ認証発動、閲覧だけならMAUゼロ）
- Invisible Captcha として Cloudflare Turnstile Managed mode を採用
  - 通常ユーザーには見えない
  - VPN等の疑わしいアクセスのみチャレンジ表示
- Kill Switch（system_flags）で無料枠逼迫時に段階停止

### LocalStorage依存の全廃

以下はすべて Supabase DB 管理に移行する。
___LocalStorageは iOS Safari の ITP で7日で消えるため、データを保持する用途には使わない___。

- お気に入り
- チュートリアル表示状態
- PWAプロンプト表示回数・最終表示日
- 初回注意モーダル表示日

ただしキャッシュ用途（API結果の一時保存）でのLocalStorage使用は許可する。

### ゲーミフィケーション

- 投稿・訪問・口コミの3軸でバッジ獲得
- 申請時点で仮バッジ、管理者承認後に確定バッジに昇格
- 却下時はカウント再計算で取消
- 匿名ユーザーも獲得可能

### 広告収益化

- 全員に広告表示（有料プラン提供なし）
- 広告収入で運用費をペイする前提
- AdSense + ペット特化アフィリエイト
- Cookie同意バナー必須

### Captcha採用の理由

過去の議論で以下の通り結論済み。

- Captcha なしだと Bot が大量に匿名ユーザーを作れる
- Supabase MAU 50,000超過で有料化される
- Invisible Captcha（Cloudflare Turnstile Managed mode）なら通常ユーザーに影響なし
- 一部のVPN・Tor・Bot挙動でのみチャレンジ表示される

___

## 作業の進め方

### セッション開始時の必須手順

1. `docs/MASTER_PLAN.md` を読む（全体計画）
2. `docs/DECISIONS.md` を読む（確定事項）
3. `docs/HANDOFF_LATEST.md` を読む（直前の状態）
4. 今回のタスクがどのPhaseかを宣言してから作業を始める

### セッション終了時の必須手順

1. `docs/HANDOFF_LATEST.md` を更新
   - 今回実装した内容
   - 動作確認した範囲
   - 未完了のタスク
   - 次回やるべきこと
2. 過去の HANDOFF は `docs/archive/HANDOFF_YYYY-MM-DD.md` にリネームして残す
3. 新しい設計判断が追加された場合は `docs/DECISIONS.md` に追記

### Phase の進め方

- Phase の順番を守る（前Phaseが動作確認されてから次へ）
- 各Phase完了時にユーザーに動作確認してもらう
- 各Phaseの実装前に「既存コード調査」を必ず行う
- 既存機能を壊していないか確認するテストを実行する

___

## 禁止事項

- 過去の議論結果を忘れて同じ議論を蒸し返すこと
- ユーザーに「どちらにしますか？」と何度も同じ選択を聞くこと
- `docs/` 配下を読まずに作業を始めること
- 既存テーブル・関数を壊す変更（ALTER で列削除等）
- Service Role Key をクライアントコードに露出させること
- 管理者認証を回避する実装

___

## コミュニケーションルール

ユーザー（えふかず）の指示スタイルに合わせる。

- `*` `**` は一切使用禁止
- 箇条書きは `-` を使用
- 強調は `#` 見出し、改行、「」、___ を使う
- 「唯一」「最も」等の最上級表現を避ける
- 共感表現・ポエム調を避ける
- 誤りを認める時は「こちらの判断ミスだった」等の事実のみ述べる
- 日本語で返答
- ターミナルコマンドは実行依頼前に説明する
- ファイルは常に完全な形で提供（部分編集しない）
- 簡潔・直接的に

___

## 実装時の基本ルール

- SQL実行前に、現在のテーブル・関数の確認クエリを流す
- クライアントコード変更前に、該当箇所を grep で確認
- 既存のRPC関数名のネーミング規則に従う（例: admin_*_v2）
- RLS有効化を忘れない
- エラーハンドリングを必ず実装
- `docs/MASTER_PLAN.md` に記載の全SQL・全コードはコピー可能な形

___

## Phase 進捗管理

現在の進捗は `docs/PROGRESS.md` に記録する。
フォーマットは以下。

```
## Phase 1: 認証基盤
- [ ] Phase 1a: 事前調査
- [ ] Phase 1b: Anonymous Sign-Ins + Invisible Captcha 導入
- [ ] Phase 1c: auth.js + turnstile.js 実装

## Phase 2: 既存機能の認証紐付け
- [ ] Phase 2a: お気に入りのSupabase化
...
```

チェックボックスの更新は Phase 完了時に行う。

___

## 迷ったら

- 設計判断に迷ったら `docs/DECISIONS.md` を確認
- それでも不明なら ユーザー（えふかず）に確認
- 勝手に判断して進めない

___

このファイルの存在理由

えふかずとの過去の議論で決まった方針を、セッションが切れても Claude Code が忘れないようにするための仕組み。
このファイルと `docs/` 配下のドキュメントを必ず読むことで、議論の蓄積を無駄にしない。
