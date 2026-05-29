import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ast
from collections import Counter

# Konfiguracja wizualna
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)

# Ładowanie danych (ścieżki zgodnie z Twoją prośbą)
try:
    df_raw = pd.read_csv('../przygotowanie_bazy/recipes_rows_przed_zmianami.csv')
    df_final = pd.read_csv('../przygotowanie_bazy/database_final_production.csv')
    df_log = pd.read_csv('../przygotowanie_bazy/cleaning_log.csv')
except FileNotFoundError:
    df_raw = pd.read_csv('recipes_rows_przed_zmianami.csv')
    df_final = pd.read_csv('database_final_production.csv')
    df_log = pd.read_csv('cleaning_log.csv')

# --- ANALIZA CZASU ---
t_data = df_final['total_time']

# --- WIZUALIZACJA ---

# [Tutaj pozostałe Twoje wykresy 1-5...]

# Wykres 6: Boxplot Czasu
plt.figure(figsize=(10, 4))
sns.boxplot(x=t_data, color='lightcoral')
plt.title('Wykres pudełkowy rozkładu czasu przygotowania potraw', fontsize=14)
plt.xlabel('Czas (minuty)')
plt.savefig('6_boxplot_czasu.png')

print("Wygenerowano dodatkowy wykres: 6_boxplot_czasu.png")