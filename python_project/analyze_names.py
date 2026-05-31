
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

names = Counter()

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            names[ing.get('name', '')] += 1

print("--- SHORT OR SUSPICIOUS NAMES ---")
for name, count in names.items():
    if len(name) < 4 or name.lower() in ['ożywić', 'można', 'móc', 'mleczarnia', 'krem', 'wapno', 'cytrynowy', 'pomarańczowy', 'czerwony', 'żółty', 'zielony']:
        print(f"'{name}': {count}")
