import json

# データ読み込み
with open("/home/ubuntu/dogmap/places_final.json", "r", encoding="utf-8") as f:
    places = json.load(f)

# HTMLテンプレート読み込み
with open("/home/ubuntu/dogmap/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# JSONデータをHTMLに埋め込む
places_json = json.dumps(places, ensure_ascii=False)
html = html.replace("PLACES_JSON_PLACEHOLDER", places_json)

# 出力
with open("/home/ubuntu/dogmap/index_built.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"ビルド完了: {len(places)}件のデータを埋め込みました")
print("出力: /home/ubuntu/dogmap/index_built.html")
