// ===== turnstile.js =====
// Cloudflare Turnstile Invisible Captcha
// 通常ユーザーには何も表示されない（Managed mode）
// VPN・Bot挙動の疑わしいアクセスのみチャレンジを表示

// Cloudflare Turnstile Site Key
// Phase 1c完了後に実際のキーに差し替える
var TURNSTILE_SITE_KEY = '0x4AAAAAAC_qmquU1n67PeMc';

// Turnstileスクリプトを動的に読み込む（初回のみ）
function loadTurnstileScript() {
  return new Promise(function(resolve) {
    if (window.turnstile) { resolve(); return; }
    var s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.async = true;
    s.defer = true;
    s.onload = resolve;
    document.head.appendChild(s);
  });
}

// Turnstileトークンを取得する（invisible mode）
// 通常ユーザーは即座にトークンが返る
// 疑わしいアクセスのみチャレンジ画面が出る
function getTurnstileToken() {
  return loadTurnstileScript().then(function() {
    return new Promise(function(resolve, reject) {
      // 画面外に非表示コンテナを設置
      var container = document.createElement('div');
      container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;';
      document.body.appendChild(container);

      var widgetId;
      // 10秒でタイムアウト
      var timeout = setTimeout(function() {
        if (widgetId !== undefined) window.turnstile.remove(widgetId);
        container.remove();
        reject(new Error('CAPTCHA_TIMEOUT'));
      }, 10000);

      widgetId = window.turnstile.render(container, {
        sitekey: TURNSTILE_SITE_KEY,
        appearance: 'execute',
        callback: function(token) {
          clearTimeout(timeout);
          window.turnstile.remove(widgetId);
          container.remove();
          resolve(token);
        },
        'error-callback': function() {
          clearTimeout(timeout);
          window.turnstile.remove(widgetId);
          container.remove();
          reject(new Error('CAPTCHA_ERROR'));
        },
      });

      // invisible modeで即座に実行
      window.turnstile.execute(widgetId);
    });
  });
}
