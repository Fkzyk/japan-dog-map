import json

# データ読み込み
with open("/home/ubuntu/dogmap/places_data.json", "r", encoding="utf-8") as f:
    places = json.load(f)

print(f"総件数: {len(places)}")

# カテゴリ再判定（より精緻なルール）
def classify(place):
    name = place.get("name", "")
    name_lower = name.lower()
    types = place.get("types", [])
    
    # ドッグラン判定キーワード
    dogrun_keywords = [
        "ドッグラン", "dog run", "dogrun", "dog park", "dogpark",
        "わんわん広場", "犬の広場", "ドッグパーク", "dog field",
        "dog garden", "dog socialize", "dog town"
    ]
    
    # ドッグカフェ判定キーワード
    dogcafe_keywords = [
        "ドッグカフェ", "dog cafe", "dogcafe", "犬カフェ", "いぬカフェ",
        "サモエドカフェ", "豆柴カフェ", "ハスキーカフェ", "husky cafe",
        "大型犬カフェ", "保護犬カフェ", "わんこカフェ", "dog friendly",
        "dog dept", "dog heart", "dog cafe", "dog one", "wankoiwa",
        "にくきゅうカフェ", "犬茶屋", "いぬカフェ", "inucafe",
        "dalmatian cafe", "dog cafe", "ドッグカフェ"
    ]
    
    # ドッグラン優先チェック
    for kw in dogrun_keywords:
        if kw in name_lower:
            return "ドッグラン"
    
    # ドッグカフェチェック
    for kw in dogcafe_keywords:
        if kw in name_lower:
            return "ドッグカフェ"
    
    # 名前に「カフェ」「cafe」が含まれる場合
    if "カフェ" in name or "cafe" in name_lower or "coffee" in name_lower:
        # ただし動物病院・トリミングなどは除外
        if any(k in name for k in ["動物病院", "トリミング", "ペットホテル", "クリニック"]):
            return "その他"
        return "ドッグカフェ"
    
    # 公園系でドッグランが含まれる
    if "公園" in name and ("ドッグ" in name or "わんわん" in name or "犬" in name):
        return "ドッグラン"
    
    return "その他"

# 再分類
for place in places:
    place["category"] = classify(place)

# 「その他」の中で明らかにドッグラン・ドッグカフェに関係するものを確認
other_places = [p for p in places if p["category"] == "その他"]
print("\n--- 「その他」に分類されたもの ---")
for p in other_places:
    print(f"  {p['name']}")

# 東京都内（緯度35.5〜35.9、経度139.3〜139.9）に絞る
def is_in_tokyo(place):
    lat = place.get("lat", 0)
    lng = place.get("lng", 0)
    return 35.4 <= lat <= 35.9 and 138.9 <= lng <= 140.0

tokyo_places = [p for p in places if is_in_tokyo(p)]
print(f"\n東京都内の件数: {len(tokyo_places)}件")

# 「その他」を除外してドッグラン・ドッグカフェのみ残す
# ただし「その他」でも明らかに関連するものは手動で確認
final_places = [p for p in tokyo_places if p["category"] in ["ドッグラン", "ドッグカフェ"]]

# 「その他」の中で関連性が高いものを手動追加
related_other_names = [
    "BONDI COFFEE SANDWICHES",  # ドッグフレンドリーカフェ
    "GREEN DOG & CAT 代官山",   # ペット用品店+カフェ
    "MANDARINE BROTHERS直営店", # ペット用品
    "Park Community KIBACO",    # 公園コミュニティ
    "HOT DOG TOWN Ariake",      # ホットドッグ店（犬ではない）
    "HOGOKEN TOKYO",            # ドッグカフェ系
    "ドックラン エム 恵比寿",   # ドッグラン
    "Dog Friendly Café LUANA",  # ドッグカフェ
    "BLUE TERRACE 恵比寿店 シーシャ&ドッグカフェバー",  # ドッグカフェ
    "Tokyo Dog Club",           # ドッグ関連
    "Dog Cafe Bee",             # ドッグカフェ
    "DogCafeFlorence",          # ドッグカフェ
    "DogCafe & Hotel Green Wood", # ドッグカフェ
    "Dog cafe MOANA 白山店",    # ドッグカフェ
]

# 「その他」の中でドッグカフェ・ドッグランに関連するものを再分類
for place in tokyo_places:
    if place["category"] == "その他":
        name = place["name"]
        name_lower = name.lower()
        
        # 追加のドッグカフェキーワード
        if any(k in name_lower for k in ["dog cafe", "dog friendly", "dog club", "dogcafe"]):
            place["category"] = "ドッグカフェ"
        elif "ドックラン" in name or "dog run" in name_lower:
            place["category"] = "ドッグラン"
        elif name in related_other_names:
            if "ラン" in name or "run" in name_lower or "park" in name_lower:
                place["category"] = "ドッグラン"
            else:
                place["category"] = "ドッグカフェ"

# 最終フィルタリング
final_places = [p for p in tokyo_places if p["category"] in ["ドッグラン", "ドッグカフェ"]]

print(f"\n最終件数: {len(final_places)}件")

dog_run = [p for p in final_places if p["category"] == "ドッグラン"]
dog_cafe = [p for p in final_places if p["category"] == "ドッグカフェ"]

print(f"ドッグラン: {len(dog_run)}件")
print(f"ドッグカフェ: {len(dog_cafe)}件")

# 最終JSONを保存
output_path = "/home/ubuntu/dogmap/places_final.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_places, f, ensure_ascii=False, indent=2)

print(f"\n最終データを保存: {output_path}")

# サンプル表示
print("\n--- ドッグラン サンプル（先頭5件）---")
for p in dog_run[:5]:
    print(f"  {p['name']} | {p['address'][:30]}... | 評価:{p['rating']}")

print("\n--- ドッグカフェ サンプル（先頭5件）---")
for p in dog_cafe[:5]:
    print(f"  {p['name']} | {p['address'][:30]}... | 評価:{p['rating']}")
