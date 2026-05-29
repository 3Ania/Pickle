import requests
import pandas as pd
import json
import re
import time
from deep_translator import GoogleTranslator

# --- KONFIGURACJA ---
API_KEY = "92a811abc88b43a88f54e9e4455ca33e"
TARGET_TOTAL = 500

translator = GoogleTranslator(source='en', target='pl')

# Wczytujemy to, co już mamy na dysku
df_existing = pd.read_csv("przygotowanie_bazy/database_final_unique.csv")
existing_names = set(df_existing['name'].dropna().tolist())

missing_count = TARGET_TOTAL - len(df_existing)
print(f"Obecna liczba przepisów: {len(df_existing)}")
print(f"Brakuje nam dokładnie: {missing_count} przepisów. Zaczynamy łowy!")

# --- FUNKCJE POMOCNICZE (z Twojego oryginalnego skryptu) ---
def translate_pl(text):
    if not text or len(text) < 2: return text
    try:
        return translator.translate(text[:4500])
    except:
        return text

def get_clean_instructions(r):
    steps_list = []
    analyzed = r.get("analyzedInstructions")
    if analyzed and len(analyzed) > 0:
        for section in analyzed:
            for step in section.get("steps", []):
                num = step.get("number")
                desc = step.get("step")
                steps_list.append(f"{num}. {desc}")
    else:
        instr = r.get("instructions")
        if instr:
            instr = re.sub(r'<[^>]+>', '', instr)
            steps_list.append(instr)
    if not steps_list: return ""
    return translate_pl("\n".join(steps_list))

def process_single_recipe(r):
    eng_name = r.get("title", "")
    pl_name = translate_pl(eng_name)
    
    # Podwójne sprawdzenie powtórek!
    if pl_name in existing_names:
        return None

    # Tłumaczenie reszty danych
    pl_instructions = get_clean_instructions(r)
    pl_description = translate_pl(re.sub(r'<[^>]+>', '', r.get("summary", "")))
    
    ingredients_list = []
    names_list = set()
    for ing in r.get("extendedIngredients", []):
        pl_ing_name = translate_pl(ing.get("name", ""))
        pl_unit = translate_pl(ing.get("unit", ""))
        amount = ing.get("amount", 0)
        
        ingredients_list.append({
            "name": pl_ing_name,
            "unit": pl_unit,
            "amount": amount
        })
        names_list.add(pl_ing_name)

    tags = []
    for tag_key in ["dishTypes", "diets", "occasions"]:
        tags.extend(r.get(tag_key, []))

    return {
        "id": r.get("id"), # Tymczasowe ID ze Spoonacular
        "name": pl_name,
        "instructions": pl_instructions,
        "description": pl_description,
        "ingredients": json.dumps(ingredients_list, ensure_ascii=False),
        "cuisine": translate_pl(r.get("cuisines", ["Międzynarodowa"])[0]) if r.get("cuisines") else "Międzynarodowa",
        "warmth": True,
        "tags": json.dumps(tags, ensure_ascii=False),
        "prep_time": r.get("preparationMinutes"),
        "cook_time": r.get("cookingMinutes"),
        "total_time": r.get("readyInMinutes"),
        "image_url": r.get("image"),
        "ingredient_names": str(list(names_list))
    }

# --- PĘTLA POBIERAJĄCA ---
new_recipes = []
current_offset = 450 # Zaczynamy daleko, żeby ominąć stare powtórki

while len(new_recipes) < missing_count:
    print(f"Odpytuję API z offsetem {current_offset}...")
    params = {
        "apiKey": API_KEY,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "instructionsRequired": True,
        "number": 30, # Pobieramy po 30 na raz
        "offset": current_offset,
        "sort": "random" # Próbujemy zmusić API do podania czegoś nowego
    }
    
    res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params=params)
    
    if res.status_code != 200:
        print("Błąd API! Przerywam.")
        break
        
    results = res.json().get("results", [])
    if not results:
        print("Brak wyników z API przy tym offsecie.")
        current_offset += 30
        continue
        
    for r in results:
        if len(new_recipes) >= missing_count:
            break # Mamy już 107!
            
        recipe_data = process_single_recipe(r)
        if recipe_data is not None:
            new_recipes.append(recipe_data)
            existing_names.add(recipe_data['name']) # Dodajemy do pamięci, żeby uniknąć duplikatów w tej samej paczce
            print(f"[{len(new_recipes)}/{missing_count}] Dodano: {recipe_data['name']}")
        
    current_offset += 30
    time.sleep(1) # Chwila oddechu dla API

# --- ZAPIS ---
df_new = pd.DataFrame(new_recipes)
df_new.to_csv("missing_107_raw.csv", index=False, encoding='utf-8')
print(f"✅ SUKCES! Zapisano surowe {len(new_recipes)} przepisów do 'missing_107_raw.csv'.")