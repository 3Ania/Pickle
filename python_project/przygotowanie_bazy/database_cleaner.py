import pandas as pd
import json
import ast
import re

# --- WIELKI SŁOWNIK NAPRAWCZY ---
# Klucz: "błędna, tłumaczona fraza", Wartość: "poprawne kulinarne określenie"
# Uwaga: Kolejność ma znaczenie dla dłuższych fraz, ale słownik jest zoptymalizowany.
TRANSLATIONS_FIXES = {
    # Hity z Twojej bazy:
    "fajny bicz": "bita śmietana",
    "marynarka wojenna": "biała fasola",
    "ożywić": "imbir",
    "kolorowy kamień nazębny na podłożu warzywnym. także dotyk": "tatar z warzyw",
    "stalówki kakaowe": "kruszone ziarno kakaowca",
    "skracanie": "tłuszcz piekarski",
    "kłoda koziego sera chavrie": "rolada z sera koziego",
    "wskazówki dotyczące polędwicy wołowej": "kawałki polędwicy wołowej",
    "groszek oczny": "groszek czarnooki",
    "zarezerwowana woda z makaronem": "woda z gotowania makaronu",
    
    # Krwawe pomarańcze:
    "sok pomarańczowy z krwi": "sok z czerwonych pomarańczy",
    "oliwa z oliwek z krwi i pomarańczy mollie stone's": "oliwa o smaku czerwonej pomarańczy",
    "krwiste pomarańcze": "czerwone pomarańcze",
    "pępek pomarańczowy": "pomarańcza navel",
    
    # Daktyle (Daty):
    "daty medjoola": "daktyle medjool",
    "daty": "daktyle",
    
    # Nabiał i tłuszcze:
    "pojedynczy krem \u200b\u200b\u200b\u200bkremowy": "śmietana kremówka",
    "pojedynczy krem": "śmietana",
    "ciężki krem": "śmietana kremówka",
    "feta w kostkę": "ser feta",
    
    # Dziwactwa wielosłowne:
    "młoda marchewka 4 łodygi selera 1 puszka grzybów 1 sztuka pieprzu 1 szklanka mąki i 3 łyżki 2 łyżki pszczoły": "włoszczyzna z grzybami i bulionem wołowym",
    "pszczoły": "bulion wołowy", # Zostało po "beef bouillon" -> "bee bouillon"
    "ech. pomidor": "pomidor",
    "glob": "bakłażan", # "Globe eggplant" potraktowane wyrywkowo
    "rozmiar - ziemniaki": "ziemniaki",
    "piekielnie": "ostry sos",
    
    # Poprawki stylistyczne:
    "kremowe gładkie masło orzechowe": "gładkie masło orzechowe",
    "marynowana papryczka jalapeño": "marynowane jalapeno",
    "możesz użyć zwykłej bazylii": "świeża bazylia",
    "dodatkowe wierzchołki cebuli": "szczypiorek",
    "arënkha msc substytut kawioru": "substytut kawioru",
    "burger warzywny kruszy się": "rozdrobniony kotlet roślinny",
    "fasola cannellini fasola granatowa": "biała fasola",
    "imbir - usuń skórę i": "świeży imbir",
    "kłosy kukurydzy - zagotuj i z kolby": "kolby kukurydzy"
}

def fix_text(text):
    """Funkcja podmieniająca błędne frazy w tekście, ignorując wielkość liter."""
    if not isinstance(text, str):
        return text
    
    fixed_text = text
    for bad, good in TRANSLATIONS_FIXES.items():
        # Używamy wyrażeń regularnych do podmieniania bez względu na wielkość liter (case-insensitive)
        # re.IGNORECASE sprawia, że "Ożywić", "ożywić" i "OŻYWIĆ" zamienią się na "imbir"
        pattern = re.compile(re.escape(bad), re.IGNORECASE)
        fixed_text = pattern.sub(good, fixed_text)
        
    return fixed_text

def clean_database(input_file, output_file):
    print(f"Wczytywanie bazy danych: {input_file}...")
    df = pd.read_csv(input_file)
    
    total_rows = len(df)
    
    for idx, row in df.iterrows():
        # 1. Naprawa Tytułu przepisu (name)
        df.at[idx, 'name'] = fix_text(row['name'])
        
        # 2. Naprawa Instrukcji (instructions)
        df.at[idx, 'instructions'] = fix_text(row['instructions'])
        
        # 3. Naprawa Składników (JSON)
        ing_json = row['ingredients']
        updated_names = set()
        
        try:
            # Rozszyfrowanie JSON/String
            ings = ast.literal_eval(ing_json) if isinstance(ing_json, str) else ing_json
            
            if isinstance(ings, list):
                for i in range(len(ings)):
                    if 'name' in ings[i]:
                        # Zmiana nazwy składnika
                        fixed_name = fix_text(ings[i]['name'])
                        ings[i]['name'] = fixed_name
                        updated_names.add(fixed_name)
                        
                # Zapisanie z powrotem jako sformatowany JSON
                df.at[idx, 'ingredients'] = json.dumps(ings, ensure_ascii=False)
        except Exception as e:
            # Puste kolumny lub błędy formatowania ignorujemy
            pass

        # 4. Naprawa pomocniczej kolumny z listą nazw składników
        if updated_names:
            df.at[idx, 'ingredient_names'] = str(list(updated_names))

        # Pasek postępu w konsoli
        if (idx + 1) % 50 == 0:
            print(f"Przetworzono {idx + 1} z {total_rows} przepisów...")

    # Zapis
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✅ SUKCES! Wyczyszczona baza została zapisana jako: {output_file}")

if __name__ == "__main__":
    # PODMIEŃ NAZWĘ SWOJEGO PLIKU WEJŚCIOWEGO PONIŻEJ
    INPUT_CSV = "przygotowanie_bazy\curr_database.csv" 
    OUTPUT_CSV = "przygotowanie_bazy\database_flawless.csv"

    clean_database(INPUT_CSV, OUTPUT_CSV)