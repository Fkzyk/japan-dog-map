import json

# ドッグラン確定キーワード（施設名に含まれる）
DOGRUN_KEYWORDS = [
    'ドッグラン', 'dog run', 'dogrun', 'ドッグパーク', 'dog park', 'dogpark',
    'わんわん広場', 'わんこ広場', 'いぬ広場', '犬の広場', 'ドッグスペース',
]

# ドッグカフェ確定キーワード（施設名に含まれる）
DOGCAFE_KEYWORDS = [
    'ドッグカフェ', '犬カフェ', 'いぬカフェ', 'イヌカフェ',
    'dog cafe', 'dogcafe', 'ペットカフェ', 'pet cafe',
    'わんこカフェ', 'ワンコカフェ', 'dog friendly cafe',
    'サモエドカフェ', 'ハスキーカフェ', 'プードルカフェ',
    'husky cafe', 'inu cafe', 'わんcafe', 'わんカフェ',
]

# ドッグフレンドリー確定キーワード（施設名に含まれる）
DOGFRIENDLY_KEYWORDS = [
    'ドッグフレンドリー', 'dog friendly', 'dogfriendly',
    'ペット可', 'ペットok', 'ペットOK', 'ペットフレンドリー', 'pet friendly',
    '犬連れ', '犬同伴', 'わんこok', 'わんこOK', 'わんちゃん可',
    'ドッグウェルカム', 'dog welcome', 'わんちゃんok',
    'ペット同伴', 'ペットウェルカム', 'pet welcome',
    # 犬種名を含むカフェ（ドッグカフェの一形態）
    'コーギーカフェ', 'ポメラニアンカフェ', 'チワワカフェ', 'ダックスカフェ',
    'ゴールデンカフェ', 'ラブラドールカフェ', 'ビーグルカフェ', 'パグカフェ',
    'ブルドッグカフェ', 'シバカフェ', '柴カフェ', '柴犬カフェ',
    'トイプードルカフェ', 'マルチーズカフェ',
    # ペット関連カフェ
    'ペットサロンカフェ', 'わんこと', 'いぬと', '犬と', 'ドッグスタンド',
]

# 動物病院確定キーワード
VET_KEYWORDS = [
    '動物病院', '獣医', 'アニマルホスピタル', 'animal hospital',
    'veterinary', 'vet clinic', '動物クリニック', '犬猫病院', 'ペット病院',
    'アニマルクリニック', '犬猫クリニック', 'ペットクリニック',
]

# 除外キーワード（これらのみを含む施設は除外）
EXCLUDE_ONLY_KEYWORDS = [
    'トリミング', 'グルーミング', 'ペットホテル', 'ペットショップ',
    'ペット霊園', 'ペット葬', '動物葬', 'ペット保険', 'ペット用品',
    'ドッグスクール', 'ドッグトレーニング', 'ドッグトレーナー',
]

def categorize(name):
    name_lower = name.lower()
    
    # 除外チェック（施設名がこれらのキーワードのみで構成される場合）
    # ただし「ドッグラン」「カフェ」も含む場合は除外しない
    has_positive = any(kw.lower() in name_lower for kw in 
                       DOGRUN_KEYWORDS + DOGCAFE_KEYWORDS + DOGFRIENDLY_KEYWORDS + VET_KEYWORDS)
    
    if any(kw.lower() in name_lower for kw in DOGRUN_KEYWORDS):
        return 'dogrun'
    if any(kw.lower() in name_lower for kw in DOGCAFE_KEYWORDS):
        return 'dogcafe'
    if any(kw.lower() in name_lower for kw in VET_KEYWORDS):
        return 'vet'
    if any(kw.lower() in name_lower for kw in DOGFRIENDLY_KEYWORDS):
        return 'dogfriendly'
    return None

# 既存データ読み込み
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

# 全データを統合
all_data = {}

# 既存データから名称ベースで分類
for p in existing:
    pid = p.get('place_id')
    if not pid:
        continue
    name = p.get('name', '')
    cat = categorize(name)
    if cat:
        p['category'] = cat
        all_data[pid] = p

# 動物病院データを追加（veterinary_care typeで取得した確実なデータ）
for p in vet_data:
    pid = p.get('place_id')
    if not pid:
        continue
    if pid not in all_data:
        p['category'] = 'vet'
        all_data[pid] = p

# ドッグフレンドリー候補から名称ベースで分類
for p in friendly_data:
    pid = p.get('place_id')
    if not pid:
        continue
    if pid in all_data:
        continue  # 既に登録済み
    name = p.get('name', '')
    cat = categorize(name)
    if cat:
        p['category'] = cat
        all_data[pid] = p

# 結果集計
result = list(all_data.values())
from collections import Counter
cats = Counter(p['category'] for p in result)

print(f"\n最終データ:")
print(f"  ドッグラン: {cats['dogrun']}件")
print(f"  ドッグカフェ: {cats['dogcafe']}件")
print(f"  ドッグフレンドリー: {cats['dogfriendly']}件")
print(f"  動物病院: {cats['vet']}件")
print(f"  合計: {len(result)}件")

# 営業中のみ（OPERATIONAL or 空）
active = [p for p in result if p.get('business_status', 'OPERATIONAL') in ['OPERATIONAL', '']]
cats_active = Counter(p['category'] for p in active)
print(f"\n営業中のみ:")
print(f"  ドッグラン: {cats_active['dogrun']}件")
print(f"  ドッグカフェ: {cats_active['dogcafe']}件")
print(f"  ドッグフレンドリー: {cats_active['dogfriendly']}件")
print(f"  動物病院: {cats_active['vet']}件")
print(f"  合計: {len(active)}件")

# サンプル確認
print("\n--- ドッグフレンドリー サンプル ---")
df_places = [p for p in active if p['category'] == 'dogfriendly']
for p in df_places[:15]:
    print(f"  {p['name']}")

# 保存
with open('/home/ubuntu/dogmap/places_merged.json', 'w', encoding='utf-8') as f:
    json.dump(active, f, ensure_ascii=False, indent=2)
print(f"\nplaces_merged.json に保存しました（{len(active)}件）")
