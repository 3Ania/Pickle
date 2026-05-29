import requests
import time
import re
from supabase import create_client, Client
from deep_translator import GoogleTranslator

# --- KONFIGURACJA ---
API_KEY = "92a811abc88b43a88f54e9e4455ca33e"
SUPABASE_URL = "https://exoctvegujulyephkzep.supabase.co"
SUPABASE_KEY = "sb_secret_wrIuCm_hBwUe5Mkwiwlflw_iuLPJFct"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
translator = GoogleTranslator(source='en', target='pl')

# Globalny zbiór nazw, by uniknąć duplikatów W TRAKCIE jednej sesji
existing_names = set()

def translate_pl(text):
    if not text or len(text) < 2: return text
    try:
        return translator.translate(text[:4500])
    except:
        return text

def get_clean_instructions(r):
    """Wyciąga instrukcje krok po kroku[cite: 49]."""
    steps_list = []
    analyzed = r.get("analyzedInstructions")
    if analyzed and len(analyzed) > 0:
        for section in analyzed:
            for step in section.get("steps", []):
                num = step.get("number")
                desc = step.get("step")
                steps_list.append(f"{num}. {desc}")
        return "\n".join(steps_list)
    return " ".join(re.sub('<.*?>', '', r.get("instructions") or "").split())

def process_and_upload(recipes_raw):
    global existing_names
    batch = []
    
    for r in recipes_raw:
        title_en = r.get("title")
        
        # Kluczowe: Sprawdzamy ZANIM wyślemy do tłumacza (oszczędność czasu i API)
        if title_en in existing_names:
            continue 

        print(f" -> Nowy przepis! Przetwarzam: {title_en}")
        
        # 1. Przygotowanie składników [cite: 50]
        detailed_ingredients = [] 
        simple_names = []
        
        for ing in r.get("extendedIngredients", []):
            metric = ing.get("measures", {}).get("metric", {})
            name_pl = translate_pl(ing.get("name")).lower().strip()
            
            detailed_ingredients.append({
                "name": name_pl,
                "amount": metric.get("amount"),
                "unit": metric.get("unitShort")
            })
            simple_names.append(name_pl)

        # 2. Budowa rekordu zgodnego z raportem [cite: 47, 48, 51, 52, 53, 54]
        recipe_data = {
            "name": translate_pl(title_en),
            "instructions": translate_pl(get_clean_instructions(r)),
            "description": translate_pl(r.get("summary")[:500]),
            "ingredients": detailed_ingredients,
            "ingredient_names": list(set(simple_names)),
            "cuisine": translate_pl(r.get("cuisines")[0]) if r.get("cuisines") else "Międzynarodowa",
            "warmth": "salad" not in title_en.lower() and "cold" not in title_en.lower(),
            "tags": list(set(r.get("dishTypes", []) + r.get("diets", []))),
            "total_time": r.get("readyInMinutes"),
            "image_url": r.get("image")
        }
        
        batch.append(recipe_data)
        # Dodajemy do zbioru, żeby kolejna misja w tym samym kodzie go nie pobrała
        existing_names.add(title_en)

    if batch:
        supabase.table("recipes").insert(batch).execute()
        print(f"✅ Dodano {len(batch)} nowych przepisów.")

def run_mission(query_params, count, offset=0):
    params = {
        "apiKey": API_KEY,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "instructionsRequired": True,
        "number": count,
        "offset": offset,
        **query_params
    }
    res = requests.get("https://api.spoonacular.com/recipes/complexSearch", params=params)
    if res.status_code == 200:
        process_and_upload(res.json().get("results", []))
    else:
        print(f"Błąd API: {res.status_code}")

# --- START SESJI ---
# 1. Pobierz aktualny stan bazy [cite: 44]
print("Sprawdzam bazę danych...")
res_init = supabase.table("recipes").select("name").execute()
existing_names = {r['name'] for r in res_init.data}

# 2. DZIEŃ 2 (Przykład: offset ustawiony tak, by omijał to co pobraliśmy wcześniej)
# Jeśli wczoraj pobrałaś 35 szybkich wege, dzisiaj ustawiasz offset=35, jutro offset=70 itd.

DAILY_OFFSET_WEGE = 205 # Zmień to jutro na 70
DAILY_OFFSET_MEAT = 73 # Zmień to jutro na 30

# WEGETARIAŃSKIE (70% bazy)
run_mission({"diet": "vegetarian", "maxReadyTime": 30}, 35, offset=DAILY_OFFSET_WEGE)
run_mission({"diet": "vegetarian", "minReadyTime": 31}, 35, offset=DAILY_OFFSET_WEGE)

# MIĘSNE (30% bazy)
run_mission({"excludeDiet": "vegetarian", "maxReadyTime": 30}, 15, offset=DAILY_OFFSET_MEAT)
run_mission({"excludeDiet": "vegetarian", "minReadyTime": 31}, 15, offset=DAILY_OFFSET_MEAT)