
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_final_production.csv'

units = Counter()
ingredient_names = Counter()
suspicious_entries = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            ingredients = json.loads(row['ingredients'])
            for ing in ingredients:
                name = ing.get('name', '')
                unit = ing.get('unit', '')
                amount = ing.get('amount', 0)
                
                units[unit] += 1
                ingredient_names[name] += 1
                
                # Check for suspicious units
                if unit.lower() in ['clove', 'cloves', 'cup', 'cups', 'oz', 'lb', 'pound', 'stick', 'can', 'bunch', 'cloves', 'clove']:
                     suspicious_entries.append(f"English unit: {unit} in {row['name']} ({name})")
                
                # Check for long floats
                if isinstance(amount, float) and len(str(amount)) > 5:
                    suspicious_entries.append(f"Long float: {amount} {unit} of {name} in {row['name']}")
                
                # Check for unit "porcje" which might be "servings" or "portions" but sometimes used for items
                if unit == 'porcje':
                    suspicious_entries.append(f"Unit 'porcje': {amount} {unit} of {name} in {row['name']}")

                # Check for "wapno" (should be limonka)
                if 'wapno' in name.lower():
                    suspicious_entries.append(f"Found 'wapno': {name} in {row['name']}")

                # Check for "goździk" near "czosnek"
                if 'goździk' in name.lower() and 'czosnek' in row['name'].lower():
                    suspicious_entries.append(f"Suspicious 'goździk' (garlic cloves?): {name} in {row['name']}")

                # Check for "móc"
                if name.lower() == 'móc' or unit.lower() == 'móc':
                    suspicious_entries.append(f"Found 'móc': {name} ({unit}) in {row['name']}")

                # Check for "krem"
                if 'krem' in name.lower() or 'krem' in unit.lower():
                     suspicious_entries.append(f"Found 'krem': {name} ({unit}) in {row['name']}")

        except Exception as e:
            print(f"Error parsing ingredients for {row.get('name')}: {e}")

print("--- UNIQUE UNITS ---")
for unit, count in units.most_common():
    print(f"{unit}: {count}")

print("\n--- SUSPICIOUS ENTRIES ---")
for entry in suspicious_entries[:50]:
    print(entry)
if len(suspicious_entries) > 50:
    print(f"... and {len(suspicious_entries) - 50} more")
