import requests
import json
import time
import math

API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

# 東京エリアを格子状に分割するための座標グリッド
# 東京都全域（23区＋多摩地区）をカバー
# 緯度: 35.50 ~ 35.85, 経度: 138.95 ~ 139.95
# 各セルの半径: 5km（重複させて漏れを防ぐ）

def generate_grid():
    """東京都全域をカバーする格子状の座標リストを生成"""
    grid_points = []
    lat_start, lat_end = 35.50, 35.85
    lng_start, lng_end = 138.95, 139.95
    step_lat = 0.07  # 約7.7km
    step_lng = 0.09  # 約8km
    
    lat = lat_start
    while lat <= lat_end:
        lng = lng_start
        while lng <= lng_end:
            grid_points.append((round(lat, 4), round(lng, 4)))
            lng += step_lng
        lat += step_lat
    
    return grid_points

SEARCH_KEYWORDS = [
    "ドッグラン",
    "ドッグカフェ",
    "犬カフェ",
    "ペットカフェ 犬",
    "dog run 東京",
    "dog cafe 東京",
    "室内ドッグラン",
    "ドッグパーク",
    "犬同伴カフェ",
    "ペット可カフェ 犬",
    "わんわん広場",
    "犬の遊び場",
]

SEARCH_RADIUS = 6000  # 6km

def search_places_nearby(keyword, lat, lng):
    """Google Places Text Search APIで場所を検索する（ページネーション対応）"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": keyword,
        "location": f"{lat},{lng}",
        "radius": SEARCH_RADIUS,
        "language": "ja",
        "key": API_KEY
    }
    
    all_results = []
    
    while True:
        response = requests.get(url, params=params)
        data = response.json()
        
        status = data.get("status")
        if status == "ZERO_RESULTS":
            break
        if status not in ["OK"]:
            print(f"  APIエラー: {status} - {data.get('error_message', '')}")
            break
        
        results = data.get("results", [])
        all_results.extend(results)
        
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
        
        # next_page_tokenが有効になるまで待機
        time.sleep(2.5)
        params = {
            "pagetoken": next_page_token,
            "key": API_KEY
        }
    
    return all_results

def get_place_details(place_id):
    """Place IDから詳細情報を取得する"""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total,opening_hours,website,formatted_phone_number,business_status,types",
        "language": "ja",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") == "OK":
        return data.get("result", {})
    return None

def classify_place(name, types, keywords_used):
    """場所をドッグランかドッグカフェに分類する"""
    name_lower = name.lower()
    
    dogrun_keywords = ["ドッグラン", "dogrun", "dog run", "dog park", "ドッグパーク", 
                       "わんわん広場", "犬の広場", "犬の遊び場", "ドッグフィールド",
                       "dogfield", "dog field"]
    dogcafe_keywords = ["ドッグカフェ", "犬カフェ", "dog cafe", "dogcafe", "ペットカフェ",
                        "犬同伴", "わんこカフェ", "いぬカフェ"]
    
    for kw in dogrun_keywords:
        if kw.lower() in name_lower:
            return "dogrun"
    
    for kw in dogcafe_keywords:
        if kw.lower() in name_lower:
            return "dogcafe"
    
    # キーワードから推測
    if any(kw in keywords_used for kw in ["ドッグラン", "dog run 東京", "室内ドッグラン", "ドッグパーク", "わんわん広場", "犬の遊び場"]):
        return "dogrun"
    if any(kw in keywords_used for kw in ["ドッグカフェ", "犬カフェ", "ペットカフェ 犬", "dog cafe 東京", "犬同伴カフェ", "ペット可カフェ 犬"]):
        return "dogcafe"
    
    return "dogrun"  # デフォルト

def is_in_tokyo_area(address):
    """住所が東京都または近隣エリアかチェック"""
    tokyo_prefectures = ["東京都", "神奈川県", "埼玉県", "千葉県"]
    for pref in tokyo_prefectures:
        if pref in address:
            return True
    return False

def main():
    print("東京エリアのドッグラン・ドッグカフェ情報を収集します...")
    
    grid_points = generate_grid()
    print(f"グリッドポイント数: {len(grid_points)}")
    print(f"検索キーワード数: {len(SEARCH_KEYWORDS)}")
    print(f"総検索回数（最大）: {len(grid_points) * len(SEARCH_KEYWORDS)}")
    
    all_places = {}  # place_id をキーにして重複排除
    keyword_map = {}  # place_id -> keyword
    
    total_searches = 0
    
    for i, (lat, lng) in enumerate(grid_points):
        for keyword in SEARCH_KEYWORDS:
            total_searches += 1
            if total_searches % 20 == 0:
                print(f"  進捗: {total_searches}回目の検索... 現在{len(all_places)}件収集済み")
            
            results = search_places_nearby(keyword, lat, lng)
            
            for place in results:
                place_id = place.get("place_id")
                if place_id and place_id not in all_places:
                    address = place.get("formatted_address", "")
                    if is_in_tokyo_area(address):
                        all_places[place_id] = place
                        keyword_map[place_id] = keyword
            
            time.sleep(0.3)  # API制限対策
    
    print(f"\n収集完了。ユニーク件数: {len(all_places)}件")
    print("詳細情報を取得中...")
    
    final_places = []
    for idx, (place_id, place) in enumerate(all_places.items()):
        if idx % 50 == 0:
            print(f"  詳細取得: {idx}/{len(all_places)}件...")
        
        details = get_place_details(place_id)
        if not details:
            details = place
        
        # 営業中かどうかチェック
        business_status = details.get("business_status", "OPERATIONAL")
        if business_status == "CLOSED_PERMANENTLY":
            continue
        
        name = details.get("name", "")
        address = details.get("formatted_address", place.get("formatted_address", ""))
        geometry = details.get("geometry", place.get("geometry", {}))
        location = geometry.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        
        if not lat or not lng or not name:
            continue
        
        keyword_used = keyword_map.get(place_id, "")
        category = classify_place(name, details.get("types", []), keyword_used)
        
        opening_hours = details.get("opening_hours", {})
        weekday_text = opening_hours.get("weekday_text", [])
        
        place_data = {
            "place_id": place_id,
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng,
            "rating": details.get("rating"),
            "user_ratings_total": details.get("user_ratings_total"),
            "website": details.get("website", ""),
            "phone": details.get("formatted_phone_number", ""),
            "opening_hours": weekday_text,
            "business_status": business_status,
            "category": category,
            "types": details.get("types", [])
        }
        
        final_places.append(place_data)
        time.sleep(0.1)
    
    # カテゴリ別集計
    dogruns = [p for p in final_places if p["category"] == "dogrun"]
    dogcafes = [p for p in final_places if p["category"] == "dogcafe"]
    
    print(f"\n最終件数: {len(final_places)}件")
    print(f"  ドッグラン: {len(dogruns)}件")
    print(f"  ドッグカフェ: {len(dogcafes)}件")
    
    # 保存
    with open("/home/ubuntu/dogmap/places_final_v2.json", "w", encoding="utf-8") as f:
        json.dump(final_places, f, ensure_ascii=False, indent=2)
    
    print("\nデータを places_final_v2.json に保存しました。")

if __name__ == "__main__":
    main()
