
import csv
import json
from collections import defaultdict

csv_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

recipes_by_name = defaultdict(list)
recipes_by_ingredients = defaultdict(list)

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    for i, row in enumerate(rows):
        name = row['name'].strip().lower()
        ingredients = json.loads(row['ingredients'])
        # Sort and stringify names for a "signature"
        ing_signature = "|".join(sorted([ing.get('name', '').lower() for ing in ingredients]))
        
        recipes_by_name[name].append(i)
        recipes_by_ingredients[ing_signature].append(i)

duplicates_to_remove = set()

print("--- DUPLICATE NAMES ---")
for name, indices in recipes_by_name.items():
    if len(indices) > 1:
        print(f"Name '{name}' found {len(indices)} times at indices {indices}")
        # Keep the first one, mark others for removal
        for idx in indices[1:]:
            duplicates_to_remove.add(idx)

print("\n--- DUPLICATE INGREDIENT LISTS (Different Names) ---")
for sig, indices in recipes_by_ingredients.items():
    if len(indices) > 1:
        indices_not_removed = [idx for idx in indices if idx not in duplicates_to_remove]
        if len(indices_not_removed) > 1:
            unique_names = set(rows[idx]['name'] for idx in indices_not_removed)
            print(f"Identical ingredients for different names: {unique_names} at indices {indices_not_removed}")
            # Keep the first one
            for idx in indices_not_removed[1:]:
                duplicates_to_remove.add(idx)

print(f"\nTotal duplicates identified: {len(duplicates_to_remove)}")

# Create the unique dataset
unique_rows = [row for i, row in enumerate(rows) if i not in duplicates_to_remove]

output_path = 'python_project/przygotowanie_bazy/database_unique_final.csv'
with open(output_path, mode='w', encoding='utf-8', newline='') as f:
    if unique_rows:
        writer = csv.DictWriter(f, fieldnames=unique_rows[0].keys())
        writer.writeheader()
        writer.writerows(unique_rows)

print(f"Saved {len(unique_rows)} unique recipes to {output_path}")
