
import csv
import json
from supabase import create_client, Client

SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_all_recipes():
    print("Downloading recipes from Supabase...")
    all_recipes = []
    limit = 1000
    offset = 0
    
    while True:
        response = supabase.table("recipes").select("*").range(offset, offset + limit - 1).execute()
        data = response.data
        if not data:
            break
        all_recipes.extend(data)
        if len(data) < limit:
            break
        offset += limit
    
    print(f"Downloaded {len(all_recipes)} recipes.")
    return all_recipes

recipes = download_all_recipes()

if recipes:
    output_path = 'python_project/przygotowanie_bazy/supabase_live_data.csv'
    keys = recipes[0].keys()
    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(recipes)
    print(f"Saved live data to {output_path}")

    # Immediate duplicate check on LIVE data
    names = [r['name'].lower().strip() for r in recipes]
    from collections import Counter
    counts = Counter(names)
    dupes = [name for name, count in counts.items() if count > 1]
    
    print(f"\n--- LIVE DATABASE DUPLICATE STATS ---")
    print(f"Total records: {len(recipes)}")
    print(f"Unique names: {len(counts)}")
    print(f"Duplicate names found: {len(dupes)}")
    if dupes:
        print("Examples of duplicates in Supabase:")
        for d in dupes[:10]:
            print(f" - '{d}' (found {counts[d]} times)")
else:
    print("No recipes found in Supabase.")
