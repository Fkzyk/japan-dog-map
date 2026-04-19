# japan-dog-map マスター実装計画書

Claude Code が参照する実装計画の全体像。
認証基盤・ゲーミフィケーション・広告導入・UX強化を1本のロードマップにまとめた。

___

## 参照先

作業前に以下も必ず読むこと。

- `CLAUDE.md`（ルートディレクトリ、セッションルール）
- `docs/DECISIONS.md`（確定した設計判断）
- `docs/HANDOFF_LATEST.md`（直前の作業状態）
- `docs/PROGRESS.md`（Phase進捗）

___

## プロジェクト情報

- リポジトリ: https://github.com/Fkzyk/japan-dog-map
- 公開URL: https://fkzyk.github.io/japan-dog-map/
- Supabase URL: https://rfcfilhqkkjmkecxzijw.supabase.co
- 構成: 静的サイト + Supabase + Google Maps + Service Worker + Vercel + GitHub Pages
- スポット数: 10,848件（places.json 静的配信）

___

## 現状把握（本番稼働中）

### UI機能

- 地図表示、クラスタリング、ポップアップ、現在地
- カテゴリフィルター（すべて/ドッグラン/飲食店/動物病院/宿泊/お気に入り）
- 検索・ジャンル絞り込み
- サイドパネルのスポット一覧
- 初回注意モーダル
- お知らせ機能
- チュートリアル（9ステップ）
- Service Worker

### ユーザー操作

- ★お気に入り（LocalStorage保存、将来Supabase化）
- 🐾行ったよ（Supabase稼働中）
- ★口コミ（Supabase稼働中、管理者承認フロー）
- 🚩問題を報告（Supabase稼働中）
- スポット追加（Supabase稼働中、管理者承認フロー）

### 運営機能

- 管理者ページ（/admin.html）Google OAuth + admin_users で保護済み
- 投稿審査・口コミ審査・削除依頼・スポット修正
- 利用統計・システム設定（Kill Switch）
- Kill Switch は system_flags テーブルで稼働中

### 既存テーブル

- spots
- submissions
- spot_reviews
- spot_overrides
- deletion_requests
- user_events（device_idベース）
- system_flags
- admin_users

### 既存RPC関数

- admin_get_submissions_v2
- admin_update_status_v2
- admin_update_submission_v2
- admin_delete_submission_v2
- admin_get_reviews_v2
- admin_update_review_status_v2
- admin_get_deletion_requests_v2
- admin_update_request_v2
- admin_get_overrides_v2
- admin_upsert_override_v2
- admin_delete_override_v2
- admin_update_system_flag_v2
- is_admin

___

## 全体ロードマップ

- Phase 1: 認証基盤（Anonymous Sign-Ins + Invisible Captcha）
- Phase 2: 既存機能の認証紐付け
- Phase 3: ゲーミフィケーション（バッジシステム）
- Phase 4: UX強化（LocalStorage全廃、PWA化）
- Phase 5: 運用強化（バックアップ、keep-alive、レート制限）
- Phase 6: 広告導入
- Phase 7: アカウント昇格導線（Google OAuth）

___

## Phase 1: 認証基盤

### Phase 1a: 事前調査

実装開始前に以下を確認しレポート出力する。

### コードベース調査

- device_id 生成処理の場所
- isFavorite() の実装と保存先
- onHelpfulClick（🐾行ったよ）実装箇所
- submitReview 実装箇所
- submitSpot 実装箇所
- submitReport 実装箇所
- チュートリアル完了フラグの保存先
- PWAプロンプト表示制御の実装箇所
- Service Worker のキャッシュ対象

### Supabase調査

- submissions.device_id カラムの有無
- spot_reviews.device_id カラムの有無
- user_events.device_id カラムの有無
- 現在のMAU・DB・Egress使用量
- Anonymous Sign-Ins の Dashboard 設定状況

### インフラ調査

- Google Maps API キーのドメイン制限設定
- 独自ドメイン取得状況
- Cloudflare アカウントの有無

### 出力

- 上記の調査結果をMarkdown形式で出力
- 認証導入で挙動が変わる箇所一覧
- マイグレーション戦略（device_id → auth.uid のバックフィル方針）

### Phase 1b: Supabase Dashboard設定

1. Authentication > Providers > Anonymous Sign-Ins を ON
2. Authentication > Rate Limits
   - Anonymous sign-ins: 10/hour/IP
3. Authentication > Attack Protection
   - Captcha Protection: ON
   - Provider: Cloudflare Turnstile

### Phase 1c: Cloudflare Turnstile設定

1. Cloudflare Dashboard でアカウント作成（無料）
2. Turnstile > Add site
   - Widget mode: Managed（invisible）
   - Domain: fkzyk.github.io
   - Domain: （Vercel URLがある場合）
3. Site key + Secret key を取得
4. Supabase Dashboard に Secret key を登録
5. Site key は index.html で使う

### Phase 1d: auth.js 実装

新規作成。

```javascript
const SUPABASE_URL = 'https://rfcfilhqkkjmkecxzijw.supabase.co';
const SUPABASE_ANON_KEY = 'xxxxx';

var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

async function getCurrentUser() {
  const { data: { user } } = await sb.auth.getUser();
  return user;
}

async function isAnonymous() {
  const user = await getCurrentUser();
  if (!user) return null;
  return user.is_anonymous === true;
}

async function ensureAuthenticated(captchaToken) {
  const existing = await getCurrentUser();
  if (existing) return existing;

  const flags = await getSystemFlags();
  if (!flags.allow_new_anonymous_auth) {
    throw new Error('NEW_AUTH_DISABLED');
  }

  if (!captchaToken) throw new Error('CAPTCHA_REQUIRED');

  const { data, error } = await sb.auth.signInAnonymously({
    options: { captchaToken },
  });

  if (error) {
    console.error('Anonymous sign-in failed', error);
    return null;
  }

  return data.user;
}

async function getSystemFlags() {
  const cached = sessionStorage.getItem('jdm-flags');
  if (cached) return JSON.parse(cached);

  const { data } = await sb.from('system_flags').select('*').single();
  sessionStorage.setItem('jdm-flags', JSON.stringify(data || {}));
  return data || {
    allow_new_anonymous_auth: true,
    allow_reviews: true,
    allow_helpfuls: true,
    allow_checkins: true,
    allow_spot_submission: true,
    allow_reports: true,
  };
}

async function requireAuth() {
  let user = await getCurrentUser();
  if (user) return user;

  const flags = await getSystemFlags();
  if (!flags.allow_new_anonymous_auth) {
    showToast('現在新規登録を停止しています');
    throw new Error('AUTH_DISABLED');
  }

  try {
    const token = await getTurnstileToken();
    user = await ensureAuthenticated(token);
    if (!user) throw new Error('AUTH_FAILED');
    return user;
  } catch (e) {
    if (e.message === 'CAPTCHA_ERROR') {
      showToast('認証に失敗しました。時間をおいて再度お試しください');
    }
    throw e;
  }
}
```

### Phase 1e: turnstile.js 実装（invisible mode）

```javascript
const TURNSTILE_SITE_KEY = 'xxxxx';

function loadTurnstileScript() {
  return new Promise((resolve) => {
    if (window.turnstile) return resolve();
    const s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.async = true;
    s.defer = true;
    s.onload = resolve;
    document.head.appendChild(s);
  });
}

async function getTurnstileToken() {
  await loadTurnstileScript();

  return new Promise((resolve, reject) => {
    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.left = '-9999px';
    document.body.appendChild(container);

    let widgetId;
    const timeout = setTimeout(() => {
      if (widgetId !== undefined) window.turnstile.remove(widgetId);
      container.remove();
      reject(new Error('CAPTCHA_TIMEOUT'));
    }, 10000);

    widgetId = window.turnstile.render(container, {
      sitekey: TURNSTILE_SITE_KEY,
      appearance: 'execute',
      callback: (token) => {
        clearTimeout(timeout);
        window.turnstile.remove(widgetId);
        container.remove();
        resolve(token);
      },
      'error-callback': () => {
        clearTimeout(timeout);
        window.turnstile.remove(widgetId);
        container.remove();
        reject(new Error('CAPTCHA_ERROR'));
      },
    });

    window.turnstile.execute(widgetId);
  });
}
```

___

## Phase 2: 既存機能の認証紐付け

### 改修方針

- 既存テーブルに user_id 列を追加（nullable、既存データ保持）
- RLS を auth.uid() ベースに変更
- 新規投稿は auth.uid() を紐付け
- device_id も並行運用（ゲーミフィケーション移行中のため）

### Phase 2a: お気に入りのSupabase化

新規テーブル作成。

```sql
CREATE TABLE spot_favorites (
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

100件上限トリガー。

```sql
CREATE OR REPLACE FUNCTION check_favorites_limit()
RETURNS TRIGGER AS $$
DECLARE
  cnt INTEGER;
BEGIN
  SELECT COUNT(*) INTO cnt FROM spot_favorites WHERE user_id = NEW.user_id;
  IF cnt >= 100 THEN
    RAISE EXCEPTION 'FAVORITES_LIMIT_REACHED';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_favorites_limit
  BEFORE INSERT ON spot_favorites
  FOR EACH ROW
  EXECUTE FUNCTION check_favorites_limit();
```

favorites.js の主要関数。

- getFavorites(): 認証済みならDB、未認証ならLocalStorageキャッシュ
- toggleFavorite(spotId): requireAuth → DB操作 → オプティミスティックUI
- isFavorite(spotId): 同期版キャッシュ参照
- migrateLocalFavorites(): 初回ログイン時にLocalStorageからDB移行

### Phase 2b〜2e: 既存テーブルへの user_id 追加

```sql
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE spot_reviews ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE deletion_requests ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE user_events ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON spot_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_user ON deletion_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON user_events(user_id);
```

既存のINSERT処理に user_id を追加する改修を行う。

対象関数。

- submitSpot（スポット投稿）
- onHelpfulClick（🐾行ったよ）
- submitReview（口コミ投稿）
- submitReport（問題報告）

改修例（submitSpot）。

```javascript
async function submitSpot() {
  let user;
  try {
    user = await requireAuth();
  } catch (e) {
    return;
  }

  const { error } = await sb.from('submissions').insert({
    user_id: user.id,
    device_id: getDeviceId(),
    name: name,
    category: category,
    address: address,
    comment: comment,
    lat: lat,
    lng: lng,
  });
}
```

device_id は並行運用期間中は継続して記録する。

___

## Phase 3: ゲーミフィケーション

### Phase 3a: achievementsテーブル + 初期バッジ投入

```sql
CREATE TABLE achievements (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL CHECK (category IN ('submission','visit','review','combo','special')),
  tier INTEGER NOT NULL DEFAULT 1,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  icon TEXT NOT NULL,
  threshold_type TEXT NOT NULL CHECK (threshold_type IN ('submit_count','visit_count','review_count','combo','special')),
  threshold_value INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "achievements_select_all"
  ON achievements FOR SELECT USING (is_active = true);

CREATE TABLE user_achievements (
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  achievement_id TEXT NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'provisional' CHECK (status IN ('provisional','confirmed')),
  unlocked_at TIMESTAMPTZ DEFAULT now(),
  confirmed_at TIMESTAMPTZ,
  PRIMARY KEY (user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);

ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ua_select_own"
  ON user_achievements FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "ua_no_direct_modify"
  ON user_achievements FOR ALL USING (false) WITH CHECK (false);
```

初期バッジ20件。

```sql
INSERT INTO achievements (id, category, tier, name, description, icon, threshold_type, threshold_value, sort_order) VALUES
('first_submit', 'submission', 1, 'はじめての一歩', '初めてスポットを投稿した', '🐾', 'submit_count', 1, 10),
('pioneer_3', 'submission', 2, '開拓者', '3件のスポットを投稿した', '🗺', 'submit_count', 3, 11),
('guide_10', 'submission', 3, '案内人', '10件のスポットを投稿した', '🧭', 'submit_count', 10, 12),
('guardian_30', 'submission', 4, '地域の守り神', '30件のスポットを投稿した', '⛩', 'submit_count', 30, 13),
('legend_50', 'submission', 5, '伝説の開拓者', '50件のスポットを投稿した', '👑', 'submit_count', 50, 14),
('first_visit', 'visit', 1, '犬散歩デビュー', '初めて行ったよを記録した', '🐕', 'visit_count', 1, 20),
('walker_10', 'visit', 2, '散歩好き', '10スポット訪問した', '🚶', 'visit_count', 10, 21),
('traveler_30', 'visit', 3, '旅犬', '30スポット訪問した', '🧳', 'visit_count', 30, 22),
('master_50', 'visit', 4, '全国お散歩マスター', '50スポット訪問した', '🏆', 'visit_count', 50, 23),
('master_100', 'visit', 5, '伝説のお散歩マスター', '100スポット訪問した', '💎', 'visit_count', 100, 24),
('first_review', 'review', 1, '語り部', '初めて口コミを書いた', '✍', 'review_count', 1, 30),
('critic_5', 'review', 2, '評論家', '5件の口コミを書いた', '📝', 'review_count', 5, 31),
('critic_10', 'review', 3, '熱心な評論家', '10件の口コミを書いた', '📖', 'review_count', 10, 32),
('critic_30', 'review', 4, '星の語り手', '30件の口コミを書いた', '⭐', 'review_count', 30, 33),
('triple_1', 'combo', 1, '三刀流', '投稿・訪問・口コミを1回ずつ達成', '🎯', 'combo', 1, 40),
('triple_5', 'combo', 2, '三刀流マスター', '投稿・訪問・口コミを5回ずつ達成', '🎖', 'combo', 5, 41),
('contributor_20', 'combo', 3, '全力ユーザー', '投稿・訪問・口コミ合計20件', '🔥', 'combo', 20, 42),
('evangelist', 'combo', 4, '伝道師', '投稿10件＋口コミ10件達成', '📣', 'combo', 100, 43);
```

### Phase 3b: RPC関数（4本）

get_my_achievements（自分のバッジ一覧取得）、check_and_unlock_achievements（イベント発生時に新規獲得バッジを返す）、confirm_achievements_on_approval（承認時に仮→確定）、revoke_achievements_on_rejection（却下時に取消）の4本をSECURITY DEFINERで実装。

具体的なSQL実装は HANDOFF に記録する。

### Phase 3c: バッジ獲得モーダル実装

index.html にモーダル + 紙吹雪アニメーション + SNSシェアボタンを追加。

- 紙吹雪アニメーション（CSS keyframes、2秒）
- 獲得バッジのアイコン・名前・説明表示
- 仮獲得には「（仮）」ラベル
- Xシェアボタン
- 閉じるボタン

### Phase 3d: 既存フックへの差し込み

- submitSpot 成功処理: check_and_unlock_achievements 呼び出し
- onHelpfulClick 成功処理: 同上（既存の口コミ誘導プロンプトとの優先順位調整）
- submitReview 成功処理: 同上

### Phase 3e: プロフィールモーダル

- ヘッダーに👤ボタン追加
- 投稿数・訪問数・口コミ数の表示
- 獲得済み/未獲得バッジ一覧
- 進捗バー表示

### Phase 3f: 管理者承認・却下連動

- admin.html の updateStatus 内に confirm_achievements_on_approval / revoke_achievements_on_rejection 呼び出しを追加
- 同様に updateReviewStatus にも追加

___

## Phase 4: UX強化

### Phase 4a: チュートリアル表示状態のDB化

既存のLocalStorage管理をSupabase管理に移行。

```sql
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  tutorial_completed_at TIMESTAMPTZ,
  pwa_prompt_last_shown_at TIMESTAMPTZ,
  pwa_prompt_shown_count INTEGER DEFAULT 0,
  caution_modal_hidden_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "prefs_select_own"
  ON user_preferences FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "prefs_upsert_own"
  ON user_preferences FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
```

### Phase 4b: PWAプロンプト制御

DB管理に移行。

- pwa_prompt_last_shown_at が30日以上前なら再表示
- インストール済み（standalone mode）なら表示しない
- 表示するたびに pwa_prompt_shown_count を増やす

### Phase 4c: 初回注意モーダル

DB管理に移行。

- caution_modal_hidden_until が今日より未来なら表示しない
- 「本日は表示しない」チェック時は翌日0時までhidden_untilを設定

### Phase 4d: manifest.json整備

既存の整備状況を確認し、PWAとしてインストール可能にする。

```json
{
  "name": "全国犬OKマップ",
  "short_name": "犬マップ",
  "start_url": "/japan-dog-map/",
  "display": "standalone",
  "theme_color": "#1a1a2e",
  "background_color": "#ffffff",
  "icons": [
    { "src": "favicon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "favicon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Phase 4e: ホーム画面追加バナー

- 2回目訪問以降に表示
- iOSは手動手順を説明
- Android/Chromeは beforeinstallprompt イベント利用

___

## Phase 5: 運用強化

### Phase 5a: GitHub Actions 日次バックアップ

.github/workflows/backup-supabase.yml を作成。

- 毎日18:00 UTC（JST 03:00）に pg_dump 実行
- GitHub Actions artifacts に30日分保存
- SUPABASE_DB_PASSWORD を Secrets に登録

### Phase 5b: GitHub Actions keep-alive Ping

.github/workflows/keepalive.yml を作成。

- 6時間ごとに Supabase に curl で ping
- 1週間pause対策

### Phase 5c: UptimeRobot登録

- 5分間隔でサイトping
- GitHub Actions と併用で冗長化

### Phase 5d: 信頼スコア自動承認（口コミ）

過去3件の承認実績があるユーザーの口コミを自動承認。

```sql
CREATE OR REPLACE FUNCTION auto_approve_trusted_reviews()
RETURNS TRIGGER AS $$
DECLARE
  approved_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO approved_count
  FROM spot_reviews
  WHERE user_id = NEW.user_id AND status = 'approved';

  IF approved_count >= 3 THEN
    NEW.status := 'approved';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_approve_reviews
  BEFORE INSERT ON spot_reviews
  FOR EACH ROW
  EXECUTE FUNCTION auto_approve_trusted_reviews();
```

### Phase 5e: 投稿レート制限

1日3件までに制限。

```sql
CREATE OR REPLACE FUNCTION check_review_rate_limit()
RETURNS TRIGGER AS $$
DECLARE
  recent_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO recent_count
  FROM spot_reviews
  WHERE user_id = NEW.user_id AND created_at > NOW() - INTERVAL '24 hours';

  IF recent_count >= 3 THEN
    RAISE EXCEPTION 'REVIEW_RATE_LIMIT';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_review_rate_limit
  BEFORE INSERT ON spot_reviews
  FOR EACH ROW
  EXECUTE FUNCTION check_review_rate_limit();
```

___

## Phase 6: 広告導入

### Phase 6a: 独自ドメイン取得

- AdSense審査で必須
- お名前ドットコム等で年1,500円程度
- .com、.jp、.xyz等から選択

### Phase 6b: 法務ページ作成

- プライバシーポリシー
- 利用規約
- お問い合わせページ

### Phase 6c: Cookie同意バナー

- 初回訪問時に表示
- 同意状態をLocalStorage（軽量データなのでこれはOK）または user_preferences に保存
- 不同意ユーザーには非パーソナライズ広告のみ

### Phase 6d: AdSense申請

- 独自ドメイン取得後に申請
- コンテンツ量・プライバシーポリシー・お問い合わせページが必要
- 審査期間1〜2週間

### Phase 6e: 広告枠実装

既存の ad-slot-map-bottom は設置済み。他3箇所を追加。

- 地図下部バナー（既存、有効化）
- サイドパネルリスト内ネイティブ広告（5件ごとに1件、PR表記）
- スポット詳細ポップアップ下部（カテゴリ連動）
- 投稿完了サンクスモーダル（ペット関連アフィリエイト）

### Phase 6f: アフィリエイトプログラム登録

- A8.net（ペット保険・ドッグフード）
- もしもアフィリエイト
- 楽天アフィリエイト

___

## Phase 7: アカウント昇格導線

お気に入り20件超過または口コミ3件投稿時にモーダル提案。

### Phase 7a: Google OAuth設定

- Supabase Dashboard で Google Provider 有効化
- OAuth Client ID 取得

### Phase 7b: マジックリンク設定

- Supabase Dashboard で Email Provider 設定
- テンプレートメールの文言調整

### Phase 7c: UI実装

- 「別端末でも使う」モーダル
- Googleで続ける（1タップ）
- メールで続ける（マジックリンク、補助）
- あとで（閉じる）

### Phase 7d: linkIdentity実装

```javascript
async function linkWithGoogle() {
  const { data, error } = await sb.auth.linkIdentity({
    provider: 'google',
    options: { redirectTo: window.location.origin },
  });
  if (error) throw error;
  return data;
}

async function linkWithEmail(email) {
  const { data, error } = await sb.auth.updateUser({ email });
  if (error) throw error;
  return data;
}
```

linkIdentity後も auth.uid は変わらない。既存データそのまま引き継ぎ。

___

## セキュリティチェックリスト

### 認証

- Anonymous Sign-In に Captcha 必須
- Rate limit 強化（10/hour/IP）
- Session duration 適切に設定
- redirectUrl 許可リスト設定

### RLS

- 全テーブル RLS 有効化
- 匿名ユーザーは自分のデータのみ操作可
- 公開読み取りは USING (true) で明示
- Service Role Key をクライアントに露出させない
- 口コミ削除は管理者のみ
- 報告閲覧は管理者のみ

### 管理者

- admin.html を Google OAuth 必須に（実装済み）
- admin_users テーブルで管理者定義（実装済み）
- admin 画面の操作ログ記録

### データ保護

- プライバシーポリシー整備
- 利用規約整備
- Cookie同意バナー実装
- 個人情報保護法対応
- GitHub Actions 日次バックアップ稼働

___

## 運用監視とKill Switch

### 定期監視

Supabase Dashboard で週1回確認。

- MAU: 40,000で警戒、45,000で対策開始
- DB Size: 400MBで警戒
- Egress: 4GBで警戒

### Kill Switch発動段階

MAU 45,000到達時点から。

- 段階1: allow_new_anonymous_auth = false
- 段階2: allow_reviews = false
- 段階3: allow_spot_submission = false
- 段階4: maintenance_mode = true

翌月MAUリセットで段階復旧。

___

## ユーザー体験の最終形

### 見るだけユーザー（大多数）

- 認証なし、MAUゼロ
- 地図・検索・スポット詳細を普通に閲覧
- 全員に広告表示

### お気に入り利用ユーザー

- 初回★タップで invisible Captcha 通過 + 匿名認証
- オプティミスティック UI で体感遅延ゼロ
- 100件まで保存可能

### 口コミ投稿ユーザー

- 投稿直後に自分だけ「承認待ち」バッジで見える
- 管理者承認後に全員に公開
- 3件承認されると以降自動承認

### アカウント昇格ユーザー（Phase 7以降）

- 1タップGoogle連携で端末引き継ぎ可能
- iOS 7日問題から守られる
- PWA化で追加保険

___

## 残存リスクと許容理由

- Google Maps API課金: 既存実装次第、Leaflet移行で解消可能
- 独自ドメイン年間費用: AdSense審査に必要、年1,500円程度
- iOS未昇格ユーザーの7日問題: 技術的に完全解決不可、昇格導線と PWA化 で緩和
- 50,000MAU超過: Kill Switchで段階縮退、翌月復旧
- Supabase仕様変更: Firebase、Cloudflare D1等への移行計画を頭の片隅に
- バックアップはGitHub Actions artifacts頼み: 30日以上古いデータは保持しない

___

## 実装時の重要ルール

- Phase の順番を守る
- 各Phase完了時にユーザーに動作確認してもらう
- 既存機能を壊していないか確認するテストを実行
- HANDOFF_LATEST.md を各作業後に更新
- DECISIONS.md に記載された判断は再議論しない
- CLAUDE.md のコミュニケーションルールに従う
