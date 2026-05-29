import requests
import json
import re
import time

API_KEY = "92a811abc88b43a88f54e9e4455ca33e"
URL = "https://api.spoonacular.com/recipes/complexSearch"

def clean_html(text):
    if not text: return ""
    clean = re.compile('<.*?>')
    return " ".join(re.sub(clean, '', text).split())

def get_instructions(r):
    analyzed = r.get("analyzedInstructions")
    if analyzed and len(analyzed) > 0:
        steps = []
        for section in analyzed:
            for step in section.get("steps", []):
                num = step.get("number")
                desc = step.get("step")
                steps.append(f"{num}. {desc}")
        return "\n".join(steps)
    return clean_html(r.get("instructions", ""))

def process_batch(query_params, limit, current_list, used_ids):
    params = {
        "apiKey": API_KEY,
        "number": limit,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "instructionsRequired": True,
        "addRecipeInstructions": True,
        **query_params
    }
    
    response = requests.get(URL, params=params)
    if response.status_code == 200:
        results = response.json().get("results", [])
        for r in results:
            rid = r.get("id")
            if rid not in used_ids:
                used_ids.add(rid)
                
                # Pobieranie czasów
                prep = r.get("preparationMinutes")
                cook = r.get("cookingMinutes")
                total = r.get("readyInMinutes")

                recipe = {
                    "id": len(current_list) + 1,
                    "name": r.get("title"),
                    "instructions": get_instructions(r),
                    "description": clean_html(r.get("summary")),
                    "ingredients": {ing["name"]: f"{ing['amount']} {ing['unit']}" for ing in r.get("extendedIngredients", [])},
                    "cuisine": r.get("cuisines")[0] if r.get("cuisines") else "International",
                    "warmth": "salad" not in r.get("title").lower() and "cold" not in r.get("title").lower(),
                    "tags": list(set(r.get("dishTypes", []) + r.get("diets", []))),
                    "prep_time": prep if prep and prep > 0 else None,
                    "cook_time": cook if cook and cook > 0 else None,
                    "total_time": total if total and total > 0 else None,
                    "image_url": r.get("image")
                }
                current_list.append(recipe)
    else:
        print(f"Błąd API: {response.status_code}")

# --- URUCHOMIENIE ---
final_list = []
used_ids = set()

# 1. 150 Wegetariańskich
print("Pobieram 150 przepisów wegetariańskich...")
process_batch({"diet": "vegetarian", "type": "main course,lunch", "sort": "popularity"}, 100, final_list, used_ids)
process_batch({"diet": "vegetarian", "type": "main course,lunch", "offset": 100}, 50, final_list, used_ids)

# 3. 150 Ogólnych (klasyki, szybkie obiady)
print("Pobieram 150 przepisów ogólnych (szybkie i popularne)...")
process_batch({"type": "main course,dinner", "maxReadyTime": 45, "sort": "popularity"}, 150, final_list, used_ids)

# Zapis
with open('database_300_wege_mix.json', 'w', encoding='utf-8') as f:
    json.dump(final_list[:300], f, indent=4, ensure_ascii=False)

print(f"\nGotowe! Baza zawiera {len(final_list)} przepisów (ok. 150 wege/vegan).")