import json
from collections import Counter

with open('/home/ubuntu/dogmap/places_filtered.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"フィルタリング前: {len(data)}件")

# 明確に除外すべきキーワード（名称に含まれる場合）
HARD_EXCLUDE = [
    'トリミング', 'グルーミング', 'ペットホテル', 'ペットサロン', 'ドッグサロン',
    'ペットシッター', 'ドッグシッター', 'ペット保険',
    'ドッグトレーニング', 'しつけ教室', 'しつけスクール',
    '動物病院', '獣医', 'アニマルホスピタル',
    'ペット霊園', '霊園', 'ペット葬', 'ペット火葬', '動物葬',
    'ペットショップ', 'ペット用品', 'ドッグフード', 'ペットフード',
    '保育園', '訓練所',
]

# ドッグカフェとして有効と判断するキーワード
VALID_CAFE = [
    'カフェ', 'cafe', 'coffee', 'コーヒー', '珈琲',
    'レストラン', 'restaurant', 'ダイニング', 'dining',
    'ビストロ', 'bistro', 'バー', 'bar', 'ランチ', 'ディナー',
    'テラス', 'terrace', 'ドッグカフェ', '犬カフェ', 'いぬカフェ', 'ペットカフェ',
    'ドッグラン', 'dog run', 'dogrun', 'ドッグパーク', 'dog park',
    'わんこ', 'ワンコ', 'わんわん', 'ワンワン',
    'inu', 'dog', 'Dog', 'DOG', 'poodle', 'husky', 'samoyed',
    'サモエド', 'ハスキー', 'プードル', 'hound', 'puppy',
    'ガーデン', 'garden', 'パーク', 'park',
    'ペット可', 'ペットフレンドリー', 'わん', 'ワン',
    'paw', 'bone', 'woof', 'bark', 'canine', 'pooch',
    '犬', 'いぬ', 'イヌ', '猫', 'ねこ', 'ネコ', 'cat', 'Cat',
    'animal', 'Animal', 'pet', 'Pet', 'ペット',
    '食堂', '食事', '料理', '定食', 'キッチン', 'kitchen',
    'ビール', 'beer', 'ワイン', 'wine', 'ブリュワリー', 'brewery',
    'パン', 'bakery', 'ベーカリー', 'スイーツ', 'sweets', 'dessert',
    'ケーキ', 'cake', 'ビストロ', 'tavern', 'pub', 'Pub',
    'lounge', 'Lounge', 'grill', 'Grill', 'burger', 'Burger',
    'pizza', 'Pizza', 'sushi', 'Sushi', 'ramen', 'Ramen', 'ラーメン',
    'brunch', 'Brunch', 'eatery', 'Eatery', 'roastery', 'Roastery',
    'tearoom', 'Tearoom', 'tea', 'Tea', 'チャイ', 'chai',
    'スパイス', 'spice', 'curry', 'カレー',
    'house', 'House', 'cottage', 'Cottage', 'table', 'Table',
    'stand', 'Stand', 'market', 'Market', 'deli', 'Deli',
    'trattoria', 'Trattoria', 'osteria', 'Osteria',
    '居酒屋', '焼き鳥', '焼鳥', '焼肉', 'しゃぶ',
    '天ぷら', 'とんかつ', 'うどん', 'そば', 'おにぎり',
    'サンドイッチ', 'sandwich', 'クレープ', 'crepe',
    'ワッフル', 'waffle', 'パンケーキ', 'pancake',
    'スムージー', 'smoothie', 'ジュース', 'juice',
    'ジェラート', 'gelato', 'アイスクリーム', 'ice cream',
    '抹茶', 'matcha', '和菓子', 'wagashi', 'ドーナツ', 'donut',
    'クロワッサン', 'croissant', 'ベーグル', 'bagel',
    'muffin', 'マフィン', 'scone', 'スコーン',
    'taco', 'タコス', 'burrito', 'ブリトー',
    'fried', 'フライ', 'steak', 'ステーキ',
    'bbq', 'BBQ', 'barbecue', 'バーベキュー',
    'noodle', 'Noodle', 'pasta', 'Pasta', 'パスタ',
    'salad', 'Salad', 'サラダ', 'soup', 'Soup', 'スープ',
    'bowl', 'Bowl', 'ボウル', 'wrap', 'Wrap',
    'izakaya', '居酒屋', 'yakitori', '焼き鳥',
    'inn', 'Inn', 'villa', 'Villa',
    'kitchen', 'Kitchen', 'KITCHEN',
    'eatery', 'Eatery', 'bistro', 'Bistro',
    'brasserie', 'Brasserie',
    'tapas', 'Tapas', 'pintxos',
    'dim sum', 'dimsum', '点心',
    'hot pot', 'hotpot', '鍋',
    'shabu', 'しゃぶしゃぶ',
    'okonomiyaki', 'お好み焼き',
    'takoyaki', 'たこ焼き',
    'gyoza', '餃子', 'gyudon', '牛丼',
    'tempura', '天ぷら',
]

filtered = []
excluded = []

for place in data:
    name = place.get('name', '')
    category = place.get('category', '')
    name_lower = name.lower()

    if category == 'dogcafe':
        should_exclude = any(kw in name for kw in HARD_EXCLUDE)
        has_valid = any(kw.lower() in name_lower for kw in VALID_CAFE)
        if should_exclude and not has_valid:
            excluded.append({'name': name, 'category': category})
            continue
    elif category == 'dogrun':
        should_exclude = any(kw in name for kw in HARD_EXCLUDE)
        has_valid = any(kw.lower() in name_lower for kw in VALID_CAFE)
        if should_exclude and not has_valid:
            excluded.append({'name': name, 'category': category})
            continue

    filtered.append(place)

print(f"フィルタリング後: {len(filtered)}件")
print(f"除外件数: {len(excluded)}件")

with open('/home/ubuntu/dogmap/places_final_clean.json', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False)

print(f"ドッグラン: {sum(1 for p in filtered if p['category']=='dogrun')}件")
print(f"ドッグカフェ: {sum(1 for p in filtered if p['category']=='dogcafe')}件")
