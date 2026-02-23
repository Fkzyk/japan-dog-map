import requests
import json
import time

API_KEY = "AIzaSyBnuKUnr6GNYY1QbiL_evpkNv60TvLeGU4"

# 東京エリアの中心座標と検索半径
TOKYO_CENTER = "35.6762,139.6503"
RADIUS = 30000  # 30km（東京都全域をカバー）

def search_places(query, location, radius):
    """Google Places Text Search APIで場所を検索する"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "language": "ja",
        "key": API_KEY
    }
    
    all_results = []
    
    while True:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            print(f"APIエラー: {data.get('status')} - {data.get('error_message', '')}")
            break
        
        results = data.get("results", [])
        all_results.extend(results)
        print(f"  取得: {len(results)}件 (累計: {len(all_results)}件)")
        
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
        
        # next_page_tokenが有効になるまで待機
        time.sleep(2)
        params = {
            "pagetoken": next_page_token,
            "key": API_KEY
        }
    
    return all_results

def get_place_details(place_id):
    """Google Places Details APIで詳細情報を取得する"""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,geometry,rating,user_ratings_total,business_status,types",
        "language": "ja",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") == "OK":
        return data.get("result", {})
    else:
        print(f"詳細取得エラー ({place_id}): {data.get('status')}")
        return None

def main():
    print("=== 東京エリア ドッグラン・ドッグカフェ情報収集 ===\n")
    
    # 検索クエリ
    queries = [
        "東京 ドッグラン",
        "東京 ドッグカフェ",
        "東京 犬カフェ",
        "東京 ペットカフェ 犬",
        "東京 dog run",
        "東京 dog cafe",
    ]
    
    all_place_ids = set()
    raw_results = []
    
    for query in queries:
        print(f"検索中: {query}")
        results = search_places(query, TOKYO_CENTER, RADIUS)
        for r in results:
            pid = r.get("place_id")
            if pid and pid not in all_place_ids:
                all_place_ids.add(pid)
                raw_results.append(r)
        time.sleep(1)
    
    print(f"\n重複除去後の総件数: {len(raw_results)}件")
    print("\n詳細情報を取得中...")
    
    places = []
    for i, result in enumerate(raw_results):
        place_id = result.get("place_id")
        print(f"  [{i+1}/{len(raw_results)}] {result.get('name', '不明')}")
        
        details = get_place_details(place_id)
        if not details:
            continue
        
        # 営業中かどうかを確認（CLOSED_PERMANENTLYは除外）
        business_status = details.get("business_status", "")
        if business_status == "CLOSED_PERMANENTLY":
            print(f"    -> 閉業済みのためスキップ")
            continue
        
        # 座標取得
        geometry = details.get("geometry", {})
        location = geometry.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        
        if not lat or not lng:
            continue
        
        # カテゴリ判定
        name = details.get("name", "")
        types = details.get("types", [])
        
        category = "その他"
        name_lower = name.lower()
        if any(k in name_lower for k in ["ドッグラン", "dog run", "dogrun"]):
            category = "ドッグラン"
        elif any(k in name_lower for k in ["ドッグカフェ", "dog cafe", "dogcafe", "犬カフェ", "いぬカフェ"]):
            category = "ドッグカフェ"
        elif any(k in name_lower for k in ["カフェ", "cafe", "coffee", "コーヒー"]):
            category = "ドッグカフェ"
        elif "park" in name_lower or "公園" in name:
            category = "ドッグラン"
        
        # 営業時間
        opening_hours = details.get("opening_hours", {})
        weekday_text = opening_hours.get("weekday_text", [])
        hours_str = " / ".join(weekday_text) if weekday_text else "情報なし"
        
        place_data = {
            "id": place_id,
            "name": name,
            "address": details.get("formatted_address", ""),
            "phone": details.get("formatted_phone_number", ""),
            "website": details.get("website", ""),
            "lat": lat,
            "lng": lng,
            "rating": details.get("rating", 0),
            "user_ratings_total": details.get("user_ratings_total", 0),
            "business_status": business_status,
            "opening_hours": weekday_text,
            "category": category,
        }
        
        places.append(place_data)
        time.sleep(0.1)
    
    print(f"\n有効な場所の件数: {len(places)}件")
    
    # JSONとして保存
    output_path = "/home/ubuntu/dogmap/places_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    
    print(f"\nデータを保存しました: {output_path}")
    
    # カテゴリ別集計
    dog_run = [p for p in places if p["category"] == "ドッグラン"]
    dog_cafe = [p for p in places if p["category"] == "ドッグカフェ"]
    other = [p for p in places if p["category"] == "その他"]
    
    print(f"\n--- カテゴリ別集計 ---")
    print(f"ドッグラン: {len(dog_run)}件")
    print(f"ドッグカフェ: {len(dog_cafe)}件")
    print(f"その他: {len(other)}件")

if __name__ == "__main__":
    main()
