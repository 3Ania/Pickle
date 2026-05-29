import pandas as pd
import json
import ast
import re

# Twoja aktualna najlepsza baza
INPUT_FILE = "przygotowanie_bazy/database_100_percent_ready.csv" 
OUTPUT_FILE = "przygotowanie_bazy/database_final_unique.csv"

# Mikro-poprawki pozostałych detali i skrótów
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

def clean_and_deduplicate(input_file, output_file):
    print(f"Rozpoczynam ostateczne czyszczenie i usuwanie duplikatów z {input_file}...")
    df = pd.read_csv(input_file)
    
    initial_count = len(df)
    
    # 1. USUNIĘCIE DUPLIKATÓW
    df = df.drop_duplicates(subset=['name'], keep='first')
    unique_count = len(df)
    
    # 2. NAPRAWA SKRÓTÓW (EVOO, oz, cup) W INSTRUKCJACH I OPISACH
    for idx, row in df.iterrows():
        # Poprawa zabawnych tytułów
        if isinstance(row['name'], str):
            if "dni dla psów" in row['name'].lower():
                df.at[idx, 'name'] = "Pomidorowe gazpacho na upalne dni"
            elif "prawdziwa wygoda" in row['name'].lower():
                df.at[idx, 'name'] = row['name'].replace(": prawdziwa wygoda", " (Comfort Food)")
                
        # Poprawa EVOO, oz, cup w instrukcjach
        if pd.notna(row['instructions']):
            instr = str(row['instructions'])
            instr = re.sub(r'\bEVOO\b', 'oliwie z oliwek', instr, flags=re.IGNORECASE)
            instr = re.sub(r'\(first break the eggs into a cup\)', '(najpierw wbij jajka do kubka)', instr, flags=re.IGNORECASE)
            instr = re.sub(r'4\s*oz\.', '115 g', instr, flags=re.IGNORECASE)
            df.at[idx, 'instructions'] = instr
            
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
    
    print(f"💎 Gotowe! Baza jest wyczyszczona i wolna od duplikatów.")
    print(f"Liczba przepisów na start: {initial_count}")
    print(f"Usunięto duplikatów: {initial_count - unique_count}")
    print(f"Ostateczna liczba unikalnych przepisów: {unique_count}")
    print(f"Zapisano jako: {output_file}")

if __name__ == "__main__":
    clean_and_deduplicate(INPUT_FILE, OUTPUT_FILE)