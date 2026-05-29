import pandas as pd
import json
import ast

# --- MAPA PEŁNYCH INSTRUKCJI ---
# Przygotowane na podstawie składników dla brakujących/błędnych rekordów
FULL_INSTRUCTIONS = {
    # Przepisy: Brokuły czosnkowo-cytrynowe i chili
    "BROCCOLI": (
        "1. Umyj brokuły i podziel je na małe różyczki. Łodygi obierz i pokrój w plasterki.\n"
        "2. Zagotuj wodę w garnku, dodaj szczyptę soli i gotuj brokuły przez około 3-4 minuty (al dente), a następnie odcedź.\n"
        "3. Na dużej patelni rozgrzej oliwę z oliwek na średnim ogniu.\n"
        "4. Dodaj drobno posiekany czosnek oraz płatki czerwonej papryki (chili). Smaż przez 1 minutę, aż czosnek zacznie pachnieć.\n"
        "5. W małej miseczce wymieszaj sok z cytryny, ocet ryżowy i musztardę Dijon.\n"
        "6. Wrzuć brokuły na patelnię, wlej sos i dokładnie wymieszaj, smażąc przez kolejne 2 minuty.\n"
        "7. Dopraw do smaku solą oraz pieprzem. Podawaj na ciepło."
    ),
    # Przepisy: Muffinki Frittata
    "FRITTATA": (
        "1. Rozgrzej piekarnik do 180°C. Formę na muffinki wysmaruj lekko oliwą.\n"
        "2. Brokuły i pomidory drobno posiekaj. Ser cheddar zetrzyj na tarce.\n"
        "3. W misce rozbij jajka, dodaj krem, sól, pieprz oraz pieprz pomarańczowy. Roztrzep dokładnie.\n"
        "4. Do masy jajecznej dodaj warzywa, ser oraz posiekany szczypiorek. Wymieszaj.\n"
        "5. Rozlej masę do formy na muffinki (do ok. 3/4 wysokości).\n"
        "6. Piecz przez 15-20 minut, aż jajka się zetną i wierzch lekko zarumieni."
    ),
    "ID_67": (
        "1. Ogórki umyj i pokrój w kawałki. Szalotki i cebulę posiekaj.\n"
        "2. Z awokado wyjmij pestkę, a miąższ wydrąż łyżką.\n"
        "3. Do blendera włóż ogórki, awokado, cebulę, szalotki, jogurt grecki i kefir.\n"
        "4. Dodaj sok z cytryny oraz małą garść winogron.\n"
        "5. Miksuj wszystko na gładką masę. W razie potrzeby dodaj odrobinę wody.\n"
        "6. Dopraw solą i pieprzem. Schłodź w lodówce przez 30 minut przed podaniem."
    ),
    "ID_265": (
        "1. Pomidory winogronowe przekrój na pół. Ogórka i cebulę pokrój w kostkę.\n"
        "2. W miseczce wymieszaj oliwę z octem balsamicznym, solą i pieprzem.\n"
        "3. W dużej misce połącz pomidory, ogórki i cebulę.\n"
        "4. Polej warzywa dressingiem i delikatnie wymieszaj.\n"
        "5. Na wierzch pokrusz ser feta. Odstaw na 10 minut przed podaniem."
    ),
    "ID_339": (
        "1. W misce wymieszaj jogurt grecki z miękkim kozim serem na gładką masę.\n"
        "2. Dodaj karmelizowaną cebulę oraz posiekany koperek, pietruszkę i szczypiorek.\n"
        "3. Wsyp przyprawę do steków i wszystko dokładnie wymieszaj.\n"
        "4. Schłodź w lodówce przez 15 minut. Podawaj z krakersami lub warzywami."
    )
}

def repair_database(input_csv):
    df = pd.read_csv(input_csv)
    print(f"Naprawiam bazę: {input_csv}...")

    for idx, row in df.iterrows():
        r_id = row['id']
        
        # --- 1. NAPRAWA SKŁADNIKÓW (Magazyn -> Bulion) ---
        # Naprawa w kolumnie 'ingredients' (JSON)
        try:
            ings = json.loads(row['ingredients'])
            changed_ing = False
            for i in ings:
                if i['name'].lower() == 'magazyn':
                    i['name'] = 'bulion warzywny'
                    changed_ing = True
            if changed_ing:
                df.at[idx, 'ingredients'] = json.dumps(ings, ensure_ascii=False)
                
                # Naprawa w kolumnie 'ingredient_names' (Lista)
                ing_names = ast.literal_eval(row['ingredient_names'])
                new_names = [n if n != 'magazyn' else 'bulion warzywny' for n in ing_names]
                df.at[idx, 'ingredient_names'] = str(new_names)
        except:
            pass

        # --- 2. NAPRAWA INSTRUKCJI ---
        current_instr = str(row['instructions'])
        
        # Sprawdzanie czy instrukcja wymaga wymiany
        needs_fix = (
            pd.isna(row['instructions']) or 
            current_instr.strip() == "" or 
            "Co za wideo" in current_instr
        )

        if needs_fix:
            if r_id in [10, 85, 142, 449]:
                df.at[idx, 'instructions'] = FULL_INSTRUCTIONS["BROCCOLI"]
            elif r_id in [50, 190]:
                df.at[idx, 'instructions'] = FULL_INSTRUCTIONS["FRITTATA"]
            elif r_id == 67:
                df.at[idx, 'instructions'] = FULL_INSTRUCTIONS["ID_67"]
            elif r_id == 265:
                df.at[idx, 'instructions'] = FULL_INSTRUCTIONS["ID_265"]
            elif r_id == 339:
                df.at[idx, 'instructions'] = FULL_INSTRUCTIONS["ID_339"]

    output_file = 'database_final_production.csv'
    df.to_csv(output_file, index=False)
    print(f"Sukces! Naprawiona baza zapisana jako: {output_file}")

if __name__ == "__main__":
    repair_database('database_polished_final.csv')