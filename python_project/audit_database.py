import json
import re
from supabase import create_client, Client

# --- KONFIGURACJA ---
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Słownik podejrzanych fraz (tłumaczenia i jednostki)
SUSPICIOUS_PHRASES = {
    "krem": "Prawdopodobna pomyłka z 'śmietana' (cream)",
    "wapno": "Błędne tłumaczenie 'lime' (powinno być limonka)",
    "goździk": "Podejrzenie błędnego tłumaczenia 'clove' (powinno być ząbek w przypadku czosnku)",
    "Móc": "Błędne tłumaczenie 'Can' (powinno być puszka)",
    "stick": "Amerykańska jednostka masła (powinno być masło w gramach)",
    "opakowanie": "Zbyt ogólna jednostka (brak wagi)",
    "pudełko": "Zbyt ogólna jednostka",
    "porcje": "Dziwna jednostka dla przypraw (sól/pieprz)",
    "C": "Skrót 'Cup' (powinno być szklanka)",
    "T": "Skrót 'Tablespoon' (powinno być łyżka)",
    "t": "Skrót 'teaspoon' (powinno być łyżeczka)",
    "Op": "Skrót 'Package' (powinno być opakowanie)",
    "uncja": "Jednostka imperialna (powinno być g/ml)",
    "funt": "Jednostka imperialna (powinno być g/kg)",
    "szklanka": "Warto sprawdzić czy nie ma tam dziwnych ułamków jak 0.33333334",
}

def audit_recipes():
    try:
        response = supabase.table("recipes").select("id, name, ingredients").execute()
        recipes = response.data
        
        report = []

        for recipe in recipes:
            recipe_id = recipe['id']
            recipe_name = recipe['name']
            ingredients = recipe.get('ingredients', [])
            
            if isinstance(ingredients, str):
                try:
                    ingredients = json.loads(ingredients)
                except:
                    continue
            
            issues = []
            
            for ing in ingredients:
                if not isinstance(ing, dict): continue
                
                ing_name = (ing.get('name') or ing.get('item') or "").lower()
                amount = str(ing.get('amount') or ing.get('quantity') or "")
                unit = (ing.get('unit') or "").lower()
                
                # 1. Sprawdzanie precyzyjnych wag (konwersje z uncji/funtów)
                # Szukamy liczb z wieloma miejscami po przecinku
                if re.search(r'\d+\.\d{2,}', amount):
                    issues.append(f"Precyzyjna/dziwna ilość: '{amount}' w składniku '{ing_name}' (prawdopodobna konwersja imperialna)")

                # 2. Sprawdzanie podejrzanych nazw i jednostek
                combined_text = f"{ing_name} {unit} {amount}"
                for phrase, reason in SUSPICIOUS_PHRASES.items():
                    if phrase.lower() in combined_text:
                        issues.append(f"Podejrzany termin '{phrase}': {reason} (znaleziono w: '{ing_name}: {amount} {unit}')")

                # 3. Specyficzne błędy logiczne
                if "czosnek" in ing_name and "goździk" in combined_text:
                    issues.append(f"Błąd 'goździk czosnku': Powinno być 'ząbek czosnku'")
                
                if "ziemniak" in ing_name and "opakowanie" in unit:
                    issues.append(f"Niejasna ilość: 'opakowanie ziemniaków' - brak wagi")

            if issues:
                report.append({
                    "id": recipe_id,
                    "name": recipe_name,
                    "issues": issues
                })

        return report

    except Exception as e:
        print(f"Błąd podczas audytu: {e}")
        return []

if __name__ == "__main__":
    full_report = audit_recipes()
    
    print(f"Zaleziono problemy w {len(full_report)} przepisach.\n")
    
    # Grupowanie problemów dla lepszej czytelności
    all_issues_summary = {}
    
    for entry in full_report:
        print(f"ID: {entry['id']} | PRZEPIS: {entry['name']}")
        for issue in entry['issues']:
            print(f"  - {issue}")
            # Statystyka
            issue_type = issue.split(':')[0]
            all_issues_summary[issue_type] = all_issues_summary.get(issue_type, 0) + 1
        print("-" * 50)

    print("\nPODSUMOWANIE TYPÓW BŁĘDÓW:")
    for itype, count in all_issues_summary.items():
        print(f"{itype}: {count}")
