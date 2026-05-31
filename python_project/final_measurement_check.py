
import csv
import json

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

weird_amounts = []
small_cup_fractions = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            name = ing.get('name', '')
            unit = ing.get('unit', '')
            amount = ing.get('amount', 0)
            
            # Check for small cup fractions (1/8 cup = 0.125, etc)
            if unit == 'szklanki' or unit == 'szklanka':
                if amount < 0.4 and amount > 0:
                    small_cup_fractions.append({'id': row['id'], 'recipe': row['name'], 'name': name, 'amount': amount, 'unit': unit})
            
            # Check for very small amounts of liquid or solids that aren't szczypta
            if amount < 0.1 and amount > 0 and unit not in ['kg', 'l', 'szczypta', 'szczypty', 'kropla', 'krople']:
                weird_amounts.append({'id': row['id'], 'recipe': row['name'], 'name': name, 'amount': amount, 'unit': unit})

print("--- SMALL CUP FRACTIONS (< 0.4 szklanki) ---")
for item in small_cup_fractions:
    print(f"ID {item['id']}: {item['amount']} {item['unit']} of {item['name']} in {item['recipe']}")

print("\n--- WEIRD SMALL AMOUNTS (< 0.1) ---")
for item in weird_amounts:
    print(f"ID {item['id']}: {item['amount']} {item['unit']} of {item['name']} in {item['recipe']}")
