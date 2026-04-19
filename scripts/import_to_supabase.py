
import json
import os
import argparse
from supabase import create_client, Client

def import_to_supabase(file_path: str):
    """指定されたJSONファイルをSupabaseにインポートする"""
    url: str = os.environ.get("SUPABASE_URL", "https://rfcfilhqkkjmkecxzijw.supabase.co")
    key: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not key:
        raise RuntimeError("環境変数 SUPABASE_SERVICE_KEY が設定されていません。.env ファイルを確認してください。")
    supabase: Client = create_client(url, key)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            places = json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {file_path}")
        return
    except json.JSONDecodeError:
        print(f"エラー: JSONのデコードに失敗しました - {file_path}")
        return

    print(f"{file_path} から {len(places)} 件のデータをインポートします。")

    batch_size = 100
    total_inserted = 0

    for i in range(0, len(places), batch_size):
        batch = places[i:i + batch_size]
        print(f"  バッチ {i//batch_size + 1}: {len(batch)}件を処理中...")
        
        try:
            # upsertを使用してplace_idの重複を無視する
            data, count = supabase.table("places").upsert(
                batch,
                on_conflict="place_id",
                ignore_duplicates=True
            ).execute()
            
            # APIレスポンスから挿入件数を取得
            inserted_in_batch = len(data[1]) if isinstance(data, list) and len(data) > 1 else 0

            total_inserted += inserted_in_batch
            print(f"    -> {inserted_in_batch} 件をインポートしました。")

        except Exception as e:
            print(f"    バッチ処理中にエラーが発生しました: {e}")

    print(f"\nインポート完了。合計 {total_inserted} 件の新規データをインポートしました。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JSONファイルからSupabaseにデータをインポートするスクリプト")
    parser.add_argument(
        "--file", 
        required=True, 
        help="インポートするJSONファイルのパス"
    )
    args = parser.parse_args()
    import_to_supabase(args.file)
