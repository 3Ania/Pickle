
import csv
import json
import re

def round_amount(amount):
    if not isinstance(amount, (int, float)):
        try: amount = float(amount)
        except: return amount
    conversions = {
        56.699: 55, 113.398: 115, 226.796: 225, 340.194: 340, 453.592: 450,
        680.389: 680, 907.185: 900, 28.35: 30, 14.175: 15, 42.524: 40,
        170.097: 170, 198.447: 200, 255.146: 250, 311.845: 310, 396.893: 400,
        118.294: 120, 236.588: 235, 354.882: 355, 473.176: 475, 946.353: 950,
    }
    for key, val in conversions.items():
        if abs(amount - key) < 0.1: return val
    if amount > 10: return round(amount / 5) * 5
    else: return round(amount, 2)

def fix_name(name):
    # Standardize to lowercase immediately
    name = name.lower().strip()
    
    # Branded and technical translations
    translations = {
        'hershey': 'czekolada',
        'kikkoman': 'sos sojowy',
        'knorr': 'sos',
        'campbell': 'zupa',
        'swanson': 'kurczak',
        'braggs': 'przyprawa',
        'duncan hines': 'mieszanka do ciasta',
        'johnsonville': 'kiełbasa',
        'extra virgin': 'tłoczona na zimno',
        'm&m\'sy': 'cukierki czekoladowe',
        'dr. pieprz': 'napoje typu cola',
        'pocałunki caramel hershey': 'karmelki czekoladowe',
        'nuggetsy hershey': 'kawałki czekolady',
        'clv czosnek': 'czosnek',
        'ewoo': 'oliwa z oliwek',
        'chile': 'chili',
        'tost teksański z czosnkiem nowojorskim': 'tosty czosnkowe',
        'tost teksański z serem nowojorskim': 'tosty serowe',
        'bochenek chleba jajecznego - skórka': 'chleb jajeczny',
        'łyżki „specjalnego ciemnego” proszku kakaowego hershey\'s': 'kakao ciemne',
        'braggs płynne aminokwasy': 'sos sojowy (aminokwasy roślinne)',
        'sos sojowy kikkomana': 'sos sojowy',
        'sos sojowy kkikkoman': 'sos sojowy',
        'mennica': 'mięta',
        'ożywić': 'imbir',
        'ożywienie': 'imbir',
        'piekielnie': 'pietruszka',
        'pępek pomarańczowy': 'pomarańcza navel',
        'pępek pomarańczy': 'pomarańcza navel'
    }
    
    # Apply word-based brand replacements
    for brand, generic in translations.items():
        if brand in name:
            name = name.replace(brand, generic)
    
    # Generic marketing strip
    name = re.sub(r'^(naturalne|świeżo|pyszne|najlepsze|dobre|wysokiej jakości|całkowicie|klasyczna|dekadencka)\s+', '', name)
    name = name.replace(' (opcjonalnie)', '').replace('(opcjonalnie)', '')
    
    # Adjective placement for ground/mielony
    if any(x in name for x in ['mielony ', 'mielona ', 'mielone ']):
        name = name.replace('mielony ', '').replace('mielona ', '').replace('mielone ', '')
        base_name = name.lower()
        if any(f in base_name for f in ['papryka', 'kolendra', 'kurkuma', 'gorczyca', 'szałwia', 'gałka', 'wołowina', 'indyk']):
            name = name + ' mielona'
        elif any(n_w in base_name for n_w in ['siemię', 'ziele', 'pomidory', 'goździki']):
            name = name + ' mielone'
        else:
            name = name + ' mielony'

    # Suffix adjectives
    for adj in ['świeży', 'świeża', 'świeże', 'suszony', 'suszona', 'suszone', 'posiekany', 'posiekana', 'posiekane']:
        if adj + ' ' in name:
            name = name.replace(adj + ' ', '')
            name = name + ' ' + adj

    # Cleanup artifacts
    name = re.sub(r'liście\s+', '', name)
    name = re.sub(r'gałązki\s+', '', name)
    name = re.sub(r'ząbki\s+', '', name)
    name = re.sub(r'ząbek\s+', '', name)
    name = re.sub(r'[■▪▪■*?+]', '', name)
    
    return name.strip()

def fix_unit(unit, name, amount):
    if not isinstance(amount, (int, float)):
        try: amount = float(amount)
        except: amount = 0
            
    unit = unit.lower().strip()
    name = name.lower().strip()
    
    # All packaging to weights
    package_map = {
        'szparagi': 250, 'dynia': 400, 'drożdże': 7, 'pomidory': 400, 'kukurydza': 340,
        'pico de gallo': 200, 'makaron': 250, 'szafran': 0.1, 'sos': 300,
        'ziemniaki': 1000, 'nasiona': 100, 'ser': 200, 'fasola': 400, 'ciecierzyca': 400,
        'sałata': 300, 'szpinak': 200, 'mleko': 400, 'tuńczyk': 185, 'łosoś': 170, 
        'grzyby': 250, 'groszek': 400, 'karmelki': 150, 'ciasto': 300
    }

    if unit in ['opakowanie', 'opakowania', 'pudełko', 'paczka', 'torba', 'puszka', 'puszki', 'słoik']:
        for item, weight in package_map.items():
            if item in name:
                return 'g', amount * weight
        return 'g', amount * 400

    unit_map = {
        'medium size': 'średnia sztuka', 'large size': 'duża sztuka', 'small size': 'mała sztuka',
        'loaf': 'bochenek', 'stick': 'sztuka (ok. 110g)', 'sticks': 'sztuki (ok. 110g)',
        'pts': 'szklanki', 'ml': 'ml', 'filiżanka': 'szklanka', 'filiżanki': 'szklanki',
        'uncje': 'g', 'funty': 'g', 'gramy': 'g', 'kilogram': 'kg', 'cal': 'cm', 'cale': 'cm',
        'tb': 'łyżka', 'litr': 'l', 'szt': 'sztuka', 'gramów': 'g', 'uncja': 'g', 'funt': 'g',
        'sześcian': 'kostka', 'mililitry': 'ml', 'kwarta': 'l', 'plasterek': 'plasterek',
        'plasterki': 'plasterki', 'butelka': 'ml'
    }
    
    final_amount = amount
    if unit in unit_map:
        if unit == 'pts': final_amount = amount * 2
        elif unit == 'uncje' or unit == 'uncja': final_amount = amount * 28.35
        elif unit == 'funty' or unit == 'funt': final_amount = amount * 453.59
        elif unit == 'cal' or unit == 'cale': final_amount = amount * 2.54
        elif unit == 'kwarta': final_amount = amount * 940
        elif unit == 'butelka': final_amount = amount * 330
        return unit_map[unit], final_amount

    if unit in ['', 'porcja', 'porcje', 'sztuka', 'sztuki', 'duży', 'średni', 'mały', 'bardzo duży']:
        if any(x in name for x in ['sól', 'pieprz', 'papryka', 'cynamon', 'zioła', 'kolendra', 'pietruszka']):
            return ('szczypta' if amount <= 1 else 'szczypty'), (1 if amount == 0 else amount)
        return unit, amount

    if (unit == 'łyżeczka' or unit == 'łyżeczki') and amount < 0.2:
        return 'szczypta', 1
    
    if unit == 'szklanka' and amount < 0.2:
        return 'łyżki', 2

    # Pluralization
    if unit == 'ząbki' and amount <= 1: return 'ząbek', amount
    if unit == 'ząbek' and amount > 1: return 'ząbki', amount
    if unit == 'łyżki' and amount <= 1: return 'łyżka', amount
    if unit == 'łyżka' and amount > 1: return 'łyżki', amount
    if unit == 'łyżeczki' and amount <= 1: return 'łyżeczka', amount
    if unit == 'łyżeczka' and amount > 1: return 'łyżeczki', amount
    if unit == 'szczypty' and amount <= 1: return 'szczypta', amount
    if unit == 'szczypta' and amount > 1: return 'szczypty', amount
    if unit == 'szklanki' and amount <= 1: return 'szklanka', amount
    if unit == 'szklanka' and amount > 1: return 'szklanki', amount
    
    return unit, final_amount

def fix_recipe_name(name):
    fixes = {
        'Sałatka z kalafiora w Egipcie': 'Sałatka z kalafiora po egipsku',
        'Zupa ze szparagami i groszkiem: prawdziwa wygoda': 'Kremowa zupa ze szparagów i groszku',
        'Schłodzone szwajcarskie płatki owsiane': 'Szwajcarskie płatki owsiane (Bircher Muesli)',
        'Miska na ziarno Quinoa Instant Pot': 'Miska obfitości z komosą ryżową',
        'Hummus grzybowy Crostini': 'Crostini z hummusem grzybowym',
        'Klin Pełny Zupy Brokułowej': 'Zupa krem z brokułów',
        'Kolejna zupa z soczewicy': 'Klasyczna zupa z soczewicy',
        'Powrót do skrzydełek kalafiora': 'Pieczone skrzydełka z kalafiora',
        'Łatwy domowy ryż i fasola': 'Ryż z fasolą po domowemu',
        'Zupa pomidorowa i soczewica': 'Zupa pomidorowa z soczewicą',
        'Przekąski: Muffinki Frittata': 'Muffinki jajeczne (Frittata)',
        'Pyszne puree ziemniaczane': 'Najlepsze puree ziemniaczane',
        'Pesto pistacjowe Penne': 'Penne z pesto pistacjowym'
    }
    return fixes.get(name, name)

csv_path = 'recipes_baza.csv'
output_path = 'python_project/przygotowanie_bazy/database_flawless_final.csv'

rows = []
with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        ingredients = json.loads(row['ingredients'])
        tags = row.get('tags', '').lower()
        is_vegetarian = 'vegetarian' in tags or 'vegan' in tags
        row['name'] = fix_recipe_name(row['name'])
        
        ing_dict = {}
        for ing in ingredients:
            name = ing.get('name', '')
            unit = ing.get('unit', '')
            amount = ing.get('amount', 0)
            
            if 'goździk' in name.lower() and ('ząbek' in unit.lower() or 'ząbki' in unit.lower() or 'ząbek' in name.lower() or 'ząbki' in name.lower()):
                name = 'czosnek'
                if unit == '': unit = 'ząbki'
            
            name = fix_name(name)
            unit, amount = fix_unit(unit, name, amount)
            
            name_lower = name.lower()
            if is_vegetarian:
                if 'bulion drobiowy' in name_lower or 'rosół z kurczaka' in name_lower:
                    name = name.replace('drobiowy', 'warzywny').replace('Drobiowy', 'Warzywny')
            if name_lower == 'potatoes': name = 'ziemniaki'
            if name_lower == 'chilli': name = 'chili'
            
            amount = round_amount(amount)
            
            key = name + "_" + unit
            if key in ing_dict:
                ing_dict[key]['amount'] += amount
            else:
                ing_dict[key] = {'name': name, 'unit': unit, 'amount': amount}
        
        final_ings = list(ing_dict.values())
        row['ingredients'] = json.dumps(final_ings, ensure_ascii=False)
        row['ingredient_names'] = str([ing['name'] for ing in final_ings])
        rows.append(row)

unique_recipes = {}
for row in rows:
    name_key = row['name'].lower().strip()
    if name_key not in unique_recipes:
        unique_recipes[name_key] = row

with open(output_path, mode='w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_recipes.values())

print(f"Processed {len(rows)} recipes. Saved {len(unique_recipes)} unique recipes.")
