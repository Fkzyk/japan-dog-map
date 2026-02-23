#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新データ（2368件）を使ってindex.htmlを再構築するスクリプト
"""
import json

# データ読み込み（営業中のみ）
with open('/home/ubuntu/dogmap/places_final_v3.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# 営業中のみフィルタリング
places = [d for d in raw_data if d.get('business_status') == 'OPERATIONAL']

# HTMLに埋め込む用にフィールドを整理
clean_places = []
for p in places:
    clean_places.append({
        'id': p.get('place_id', ''),
        'name': p.get('name', ''),
        'address': p.get('address', '').replace('日本、', ''),
        'lat': p.get('lat', 0),
        'lng': p.get('lng', 0),
        'rating': p.get('rating', 0),
        'user_ratings_total': p.get('user_ratings_total', 0),
        'website': p.get('website', ''),
        'phone': p.get('phone', ''),
        'opening_hours': p.get('opening_hours', []),
        'category': p.get('category', 'dogcafe'),
    })

places_json = json.dumps(clean_places, ensure_ascii=False)

dogrun_count = sum(1 for p in clean_places if p['category'] == 'dogrun')
dogcafe_count = sum(1 for p in clean_places if p['category'] == 'dogcafe')
total_count = len(clean_places)

print(f'ビルド対象: {total_count}件（ドッグラン{dogrun_count}件・ドッグカフェ{dogcafe_count}件）')

# HTMLテンプレートを生成
html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>東京ドッグマップ | ドッグラン・ドッグカフェ</title>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
      background: #f5f5f5;
      color: #333;
    }}
    header {{
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 100;
      height: 52px;
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .header-logo {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      object-fit: cover;
    }}
    .header-title {{
      font-size: 16px;
      font-weight: 700;
      color: #333;
    }}
    .header-count {{
      font-size: 12px;
      color: #888;
    }}
    .filter-bar {{
      position: fixed;
      top: 52px;
      left: 0;
      right: 0;
      z-index: 99;
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      padding: 8px 16px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    .filter-bar::-webkit-scrollbar {{ display: none; }}
    .filter-btn {{
      flex-shrink: 0;
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid #ddd;
      background: #fff;
      font-size: 13px;
      cursor: pointer;
      color: #555;
      transition: all 0.15s;
    }}
    .filter-btn.active {{
      background: #333;
      color: #fff;
      border-color: #333;
    }}
    .filter-btn.dogrun.active {{
      background: #2e7d32;
      border-color: #2e7d32;
    }}
    .filter-btn.dogcafe.active {{
      background: #c0392b;
      border-color: #c0392b;
    }}
    #map {{
      position: fixed;
      top: 96px;
      left: 0;
      right: 0;
      bottom: 0;
    }}
    #loading {{
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(255,255,255,0.95);
      padding: 20px 30px;
      border-radius: 12px;
      font-size: 14px;
      color: #555;
      z-index: 200;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }}
    /* ボトムシート */
    #bottom-sheet {{
      position: fixed;
      bottom: -100%;
      left: 0;
      right: 0;
      background: #fff;
      border-radius: 16px 16px 0 0;
      box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
      z-index: 150;
      transition: bottom 0.3s ease;
      max-height: 70vh;
      overflow-y: auto;
      padding: 0 0 env(safe-area-inset-bottom, 16px);
    }}
    #bottom-sheet.open {{
      bottom: 0;
    }}
    .sheet-handle {{
      width: 36px;
      height: 4px;
      background: #ddd;
      border-radius: 2px;
      margin: 10px auto 0;
    }}
    .sheet-content {{
      padding: 12px 16px 20px;
    }}
    .sheet-category {{
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 10px;
      margin-bottom: 6px;
    }}
    .sheet-category.dogrun {{
      background: #e8f5e9;
      color: #2e7d32;
    }}
    .sheet-category.dogcafe {{
      background: #fdecea;
      color: #c0392b;
    }}
    .sheet-name {{
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 4px;
      line-height: 1.3;
    }}
    .sheet-address {{
      font-size: 13px;
      color: #666;
      margin-bottom: 10px;
    }}
    .sheet-rating {{
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      margin-bottom: 10px;
    }}
    .stars {{
      color: #f4a100;
    }}
    .rating-count {{
      color: #888;
      font-size: 12px;
    }}
    .sheet-hours {{
      font-size: 12px;
      color: #555;
      margin-bottom: 10px;
      line-height: 1.6;
    }}
    .sheet-hours-title {{
      font-weight: 600;
      margin-bottom: 4px;
      font-size: 13px;
    }}
    .sheet-actions {{
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }}
    .sheet-btn {{
      flex: 1;
      padding: 10px;
      border-radius: 8px;
      border: none;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      text-align: center;
      display: block;
    }}
    .sheet-btn.primary {{
      background: #333;
      color: #fff;
    }}
    .sheet-btn.secondary {{
      background: #f0f0f0;
      color: #333;
    }}
    .sheet-btn.maps {{
      background: #4285f4;
      color: #fff;
    }}
    /* リスト表示ボタン */
    #list-toggle {{
      position: fixed;
      bottom: 24px;
      right: 16px;
      z-index: 120;
      background: #333;
      color: #fff;
      border: none;
      border-radius: 24px;
      padding: 10px 16px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    /* リストパネル */
    #list-panel {{
      position: fixed;
      bottom: -100%;
      left: 0;
      right: 0;
      background: #fff;
      border-radius: 16px 16px 0 0;
      box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
      z-index: 140;
      transition: bottom 0.3s ease;
      max-height: 75vh;
      display: flex;
      flex-direction: column;
    }}
    #list-panel.open {{
      bottom: 0;
    }}
    .list-header {{
      padding: 12px 16px 8px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }}
    .list-header-title {{
      font-size: 15px;
      font-weight: 700;
    }}
    .list-close {{
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
      color: #888;
      padding: 4px;
    }}
    #list-container {{
      overflow-y: auto;
      flex: 1;
      -webkit-overflow-scrolling: touch;
    }}
    .list-item {{
      padding: 12px 16px;
      border-bottom: 1px solid #f5f5f5;
      cursor: pointer;
      display: flex;
      align-items: flex-start;
      gap: 10px;
    }}
    .list-item:active {{
      background: #f9f9f9;
    }}
    .list-item-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-top: 5px;
      flex-shrink: 0;
    }}
    .list-item-dot.dogrun {{ background: #2e7d32; }}
    .list-item-dot.dogcafe {{ background: #c0392b; }}
    .list-item-info {{
      flex: 1;
      min-width: 0;
    }}
    .list-item-name {{
      font-size: 14px;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .list-item-address {{
      font-size: 12px;
      color: #888;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 2px;
    }}
    .list-item-rating {{
      font-size: 12px;
      color: #f4a100;
      margin-top: 2px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-left">
      <img src="favicon-32x32.png" alt="ぽんず" class="header-logo">
      <span class="header-title">東京ドッグマップ</span>
    </div>
    <span class="header-count" id="count-display">{total_count}件</span>
  </header>

  <div class="filter-bar">
    <button class="filter-btn active" onclick="setFilter('all', this)">すべて（{total_count}件）</button>
    <button class="filter-btn dogrun" onclick="setFilter('dogrun', this)">ドッグラン（{dogrun_count}件）</button>
    <button class="filter-btn dogcafe" onclick="setFilter('dogcafe', this)">ドッグカフェ（{dogcafe_count}件）</button>
  </div>

  <div id="map"></div>
  <div id="loading">地図を読み込み中...</div>

  <!-- ボトムシート（詳細） -->
  <div id="bottom-sheet">
    <div class="sheet-handle"></div>
    <div class="sheet-content" id="sheet-content"></div>
  </div>

  <!-- リスト表示ボタン -->
  <button id="list-toggle" onclick="toggleList()">
    <span>&#9776;</span> リスト
  </button>

  <!-- リストパネル -->
  <div id="list-panel">
    <div class="list-header">
      <span class="list-header-title" id="list-title">スポット一覧</span>
      <button class="list-close" onclick="toggleList()">&#10005;</button>
    </div>
    <div id="list-container"></div>
  </div>

  <script>
const PLACES_DATA = {places_json};

const CATEGORY_CONFIG = {{
  dogrun: {{ color: '#2e7d32', label: 'ドッグラン' }},
  dogcafe: {{ color: '#c0392b', label: 'ドッグカフェ' }}
}};

let map, infoWindow;
let markers = [];
let currentFilter = 'all';
let listOpen = false;

function initMap() {{
  map = new google.maps.Map(document.getElementById('map'), {{
    center: {{ lat: 35.6762, lng: 139.6503 }},
    zoom: 11,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false,
    styles: [
      {{ featureType: 'poi', elementType: 'labels', stylers: [{{ visibility: 'off' }}] }}
    ]
  }});
  infoWindow = new google.maps.InfoWindow();
  renderMarkers();
  renderList();
  document.getElementById('loading').style.display = 'none';
}}

function getFilteredPlaces() {{
  if (currentFilter === 'all') return PLACES_DATA;
  return PLACES_DATA.filter(p => p.category === currentFilter);
}}

function setFilter(filter, btn) {{
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderMarkers();
  renderList();
  closeBottomSheet();
}}

function renderMarkers() {{
  markers.forEach(m => m.marker.setMap(null));
  markers = [];
  const filtered = getFilteredPlaces();
  document.getElementById('count-display').textContent = filtered.length + '件';

  filtered.forEach(place => {{
    const config = CATEGORY_CONFIG[place.category] || CATEGORY_CONFIG['dogcafe'];
    const marker = new google.maps.Marker({{
      position: {{ lat: place.lat, lng: place.lng }},
      map: map,
      title: place.name,
      icon: {{
        path: google.maps.SymbolPath.CIRCLE,
        scale: 7,
        fillColor: config.color,
        fillOpacity: 0.9,
        strokeColor: '#fff',
        strokeWeight: 2
      }}
    }});
    marker.addListener('click', () => openBottomSheet(place.id));
    markers.push({{ marker, place }});
  }});
}}

function renderList() {{
  const filtered = getFilteredPlaces();
  const container = document.getElementById('list-container');
  const title = document.getElementById('list-title');
  title.textContent = `スポット一覧（${{filtered.length}}件）`;

  container.innerHTML = filtered.map(place => {{
    const config = CATEGORY_CONFIG[place.category] || CATEGORY_CONFIG['dogcafe'];
    const addr = place.address.replace(/^日本、/, '').replace(/〒\\d{{3}}-\\d{{4}}\\s*/, '');
    const stars = place.rating > 0 ? '★ ' + place.rating.toFixed(1) : '';
    return `<div class="list-item" onclick="focusPlace('${{escapeHtml(place.id)}}')">
      <div class="list-item-dot ${{place.category}}"></div>
      <div class="list-item-info">
        <div class="list-item-name">${{escapeHtml(place.name)}}</div>
        <div class="list-item-address">${{escapeHtml(addr)}}</div>
        ${{stars ? `<div class="list-item-rating">${{stars}}</div>` : ''}}
      </div>
    </div>`;
  }}).join('');
}}

function focusPlace(placeId) {{
  const item = markers.find(m => m.place.id === placeId);
  if (item) {{
    map.panTo(item.marker.getPosition());
    map.setZoom(15);
    toggleList();
    openBottomSheet(placeId);
  }}
}}

function openBottomSheet(placeId) {{
  const place = PLACES_DATA.find(p => p.id === placeId);
  if (!place) return;
  const config = CATEGORY_CONFIG[place.category] || CATEGORY_CONFIG['dogcafe'];
  const addr = place.address.replace(/^日本、/, '').replace(/〒\\d{{3}}-\\d{{4}}\\s*/, '');

  let starsHtml = '';
  if (place.rating > 0) {{
    const full = Math.floor(place.rating);
    const half = (place.rating - full) >= 0.5;
    let s = '';
    for (let i = 0; i < full; i++) s += '★';
    if (half) s += '☆';
    starsHtml = `<div class="sheet-rating"><span class="stars">${{s}}</span> <span>${{place.rating.toFixed(1)}}</span> <span class="rating-count">(${{place.user_ratings_total}}件)</span></div>`;
  }}

  let hoursHtml = '';
  if (place.opening_hours && place.opening_hours.length > 0) {{
    hoursHtml = `<div class="sheet-hours"><div class="sheet-hours-title">営業時間</div>${{place.opening_hours.map(h => `<div>${{escapeHtml(h)}}</div>`).join('')}}</div>`;
  }}

  let actionsHtml = `<a class="sheet-btn maps" href="https://www.google.com/maps/place/?q=place_id:${{place.id}}" target="_blank" rel="noopener">Google Mapsで開く</a>`;
  if (place.website) {{
    actionsHtml += `<a class="sheet-btn secondary" href="${{escapeHtml(place.website)}}" target="_blank" rel="noopener">公式サイト</a>`;
  }}

  document.getElementById('sheet-content').innerHTML = `
    <div class="sheet-category ${{place.category}}">${{config.label}}</div>
    <div class="sheet-name">${{escapeHtml(place.name)}}</div>
    <div class="sheet-address">${{escapeHtml(addr)}}</div>
    ${{starsHtml}}
    ${{place.phone ? `<div style="font-size:13px;color:#555;margin-bottom:8px;">&#128222; ${{escapeHtml(place.phone)}}</div>` : ''}}
    ${{hoursHtml}}
    <div class="sheet-actions">${{actionsHtml}}</div>
  `;
  document.getElementById('bottom-sheet').classList.add('open');
}}

function closeBottomSheet() {{
  document.getElementById('bottom-sheet').classList.remove('open');
}}

function toggleList() {{
  listOpen = !listOpen;
  document.getElementById('list-panel').classList.toggle('open', listOpen);
}}

function escapeHtml(str) {{
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}}

document.getElementById('map').addEventListener('click', closeBottomSheet);
document.getElementById('bottom-sheet').addEventListener('click', e => e.stopPropagation());
  </script>
  <script async defer
    src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBnuKUnr6GNYY1QbiL_evpkNv60TvLeGU4&callback=initMap&language=ja">
  </script>
</body>
</html>'''

with open('/home/ubuntu/dogmap/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'index.html を再構築しました（{total_count}件）')
print(f'ファイルサイズ: {len(html.encode("utf-8")) / 1024 / 1024:.1f} MB')
