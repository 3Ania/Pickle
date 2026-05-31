
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

units = Counter()
suspicious = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            unit = ing.get('unit', '')
            name = ing.get('name', '')
            units[unit] += 1
            
            # Look for "T", "t", "tsp", "tbsp", "oz", "lb", "c"
            if unit in ['T', 't', 'tsp', 'tbsp', 'oz', 'lb', 'c', 'C']:
                suspicious.append(f"Found abbreviation '{unit}' in {row['name']} ({name})")
            
            # Check for English words in units
            english_units = ['tablespoon', 'teaspoon', 'cup', 'ounce', 'pound', 'clove', 'cloves']
            for eu in english_units:
                if eu in unit.lower():
                    suspicious.append(f"Found English unit '{eu}' in {row['name']} ({name}: {unit})")

print("--- ALL UNIQUE UNITS ---")
for unit, count in units.most_common():
    print(f"'{unit}': {count}")

print("\n--- SUSPICIOUS ABBREVIATIONS/UNITS ---")
for s in suspicious:
    print(s)
