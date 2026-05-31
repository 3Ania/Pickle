
import csv
import json
import re

def round_amount(amount):
    if not isinstance(amount, (int, float)):
        try: amount = float(amount)
        except: return 0
    
    # Standard kitchen rounding for imperial-to-metric leftovers
    conversions = {
        56.699: 55, 113.398: 115, 226.796: 225, 340.194: 340, 453.592: 450,
        680.389: 680, 907.185: 900, 28.35: 30, 14.175: 15, 42.524: 40,
        170.097: 170, 198.447: 200, 255.146: 250, 311.845: 310, 396.893: 400,
        118.294: 120, 236.588: 235, 354.882: 355, 473.176: 475, 946.353: 950,
    }
    for key, val in conversions.items():
        if abs(amount - key) < 0.1: amount = val; break
    
    if amount > 10: amount = round(amount / 5) * 5
    else: amount = round(amount, 2)
    
    # Final step: Remove .0 by converting to int if it's a whole number
    if amount == int(amount):
        return int(amount)
    return amount

def fix_name(name):
    name = name.lower().strip()
    translations = {
        'cytrynowy': 'cytryna', 'pomarańczowy': 'pomarańcza', 'limonkowy': 'limonka',
        'opatrunek': 'sos sałatkowy', 'szpinaku': 'szpinak', 'czosnku': 'czosnek',
        'cebuli': 'cebula', 'papryki': 'papryka', 'curd cytrynowy': 'krem cytrynowy (lemon curd)',
        'winegret cytrynowy meyera': 'winegret cytrynowy', 'pępek pomarańczy': 'pomarańcza navel',
        'pępek pomarańczowy': 'pomarańcza navel'
    }
    if name in translations: return translations[name]
    nominative_map = {
        'oliwy': 'oliwa z oliwek', 'wody': 'woda', 'mleka': 'mleko', 'cukru': 'cukier',
        'soli': 'sól', 'pieprzu': 'pieprz', 'mąki': 'mąka', 'ryżu': 'ryż', 'imbiru': 'imbir',
        'mięty': 'mięta', 'kolendry': 'kolendra', 'pietruszki': 'pietruszka', 'bazylii': 'bazylia',
        'rozmarynu': 'rozmaryn', 'tymianku': 'tymianek', 'szałwii': 'szałwia',
        'kapusty włoskiej': 'kapusta włoska', 'komosy ryżowej': 'komosa ryżowa', 'melasa z granatów': 'melasa z granatu'
    }
    if name in nominative_map: return nominative_map[name]
    if any(x in name for x in ['mielony ', 'mielona ', 'mielone ']):
        base = name.replace('mielony ', '').replace('mielona ', '').replace('mielone ', '')
        if any(f in base for f in ['papryka', 'kolendra', 'kurkuma', 'gorczyca', 'szałwia', 'gałka', 'wołowina', 'indyk']):
            name = base + ' mielona'
        elif any(n_val in base for n_val in ['siemię', 'ziele', 'pomidory', 'goździki']):
            name = base + ' mielone'
        else:
            name = base + ' mielony'
    return name.strip()

def get_correct_unit_and_amount(name_l, unit_l, amount_raw):
    try: amount = float(amount_raw)
    except: amount = 0
    if 'uncj' in unit_l: return 'g', amount * 28.35
    if any(x in name_l for x in ['oliwa', 'olej', 'woda', 'mleko', 'sok', 'ocet', 'bulion', 'syrop', 'melasa', 'soda', 'rum', 'sherry']):
        if 'szczypt' in unit_l or unit_l == '':
            if amount < 2: return 'łyżeczka', amount
            return 'ml', amount * 15
        return unit_l, amount
    if any(x in name_l for x in ['kapusta', 'sałata', 'komosa', 'ryż', 'fasola', 'ciecierzyca', 'ziemniak', 'marchew', 'soczewica', 'szpinak', 'kalafior', 'makaron', 'tagliatelle', 'penne', 'tofu']):
        if 'szczypt' in unit_l or unit_l == '':
            if any(y in name_l for y in ['kapusta', 'sałata', 'kalafior']): return 'główka', (0.5 if amount < 1 else amount)
            return 'g', (100 if amount < 5 else amount)
        return unit_l, amount
    if any(x in name_l for x in ['sól', 'pieprz', 'cynamon', 'gałka', 'papryka', 'kurkuma', 'kmin', 'zioła']):
        if amount <= 1 and unit_l in ['szczypta', 'szczypty', '']: return 'szczypta', 1
        if unit_l == '': return 'łyżeczka', amount
        return unit_l, amount
    return unit_l, amount

def get_declension(unit_base, amount):
    u_map = {
        'łyżeczka': {'sing': 'łyżeczka', 'dual': 'łyżeczki', 'plural': 'łyżeczek', 'gen': 'łyżeczki'},
        'łyżka': {'sing': 'łyżka', 'dual': 'łyżki', 'plural': 'łyżek', 'gen': 'łyżki'},
        'szklanka': {'sing': 'szklanka', 'dual': 'szklanki', 'plural': 'szklanek', 'gen': 'szklanki'},
        'szczypta': {'sing': 'szczypta', 'dual': 'szczypty', 'plural': 'szczypt', 'gen': 'szczypty'},
        'gałązka': {'sing': 'gałązka', 'dual': 'gałązki', 'plural': 'gałązek', 'gen': 'gałązki'},
        'ząbek': {'sing': 'ząbek', 'dual': 'ząbki', 'plural': 'ząbków', 'gen': 'ząbka'},
        'pęczek': {'sing': 'pęczek', 'dual': 'pęczki', 'plural': 'pęczków', 'gen': 'pęczka'},
        'plasterek': {'sing': 'plasterek', 'dual': 'plasterki', 'plural': 'plasterków', 'gen': 'plasterka'},
        'garść': {'sing': 'garść', 'dual': 'garście', 'plural': 'garści', 'gen': 'garści'},
        'główka': {'sing': 'główka', 'dual': 'główki', 'plural': 'główek', 'gen': 'główki'},
        'kropla': {'sing': 'kropla', 'dual': 'krople', 'plural': 'kropel', 'gen': 'kropli'}
    }
    found = None
    for k in u_map:
        if k in unit_base: found = k; break
    if not found: return unit_base
    if amount == 1: return u_map[found]['sing']
    if 1 < amount < 5 and int(amount) == amount: return u_map[found]['dual']
    if amount >= 5 and int(amount) == amount: return u_map[found]['plural']
    return u_map[found]['gen']

csv_path = 'recipes_baza.csv'
output_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'
rows = []
with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        ing_dict = {}
        for ing in ingredients:
            name = fix_name(ing.get('name', ''))
            unit, amount = get_correct_unit_and_amount(name, ing.get('unit', '').lower(), ing.get('amount', 0))
            amount = round_amount(amount)
            unit = get_declension(unit, amount)
            key = name + "_" + unit
            if key in ing_dict: ing_dict[key]['amount'] += amount
            else: ing_dict[key] = {'name': name, 'unit': unit, 'amount': amount}
        # Final pass for merged amounts to remove .0
        final_ings = []
        for ing in ing_dict.values():
            ing['amount'] = round_amount(ing['amount'])
            final_ings.append(ing)
        row['ingredients'] = json.dumps(final_ings, ensure_ascii=False)
        row['ingredient_names'] = str([i['name'] for i in final_ings])
        rows.append(row)
unique_recipes = {}
for row in rows:
    name_key = row['name'].lower().strip()
    if name_key not in unique_recipes: unique_recipes[name_key] = row
with open(output_path, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(unique_recipes.values())
print("Final aesthetic and numeric polish complete.")
