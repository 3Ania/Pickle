import pandas as pd
import json
import ast
import re

INPUT_FILE = "przygotowanie_bazy/database_500_perfect.csv"
OUTPUT_FILE = "przygotowanie_bazy/database_500_ultimate.csv"

# MEGA-ŁATKA na błędy z najnowszej puli 107 przepisów
NEW_FIXES = {
    "krem z kamienia nazębnego": "kamień winny",
    "stan nietrzeźwy": "szklanka", # (Pint to ok 2 szklanki, jednostka w przepisie to 1.5, pasuje idealnie do bitej śmietany)
    "koszerna sól i pieprz": "sól i pieprz",
    "kurczak – ten tutaj waży 4,5 funta.": "kurczak",
    "grzyby namoczone w ciepłych 2 łyżeczkach korzenia imbiru": "grzyby",
    "0,3 uncji pomidorków koktajlowych": "pomidorki koktajlowe",
    "na 4 zielone cebule": "dymka",
    "bulion knorr. kostki diss 2 szklanki": "kostka bulionowa",
    "słodkie ziemniaki ignamy -lub- 5 i słodkie ziemniaki": "bataty",
    "przyprawy: słodka papryka 1": "słodka papryka",
    "1/2 szklanki jabłka": "jabłko",
    "0,6 uncji bekonu": "boczek",
    "daiya wegański m zarella „ser": "wegańska mozzarella",
    "daiya wegański m zarella „ser\"": "wegańska mozzarella",
    "env niskokaloryczna mieszanka budyniowa czekoladowa": "budyń czekoladowy",
    "es okrągłe owijki do sajgonek": "papier ryżowy",
    "kawa w proszku": "kawa rozpuszczalna",
    "zmielony kokos": "wiórki kokosowe",
    "mleko/śmietanka kokosowa": "mleko kokosowe",
    "odrobina oliwy z oliwek": "oliwa z oliwek"
}

# Całe zdania / śmieci, które musimy całkowicie wyrzucić z listy składników
TO_DELETE_ENTIRELY = [
    "czas pieczenia: minuty",
    "czas przygotowania: minuty",
    "czas gotowania: minuty"
]

def fix_text(text):
    if not isinstance(text, str): return text
    fixed_text = text
    
    # Naprawa z nowego słownika
    for bad, good in NEW_FIXES.items():
        # Używamy re.escape by uniknąć problemów ze znakami specjalnymi
        pattern = re.compile(re.escape(bad), re.IGNORECASE)
        fixed_text = pattern.sub(good, fixed_text)
        
    return fixed_text.strip()

def run_ultimate_sweep(input_file, output_file):
    print(f"Rozpoczynam OSTATECZNE pranie bazy: {input_file}...")
    df = pd.read_csv(input_file)
    
    for idx, row in df.iterrows():
        # 1. Poprawa nazw i instrukcji
        df.at[idx, 'name'] = fix_text(row['name'])
        df.at[idx, 'instructions'] = fix_text(row['instructions'])
        df.at[idx, 'description'] = fix_text(row['description'])
        
        # 2. Poprawa JSONa ze składnikami
        ing_json = row['ingredients']
        updated_ingredients = []
        updated_names = set()
        
        try:
            ings = ast.literal_eval(ing_json) if isinstance(ing_json, str) else ing_json
            if isinstance(ings, list):
                for ing in ings:
                    if 'name' in ing:
                        name_lower = str(ing['name']).lower().strip()
                        
                        # Zignoruj śmieci
                        if any(trash in name_lower for trash in TO_DELETE_ENTIRELY):
                            continue
                        
                        # Napraw nazwę składnika
                        fixed_name = fix_text(ing['name'])
                        
                        # Czasem z długiego zdania po naprawie mogło nic nie zostać
                        if len(fixed_name) > 0:
                            ing['name'] = fixed_name
                            
                            # Poprawa jednostki (jeśli translator wcisnął "stan nietrzeźwy" jako unit)
                            if 'unit' in ing:
                                ing['unit'] = fix_text(str(ing['unit']))
                                
                            updated_ingredients.append(ing)
                            updated_names.add(fixed_name)
                            
                # Zapisz naprawionego JSONa z powrotem
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(updated_names))
        except Exception as e:
            pass

    # Zapis bazy
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Baza ostatecznie wyczyszczona z translatorskich absurdów!")
    print(f"Ilość przepisów: {len(df)}")
    print(f"Zapisano w: {output_file}")

if __name__ == "__main__":
    run_ultimate_sweep(INPUT_FILE, OUTPUT_FILE)