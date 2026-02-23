import json
from collections import Counter

# ドッグラン確定キーワード（施設名に含まれる）
DOGRUN_KEYWORDS = [
    'ドッグラン', 'dog run', 'dogrun', 'ドッグパーク', 'dog park', 'dogpark',
    'わんわん広場', 'わんこ広場', 'いぬ広場', '犬の広場', 'ドッグスペース',
    'わんわんひろば', 'ドッグエリア',
]

# 犬連れ喫食可カフェ確定キーワード（施設名に含まれる）
# 定義：犬を連れて喫食できる飲食店
DOGCAFE_KEYWORDS = [
    # 「犬連れで飲食できる」を明示するキーワード
    'ドッグカフェ', 'dog cafe', 'dogcafe',
    'ドッグフレンドリー', 'dog friendly', 'dogfriendly',
    'ペット可', 'ペットok', 'ペットOK', 'ペットフレンドリー', 'pet friendly',
    '犬連れ', '犬同伴', 'わんこok', 'わんこOK', 'わんちゃん可',
    'ドッグウェルカム', 'dog welcome', 'わんちゃんok', 'わんちゃんOK',
    'ペット同伴', 'ペットウェルカム', 'pet welcome',
    '犬ok', '犬OK', '犬可',
    # 犬種名を冠した「連れて行けるカフェ」
    'コーギーカフェ', 'ポメラニアンカフェ', 'チワワカフェ', 'ダックスカフェ',
    'ゴールデンカフェ', 'ラブラドールカフェ', 'ビーグルカフェ', 'パグカフェ',
    'ブルドッグカフェ', 'シバカフェ', '柴カフェ', '柴犬カフェ',
    'トイプードルカフェ', 'マルチーズカフェ', 'サモエドカフェ', 'ハスキーカフェ',
    'プードルカフェ', 'husky cafe', '豆柴カフェ',
    # 「わんこと」系の飲食店
    'わんことご飯', 'わんことカフェ', 'わんこと食事', 'いぬとカフェ',
    '犬とカフェ', '犬とご飯', 'ドッグスタンド',
    # 施設名に「カフェ」+「ドッグ/犬/ペット/わんこ」が含まれる
    # → 下記の複合チェックで対応
]

# 「体験型」除外キーワード（これらを含むものは犬連れ喫食可ではない）
EXCLUDE_EXPERIENCE_KEYWORDS = [
    'いぬカフェ', 'いぬかふぇ', 'inu cafe', 'inucafe',
    '猫カフェ', 'ねこカフェ', 'cat cafe',
    'うさぎカフェ', 'ふくろうカフェ', 'は虫類カフェ',
    'トリミング', 'グルーミング', 'ペットホテル', 'ペットショップ',
    'ドッグスクール', 'ドッグトレーニング', 'ペット霊園', 'ペット葬',
    '動物病院', '獣医', 'アニマルホスピタル', 'ペット病院',
    # 体験型カフェ（犬を連れていかない施設）
    'サモエドカフェ', 'ハスキーカフェ', 'husky cafe', '豆柴カフェ',
    'コーギーカフェ', 'ポメラニアンカフェ', 'チワワカフェ', 'ダックスカフェ',
    'ゴールデンカフェ', 'ラブラドールカフェ', 'ビーグルカフェ', 'パグカフェ',
    'ブルドッグカフェ', 'シバカフェ', '柴カフェ', '柴犬カフェ',
    'トイプードルカフェ', 'マルチーズカフェ', 'プードルカフェ',
    'ふれあいカフェ', 'ふれあい', 'moffle', 'もふちる', 'もふれる',
    '保護犬カフェ', '保護猫カフェ', '保護犬猫', 'ふれあい',
    'ペットサロン', 'ドッグサロン', 'salon',
    'ペット可！', # 看板猫など主目的が犬連れではないもの
    # 個別除外：体験型（犬を連れていく場所ではない）
    '大型犬カフェ', '犬みみカフェ', 'puppy cafe', 'Rio puppy',
    'ふれあいカフェ', 'もふれる', 'moffle',
    'FASTENING', # ペットサロン系
    'DogSalon', 'Dog Salon', 'RaiM', # サロン系
    'Rainbow Cafe/Poodle shop', # ショップ系
    'ANELLA CAFE', # 保護犬ふれあい系
    # グッズショップ系
    'DOG GOODS', 'dog goods',
    # ホットドッグスタンド（犬連れではない）
    'HOTDOG CAFESTAND', 'hotdog cafestand',
    # ペットホテル系
    'Hotel Green Wood', 'hotel green wood',
    # 体験型（犬を連れていかない）
    'CATS&DOGS CAFE', 'cats&dogs cafe', 'cats and dogs cafe',
    'kimama83', 'kimama 83',
    # 猫も居る飲食店（犬連れではない可能性）
    '犬猫食堂', '犬猫カフェ',
]

# 動物病院確定キーワード
VET_KEYWORDS = [
    '動物病院', '獣医', 'アニマルホスピタル', 'animal hospital',
    'veterinary', 'vet clinic', '動物クリニック', '犬猫病院', 'ペット病院',
    'アニマルクリニック', '犬猫クリニック', 'ペットクリニック',
]

def is_dogrun(name):
    name_lower = name.lower()
    return any(kw.lower() in name_lower for kw in DOGRUN_KEYWORDS)

def is_dogcafe(name):
    name_lower = name.lower()
    # 除外チェック
    if any(kw.lower() in name_lower for kw in EXCLUDE_EXPERIENCE_KEYWORDS):
        return False
    # 直接キーワードマッチ
    if any(kw.lower() in name_lower for kw in DOGCAFE_KEYWORDS):
        return True
    # 複合チェック：「カフェ or レストラン or 食堂 or ビストロ」+「犬 or ペット or わんこ or dog or pet」
    has_food = any(w in name_lower for w in ['カフェ', 'cafe', 'レストラン', 'restaurant', '食堂', 'ビストロ', 'bistro', 'ダイニング', 'dining', 'バー', 'bar', 'ベーカリー', 'bakery', 'キッチン', 'kitchen'])
    has_dog = any(w in name_lower for w in ['犬', 'いぬ', 'わんこ', 'わんちゃん', 'ペット', 'dog', 'pet', 'paw', 'paws', 'pooch', 'hound', 'puppy', 'pup', 'bau', 'woof', 'bark'])
    return has_food and has_dog

def is_vet(name):
    name_lower = name.lower()
    return any(kw.lower() in name_lower for kw in VET_KEYWORDS)

# データ読み込み
print("データ読み込み中...")
with open('/home/ubuntu/dogmap/places_final_v3.json', 'r', encoding='utf-8') as f:
    existing = json.load(f)

with open('/home/ubuntu/dogmap/places_vet.json', 'r', encoding='utf-8') as f:
    vet_data = json.load(f)

with open('/home/ubuntu/dogmap/places_dogfriendly.json', 'r', encoding='utf-8') as f:
    friendly_data = json.load(f)

print(f"既存データ: {len(existing)}件")
print(f"動物病院データ: {len(vet_data)}件")
print(f"ドッグフレンドリー候補: {len(friendly_data)}件")

all_data = {}

# 既存データから分類
for p in existing:
    pid = p.get('place_id')
    if not pid:
        continue
    name = p.get('name', '')
    if is_dogrun(name):
        p['category'] = 'dogrun'
        all_data[pid] = p
    elif is_dogcafe(name):
        p['category'] = 'dogcafe'
        all_data[pid] = p
    elif is_vet(name):
        p['category'] = 'vet'
        all_data[pid] = p

# 動物病院データを追加
for p in vet_data:
    pid = p.get('place_id')
    if not pid:
        continue
    if pid not in all_data:
        p['category'] = 'vet'
        all_data[pid] = p

# ドッグフレンドリー候補から分類
for p in friendly_data:
    pid = p.get('place_id')
    if not pid:
        continue
    if pid in all_data:
        continue
    name = p.get('name', '')
    if is_dogrun(name):
        p['category'] = 'dogrun'
        all_data[pid] = p
    elif is_dogcafe(name):
        p['category'] = 'dogcafe'
        all_data[pid] = p

# 営業中のみ
result = [p for p in all_data.values() if p.get('business_status', 'OPERATIONAL') in ['OPERATIONAL', '']]
cats = Counter(p['category'] for p in result)

print(f"\n最終データ（営業中のみ）:")
print(f"  ドッグラン: {cats['dogrun']}件")
print(f"  犬連れOKカフェ: {cats['dogcafe']}件")
print(f"  動物病院: {cats['vet']}件")
print(f"  合計: {len(result)}件")

# サンプル確認
print("\n--- 犬連れOKカフェ サンプル（全件） ---")
cafe_places = [p for p in result if p['category'] == 'dogcafe']
for p in cafe_places:
    print(f"  {p['name']}")

# 保存
with open('/home/ubuntu/dogmap/places_final.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\nplaces_final.json に保存しました（{len(result)}件）")
