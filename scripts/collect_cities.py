'''#!/usr/bin/env python3
"""
Google Places API を使って指定したエリアのドッグラン・ドッグカフェ情報を収集する汎用スクリプト。

コマンドライン引数で収集対象のエリア（中心座標）、都道府県、APIキー、出力ファイルパスを指定できる。

使用例:
python collect_cities.py \
    --areas '[{"name": "札幌・中央区", "lat": 43.055, "lng": 141.34}, {"name": "札幌・北区", "lat": 43.08, "lng": 141.35}]' \
    --prefectures "北海道" \
    --api-key "YOUR_API_KEY" \
    --output "/home/ubuntu/dogmap/places_sapporo.json"
"""
import requests
import json
import time
import argparse

# 検索キーワード（固定）
DOGRUN_KEYWORDS = [
    "ドッグラン", "室内ドッグラン", "ドッグパーク", "dog run", "犬の遊び場 公園",
]
DOGCAFE_KEYWORDS = [
    "ドッグカフェ", "犬カフェ", "dog cafe", "犬同伴カフェ", "ペット可カフェ 犬", "わんこカフェ",
]
ALL_KEYWORDS = DOGRUN_KEYWORDS + DOGCAFE_KEYWORDS

def search_places(api_key, keyword, lat, lng, radius=5000):
    """Google Places Text Search APIで場所を検索（ページネーション対応・最大60件）"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": keyword,
        "location": f"{lat},{lng}",
        "radius": radius,
        "language": "ja",
        "key": api_key
    }

    all_results = []
    page = 0

    while page < 3:  # 最大3ページ（60件）まで取得
        try:
            response = requests.get(url, params=params, timeout=15)
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
            print(f"    APIエラー: {status} - {data.get('error_message', '')}")
            break

        results = data.get("results", [])
        all_results.extend(results)
        page += 1

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        time.sleep(2.5) # next_page_tokenが有効になるまでの待機
        params = {"pagetoken": next_page_token, "key": api_key}

    return all_results

def get_place_details(api_key, place_id):
    """Place IDから詳細情報を取得"""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total,opening_hours,website,formatted_phone_number,business_status,types",
        "language": "ja",
        "key": api_key
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception:
        pass
    return None

def classify_place(name, keyword_used):
    """場所をドッグランかドッグカフェに分類"""
    name_lower = name.lower()
    dogrun_words = ["ドッグラン", "dogrun", "dog run", "dog park", "ドッグパーク", "わんわん広場", "犬の広場", "犬の遊び場", "ドッグフィールド"]
    dogcafe_words = ["ドッグカフェ", "犬カフェ", "dog cafe", "dogcafe", "ペットカフェ", "犬同伴", "わんこカフェ", "いぬカフェ", "dog friendly"]

    for w in dogrun_words:
        if w.lower() in name_lower:
            return "dogrun"
    for w in dogcafe_words:
        if w.lower() in name_lower:
            return "dogcafe"

    # 名前で分類できない場合は使用したキーワードで判断
    if keyword_used in DOGRUN_KEYWORDS:
        return "dogrun"
    if keyword_used in DOGCAFE_KEYWORDS:
        return "dogcafe"

    return "dogrun" # デフォルト

def main(args):
    # 引数から設定を読み込む
    API_KEY = args.api_key
    try:
        AREA_CENTERS = json.loads(args.areas)
    except json.JSONDecodeError:
        print("エラー: --areas引数のJSON形式が正しくありません。")
        return
        
    TARGET_PREFECTURES = args.prefectures.split(',')
    output_path = args.output

    print(f"{len(TARGET_PREFECTURES)}都道府県のドッグラン・ドッグカフェ情報を収集します")
    print(f"エリア数: {len(AREA_CENTERS)}, キーワード数: {len(ALL_KEYWORDS)}")

    all_places = {}  # place_id -> (place_data, keyword)
    total_api_calls = 0

    for area in AREA_CENTERS:
        area_name, lat, lng = area['name'], area['lat'], area['lng']
        print(f"\n[エリア: {area_name} ({lat},{lng})]")

        for keyword in ALL_KEYWORDS:
            results = search_places(API_KEY, keyword, lat, lng)
            total_api_calls += 1

            new_count = 0
            for place in results:
                place_id = place.get("place_id")
                addr = place.get("formatted_address", "")
                if place_id and place_id not in all_places:
                    if any(p in addr for p in TARGET_PREFECTURES):
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

        details = get_place_details(API_KEY, place_id)
        if not details:
            details = place # 詳細取得失敗時は検索結果で代替

        if details.get("business_status") == "CLOSED_PERMANENTLY":
            continue

        name = details.get("name", "")
        address = details.get("formatted_address", place.get("formatted_address", ""))
        location = details.get("geometry", {}).get("location", {})
        lat_val, lng_val = location.get("lat"), location.get("lng")

        if not lat_val or not lng_val or not name:
            continue

        category = classify_place(name, keyword)
        weekday_text = details.get("opening_hours", {}).get("weekday_text", [])

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
            "source": "",
            "genre": "",
        })
        time.sleep(0.08)

    dogruns = [p for p in final_places if p["category"] == "dogrun"]
    dogcafes = [p for p in final_places if p["category"] == "dogcafe"]

    print(f"\n最終件数: {len(final_places)}件")
    print(f"  ドッグラン: {len(dogruns)}件")
    print(f"  ドッグカフェ: {len(dogcafes)}件")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_places, f, ensure_ascii=False, indent=2)

    print(f"\nデータを {output_path} に保存しました。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Places API を使って指定したエリアのドッグラン・ドッグカフェ情報を収集する汎用スクリプト")
    parser.add_argument(
        "--areas", 
        required=True, 
        help='収集対象エリアのJSON文字列。例: \'[{"name": "札幌・中央区", "lat": 43.055, "lng": 141.34}]\''
    )
    parser.add_argument(
        "--prefectures", 
        required=True, 
        help="対象都道府県のカンマ区切り文字列。例: '北海道,青森県'"
    )
    parser.add_argument(
        "--api-key", 
        required=True, 
        help="Google Maps APIキー"
    )
    parser.add_argument(
        "--output", 
        default="/home/ubuntu/dogmap/places_new_cities.json", 
        help="出力ファイルパス"
    )
    args = parser.parse_args()
    main(args)
'''''''
