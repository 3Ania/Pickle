import json
import re
from supabase import create_client, Client

# --- KONFIGURACJA ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def round_amount(amount_str):
    try:
        val = float(amount_str)
        # Jeśli liczba ma wiele miejsc po przecinku (prawdopodobna konwersja)
        if '.' in str(amount_str):
            # Zaokrąglanie do rozsądnych wartości kuchennych
            if val > 10:
                # Zaokrąglamy do pełnych 5 lub 10 dla gramów/ml
                return str(int(5 * round(val / 5)))
            else:
                # Zaokrąglamy do 1 lub 2 miejsc po przecinku dla mniejszych ilości
                return str(round(val, 2))
    except:
        pass
    return amount_str

def fix_ingredient(ing):
    if not isinstance(ing, dict):
        return ing

    name = (ing.get('name') or ing.get('item') or "").lower()
    amount = str(ing.get('amount') or ing.get('quantity') or "")
    unit = (ing.get('unit') or "").lower()

    # 1. Naprawa nazw (Błędy tłumaczenia)
    if "wapno" in name:
        ing['name'] = name.replace("wapno", "limonka")
    if "goździk" in unit or "goździki" in unit:
        if "czosnek" in name:
            ing['unit'] = unit.replace("goździki", "ząbki").replace("goździk", "ząbek")
    if "krem" in name and "śmietana" not in name:
        # Ostrożnie zamieniamy krem na śmietanę, o ile to nie jest np. "krem czekoladowy"
        if any(x in name for x in ["fraiche", "sour", "świeży", "gęsty"]):
            ing['name'] = name.replace("krem", "śmietana")
    
    # 2. Naprawa jednostek
    unit_map = {
        "móc": "puszka",
        "c": "szklanka",
        "t": "łyżeczka", # Uwaga: w angielskim 't' to teaspoon, 'T' to tablespoon
        "stick": "sztuka (ok. 110g)",
        "funt": "g",
        "uncja": "g",
        "porcje": "szczypta", # Dla soli/pieprzu "porcje" to zazwyczaj "szczypta"
    }

    # Obsługa specyficznego przypadku T vs t
    original_unit = ing.get('unit', "")
    if original_unit == "T":
        ing['unit'] = "łyżka"
    elif original_unit == "t":
        ing['unit'] = "łyżeczka"
    elif unit in unit_map:
        ing['unit'] = unit_map[unit]
    
    # Przeliczenia wagowe dla funtów/uncji jeśli jednostka się zmieniła
    try:
        val = float(amount)
        if unit == "funt":
            ing['amount'] = str(round(val * 453.59, 0))
            ing['unit'] = "g"
        elif unit == "uncja":
            ing['amount'] = str(round(val * 28.35, 0))
            ing['unit'] = "g"
        elif "stick" in unit:
             # Pozostawiamy ilość, zmieniamy opis jednostki
             pass
    except:
        pass

    # 3. Zaokrąglanie ilości
    ing['amount'] = round_amount(ing.get('amount', amount))
    
    # 4. Czyszczenie nazwy (usuwanie zbędnych spacji)
    if 'name' in ing: ing['name'] = ing['name'].strip()
    if 'unit' in ing: ing['unit'] = ing['unit'].strip()

    return ing

def repair_database():
    print("Pobieranie przepisów...")
    response = supabase.table("recipes").select("id, name, ingredients").execute()
    recipes = response.data
    
    total = len(recipes)
    print(f"Rozpoczynam naprawę {total} przepisów...")

    for i, recipe in enumerate(recipes):
        recipe_id = recipe['id']
        ingredients = recipe.get('ingredients', [])
        
        if isinstance(ingredients, str):
            try:
                ingredients = json.loads(ingredients)
            except:
                continue

        if isinstance(ingredients, list):
            new_ingredients = [fix_ingredient(dict(ing)) for ing in ingredients]
            
            # Aktualizacja w bazie
            try:
                supabase.table("recipes").update({"ingredients": new_ingredients}).eq("id", recipe_id).execute()
                if (i + 1) % 50 == 0:
                    print(f"Przetworzono {i + 1}/{total}...")
            except Exception as e:
                print(f"Błąd przy ID {recipe_id}: {e}")

    print("\n--- NAPRAWA ZAKOŃCZONA! ---")

if __name__ == "__main__":
    repair_database()
