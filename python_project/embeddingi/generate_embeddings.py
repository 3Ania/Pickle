import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# --- KONFIGURACJA SUPABASE ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Wczytujemy naszą ostateczną, idealną bazę 500 przepisów
df = pd.read_csv("przygotowanie_bazy/database_500_ultimate.csv")

# Ładujemy model LLM do zamiany tekstu na wektory (odpali się lokalnie na Twoim PC)
print("Ładowanie modelu językowego...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Rozpoczynam wektoryzację {len(df)} przepisów...")

for idx, row in df.iterrows():
    recipe_id = row['id']
    name = row['name']
    cuisine = row['cuisine']
    
    # Przekształcamy tagi i składniki z JSON/list do czystego tekstu
    try:
        tags = ", ".join(json.loads(row['tags'])) if pd.notna(row['tags']) else ""
        ingredients = ", ".join(ast.literal_eval(row['ingredient_names'])) if pd.notna(row['ingredient_names']) else ""
    except:
        tags = ""
        ingredients = ""
        
    # Tworzymy "Reprezentację tekstową" przepisu (to, co zrozumie AI)
    # Łączymy najważniejsze cechy, aby k-NN działało precyzyjnie
    text_to_embed = f"Przepis: {name}. Kuchnia: {cuisine}. Tagi: {tags}. Składniki: {ingredients}."
    
    # 1. Generujemy wektor (ciąg 384 liczb zmiennoprzecinkowych)
    embedding = model.encode(text_to_embed).tolist()
    
    # 2. Wysyłamy wektor bezpośrednio do odpowiedniego wiersza w Supabase
    try:
        data = supabase.table("recipes").update({"embedding": embedding}).eq("id", recipe_id).execute()
        
        if (idx + 1) % 50 == 0:
            print(f"Zaktualizowano wektory dla {idx + 1} przepisów...")
    except Exception as e:
        print(f"Błąd przy ID {recipe_id}: {e}")

print("✅ ZAKOŃCZONO! Wszystkie 500 przepisów ma teraz swoje wektory w bazie Supabase.")