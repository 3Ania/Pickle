import json
import pandas as pd
import csv
import os

# --- DODATKOWE MAPOWANIE SZLIFUJĄCE ---
# Obsługa jednostek z przymiotnikami oraz konkretnych błędów
FINAL_UNIT_FIXES = {
    'large head': 'duża główka',
    'small head': 'mała główka',
    'medium head': 'średnia główka',
    'large bunch': 'duży pęczek',
    'small bunch': 'mały pęczek',
    'large can': 'duża puszka',
    'small can': 'mała puszka',
    'small pinch': 'mała szczypta',
    'large pinch': 'duża szczypta',
    '8-inch': '20 cm (sztuka)',
    'medium': 'średnia sztuka',
    'large': 'duża sztuka',
    'small': 'mała sztuka'
}

FINAL_ING_FIXES = {
    'sałata kosmiczna': 'sałata rzymska',
    'cos lettuce': 'sałata rzymska',
    'extra virgin olive oil': 'oliwa z oliwek extra virgin'
}

def polish_database(input_file, log_file):
    df = pd.read_csv(input_file)
    changes_log = []
    
    print(f"Rozpoczynam szlifowanie {len(df)} rekordów...")

    for idx, row in df.iterrows():
        recipe_id = row['id']
        try:
            ingredients = json.loads(row['ingredients'])
            updated_ingredients = []
            updated_names = []
            row_changed = False

            for ing in ingredients:
                old_name = ing.get('name', '')
                old_unit = str(ing.get('unit', '')).strip()
                
                new_name = old_name.lower()
                new_unit = old_unit.lower()

                # 1. Poprawa specyficznych nazw (np. sałata kosmiczna)
                for key, val in FINAL_ING_FIXES.items():
                    if key in new_name:
                        new_name = new_name.replace(key, val)
                
                if old_name.lower() != new_name:
                    changes_log.append([recipe_id, "Korekta Nazwy", old_name, new_name])
                    row_changed = True

                # 2. Poprawa złożonych jednostek (np. large head)
                if new_unit in FINAL_UNIT_FIXES:
                    translated_unit = FINAL_UNIT_FIXES[new_unit]
                    changes_log.append([recipe_id, "Korekta Jednostki", f"{old_unit} ({new_name})", translated_unit])
                    new_unit = translated_unit
                    row_changed = True
                else:
                    new_unit = old_unit # Zostawiamy jak było, jeśli nie ma w słowniku

                ing['name'] = new_name
                ing['unit'] = new_unit
                updated_ingredients.append(ing)
                updated_names.append(new_name)

            if row_changed:
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(set(updated_names)))

        except Exception as e:
            print(f"Błąd w ID {recipe_id}: {e}")

    # Zapis bazy
    output_name = 'database_polished_final.csv'
    df.to_csv(output_name, index=False)
    
    # Dopisywanie do istniejącego logu lub tworzenie nowego
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["ID Przepisu", "Typ Zmiany", "Stara Wartość", "Nowa Wartość"])
        writer.writerows(changes_log)

    print(f"Szlifowanie zakończone! Zapisano {len(changes_log)} dodatkowych poprawek.")
    print(f"Nowa baza: {output_name}")

# Uruchomienie
polish_database('database_cleaned_final.csv', 'cleaning_log.csv')