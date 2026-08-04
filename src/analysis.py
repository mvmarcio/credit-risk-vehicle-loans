import os
import sqlite3
import pandas as pd

# 1. Resolução robusta de caminho absoluto para a raiz do projeto
CURRENT_FILE_PATH = os.path.abspath(__file__)
SRC_DIR = os.path.dirname(CURRENT_FILE_PATH)
BASE_DIR = os.path.dirname(SRC_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "credit_risk.db")


def run_analytical_pipeline():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"O banco de dados não foi encontrado em: {DB_PATH}.\n"
            f"Execute primeiro 'python -m src.extraction' para gerar os dados."
        )

    conn = sqlite3.connect(DB_PATH)

    try:
        # 2. Leitura das tabelas brutas/staging
        scr_df = pd.read_sql("SELECT * FROM bacen_scr_state", conn)
        macro_df = pd.read_sql("SELECT * FROM macro_indicators_state", conn)

        # 3. Cruzamento dos dados
        merged = pd.merge(
            scr_df, macro_df, on=["reference_month", "state_code"], how="inner"
        )

        # 4. Cálculo dos percentuais de inadimplência (Over 30, Over 60, Over 90)
        merged["over_30_pct"] = (
            merged["over_30_balance"] / merged["outstanding_balance"]
        )
        merged["over_60_pct"] = (
            merged["over_60_balance"] / merged["outstanding_balance"]
        )
        merged["over_90_pct"] = (
            merged["over_90_balance"] / merged["outstanding_balance"]
        )

        # 5. Índice (Mediana da Renda) / (Mediana do Aluguel)
        merged["income_to_rent_ratio"] = (
            merged["median_income"] / merged["median_rent"]
        )

        # 6. Ranking mensal de endividamento/inadimplência por estado (ordenado pelo Over 90)
        merged["indebtedness_rank"] = (
            merged.groupby("reference_month")["over_90_pct"]
            .rank(ascending=False, method="min")
            .astype(int)
        )

        # 7. Persistência dos dados na tabela analítica final
        merged.to_sql(
            "analytical_master", conn, if_exists="replace", index=False
        )

        print("\n=======================================================")
        print("    STATE LEVEL MEDIAN DELINQUENCY & INCOME/RENT INDEX ")
        print("=======================================================")
        summary = (
            merged.groupby("state_code")
            .agg(
                {
                    "over_30_pct": "median",
                    "over_60_pct": "median",
                    "over_90_pct": "median",
                    "income_to_rent_ratio": "median",
                }
            )
            .reset_index()
            .head(10)
        )
        print(summary.to_string(index=False))

        print("\n=======================================================")
        print("       CORRELATION WITH OVER 90% DELINQUENCY           ")
        print("=======================================================")
        cols = [
            "over_90_pct",
            "income_to_rent_ratio",
            "unemployment_rate",
            "gini_index",
            "igpm_variation",
            "median_income",
        ]
        corr_matrix = merged[cols].corr()
        print(
            corr_matrix[["over_90_pct"]].sort_values(
                by="over_90_pct", ascending=False
            )
        )

    finally:
        conn.close()


if __name__ == "__main__":
    run_analytical_pipeline()