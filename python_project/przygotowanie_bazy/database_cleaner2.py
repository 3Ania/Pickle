import pandas as pd
import json
import ast
import re

# SŁOWNIK KOŃCOWYCH POPRAWEK
REPLACEMENTS = {
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
    "łyżka oliwy z oliwek": "oliwa z oliwek"
}

# Rzeczy do CAŁKOWITEGO USUNIĘCIA (śmieci ze stron www)
TO_DELETE = [
    "czas gotowania: minuty",
    "praktyczne na czas: minuty",
    "do 0,5 szklanki wody"
]

def fix_text(text):
    if not isinstance(text, str):
        return text
    fixed_text = text
    for bad, good in REPLACEMENTS.items():
        pattern = re.compile(re.escape(bad), re.IGNORECASE)
        fixed_text = pattern.sub(good, fixed_text)
    return fixed_text

def clean_database(input_file, output_file):
    print(f"Rozpoczynam OSTATECZNE czyszczenie pliku {input_file}...")
    df = pd.read_csv(input_file)
    
    for idx, row in df.iterrows():
        df.at[idx, 'name'] = fix_text(row['name'])
        df.at[idx, 'instructions'] = fix_text(row['instructions'])
        
        ing_json = row['ingredients']
        updated_ingredients = []
        updated_names = set()
        
        try:
            ings = ast.literal_eval(ing_json) if isinstance(ing_json, str) else ing_json
            if isinstance(ings, list):
                for ing in ings:
                    if 'name' in ing:
                        name_lower = ing['name'].lower().strip()
                        # Pomijamy śmieci
                        if name_lower in TO_DELETE:
                            continue
                        
                        fixed_name = fix_text(ing['name']).strip()
                        ing['name'] = fixed_name
                        updated_ingredients.append(ing)
                        updated_names.add(fixed_name)
                        
                df.at[idx, 'ingredients'] = json.dumps(updated_ingredients, ensure_ascii=False)
                df.at[idx, 'ingredient_names'] = str(list(updated_names))
        except:
            pass

    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Baza w 100% zdezynfekowana! Zapisano jako: {output_file}")

if __name__ == "__main__":
    # Zakładam, że Twoja najnowsza baza to database_flawless.csv
    clean_database("przygotowanie_bazy\database_flawless.csv", "przygotowanie_bazy\database_perfect.csv")