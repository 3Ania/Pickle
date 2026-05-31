
import csv
import json
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"
CSV_PATH = "python_project/przygotowanie_bazy/database_flawless_final.csv"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_to_supabase():
    print(f"Reading data from {CSV_PATH}...")
    rows = []
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Type conversions based on current CSV columns
            row['id'] = int(row['id'])
            
            # Numeric fields (with safety for empty strings)
            row['total_time'] = int(row['total_time']) if row.get('total_time') else 0
            row['prep_time'] = int(row['prep_time']) if row.get('prep_time') else 0
            row['cook_time'] = int(row['cook_time']) if row.get('cook_time') else 0
            
            # JSON fields
            row['ingredients'] = json.loads(row['ingredients'])
            
            # Tags are JSON array
            try:
                row['tags'] = json.loads(row['tags'])
            except:
                # If it's not a JSON string, assume it's already list or string
                pass
            
            # Instructions: if they are not JSON list, keep as string
            try:
                # If they start with [, try parsing
                if row['instructions'].strip().startswith('['):
                    row['instructions'] = json.loads(row['instructions'])
                else:
                    # Keep as plain string
                    pass
            except:
                pass
            
            # ingredient_names is already a list-like string in our CSV
            if isinstance(row['ingredient_names'], str):
                try:
                    row['ingredient_names'] = eval(row['ingredient_names'])
                except:
                    row['ingredient_names'] = [n.strip("' ") for n in row['ingredient_names'].strip("[]").split(",")]
            
            # Embedding handling
            if row.get('embedding'):
                try:
                    # Embeddings in Supabase are usually vector/list
                    if isinstance(row['embedding'], str):
                        row['embedding'] = json.loads(row['embedding'])
                except:
                    pass
            else:
                # Ensure it's not empty string
                row['embedding'] = None
            
            rows.append(row)

    print(f"Clearing existing recipes in Supabase...")
    supabase.table("recipes").delete().neq("id", -1).execute()

    print(f"Uploading {len(rows)} perfected recipes...")
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        response = supabase.table("recipes").insert(batch).execute()
        print(f"Uploaded batch {i//batch_size + 1}/{(len(rows)-1)//batch_size + 1}")

    print("Success! Database has been refreshed with perfected data.")

if __name__ == "__main__":
    import_to_supabase()
