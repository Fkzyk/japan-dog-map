#!/usr/bin/env python3.11
"""
places.json を Supabase の places テーブルにインポートするスクリプト
"""
import json
import os
import requests
import time

# キーは環境変数から読み込む（.envファイルに設定するか export SUPABASE_SERVICE_KEY=... を実行）
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rfcfilhqkkjmkecxzijw.supabase.co")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY")
if not SERVICE_KEY:
    raise RuntimeError("環境変数 SUPABASE_SERVICE_KEY が設定されていません。.env ファイルを確認してください。")

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

BATCH_SIZE = 100


def load_places():
    with open("/home/ubuntu/dogmap/places.json", encoding="utf-8") as f:
        return json.load(f)


def transform_record(item):
    """places.json の各レコードを DB スキーマに合わせて変換する"""
    return {
        "place_id": item.get("place_id", ""),
        "name": item.get("name", ""),
        "address": item.get("address", ""),
        "lat": item.get("lat"),
        "lng": item.get("lng"),
        "rating": item.get("rating"),
        "user_ratings_total": item.get("user_ratings_total"),
        "website": item.get("website", ""),
        "phone": item.get("phone", ""),
        "opening_hours": item.get("opening_hours"),  # JSONB
        "business_status": item.get("business_status", "OPERATIONAL"),
        "category": item.get("category", ""),
        "source": item.get("source", ""),
        "genre": item.get("genre", ""),
    }


def insert_batch(records):
    url = f"{SUPABASE_URL}/rest/v1/places"
    resp = requests.post(url, headers=HEADERS, json=records, timeout=30)
    return resp.status_code, resp.text


def main():
    places = load_places()
    print(f"Total records: {len(places)}")

    # 重複を除去 (place_id で)
    seen = set()
    unique = []
    for item in places:
        pid = item.get("place_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(item)
    print(f"Unique records: {len(unique)}")

    records = [transform_record(item) for item in unique]

    success = 0
    errors = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        status, text = insert_batch(batch)
        if status in (200, 201):
            success += len(batch)
            print(f"  [{i+len(batch)}/{len(records)}] OK")
        else:
            errors += len(batch)
            print(f"  [{i+len(batch)}/{len(records)}] ERROR {status}: {text[:200]}")
            # エラー時は少し待ってリトライ
            time.sleep(2)
            status2, text2 = insert_batch(batch)
            if status2 in (200, 201):
                success += len(batch)
                errors -= len(batch)
                print(f"    Retry OK")
            else:
                print(f"    Retry FAILED: {text2[:200]}")

    print(f"\nDone. success={success}, errors={errors}")


if __name__ == "__main__":
    main()
