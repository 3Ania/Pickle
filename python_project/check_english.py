
import csv
import json
import re

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

english_words = ['clove', 'cup', 'ounce', 'pound', 'tablespoon', 'teaspoon', 'cloves', 'cups', 'ounces', 'pounds', 'tablespoons', 'teaspoons', 'fresh', 'dried', 'chopped', 'sliced', 'minced']
suspicious = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            name = ing.get('name', '').lower()
            unit = ing.get('unit', '').lower()
            
            for word in english_words:
                if word in name or word in unit:
                    suspicious.append(f"English word '{word}': {name} / {unit} in {row['name']}")

print("--- SUSPICIOUS ENGLISH WORDS ---")
for s in set(suspicious):
    print(s)
