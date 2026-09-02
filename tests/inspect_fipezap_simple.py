"""
Script simples e independente para inspecionar a estrutura do arquivo FipeZAP.
Não depende de nenhum outro módulo do projeto.
"""

import pandas as pd
from pathlib import Path
import sys

def inspect_fipezap():
    """
    Inspeciona a estrutura do arquivo FipeZAP Excel.
    Mostra informações detalhadas sobre cada aba.
    """
    print("=" * 80)
    print("🔍 INSPEÇÃO DO ARQUIVO FIPEZAP")
    print("=" * 80)
    
    # Caminho do arquivo
    file_path = Path("data/raw/fipezap_serieshistoricas.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        print("\n   Baixe o arquivo de:")
        print("   https://downloads.fipe.org.br/indices/fipezap/fipezap-serieshistoricas.xlsx")
        print(f"   E salve como: {file_path}")
        return
    
    print(f"✅ Arquivo encontrado: {file_path}")
    print()
    
    try:
        # Carregar o Excel
        xl = pd.ExcelFile(file_path)
        print(f"📊 Total de abas: {len(xl.sheet_names)}")
        print("-" * 80)
        print()
        
        # Mapeamento cidade -> estado
        city_state_map = {
            'SaoPaulo': 'SP', 'RioDeJaneiro': 'RJ', 'BeloHorizonte': 'MG',
            'PortoAlegre': 'RS', 'Curitiba': 'PR', 'Florianopolis': 'SC',
            'Salvador': 'BA', 'Recife': 'PE', 'Fortaleza': 'CE',
            'Brasilia': 'DF', 'Goiania': 'GO', 'Vitoria': 'ES',
            'CampoGrande': 'MS', 'Cuiaba': 'MT', 'Belem': 'PA',
            'Manaus': 'AM', 'SaoLuis': 'MA', 'JoaoPessoa': 'PB',
            'Teresina': 'PI', 'Natal': 'RN', 'Maceio': 'AL',
            'Aracaju': 'SE', 'Palmas': 'TO', 'PortoVelho': 'RO',
            'RioBranco': 'AC', 'Macapa': 'AP', 'BoaVista': 'RR'
        }
        
        # Abas para pular
        skip_sheets = ['Resumo', 'Aux', 'Índice FipeZAP']
        
        for idx, sheet_name in enumerate(xl.sheet_names):
            print(f"--- ABA {idx + 1}: {sheet_name} ---")
            
            # Verificar se é uma cidade
            is_city = sheet_name not in skip_sheets
            if is_city:
                # Tentar identificar o estado
                state_code = None
                sheet_clean = sheet_name.replace(' ', '').replace('-', '').replace('_', '')
                for city, code in city_state_map.items():
                    if city.lower() in sheet_clean.lower():
                        state_code = code
                        break
                
                if state_code:
                    print(f"  🏷️  Estado: {state_code}")
                else:
                    print(f"  ⚠️  Estado não identificado")
            else:
                print(f"  📋 Aba de resumo/auxiliar")
            
            try:
                # Ler apenas as primeiras linhas para entender a estrutura
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10, header=0)
                
                print(f"  📋 Shape: {df.shape[0]} linhas x {df.shape[1]} colunas")
                print(f"  📋 Colunas: {df.columns.tolist()}")
                print()
                print("  📄 Primeiras 5 linhas:")
                print(df.head(5).to_string())
                print()
                
                # Mostrar tipos das colunas
                print("  📊 Tipos das colunas:")
                for col in df.columns:
                    print(f"    {col}: {df[col].dtype}")
                print()
                
            except Exception as e:
                print(f"  ❌ Erro ao ler: {e}")
            
            print("-" * 40)
            print()
        
        print("=" * 80)
        print("✅ Inspeção concluída!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro ao abrir arquivo: {e}")

if __name__ == "__main__":
    inspect_fipezap()