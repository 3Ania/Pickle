
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

names = Counter()
units = Counter()
full_ingredients = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            name = ing.get('name', '')
            unit = ing.get('unit', '')
            amount = ing.get('amount', 0)
            names[name] += 1
            units[unit] += 1
            full_ingredients.append({'name': name, 'unit': unit, 'amount': amount, 'recipe': row['name']})

# 1. Output all unique units
print("--- ALL UNIQUE UNITS ---")
for unit, count in sorted(units.items(), key=lambda x: x[1], reverse=True):
    print(f"'{unit}': {count}")

# 2. Output suspicious names (too short, too long, contain non-Polish chars, or known bad words)
print("\n--- SUSPICIOUS NAMES ---")
bad_keywords = ['ożywić', 'można', 'móc', 'mleczarnia', 'wapno', 'cytrynowy', 'pomarańczowy', 'czerwony', 'żółty', 'zielony', 'ciężki', 'lekki', 'pojedynczy', 'podwójny', 'duży', 'mały', 'średni']
for name, count in sorted(names.items()):
    name_l = name.lower()
    is_suspicious = False
    if len(name) < 3: is_suspicious = True
    if any(k in name_l for k in bad_keywords): is_suspicious = True
    if any(char in name_l for char in 'abcdefghijklmnopqrstuvwxyz') and not any(char in name_l for char in 'ąćęłńóśźż'):
        # This is a bit weak because many words like 'pasta' or 'mango' are same in English/Polish
        # but maybe check for common English suffixes or words
        english_indicators = ['chopped', 'sliced', 'minced', 'dried', 'fresh', 'frozen', 'clove', 'cup', 'ounce', 'pound']
        if any(ei in name_l for ei in english_indicators):
            is_suspicious = True
    
    if is_suspicious:
        print(f"'{name}': {count}")

# 3. Check for amount outliers
print("\n--- AMOUNT OUTLIERS ---")
for ing in full_ingredients:
    if isinstance(ing['amount'], (int, float)):
        if ing['amount'] > 2000 and ing['unit'] != 'ml' and ing['unit'] != 'g':
            print(f"Large amount: {ing['amount']} {ing['unit']} of {ing['name']} in {ing['recipe']}")
        if 0 < ing['amount'] < 0.01:
             print(f"Tiny amount: {ing['amount']} {ing['unit']} of {ing['name']} in {ing['recipe']}")
