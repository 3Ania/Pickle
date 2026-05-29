import pandas as pd
import ast
import json
from supabase import create_client, Client

# --- KONFIGURACJA ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"
CSV_FILE = "przygotowanie_bazy/database_500_ultimate.csv"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_data():
    # 1. Wczytanie pliku CSV
    print(f"Wczytuję plik {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    records = []
    for _, row in df.iterrows():
        try:
            # CSV przechowuje listy jako tekst, np. "['tag1', 'tag2']"
            # ast.literal_eval zamienia je z powrotem na prawdziwe listy Pythona
            ingredients = json.loads(row['ingredients']) if isinstance(row['ingredients'], str) else row['ingredients']
            ing_names = ast.literal_eval(row['ingredient_names']) if isinstance(row['ingredient_names'], str) else row['ingredient_names']
            tags = ast.literal_eval(row['tags']) if isinstance(row['tags'], str) else row['tags']
            
            record = {
                "id": int(row['id']),
                "name": row['name'],
                "instructions": row['instructions'] if pd.notna(row['instructions']) else "",
                "description": row['description'],
                "ingredients": ingredients, # JSONB w Supabase
                "ingredient_names": ing_names, # text[] w Supabase
                "cuisine": row['cuisine'],
                "warmth": bool(row['warmth']),
                "tags": tags, # text[] w Supabase
                "total_time": int(row['total_time']),
                "image_url": row['image_url']
            }
            records.append(record)
        except Exception as e:
            print(f"Błąd parsowania w ID {row.get('id')}: {e}")

    # 2. Wysyłka w paczkach (Batching) - szybciej i bezpieczniej
    print(f"Rozpoczynam wysyłkę {len(records)} przepisów...")
    batch_size = 50
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        response = supabase.table("recipes").insert(batch).execute()
        print(f"✅ Wysłano rekordy od {i} do {i + len(batch)}")

    print("\n--- IMPORT ZAKOŃCZONY! Twoja baza 'Pickle' jest gotowa. ---")

if __name__ == "__main__":
    upload_data()