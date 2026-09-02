"""
Script para analisar detalhadamente a estrutura de uma aba específica do FipeZAP.
"""

import pandas as pd
from pathlib import Path

def analyze_sheet(sheet_name: str = "Rio de Janeiro"):
    """
    Analisa a estrutura de uma aba específica do FipeZAP.
    """
    print("=" * 80)
    print(f"🔍 ANÁLISE DA ABA: {sheet_name}")
    print("=" * 80)
    
    file_path = Path("data/raw/fipezap_serieshistoricas.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return
    
    try:
        # Ler a planilha inteira
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        print(f"📋 Shape total: {df.shape}")
        print()
        
        # Mostrar todas as linhas
        print("📄 TODAS AS LINHAS:")
        print("-" * 80)
        for idx, row in df.iterrows():
            print(f"Linha {idx}: {row.tolist()[:10]}")
        print()
        
        # Mostrar estrutura de colunas
        print("📊 ESTRUTURA DAS COLUNAS (primeiras 20):")
        print("-" * 80)
        for col_idx in range(min(20, df.shape[1])):
            col_data = df[col_idx].tolist()
            print(f"Coluna {col_idx}: {col_data[:10]}")
        print()
        
        # Identificar onde estão os dados de locação
        print("🔍 IDENTIFICANDO DADOS DE LOCAÇÃO:")
        print("-" * 80)
        
        # Procurar por "Locação" ou "Preços de locação"
        locacao_cols = []
        for col_idx in range(df.shape[1]):
            for row_idx in range(min(5, df.shape[0])):
                val = df.iloc[row_idx, col_idx]
                if isinstance(val, str):
                    if 'Locação' in val or 'loca' in val.lower():
                        locacao_cols.append(col_idx)
                        break
        
        print(f"Colunas com 'Locação': {locacao_cols}")
        
        # Mostrar dados das colunas de locação
        for col_idx in locacao_cols:
            print(f"\nColuna {col_idx}:")
            print(df[col_idx].tolist()[:20])
        
        print("\n" + "=" * 80)
        print("✅ Análise concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    # Analisar a aba do Rio de Janeiro
    analyze_sheet("Rio de Janeiro")