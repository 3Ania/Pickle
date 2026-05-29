import json
import pandas as pd
import csv

# --- KONFIGURACJA MAPOWANIA ---
UNIT_MAP = {
    'clove': 'ząbek', 'cloves': 'ząbki', 'large cloves': 'duże ząbki',
    'tbsp': 'łyżka', 'tbsps': 'łyżki', 'tb': 'łyżka',
    'tsp': 'łyżeczka', 'tsps': 'łyżeczki',
    'cup': 'szklanka', 'cups': 'szklanki',
    'bag': 'opakowanie', 'bottle': 'butelka', 'box': 'pudełko',
    'bunch': 'pęczek', 'bunches': 'pęczki',
    'can': 'puszka', 'cans': 'puszki',
    'dash': 'szczypta', 'dashes': 'szczypty', 'pinch': 'szczypta', 'pinches': 'szczypty',
    'head': 'główka', 'heads': 'główki',
    'stalk': 'łodyga', 'stalks': 'łodygi',
    'leaf': 'liść', 'leaves': 'liście',
    'serving': 'porcja', 'servings': 'porcje',
    'handful': 'garść', 'handfuls': 'garście',
    'pkg': 'opakowanie', 'pkt': 'opakowanie',
    'slice': 'plasterek', 'slices': 'plasterki',
    'sprig': 'gałązka', 'sprigs': 'gałązki',
    'inch': 'cm', 'inches': 'cm'
}

ING_MAP = {
    'ewoo': 'oliwa z oliwek extra virgin',
    'evoo': 'oliwa z oliwek extra virgin',
    'olej ew': 'oliwa z oliwek extra virgin',
    'asparagus': 'szparagi',
    'sałata kosmiczna': 'sałata rzymska',
    'brinjal': 'bakłażan',
    'cilantro': 'kolendra',
    'bok choy': 'kapusta pak choi',
    'scallion': 'dymka'
}

def clean_and_log(input_file):
    df = pd.read_csv(input_file)
    changes_log = []

    print(f"Rozpoczynam proces dla {len(df)} przepisów...")

    for idx, row in df.iterrows():
        recipe_id = row['id']
        try:
            ingredients = json.loads(row['ingredients'])
            updated_ingredients = []
            updated_names = []
            row_changed = False

            for ing in ingredients:
                old_name = ing.get('name', '')
                old_unit = ing.get('unit', '')
                
                new_name = old_name.lower().strip()
                new_unit = str(old_unit).lower().replace('.', '').strip()

                # 1. Logika poprawy nazw składników
                for key, val in ING_MAP.items():
                    if key in new_name:
                        new_name = new_name.replace(key, val)
                
                if old_name.lower() != new_name:
                    changes_log.append([recipe_id, "Składnik", old_name, new_name])
                    row_changed = True

                # 2. Logika tłumaczenia jednostek
                if new_unit in UNIT_MAP:
                    translated_unit = UNIT_MAP[new_unit]
                    if old_unit != translated_unit:
                        changes_log.append([recipe_id, "Jednostka", f"{old_unit} ({old_name})", translated_unit])
                        new_unit = translated_unit
                        row_changed = True
                else:
                    new_unit = old_unit # Zostawiamy oryginał jeśli nie ma w słowniku

                ing['name'] = new_name
                ing['unit'] = new_unit
                updated_ingredients.append(ing)
                updated_names.append(new_name)

            # Zapis zmian do DataFrame
            if row_changed:
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(set(updated_names))) # Aktualizacja kolumny pomocniczej [cite: 52]

        except Exception as e:
            print(f"Błąd w ID {recipe_id}: {e}")

    # Zapis bazy
    df.to_csv('database_cleaned_final.csv', index=False)
    
    # Zapis logu zmian
    with open('cleaning_log.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID Przepisu", "Typ Zmiany", "Stara Wartość", "Nowa Wartość"])
        writer.writerows(changes_log)

    print(f"Zakończono! Zapisano {len(changes_log)} zmian w 'cleaning_log.csv'.")
    print("Baza bez usuwania rekordów zapisana w 'database_cleaned_final.csv'.")

# Uruchomienie skryptu
clean_and_log('recipes_rows_przed_zmianami.csv')