
import csv
import json
from collections import Counter

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

ingredient_names = Counter()
recipe_names = []

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        recipe_names.append(row['name'])
        ingredients = json.loads(row['ingredients'])
        for ing in ingredients:
            ingredient_names[ing.get('name', '')] += 1

# 1. Output all unique ingredient names sorted alphabetically for visual inspection
print("--- ALL UNIQUE INGREDIENTS (A-Z) ---")
sorted_ingredients = sorted(ingredient_names.items())
for name, count in sorted_ingredients:
    # Print only if it looks suspicious or just print all in chunks
    # Let's focus on potentially weird starts/ends or common translation traps
    name_l = name.lower()
    suspicious = False
    
    # Common machine translation artifacts or weird patterns
    bad_patterns = ['z ', 'do ', 'na ', 'dla ', 'z s ', ' i ', ' (', ' - ', '.', ',', '!', '?', ')']
    # Many valid ingredients have these, but let's look for unusual ones
    
    # English-sounding or untranslated
    if any(word in name_l for word in ['fresh', 'dried', 'chopped', 'sliced', 'minced', 'ground', 'frozen', 'large', 'small', 'medium']):
        suspicious = True
        
    # Very long names often contain instructions
    if len(name) > 35:
        suspicious = True

    # Names starting with lowercase (except known ones)
    if name and name[0].islower() and name_l not in ['sól', 'pieprz', 'oliwa', 'woda']:
        # Most our ingredients are lowercase, which is fine, but let's check
        pass

    if suspicious or count == 1: # Rare ingredients are often typos
        print(f"'{name}' ({count})")

print("\n--- ALL UNIQUE INGREDIENTS (First 100) ---")
for name, count in sorted_ingredients[:100]:
    print(f"'{name}' ({count})")

print("\n--- RECIPE NAMES (First 50) ---")
for name in recipe_names[:50]:
    print(name)
