import requests
import json
import re
import time

# --- KONFIGURACJA ---
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

def fetch_recipes(query_params, target_count, current_list, used_ids):
    offset = 0
    while len(current_list) < target_count:
        params = {
            "apiKey": API_KEY,
            "addRecipeInformation": True,
            "fillIngredients": True,
            "instructionsRequired": True,
            "number": 50,  # Pobieramy w mniejszych paczkach
            "offset": offset,
            **query_params
        }
        
        print(f"Pobieram {params.get('diet', 'ogólne')} | Offset: {offset} | Obecnie: {len(current_list)}")
        response = requests.get(URL, params=params)
        
        if response.status_code == 402:
            print("!!! Przekroczono limit punktów API na dziś. Zapisuję to, co mamy. !!!")
            break
        elif response.status_code != 200:
            print(f"Błąd: {response.status_code}")
            break
            
        results = response.json().get("results", [])
        if not results:
            break
            
        for r in results:
            rid = r.get("id")
            if rid not in used_ids:
                used_ids.add(rid)
                
                prep = r.get("preparationMinutes") or 0
                cook = r.get("cookingMinutes") or 0
                total = r.get("readyInMinutes") or 0

                recipe = {
                    "id": len(current_list) + 1,
                    "name": r.get("title"),
                    "instructions": get_instructions(r),
                    "description": clean_html(r.get("summary")),
                    "ingredients": {ing["name"]: f"{ing['amount']} {ing['unit']}" for ing in r.get("extendedIngredients", [])},
                    "cuisine": r.get("cuisines")[0] if r.get("cuisines") else "International",
                    "warmth": "salad" not in r.get("title").lower() and "cold" not in r.get("title").lower(),
                    "tags": list(set(r.get("dishTypes", []) + r.get("diets", []))),
                    "prep_time": prep if prep > 0 else None,
                    "cook_time": cook if cook > 0 else None,
                    "total_time": total if total > 0 else None,
                    "image_url": r.get("image")
                }                
                current_list.append(recipe)
                if len(current_list) >= target_count:
                    break
        
        offset += 50
        time.sleep(1) # Ochrona przed spamem

# --- START MISJI ---
final_database = []
used_ids = set()

# 1. Szybkie i bezpieczne (max 20 min) - 150 sztuk
print("\n--- MISJA 1: Szybkie posiłki ---")
fetch_recipes({"maxReadyTime": 20, "type": "main course,lunch"}, 150, final_database, used_ids)

# 2. Wegetariańskie klasyki (obiady/lunche) - 450 sztuk
print("\n--- MISJA 2: Wegetariańskie ---")
fetch_recipes({"diet": "vegetarian", "type": "main course,lunch", "sort": "popularity"}, 600, final_database, used_ids)

# 3. Desery - 150 sztuk
print("\n--- MISJA 3: Desery ---")
fetch_recipes({"type": "dessert", "sort": "popularity"}, 750, final_database, used_ids)

# 4. Ogólne popularne (reszta do 1000)
print("\n--- MISJA 4: Ogólne popularne ---")
fetch_recipes({"type": "main course", "sort": "popularity"}, 1000, final_database, used_ids)

# ZAPIS
with open('database_1000_final.json', 'w', encoding='utf-8') as f:
    json.dump(final_database, f, indent=4, ensure_ascii=False)

print(f"\nKONIEC! Zebrano łącznie: {len(final_database)} przepisów.")