import requests
import json
import time

API_KEY = "AIzaSyBnuKUnr6GNYY1QbiL_evpkNv60TvLeGU4"

# 東京の主要エリア中心座標（23区＋多摩地区の主要スポット）
# 半径5kmで重複カバー
AREA_CENTERS = [
    # 23区 東部
    ("千代田・中央", 35.6895, 139.6917),
    ("台東・墨田", 35.7090, 139.7980),
    ("江東", 35.6730, 139.8170),
    ("江戸川", 35.7070, 139.8680),
    ("葛飾", 35.7440, 139.8470),
    ("足立", 35.7750, 139.8040),
    ("荒川・北", 35.7380, 139.7730),
    # 23区 西部
    ("新宿・渋谷", 35.6900, 139.7000),
    ("港・品川", 35.6450, 139.7400),
    ("目黒・世田谷東", 35.6430, 139.6980),
    ("世田谷西・杉並", 35.6570, 139.6400),
    ("中野・練馬", 35.7080, 139.6640),
    ("板橋・豊島", 35.7380, 139.6900),
    ("文京・豊島南", 35.7180, 139.7330),
    ("大田", 35.5980, 139.7160),
    # 多摩地区
    ("三鷹・武蔵野", 35.7030, 139.5600),
    ("調布・府中", 35.6620, 139.5440),
    ("立川・昭島", 35.6980, 139.4130),
    ("八王子", 35.6660, 139.3160),
    ("町田", 35.5430, 139.4460),
    ("多摩・稲城", 35.6360, 139.4770),
    ("西東京・東久留米", 35.7270, 139.5380),
    ("青梅・福生", 35.7870, 139.2480),
]

# 検索キーワード（ドッグラン系・ドッグカフェ系に分けて精度向上）
DOGRUN_KEYWORDS = [
    "ドッグラン",
    "室内ドッグラン",
    "ドッグパーク",
    "dog run",
    "わんわん広場",
    "犬の遊び場 公園",
]

DOGCAFE_KEYWORDS = [
    "ドッグカフェ",
    "犬カフェ",
    "dog cafe",
    "犬同伴カフェ",
    "ペット可カフェ 犬",
    "いぬカフェ",
    "わんこカフェ",
]

ALL_KEYWORDS = DOGRUN_KEYWORDS + DOGCAFE_KEYWORDS

def search_places(keyword, lat, lng, radius=5000):
    """Google Places Text Search APIで場所を検索（ページネーション対応・最大60件）"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": keyword,
        "location": f"{lat},{lng}",
        "radius": radius,
        "language": "ja",
        "key": API_KEY
    }
    
    all_results = []
    page = 0
    
    while page < 3:  # 最大3ページ（60件）
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
        except Exception as e:
            print(f"    リクエストエラー: {e}")
            break
        
        status = data.get("status")
        if status == "ZERO_RESULTS":
            break
        if status == "OVER_QUERY_LIMIT":
            print("    クエリ制限に達しました。60秒待機...")
            time.sleep(60)
            continue
        if status not in ["OK"]:
            break
        
        results = data.get("results", [])
        all_results.extend(results)
        page += 1
        
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
        
        time.sleep(2.5)
        params = {"pagetoken": next_page_token, "key": API_KEY}
    
    return all_results

def get_place_details(place_id):
    """Place IDから詳細情報を取得"""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total,opening_hours,website,formatted_phone_number,business_status,types",
        "language": "ja",
        "key": API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception:
        pass
    return None

def classify_place(name, keyword_used):
    """場所をドッグランかドッグカフェに分類"""
    name_lower = name.lower()
    
    dogrun_words = ["ドッグラン", "dogrun", "dog run", "dog park", "ドッグパーク",
                    "わんわん広場", "犬の広場", "犬の遊び場", "ドッグフィールド",
                    "dogfield", "dog field", "ドッグパーク"]
    dogcafe_words = ["ドッグカフェ", "犬カフェ", "dog cafe", "dogcafe", "ペットカフェ",
                     "犬同伴", "わんこカフェ", "いぬカフェ", "豆柴カフェ", "サモエドカフェ",
                     "大型犬カフェ", "ハスキーカフェ", "husky cafe", "dog friendly"]
    
    for w in dogrun_words:
        if w.lower() in name_lower:
            return "dogrun"
    for w in dogcafe_words:
        if w.lower() in name_lower:
            return "dogcafe"
    
    if keyword_used in DOGRUN_KEYWORDS:
        return "dogrun"
    if keyword_used in DOGCAFE_KEYWORDS:
        return "dogcafe"
    
    return "dogrun"

def main():
    print("東京エリアのドッグラン・ドッグカフェ情報を収集します（v3）")
    print(f"エリア数: {len(AREA_CENTERS)}, キーワード数: {len(ALL_KEYWORDS)}")
    
    all_places = {}  # place_id -> (place_data, keyword)
    total_api_calls = 0
    
    for area_name, lat, lng in AREA_CENTERS:
        print(f"\n[エリア: {area_name} ({lat},{lng})]")
        area_count = 0
        
        for keyword in ALL_KEYWORDS:
            results = search_places(keyword, lat, lng)
            total_api_calls += 1
            
            new_count = 0
            for place in results:
                place_id = place.get("place_id")
                addr = place.get("formatted_address", "")
                # 東京都・近隣県のみ
                if place_id and place_id not in all_places:
                    if any(p in addr for p in ["東京都", "神奈川県", "埼玉県", "千葉県"]):
                        all_places[place_id] = (place, keyword)
                        new_count += 1
            
            if new_count > 0:
                print(f"  [{keyword}] +{new_count}件 (累計: {len(all_places)}件)")
            
            time.sleep(0.3)
        
        print(f"  エリア小計: {len(all_places)}件")
    
    print(f"\n収集完了。ユニーク件数: {len(all_places)}件")
    print(f"API呼び出し回数: {total_api_calls}回")
    print("\n詳細情報を取得中...")
    
    final_places = []
    for idx, (place_id, (place, keyword)) in enumerate(all_places.items()):
        if (idx + 1) % 30 == 0:
            print(f"  詳細取得: {idx+1}/{len(all_places)}件...")
        
        details = get_place_details(place_id)
        if not details:
            details = place
        
        # 永久閉業はスキップ
        if details.get("business_status") == "CLOSED_PERMANENTLY":
            continue
        
        name = details.get("name", "")
        address = details.get("formatted_address", place.get("formatted_address", ""))
        geometry = details.get("geometry", place.get("geometry", {}))
        location = geometry.get("location", {})
        lat_val = location.get("lat")
        lng_val = location.get("lng")
        
        if not lat_val or not lng_val or not name:
            continue
        
        category = classify_place(name, keyword)
        opening_hours = details.get("opening_hours", {})
        weekday_text = opening_hours.get("weekday_text", [])
        
        final_places.append({
            "place_id": place_id,
            "name": name,
            "address": address,
            "lat": lat_val,
            "lng": lng_val,
            "rating": details.get("rating"),
            "user_ratings_total": details.get("user_ratings_total"),
            "website": details.get("website", ""),
            "phone": details.get("formatted_phone_number", ""),
            "opening_hours": weekday_text,
            "business_status": details.get("business_status", "OPERATIONAL"),
            "category": category,
        })
        time.sleep(0.08)
    
    dogruns = [p for p in final_places if p["category"] == "dogrun"]
    dogcafes = [p for p in final_places if p["category"] == "dogcafe"]
    
    print(f"\n最終件数: {len(final_places)}件")
    print(f"  ドッグラン: {len(dogruns)}件")
    print(f"  ドッグカフェ: {len(dogcafes)}件")
    
    with open("/home/ubuntu/dogmap/places_final_v3.json", "w", encoding="utf-8") as f:
        json.dump(final_places, f, ensure_ascii=False, indent=2)
    
    print("\nデータを places_final_v3.json に保存しました。")

if __name__ == "__main__":
    main()
