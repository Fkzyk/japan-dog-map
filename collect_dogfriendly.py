import requests
import json
import time

API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

AREA_CENTERS = [
    {"name": "千代田・中央", "lat": 35.6762, "lng": 139.7503, "radius": 4000},
    {"name": "港・渋谷", "lat": 35.6580, "lng": 139.7016, "radius": 4000},
    {"name": "新宿・中野", "lat": 35.6938, "lng": 139.7034, "radius": 4000},
    {"name": "文京・台東", "lat": 35.7081, "lng": 139.7524, "radius": 4000},
    {"name": "墨田・江東", "lat": 35.6900, "lng": 139.8100, "radius": 4000},
    {"name": "品川・大田", "lat": 35.6100, "lng": 139.7300, "radius": 5000},
    {"name": "目黒・世田谷", "lat": 35.6400, "lng": 139.6800, "radius": 5000},
    {"name": "杉並・練馬", "lat": 35.7000, "lng": 139.6400, "radius": 5000},
    {"name": "豊島・北", "lat": 35.7300, "lng": 139.7200, "radius": 4000},
    {"name": "荒川・足立", "lat": 35.7600, "lng": 139.7800, "radius": 5000},
    {"name": "葛飾・江戸川", "lat": 35.7300, "lng": 139.8700, "radius": 5000},
    {"name": "板橋・練馬西", "lat": 35.7600, "lng": 139.6500, "radius": 5000},
    {"name": "三鷹・武蔵野・調布", "lat": 35.6800, "lng": 139.5600, "radius": 5000},
    {"name": "府中・国分寺", "lat": 35.6700, "lng": 139.4800, "radius": 5000},
    {"name": "立川・昭島", "lat": 35.7000, "lng": 139.4100, "radius": 5000},
    {"name": "八王子", "lat": 35.6600, "lng": 139.3200, "radius": 6000},
    {"name": "町田", "lat": 35.5400, "lng": 139.4500, "radius": 5000},
    {"name": "多摩・稲城", "lat": 35.6300, "lng": 139.4400, "radius": 5000},
    {"name": "西東京・東久留米", "lat": 35.7300, "lng": 139.5400, "radius": 5000},
    {"name": "青梅・福生・羽村", "lat": 35.7800, "lng": 139.2500, "radius": 6000},
    {"name": "日野・東村山", "lat": 35.6700, "lng": 139.4000, "radius": 5000},
    {"name": "清瀬・東大和・武蔵村山", "lat": 35.7700, "lng": 139.5000, "radius": 5000},
    {"name": "あきる野・瑞穂", "lat": 35.7300, "lng": 139.2900, "radius": 6000},
]

# ドッグフレンドリーキーワード（施設名に含まれるもの）
DOGFRIENDLY_NAME_KEYWORDS = [
    'ドッグフレンドリー', 'dog friendly', 'Dog Friendly', 'DOG FRIENDLY',
    'dogfriendly', 'DogFriendly',
    'ペット可', 'ペットOK', 'ペットok', 'わんこok', 'わんこOK',
    'ペットフレンドリー', 'pet friendly', 'Pet Friendly',
    '犬連れ', '犬同伴', 'ドッグウェルカム', 'dog welcome',
    'わんちゃんok', 'わんちゃんOK', 'わんちゃん可',
]

# 検索キーワード
SEARCH_KEYWORDS = [
    'ドッグフレンドリーカフェ 東京',
    'ペット可カフェ 東京',
    'dog friendly cafe 東京',
    'ペット同伴可 レストラン 東京',
    '犬連れ カフェ 東京',
    '犬同伴可 カフェ 東京',
]

all_places = []
seen_ids = set()

def fetch_places_keyword(lat, lng, radius, keyword):
    places = []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": API_KEY,
        "language": "ja",
        "type": "cafe|restaurant|bar",
    }
    
    page = 0
    while page < 3:  # 最大3ページ（60件）
        resp = requests.get(url, params=params)
        data = resp.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            break
        
        for p in data.get("results", []):
            pid = p.get("place_id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                places.append({
                    "place_id": pid,
                    "name": p.get("name", ""),
                    "address": p.get("vicinity", ""),
                    "lat": p["geometry"]["location"]["lat"],
                    "lng": p["geometry"]["location"]["lng"],
                    "rating": p.get("rating", 0),
                    "user_ratings_total": p.get("user_ratings_total", 0),
                    "business_status": p.get("business_status", ""),
                    "category": "dogfriendly",
                })
        
        next_token = data.get("next_page_token")
        if not next_token:
            break
        page += 1
        time.sleep(2)
        params = {"pagetoken": next_token, "key": API_KEY}
    
    return places

print("ドッグフレンドリー施設の収集開始...")
for area in AREA_CENTERS:
    for kw in ['ドッグフレンドリー', 'ペット可 カフェ', '犬同伴可', 'dog friendly cafe']:
        places = fetch_places_keyword(area["lat"], area["lng"], area["radius"], kw)
        all_places.extend(places)
        time.sleep(0.3)
    print(f"  {area['name']}: 累計 {len(all_places)}件")

# 施設名にドッグフレンドリーキーワードが含まれるものだけに絞り込む
print(f"\n収集前総数: {len(all_places)}件")
filtered = []
for p in all_places:
    name_lower = p.get("name", "").lower()
    if any(kw.lower() in name_lower for kw in DOGFRIENDLY_NAME_KEYWORDS):
        filtered.append(p)

print(f"名称フィルタ後: {len(filtered)}件")

# 既存データ（ドッグラン・ドッグカフェ）と重複しないように保存
with open("/home/ubuntu/dogmap/places_dogfriendly.json", "w", encoding="utf-8") as f:
    json.dump(all_places, f, ensure_ascii=False)
print("places_dogfriendly.json に保存しました（全収集データ）")

with open("/home/ubuntu/dogmap/places_dogfriendly_filtered.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False)
print("places_dogfriendly_filtered.json に保存しました（名称フィルタ後）")
