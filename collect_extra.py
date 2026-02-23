import requests
import json
import time

API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"

# 追加エリア（日野・東村山・清瀬・東大和・武蔵村山・あきる野・瑞穂・羽村）
EXTRA_AREAS = [
    ("日野", 35.6714, 139.3953),
    ("東村山", 35.7547, 139.4685),
    ("清瀬", 35.7857, 139.5257),
    ("東大和", 35.7374, 139.4272),
    ("武蔵村山", 35.7547, 139.3904),
    ("あきる野", 35.7286, 139.2942),
    ("瑞穂", 35.7877, 139.3147),
    ("羽村", 35.7680, 139.3113),
]

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
    while page < 3:
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
            print("    クエリ制限。60秒待機...")
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
    name_lower = name.lower()
    dogrun_words = ["ドッグラン", "dogrun", "dog run", "dog park", "ドッグパーク",
                    "わんわん広場", "犬の広場", "犬の遊び場", "ドッグフィールド",
                    "dogfield", "dog field"]
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
    # 既存データを読み込む
    existing_ids = set()
    existing_data = []
    try:
        with open("/home/ubuntu/dogmap/places_final_v3.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_ids = {p["place_id"] for p in existing_data}
        print(f"既存データ読み込み: {len(existing_data)}件")
    except FileNotFoundError:
        print("既存データなし。新規作成します。")

    print(f"\n追加エリアの収集開始: {len(EXTRA_AREAS)}エリア")
    new_places = {}  # place_id -> (place_data, keyword)

    for area_name, lat, lng in EXTRA_AREAS:
        print(f"\n[エリア: {area_name} ({lat},{lng})]")
        for keyword in ALL_KEYWORDS:
            results = search_places(keyword, lat, lng)
            new_count = 0
            for place in results:
                place_id = place.get("place_id")
                addr = place.get("formatted_address", "")
                if place_id and place_id not in existing_ids and place_id not in new_places:
                    if any(p in addr for p in ["東京都", "神奈川県", "埼玉県", "千葉県"]):
                        new_places[place_id] = (place, keyword)
                        new_count += 1
            if new_count > 0:
                print(f"  [{keyword}] +{new_count}件 (新規累計: {len(new_places)}件)")
            time.sleep(0.3)

    print(f"\n追加収集完了。新規件数: {len(new_places)}件")
    print("詳細情報を取得中...")

    new_final = []
    for idx, (place_id, (place, keyword)) in enumerate(new_places.items()):
        if (idx + 1) % 20 == 0:
            print(f"  詳細取得: {idx+1}/{len(new_places)}件...")
        details = get_place_details(place_id)
        if not details:
            details = place
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
        new_final.append({
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

    # 既存データと結合
    all_final = existing_data + new_final
    dogruns = [p for p in all_final if p["category"] == "dogrun"]
    dogcafes = [p for p in all_final if p["category"] == "dogcafe"]

    print(f"\n最終合計: {len(all_final)}件")
    print(f"  ドッグラン: {len(dogruns)}件")
    print(f"  ドッグカフェ: {len(dogcafes)}件")
    print(f"  追加分: {len(new_final)}件")

    with open("/home/ubuntu/dogmap/places_final_v3.json", "w", encoding="utf-8") as f:
        json.dump(all_final, f, ensure_ascii=False, indent=2)

    print("\nデータを places_final_v3.json に更新しました。")

if __name__ == "__main__":
    main()
