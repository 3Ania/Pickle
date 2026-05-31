
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_final_production.csv'

units = Counter()
names = Counter()

bad_names = []
bad_units = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            ingredients = json.loads(row['ingredients'])
            for ing in ingredients:
                name = ing.get('name', '').lower()
                unit = ing.get('unit', '').lower()
                
                units[unit] += 1
                names[name] += 1
                
                # Targeted name checks
                if 'wapno' in name:
                    bad_names.append(f"Found 'wapno': {name} in {row['name']}")
                if name == 'móc':
                    bad_names.append(f"Found 'móc': {name} in {row['name']}")
                if 'goździk' in name:
                    bad_names.append(f"Found 'goździk': {name} in {row['name']}")
                if 'krem' in name:
                    bad_names.append(f"Found 'krem': {name} in {row['name']}")
                
                # English units to catch
                english_units = ['medium size', 'pts', 'loaf', 'handful', 'stick', 'sheet', 'drop', 'strip', 'cube', 'fillet', 'small size', 'large size', 'medium piece', 'cup', 'oz', 'lb']
                for eu in english_units:
                    if eu in unit:
                        bad_units.append(f"English unit '{eu}': {unit} in {row['name']} ({name})")

        except Exception as e:
            pass

print("--- TARGETED BAD NAMES ---")
for bn in set(bad_names):
    print(bn)

print("\n--- TARGETED BAD UNITS ---")
for bu in set(bad_units):
    print(bu)

# Print all unique units again to look for more
print("\n--- ALL UNIQUE UNITS (LOWER) ---")
for unit, count in sorted(units.items(), key=lambda x: x[1], reverse=True):
    print(f"'{unit}': {count}")
