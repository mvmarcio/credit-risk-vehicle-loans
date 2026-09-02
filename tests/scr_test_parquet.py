from pathlib import Path
import numpy as np
import pandas as pd


# 1. Primeiro definimos a função
def carregar_e_tratar_scr(caminho_arquivo: Path | str) -> pd.DataFrame:
    """Carrega e trata a base de dados do SCR (Bacen) a partir de um objeto Path ou string."""
    caminho = Path(caminho_arquivo)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho.resolve()}"
        )

    print(f"Lendo arquivo: {caminho.resolve()}")

    # Leitura do CSV
    df = pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        low_memory=False,
    )

    # Conversão de data
    df["data_base"] = pd.to_datetime(df["data_base"], format="%Y-%m-%d")

    # Otimização de memória (tipos categóricos)
    colunas_categoricas = [
        "uf",
        "segmento",
        "cliente",
        "porte",
        "modalidade",
        "submodalidade",
        "origem",
        "indexador",
        "cnae_ocupacao",
    ]
    for col in colunas_categoricas:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # Tratamento do sigilo bancário (-1 representa <= 3 operações)
    df["sigilo_operacoes"] = df["numero_de_operacoes"] == -1
    df["numero_de_operacoes_tratado"] = df["numero_de_operacoes"].replace(
        -1, np.nan
    )

    # Tratamento numérico financeiro
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

    # Indicadores de crédito
    denominador = df["carteira_ativa"].replace(0, np.nan)
    df["taxa_inadimplencia"] = df["carteira_inadimplencia"] / denominador
    df["taxa_ativo_problematico"] = df["ativo_problematico"] / denominador
    df["taxa_carteira_vencida"] = df["carteira_vencida"] / denominador

    # Validação contábil
    diferenca = df["carteira_ativa"] - (
        df["carteira_a_vencer"] + df["carteira_vencida"]
    )
    df["inconsistencia_contabil"] = diferenca.abs() > 0.05

    return df


# 2. Depois executamos passando o caminho
caminho_arquivo = Path(
    r"C:\Users\user\Downloads\scrdata_2026\scrdata_202606.csv"
)

# Execução
df_scr = carregar_e_tratar_scr(caminho_arquivo)

print("\n--- Resumo do Processamento ---")
print(f"Dimensões: {df_scr.shape[0]:,} linhas x {df_scr.shape[1]} colunas")
print(
    f"Uso de memória: {df_scr.memory_usage(deep=True).sum() / (1024 ** 2):.2f} MB"
)

# Exportando para Parquet (recomendado para 300k+ linhas)
caminho_saida = caminho_arquivo.with_name("scrdata_202606_tratado.parquet")
df_scr.to_parquet(caminho_saida, index=False)
print(f"Arquivo exportado com sucesso para: {caminho_saida.resolve()}")