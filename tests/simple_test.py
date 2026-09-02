import pandas as pd
import os

# 1. CORREÇÃO DO CAMINHO DO ARQUIVO
# Ajuste este caminho para o local exato onde está o seu arquivo
caminho_arquivo = 'C:\\Users\\user\\Documents\\Projects\\credit-risk-vehicle-loans\\files\\fipezap-serieshistoricas.xlsx' 

if not os.path.exists(caminho_arquivo):
    print(f"❌ Arquivo não encontrado no caminho: {caminho_arquivo}")
else:
    print("✅ Arquivo encontrado! Iniciando leitura...")

    def ler_aba_cidade_iloc(caminho, nome_cidade):
        # Lê o arquivo inteiro com header=None (para não confundir o pandas)
        df = pd.read_excel(caminho, sheet_name=nome_cidade, header=None)
        
        # Baseado na estrutura exata do arquivo (visto no seu anexo):
        # Índice 0-3: Títulos
        # Índice 4: Cabeçalhos das colunas (Data, Total, etc.)
        # Índice 5: Início dos dados reais (2008-01-01)
        
        # Vamos pegar a linha de cabeçalho (índice 4) e atribuir aos dados
        # Usamos a primeira linha de dados como referência de onde começar
        dados = df.iloc[5:].reset_index(drop=True)
        
        # Selecionamos as colunas exatas por posição (0=Data, 1=Total, 5=Var Mensal, 10=Var 12m, 15=Preço)
        df_limpo = dados.iloc[:, [0, 1, 5, 10, 15]]
        
        # Nomeamos as colunas
        df_limpo.columns = ['Data', 'Total_Venda_Indice', 'Var_Mensal_Res', 'Var_12M_Res', 'Preco_Medio_Res']
        
        # Remove linhas onde a Data é NaN ou vazia (rodapés/fórmulas)
        df_limpo = df_limpo[df_limpo['Data'].notna()]
        
        # Converte a Data para datetime, forçando e ignorando erros
        df_limpo['Data'] = pd.to_datetime(df_limpo['Data'], errors='coerce')
        
        # Remove linhas que não conseguiram converter a data (valores inválidos)
        df_limpo = df_limpo.dropna(subset=['Data'])
        
        # Converte os valores numéricos (remove strings como 'não disponível' e '.')
        for col in df_limpo.columns[1:]:
            df_limpo[col] = pd.to_numeric(df_limpo[col], errors='coerce')
        
        return df_limpo

    try:
        df_sp = ler_aba_cidade_iloc(caminho_arquivo, 'São Paulo')
        print(f"\n✅ Dados de São Paulo extraídos com sucesso!")
        print(df_sp.head())
        print(f"\nFormato: {df_sp.shape}")
    except Exception as e:
        print(f"\n❌ Erro ao processar São Paulo: {e}")