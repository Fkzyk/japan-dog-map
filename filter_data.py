import json
from collections import Counter

with open('/home/ubuntu/dogmap/places.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"フィルタリング前: {len(data)}件")

# ドッグカフェカテゴリから除外するキーワード（名称に含まれる場合）
EXCLUDE_KEYWORDS_CAFE = [
    'トリミング', 'グルーミング', 'ペットホテル', '動物病院', 'ペットショップ',
    'ペット用品', 'ペットサロン', 'ドッグサロン', '保育園', 'スクール',
    'ペット保険', '獣医', 'クリニック', 'ホスピタル', 'アニマルホスピタル',
    'ペット霊園', '霊園', '葬儀', 'ペット葬', 'ペット火葬',
    'ペットシッター', 'ドッグシッター', 'ドッグトレーニング', 'トレーニングスクール',
    'ペットフード', 'ドッグフード', 'ペット薬局',
]

# ドッグランカテゴリから除外するキーワード
EXCLUDE_KEYWORDS_RUN = [
    'トリミング', 'グルーミング', 'ペットホテル', '動物病院', 'ペットショップ',
    'ペット用品', 'ペットサロン', 'ドッグサロン',
    '獣医', 'クリニック', 'ホスピタル', 'アニマルホスピタル',
    'ペット霊園', '霊園', '葬儀', 'ペット葬', 'ペット火葬',
    'ペットシッター', 'ドッグシッター',
    'ペットフード', 'ドッグフード', 'ペット薬局',
]

# ドッグカフェとして有効なキーワード（名称または種類に含まれる場合）
VALID_CAFE_KEYWORDS = [
    'カフェ', 'cafe', 'Cafe', 'CAFE', 'コーヒー', 'coffee', 'Coffee',
    'レストラン', 'restaurant', 'Restaurant', 'ダイニング', 'dining',
    'ビストロ', 'bistro', 'バー', 'bar', 'Bar', 'BAR',
    'ドッグカフェ', 'dog cafe', 'ドッグラン', 'dog run', 'dogrun',
    '犬カフェ', '犬と', 'わんこ', 'ワンコ', 'ペットカフェ',
    'ランチ', 'ディナー', 'ブランチ', 'テラス',
    'ドッグフレンドリー', 'ペットフレンドリー', 'ペット可',
    'ドッグパーク', 'わんわん', 'ワンワン',
]

# ドッグランとして有効なキーワード
VALID_RUN_KEYWORDS = [
    'ドッグラン', 'dog run', 'dogrun', 'Dog Run', 'DOG RUN',
    'ドッグパーク', 'dog park', 'Dog Park',
    'わんわん広場', '犬の広場', '犬広場', 'ドッグエリア',
    'ドッグガーデン', 'dog garden', 'ドッグスペース',
    'ドッグプレイ', 'ドッグフィールド', 'ドッグゾーン',
    '室内ドッグラン', '屋内ドッグラン', 'インドアドッグラン',
    'ドッグカフェ', 'カフェ', 'cafe', 'Cafe',  # ドッグランカフェ兼用
]

filtered = []
excluded = []

for place in data:
    name = place.get('name', '')
    category = place.get('category', '')
    types = place.get('types', [])
    
    if category == 'dogcafe':
        # 除外キーワードチェック
        should_exclude = any(kw in name for kw in EXCLUDE_KEYWORDS_CAFE)
        
        # ただし、除外キーワードがあっても有効キーワードも含む場合は残す
        # 例: 「ドッグランカフェ＆トリミング」はカフェ要素があるので残す
        has_valid = any(kw.lower() in name.lower() for kw in VALID_CAFE_KEYWORDS)
        
        if should_exclude and not has_valid:
            excluded.append({'name': name, 'reason': '除外キーワードのみ', 'category': category})
            continue
            
    elif category == 'dogrun':
        # ドッグランは除外キーワードのみの場合に除外
        should_exclude = any(kw in name for kw in EXCLUDE_KEYWORDS_RUN)
        has_valid = any(kw.lower() in name.lower() for kw in VALID_RUN_KEYWORDS)
        
        if should_exclude and not has_valid:
            excluded.append({'name': name, 'reason': '除外キーワードのみ', 'category': category})
            continue
    
    filtered.append(place)

print(f"フィルタリング後: {len(filtered)}件")
print(f"除外件数: {len(excluded)}件")
print("\n除外された施設（先頭30件）:")
for e in excluded[:30]:
    print(f"  [{e['category']}] {e['name']} ({e['reason']})")

# 除外されたカテゴリ分布
cat_counter = Counter(e['category'] for e in excluded)
print(f"\n除外カテゴリ分布: {dict(cat_counter)}")

# 保存
with open('/home/ubuntu/dogmap/places_filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"\nplaces_filtered.json に保存完了")
print(f"ドッグラン: {sum(1 for p in filtered if p['category']=='dogrun')}件")
print(f"ドッグカフェ: {sum(1 for p in filtered if p['category']=='dogcafe')}件")
