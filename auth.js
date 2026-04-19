// ===== auth.js =====
// Lazy Anonymous Auth 基盤
// 書き込み操作（お気に入り・行ったよ・口コミ・投稿）の初回のみ認証発動
// 閲覧だけのユーザーは認証しない（MAU最小化）

var SUPABASE_URL      = 'https://rfcfilhqkkjmkecxzijw.supabase.co';
var SUPABASE_ANON_KEY = 'sb_publishable_6BlkQzDAGM7lyDnpRgMI8Q_4NHRR_lw';

// Supabaseクライアント（index.htmlから sb として参照）
var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

// 現在のログインユーザーを返す（未ログインはnull）
function getCurrentUser() {
  return sb.auth.getUser().then(function(result) {
    return result.data.user || null;
  });
}

// 匿名ユーザーかどうか判定
function isAnonymous() {
  return getCurrentUser().then(function(user) {
    if (!user) return null;
    return user.is_anonymous === true;
  });
}

// system_flags を取得（sessionStorageキャッシュあり）
function getSystemFlags() {
  var cached = sessionStorage.getItem('jdm-flags');
  if (cached) {
    try { return Promise.resolve(JSON.parse(cached)); } catch(e) {}
  }
  return sb.from('system_flags').select('*').eq('id', 1).single().then(function(result) {
    var flags = result.data || {};
    sessionStorage.setItem('jdm-flags', JSON.stringify(flags));
    return flags;
  });
}

// Lazy Anonymous Auth 本体
// 書き込み操作の直前に呼ぶ。ログイン済みならそのまま返す。未ログインなら匿名認証を発動。
function ensureAuthenticated(captchaToken) {
  return getCurrentUser().then(function(existing) {
    if (existing) return existing;

    return getSystemFlags().then(function(flags) {
      if (flags.allow_new_anonymous_auth === false) {
        throw new Error('NEW_AUTH_DISABLED');
      }
      if (!captchaToken) throw new Error('CAPTCHA_REQUIRED');

      return sb.auth.signInAnonymously({
        options: { captchaToken: captchaToken },
      }).then(function(result) {
        if (result.error) {
          console.error('匿名認証エラー:', result.error);
          return null;
        }
        return result.data.user;
      });
    });
  });
}

// requireAuth: 書き込み操作の入口
// Turnstileトークン取得 → 匿名認証 → ユーザーを返す
function requireAuth() {
  return getCurrentUser().then(function(user) {
    if (user) return user;

    return getSystemFlags().then(function(flags) {
      if (flags.allow_new_anonymous_auth === false) {
        if (typeof showToast === 'function') showToast('現在新規登録を停止しています');
        throw new Error('AUTH_DISABLED');
      }

      return getTurnstileToken().then(function(token) {
        return ensureAuthenticated(token);
      }).then(function(authedUser) {
        if (!authedUser) throw new Error('AUTH_FAILED');
        return authedUser;
      }).catch(function(e) {
        if (e.message === 'CAPTCHA_ERROR' || e.message === 'CAPTCHA_TIMEOUT') {
          if (typeof showToast === 'function') showToast('認証に失敗しました。時間をおいて再度お試しください');
        }
        throw e;
      });
    });
  });
}
