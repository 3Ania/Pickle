import json
from supabase import create_client, Client

# --- KONFIGURACJA ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_print_recipes():
    try:
        # Pobieranie wszystkich przepisów (może być ich dużo, ale limit to domyślnie 1000 w Supabase)
        response = supabase.table("recipes").select("name, ingredients").execute()
        recipes = response.data

        if not recipes:
            print("Nie znaleziono przepisów w bazie.")
            return

        print(f"Znaleziono {len(recipes)} przepisów.\n")
        print("="*50)

        for recipe in recipes:
            name = recipe.get('name', 'Brak nazwy')
            ingredients = recipe.get('ingredients', [])

            print(f"\nPRZEPIS: {name}")
            print("-" * (len(name) + 9))
            
            # Zakładamy, że ingredients to lista słowników z polami 'name' i 'amount' (lub podobnie)
            # Sprawdźmy strukturę na pierwszym elemencie jeśli to nie jest oczywiste
            if isinstance(ingredients, str):
                try:
                    ingredients = json.loads(ingredients)
                except:
                    print(f"  Błąd parsowania składników: {ingredients}")
                    continue

            if isinstance(ingredients, list):
                for ing in ingredients:
                    if isinstance(ing, dict):
                        # Próbujemy różnych kluczy, które mogą występować
                        ing_name = ing.get('name') or ing.get('item') or ing.get('ingredient', 'Nieznany składnik')
                        amount = ing.get('amount') or ing.get('quantity') or ing.get('value', '')
                        unit = ing.get('unit', '')
                        
                        print(f"  • {ing_name}: {amount} {unit}".strip())
                    else:
                        print(f"  • {ing}")
            else:
                print(f"  Składniki: {ingredients}")
            
            print("-" * 30)

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    fetch_and_print_recipes()
