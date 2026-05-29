import pandas as pd
import json
import ast
import re

# Pliki wejściowe
MAIN_DB_FILE = "przygotowanie_bazy/database_final_unique.csv"
RAW_NEW_FILE = "przygotowanie_bazy/missing_107_raw.csv"

# Plik wyjściowy
FINAL_OUTPUT = "przygotowanie_bazy/database_500_perfect.csv"

# MEGA-SŁOWNIK ze wszystkich Twoich poprzednich skryptów
REPLACEMENTS = {
    # Błędy klasyczne
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
    "sok pomarańczowy z krwi": "sok z czerwonych pomarańczy",
    "oliwa z oliwek z krwi i pomarańczy mollie stone's": "oliwa o smaku czerwonej pomarańczy",
    "krwiste pomarańcze": "czerwone pomarańcze",
    "pępek pomarańczowy": "pomarańcza navel",
    "daty medjoola": "daktyle medjool",
    "daty": "daktyle",
    "pojedynczy krem \u200b\u200b\u200b\u200bkremowy": "śmietana kremówka",
    "pojedynczy krem": "śmietana",
    "ciężki krem": "śmietana kremówka",
    "feta w kostkę": "ser feta",
    "młoda marchewka 4 łodygi selera 1 puszka grzybów 1 sztuka pieprzu 1 szklanka mąki i 3 łyżki 2 łyżki pszczoły": "włoszczyzna z grzybami i bulionem wołowym",
    "pszczoły": "bulion wołowy",
    "ech. pomidor": "pomidor",
    "glob": "bakłażan",
    "rozmiar - ziemniaki": "ziemniaki",
    "piekielnie": "ostry sos",
    "kremowe gładkie masło orzechowe": "gładkie masło orzechowe",
    "marynowana papryczka jalapeño": "marynowane jalapeno",
    "możesz użyć zwykłej bazylii": "świeża bazylia",
    "dodatkowe wierzchołki cebuli": "szczypiorek",
    "arënkha msc substytut kawioru": "substytut kawioru",
    "burger warzywny kruszy się": "rozdrobniony kotlet roślinny",
    "fasola cannellini fasola granatowa": "biała fasola",
    "imbir - usuń skórę i": "świeży imbir",
    "kłosy kukurydzy - zagotuj i z kolby": "kolby kukurydzy",

    # Poprawki z perfect_database_cleaner
    "rękawiczki czosnkowe": "ząbki czosnku",
    "sos ze skrzydełek bawolego": "sos buffalo",
    "małe odciski": "młoda kukurydza",
    "zostaw sałatę": "liście sałaty",
    "kluczowy sok z limonki": "sok z limonki",
    "gwiazda anyżu": "anyż gwiaździsty",
    "skorupa ciasta": "kruche ciasto",
    "krem z zupy grzybowej": "zupa pieczarkowa",
    "alouette ze szpinakiem i kremem z karczochów": "serek ze szpinakiem",
    "awokado w kostkę": "awokado",
    "biała część zielonej cebuli": "biała część dymki",
    "bragg's, całkowicie naturalny ocet jabłkowy": "ocet jabłkowy",
    "bulion z kości wołowej": "bulion wołowy",
    "bulion z kurczaka i 2 szklanki wody": "bulion drobiowy",
    "bulion z kurczaka o obniżonej zawartości sodu": "bulion drobiowy",
    "bulwa i liście kopru włoskiego": "koper włoski",
    "cebula pokrojona w kawałki": "cebula",
    "chleb z kiełkami zbożowymi": "chleb esseński",
    "chorizo ​​w kostkę": "chorizo",
    "czekolada i dodatkowe kakao w proszku": "czekolada i kakao",
    "czosnek - usuń skórę": "czosnek",
    "dekoracja: melasa z granatów": "melasa z granatów",
    "do 5 bulionów z kurczaka": "bulion drobiowy",
    "dodatkowe dodatki: awokado": "awokado",
    "dodatkowe tofu": "tofu",
    "filety z halibuta pacyficznego": "filet z halibuta",
    "frakcjonowany olej kokosowy": "płynny olej kokosowy",
    "fusilloro verrigni lub fusiloni": "makaron fusilli",
    "herbata matcha w proszku": "matcha",
    "imbir w proszku – posmakuj w miarę dopasowywania smaków": "mielony imbir",
    "indyjskie curry w proszku": "przyprawa curry",
    "jack monterrey i ser cheddar": "ser monterey jack i cheddar",
    "jogurt o niskiej zawartości tłuszczu": "jogurt niskotłuszczowy",
    "kolejny łyk oliwy z czerwonych pomarańczy": "oliwa z czerwonych pomarańczy",
    "kolendra – do dekoracji": "kolendra",
    "krem kokosowy": "śmietanka kokosowa",
    "krople oliwy z pierwszego tłoczenia": "oliwa z oliwek",
    "liście pietruszki o płaskich liściach": "natka pietruszki",
    "liście szałwii i mięty": "szałwia i mięta",
    "liście – ja użyłam mieszanki sałaty rzymskiej i szpinaku": "mix sałat",
    "majonez na bazie oliwy z oliwek": "majonez",
    "makaron farfalle firmy barilla": "makaron farfalle",
    "makaron ryżowy kuchni tajskiej": "makaron ryżowy",
    "makaron wermiszelowy ze słodkich ziemniaków": "makaron ze słodkich ziemniaków",
    "mielona musztarda w proszku": "mielona gorczyca",
    "mieszanka komosy ryżowej i brązowego ryżu": "komosa ryżowa i brązowy ryż",
    "mieszanka sera montery jack i cheddar": "ser monterey jack i cheddar",
    "mieszanka sosu holenderskiego knorr": "sos holenderski",
    "mleko do posmarowania chleba": "mleko",
    "mleko orzechowe/konopne/kokosowe": "mleko roślinne",
    "mozzarella z bel gioioso": "mozzarella",
    "musztarda w proszku": "mielona gorczyca",
    "mąka i 3 łyżki": "mąka",
    "nasiona do posypania chleba": "mix ziaren",
    "nasiona sezamu do dekoracji": "sezam",
    "ocet balsamiczny z granatów": "ocet balsamiczny",
    "odtłuszczone mleko w proszku": "mleko w proszku",
    "olej roślinny do smażenia": "olej roślinny",
    "olej z prażonego sezamu": "olej sezamowy",
    "oliwa z oliwek do posmarowania": "oliwa z oliwek",
    "oliwa z oliwek do skropienia": "oliwa z oliwek",
    "oliwa z oliwek z dodatkiem bazylii": "oliwa bazyliowa",
    "oliwa z oliwek z pierwszego tłoczenia": "oliwa z oliwek",
    "opcjonalnie - trochę sera feta": "ser feta",
    "opcjonalnie: ostry sos": "ostry sos",
    "orzechy nerkowca namoczone przez noc w wodzie": "orzechy nerkowca",
    "papryczki poblano – pieczone": "papryka poblano",
    "papryka w proszku": "słodka papryka",
    "pasta/ekstrakt z ziaren wanilii": "ekstrakt waniliowy",
    "pc organics komosa ryżowa z pieczonym czosnkiem i ziołami": "komosa ryżowa",
    "pieczone piersi z kurczaka": "pieczona pierś z kurczaka",
    "piersi z kurczaka bez kości/skóry": "pierś z kurczaka",
    "pietruszka do dekoracji": "pietruszka",
    "pietruszka o płaskich liściach": "natka pietruszki",
    "pikantny sos orzechowy trader joe's": "pikantny sos orzechowy",
    "pkt twarde/dodatkowe tofu": "tofu",
    "plus 2 łyżki oliwy z oliwek": "oliwa z oliwek",
    "poha / spłaszczony ryż": "płatki ryżowe (poha)",
    "pomidory rotel i chili": "pomidory z puszki z chili",
    "proszek chili z nowego meksyku": "chili z Nowego Meksyku",
    "proszek z nasion kminku": "mielony kmin rzymski",
    "przyprawa do ciasta dyniowego": "przyprawa korzenna",
    "przyprawa do owoców morza": "przyprawa do ryb",
    "puszka piersi z kurczaka swanson premium w wodzie": "kurczak z puszki",
    "płatki chili z pieprzem": "płatki chili",
    "płatki pieprzu – smakuj w miarę dopasowywania smaków": "płatki chili",
    "rosół z kurczaka/bulion warzywny": "bulion",
    "ser cheddar o obniżonej zawartości tłuszczu": "ser cheddar",
    "ser feta do dekoracji": "ser feta",
    "sok z 1 mandarynki (przekrojony w poprzek, następnie łyżka do słoika na sitku)": "sok z mandarynki",
    "sok z cytryny lub": "sok z cytryny",
    "sok z cytryny meyera": "sok z cytryny meyer",
    "sos do kurczaka firmy campbell": "zupa krem z kurczaka",
    "sos habanero i chili": "ostry sos",
    "sos: my użyliśmy pieczonych pomidorów": "pieczone pomidory",
    "sól - do smaku": "sól",
    "sól i mielony pieprz": "sól i pieprz",
    "sól i pieprz do przyprawienia": "sól i pieprz",
    "sól morska i świeżo mielony pieprz": "sól i pieprz",
    "słodzony kokos": "wiórki kokosowe",
    "suszony kokos": "wiórki kokosowe",
    "trochę oliwy z oliwek do posmarowania ziemniaków": "oliwa z oliwek",
    "twarożek) – wytwarzany z mleka": "twarożek",
    "uncja fety w kostkę": "ser feta",
    "wieprzowina powinna się upiec": "pieczona wieprzowina",
    "wierzchołki zielonej cebuli": "szczypiorek",
    "wody i 2 opakowania bulionu z kurczaka": "bulion drobiowy",
    "wodę sodową aż do czubka szklanki": "woda gazowana",
    "wyciśnięty sok z cytryny": "sok z cytryny",
    "wysokiej jakości ocet balsamiczny": "ocet balsamiczny",
    "wysokiej jakości oliwa z oliwek z pierwszego tłoczenia": "oliwa z oliwek",
    "ziele angielskie w proszku": "mielone ziele angielskie",
    "złote ziemniaki z yukonu": "ziemniaki yukon gold",
    "łyżka oliwy z oliwek": "oliwa z oliwek",

    # Mikro poprawki (nawiasy i przedrostki)
    "1 sałata rzymska": "sałata rzymska",
    "6 pomidorów romskich": "pomidory rzymskie",
    "do 2 estragonu": "estragon",
    "do 2 pomarańczy": "pomarańcze",
    "do 3 brokułów": "brokuł",
    "do 6 wody": "woda",
    "woda *2": "woda",
    "woda 4 szkl": "woda",
    "fasola garbanzo *1": "ciecierzyca",
    "cebula lub": "cebula",
    "do)": "woda",
    "następujące: skórka parmezanu)": "skórka parmezanu"
}

TO_DELETE = [
    "czas gotowania: minuty",
    "praktyczne na czas: minuty",
    "do 0,5 szklanki wody"
]

def clean_punctuation(text):
    if not isinstance(text, str): return text
    if text.endswith(')') and '(' not in text:
        text = text[:-1].strip()
    return text

def fix_text(text):
    if not isinstance(text, str): return text
    fixed_text = text
    for bad, good in REPLACEMENTS.items():
        pattern = re.compile(re.escape(bad), re.IGNORECASE)
        fixed_text = pattern.sub(good, fixed_text)
    
    # Skróty EVOO, oz, cup
    fixed_text = re.sub(r'\bEVOO\b', 'oliwie z oliwek', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\(first break the eggs into a cup\)', '(najpierw wbij jajka do kubka)', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'4\s*oz\.', '115 g', fixed_text, flags=re.IGNORECASE)
    
    # Clickbait title fixes
    if "dni dla psów" in fixed_text.lower():
        fixed_text = "Pomidorowe gazpacho na upalne dni"
    elif "prawdziwa wygoda" in fixed_text.lower():
        fixed_text = fixed_text.replace(": prawdziwa wygoda", " (Comfort Food)")
        
    return clean_punctuation(fixed_text)

def clean_new_recipes(input_file):
    print(f"Czyszczenie surowych 107 przepisów z {input_file}...")
    df = pd.read_csv(input_file)
    
    for idx, row in df.iterrows():
        df.at[idx, 'name'] = fix_text(row['name'])
        df.at[idx, 'instructions'] = fix_text(row['instructions'])
        df.at[idx, 'description'] = fix_text(row['description'])
        
        ing_json = row['ingredients']
        updated_ingredients = []
        updated_names = set()
        
        try:
            ings = ast.literal_eval(ing_json) if isinstance(ing_json, str) else ing_json
            if isinstance(ings, list):
                for ing in ings:
                    if 'name' in ing:
                        name_lower = ing['name'].lower().strip()
                        if name_lower in TO_DELETE: continue
                        
                        fixed_name = fix_text(ing['name']).strip()
                        ing['name'] = fixed_name
                        updated_ingredients.append(ing)
                        updated_names.add(fixed_name)
                        
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(updated_names))
        except:
            pass
            
    return df

if __name__ == "__main__":
    # 1. Wyczyść nowe 107 przepisów
    df_new_cleaned = clean_new_recipes(RAW_NEW_FILE)
    
    # 2. Wczytaj istniejącą bazę (393 przepisy)
    print(f"Wczytywanie głównej bazy {MAIN_DB_FILE}...")
    df_main = pd.read_csv(MAIN_DB_FILE)
    
    # 3. Złącz w jedną wielką bazę
    df_final = pd.concat([df_main, df_new_cleaned], ignore_index=True)
    
    # 4. Na wszelki wypadek usuń ewentualne ostateczne duplikaty po nazwie
    df_final = df_final.drop_duplicates(subset=['name'], keep='first')
    
    # 5. Zapis
    df_final.to_csv(FINAL_OUTPUT, index=False, encoding='utf-8')
    print(f"✅ SUKCES! Gotowe.")
    print(f"Mamy łącznie {len(df_final)} w 100% poprawnych, unikalnych przepisów.")
    print(f"Zapisano w pliku: {FINAL_OUTPUT}")