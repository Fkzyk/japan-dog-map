// Japan Dog Map - Service Worker
// キャッシュバージョン: デプロイ時に更新することで自動更新が走る
var CACHE_VERSION = 'v1';
var CACHE_NAME = 'japan-dog-map-' + CACHE_VERSION;

// キャッシュするリソース（アプリシェル）
var PRECACHE_URLS = [
  '/',
  '/index.html',
  '/news.json',
  '/favicon.ico'
];

// インストール時にアプリシェルをキャッシュ
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(PRECACHE_URLS);
    })
  );
});

// アクティベート時に古いキャッシュを削除
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) { return key !== CACHE_NAME; })
            .map(function(key) { return caches.delete(key); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

// フェッチ: ネットワークファースト（失敗時にキャッシュにフォールバック）
self.addEventListener('fetch', function(event) {
  // Supabase・Google Maps等の外部APIはキャッシュしない
  var url = event.request.url;
  if (url.indexOf('supabase.co') >= 0 ||
      url.indexOf('googleapis.com') >= 0 ||
      url.indexOf('unpkg.com') >= 0 ||
      url.indexOf('jsdelivr.net') >= 0) {
    return;
  }

  event.respondWith(
    fetch(event.request).then(function(response) {
      // 成功したレスポンスをキャッシュに保存
      if (response.ok) {
        var clone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, clone);
        });
      }
      return response;
    }).catch(function() {
      // ネットワーク失敗時はキャッシュから返す
      return caches.match(event.request);
    })
  );
});

// skipWaitingメッセージを受け取ったら即座に有効化
self.addEventListener('message', function(event) {
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
});
