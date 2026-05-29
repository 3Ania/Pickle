import pandas as pd
import json
import ast
import re

# Mikro-poprawki pozostałych detali
MICRO_FIXES = {
    "1 sałata rzymska": "sałata rzymska",
    "6 pomidorów romskich": "pomidory rzymskie",
    "do 2 estragonu": "estragon",
    "do 2 pomarańczy": "pomarańcze",
    "do 3 brokułów": "brokuł",
    "do 6 wody": "woda",
    "woda *2": "woda",
    "woda 4 szkl": "woda",
    "fasola garbanzo *1": "ciecierzyca",
    "cebula lub": "cebula",
    "do)": "woda",
    "następujące: skórka parmezanu)": "skórka parmezanu"
}

def clean_punctuation(text):
    if not isinstance(text, str):
        return text
    # Jeśli tekst ma na końcu znak zamykający bez otwierającego, usuń go
    if text.endswith(')') and '(' not in text:
        text = text[:-1].strip()
    return text

def fix_micro_errors(text):
    if not isinstance(text, str):
        return text
    fixed = text
    for bad, good in MICRO_FIXES.items():
        pattern = re.compile(re.escape(bad), re.IGNORECASE)
        fixed = pattern.sub(good, fixed)
    return clean_punctuation(fixed)

def polish_database(input_file, output_file):
    print(f"Rozpoczynam nakładanie ostatniego połysku na {input_file}...")
    df = pd.read_csv(input_file)
    
    for idx, row in df.iterrows():
        # Poprawa zabawnych tytułów
        if isinstance(row['name'], str):
            if "dni dla psów" in row['name'].lower():
                df.at[idx, 'name'] = "Pomidorowe gazpacho na upalne dni"
            elif "prawdziwa wygoda" in row['name'].lower():
                df.at[idx, 'name'] = row['name'].replace(": prawdziwa wygoda", " (Comfort Food)")
                
        # Poprawa resztek składników
        ing_json = row['ingredients']
        updated_ingredients = []
        updated_names = set()
        
        try:
            ings = ast.literal_eval(ing_json) if isinstance(ing_json, str) else ing_json
            if isinstance(ings, list):
                for ing in ings:
                    if 'name' in ing:
                        fixed_name = fix_micro_errors(ing['name']).strip()
                        ing['name'] = fixed_name
                        updated_ingredients.append(ing)
                        updated_names.add(fixed_name)
                        
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(updated_names))
        except:
            pass

    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"💎 Gotowe! Baza jest absolutnie perfekcyjna. Zapisano jako: {output_file}")

if __name__ == "__main__":
    polish_database("przygotowanie_bazy\database_perfect.csv", "przygotowanie_bazy\database_100_percent_ready.csv")