import os
import sqlite3
import pandas as pd
import numpy as np
import requests

# 1. Garante que o caminho absoluto seja sempre a raiz do projeto (credit-risk-vehicle-loans)
CURRENT_FILE_PATH = os.path.abspath(__file__)
SRC_DIR = os.path.dirname(CURRENT_FILE_PATH)
BASE_DIR = os.path.dirname(SRC_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "credit_risk.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")


def init_db():
    """Inicializa o banco de dados SQLite com o arquivo schema.sql."""
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(
            f"O arquivo de schema não foi encontrado em: {SCHEMA_PATH}.\n"
            f"Certifique-se de que o arquivo 'schema.sql' existe na pasta 'sql'."
        )
        
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


def fetch_bacen_scr_data(start_date="2024-01-01"):
    """Simula/Extrai dados mensais do Bacen SCR para financiamento de veículos por UF."""
    print("[+] Extracting BACEN SCR Auto Loan data...")
    dates = pd.date_range(start=start_date, end=pd.Timestamp.now(), freq='MS')
    states = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
              'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 
              'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
    records = []
    np.random.seed(42)
    
    for d in dates:
        for st in states:
            balance = np.random.uniform(5e8, 5e9)
            records.append({
                'reference_month': d.strftime('%Y-%m-01'),
                'state_code': st,
                'outstanding_balance': balance,
                'over_30_balance': balance * np.random.uniform(0.015, 0.035),
                'over_60_balance': balance * np.random.uniform(0.010, 0.025),
                'over_90_balance': balance * np.random.uniform(0.030, 0.070)
            })
    return pd.DataFrame(records)


def fetch_macro_indicators(start_date="2024-01-01"):
    """Simula/Extrai indicadores macroeconômicos e sociais por UF."""
    print("[+] Extracting Macroeconomic & Income metrics (IBGE/FIPE/FGV)...")
    dates = pd.date_range(start=start_date, end=pd.Timestamp.now(), freq='MS')
    states = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
              'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 
              'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
    records = []
    np.random.seed(101)
    
    for d in dates:
        for st in states:
            records.append({
                'reference_month': d.strftime('%Y-%m-01'),
                'state_code': st,
                'median_income': np.random.uniform(2200, 4800),
                'median_rent': np.random.uniform(800, 2100),
                'unemployment_rate': np.random.uniform(0.05, 0.14),
                'gini_index': np.random.uniform(0.45, 0.58),
                'igpm_variation': np.random.uniform(-0.005, 0.012)
            })
    return pd.DataFrame(records)


def run_extraction():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    
    df_scr = fetch_bacen_scr_data()
    df_scr.to_sql('bacen_scr_state', conn, if_exists='replace', index=False)
    
    df_macro = fetch_macro_indicators()
    df_macro.to_sql('macro_indicators_state', conn, if_exists='replace', index=False)
    
    conn.close()
    print("[✔] Ingestion complete. Staging tables updated in SQLite.")


if __name__ == "__main__":
    run_extraction()