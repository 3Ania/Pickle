# Pickle 🥒

**Pickle** to innowacyjna aplikacja mobilna na system Android, zaprojektowana w celu eliminacji zjawiska paraliżu decyzyjnego podczas wyboru codziennych posiłków. System wykorzystuje zaawansowane algorytmy wyszukiwania oraz modele sztucznej inteligencji, aby dostarczać precyzyjne i w pełni spersonalizowane rekomendacje kulinarne.

## ✨ Kluczowe funkcjonalności

* **Hybrydowy system rekomendacji:** Łączy algorytm przeszukiwania wektorowego ($k$-NN) operujący na wbudowanej bazie danych z generatywnym modelem językowym (LLM) tworzącym przepisy na życzenie, co skutecznie rozwiązuje problem "zimnego startu".
* **Adaptacyjny profil użytkownika:** Aplikacja uczy się preferencji na bieżąco – analizuje tekstowe notatki z recenzji przy użyciu AI i automatycznie modyfikuje wagi lubianych oraz nielubianych składników.
* **Generowanie obrazów AI:** Dynamicznie stworzone przez sztuczną inteligencję przepisy są automatycznie wzbogacane o fotorealistyczne zdjęcia potraw wygenerowane przez model **Flux**.
* **Inteligentne filtrowanie (Więzy twarde):** Błyskawiczna eliminacja potraw zawierających alergeny lub składniki wykluczone przez dietę, połączona z rygorystycznym filtrowaniem czasu przygotowania i temperatury posiłku.

## 🛠️ Architektura i technologie

Projekt został podzielony na warstwę mobilną oraz potężny silnik obliczeniowy i bazodanowy w chmurze:

* **Frontend (Aplikacja Mobilna):** Kotlin, Jetpack Compose, Kotlin Coroutines, architektura MVVM.
* **Backend & Baza Danych:** Supabase (Backend-as-a-Service), PostgreSQL (wykorzystanie struktur `JSONB` oraz zdalnych procedur `RPC`).
* **Silnik ML & AI:** Python (preprocessing danych z API Spoonacular, implementacja k-NN), Google Gemini API (analiza sentymentu i generowanie przepisów), Pollinations.ai API (synteza obrazu Flux).

## 🚀 Uruchomienie projektu

Do poprawnego uruchomienia aplikacji w środowisku lokalnym wymagane są:
1. Zainstalowane środowisko **Android Studio** wspierające Jetpack Compose.
2. Skonfigurowany projekt na platformie **Supabase** (tabele `recipes` oraz `profiles`, ustawione uprawnienia Auth).
3. Wygenerowany klucz API dla modelu **Google Gemini** podpięty do silnika rekomendacji.

---
*Projekt indywidualny – Algorytm rekomendacji żywieniowych oparty o Large Language Model osadzony w aplikacji mobilnej. (2026)*
