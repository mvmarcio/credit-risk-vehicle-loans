from pathlib import Path
import numpy as np
import pandas as pd


def carregar_e_tratar_scr(caminho_arquivo: Path | str) -> pd.DataFrame:
    """Carrega e trata a base de dados do SCR (Bacen) a partir de um objeto Path ou string."""
    caminho = Path(caminho_arquivo)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho.resolve()}"
        )

    print(f"Lendo arquivo: {caminho.resolve()}")

    # 1. Leitura do CSV original
    df = pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        low_memory=False,
    )

    # 2. Conversão de datas
    df["data_base"] = pd.to_datetime(df["data_base"], format="%Y-%m-%d")

    # 3. Tratamento do sigilo bancário (-1 representa <= 3 operações)
    df["sigilo_operacoes"] = df["numero_de_operacoes"] == -1
    df["numero_de_operacoes_tratado"] = df["numero_de_operacoes"].replace(
        -1, np.nan
    )

    # 4. Tratamento numérico dos campos financeiros
    colunas_financeiras = [
        "a_vencer_ate_90_dias",
        "a_vencer_de_91_ate_360_dias",
        "a_vencer_de_361_ate_1080_dias",
        "a_vencer_de_1081_ate_1800_dias",
        "a_vencer_de_1801_ate_5400_dias",
        "a_vencer_acima_de_5400_dias",
        "carteira_a_vencer",
        "vencido_de_15_ate_90_dias",
        "vencido_acima_de_90_dias",
        "carteira_vencida",
        "carteira_ativa",
        "carteira_inadimplencia",
        "ativo_problematico",
    ]
    for col in colunas_financeiras:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 5. Indicadores de crédito
    denominador = df["carteira_ativa"].replace(0, np.nan)
    df["taxa_inadimplencia"] = df["carteira_inadimplencia"] / denominador
    df["taxa_ativo_problematico"] = df["ativo_problematico"] / denominador
    df["taxa_carteira_vencida"] = df["carteira_vencida"] / denominador

    # 6. Validação contábil
    diferenca = df["carteira_ativa"] - (
        df["carteira_a_vencer"] + df["carteira_vencida"]
    )
    df["inconsistencia_contabil"] = diferenca.abs() > 0.05

    return df


# ---------------------------------------------------------
# EXECUÇÃO E EXPORTAÇÃO PARA EXCEL
# ---------------------------------------------------------
caminho_arquivo = Path(
    r"C:\Users\user\Downloads\scrdata_2026\scrdata_202606.csv"
)

# 1. Carrega e trata os dados
df_scr = carregar_e_tratar_scr(caminho_arquivo)
print(f"Dados processados: {df_scr.shape[0]:,} linhas x {df_scr.shape[1]} colunas")

# 2. Define o nome do arquivo Excel de saída
caminho_saida_excel = caminho_arquivo.with_name("scrdata_202606_tratado.xlsx")

print(f"Exportando para Excel em: {caminho_saida_excel.resolve()}...")

# 3. Exporta para .xlsx usando openpyxl
# Dica: 'openpyxl' precisa estar instalado (pip install openpyxl)
df_scr.to_excel(caminho_saida_excel, index=False, engine="openpyxl")

print("Exportação para Excel finalizada com sucesso!")