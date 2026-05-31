
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

units = Counter()
names = Counter()
suspicious = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            name = ing.get('name', '')
            unit = ing.get('unit', '')
            amount = ing.get('amount', 0)
            
            units[unit] += 1
            names[name] += 1
            
            if isinstance(amount, float) and len(str(amount)) > 5:
                suspicious.append(f"Long float: {amount} {unit} of {name} in {row['name']}")
            
            if unit.lower() in ['cup', 'oz', 'lb', 'pts', 'stick']:
                suspicious.append(f"English unit: {unit} in {row['name']}")

print("--- TOP UNITS ---")
for unit, count in units.most_common(20):
    print(f"{unit}: {count}")

print("\n--- SUSPICIOUS ---")
for s in suspicious[:20]:
    print(s)
if len(suspicious) > 20:
    print(f"... and {len(suspicious)-20} more")
