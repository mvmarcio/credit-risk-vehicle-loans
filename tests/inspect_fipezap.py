#!/usr/bin/env python
"""
Script para inspecionar a estrutura do arquivo FipeZAP.
Funciona tanto no Jupyter quanto na linha de comando.
"""

import pandas as pd
from pathlib import Path
import sys
import os

def get_project_root():
    """
    Encontra o diretório raiz do projeto.
    Funciona tanto no Jupyter quanto na linha de comando.
    """
    # Tentar encontrar pelo caminho atual
    current_path = Path.cwd()
    
    # Procurar por um arquivo que identifica a raiz do projeto
    markers = ['config.yaml', 'main.py', 'requirements.txt', 'src']
    
    # Começar do diretório atual e subir até encontrar um marcador
    for parent in [current_path] + list(current_path.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent
    
    # Se não encontrou, usar o diretório atual
    return current_path

# Encontrar a raiz do projeto
PROJECT_ROOT = get_project_root()
sys.path.insert(0, str(PROJECT_ROOT))

print(f"🔍 Project root: {PROJECT_ROOT}")
print(f"🔍 sys.path[0]: {sys.path[0]}")

# Verificar se src/extraction.py existe
src_file = PROJECT_ROOT / 'src' / 'extraction.py'
if src_file.exists():
    print("✅ src/extraction.py encontrado!")
else:
    print(f"❌ src/extraction.py NÃO encontrado em: {src_file}")
    print("   Verifique se você está no diretório correto do projeto")
    sys.exit(1)

# Importar
try:
    from src.extraction import DataExtractor
    print("✅ Importação bem-sucedida!")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    print(f"   Python path: {sys.path[:3]}")
    sys.exit(1)

def inspect_fipezap_file(file_path: Path):
    """
    Inspeciona a estrutura do arquivo FipeZAP Excel.
    """
    print("=" * 80)
    print("🔍 INSPEÇÃO DO ARQUIVO FIPEZAP")
    print("=" * 80)
    print(f"Arquivo: {file_path}")
    print(f"Arquivo existe: {file_path.exists()}")
    print()
    
    if not file_path.exists():
        print("❌ Arquivo não encontrado!")
        print("   Certifique-se de que o arquivo está em:")
        print(f"   {file_path}")
        print()
        print("   Se não tiver o arquivo, baixe manualmente de:")
        print("   https://www.fipe.org.br/pt-br/indices/fipezap/")
        return
    
    try:
        # Carregar o arquivo Excel
        xl = pd.ExcelFile(file_path)
        print(f"📊 Total de abas: {len(xl.sheet_names)}")
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
        
        for idx, sheet_name in enumerate(xl.sheet_names):
            print(f"--- ABA {idx + 1}: {sheet_name} ---")
            
            # Tentar identificar o estado
            state_code = None
            sheet_clean = sheet_name.replace(' ', '').replace('-', '').replace('_', '')
            for city, code in city_state_map.items():
                if city.lower() in sheet_clean.lower():
                    state_code = code
                    break
            
            if state_code:
                print(f"  🏷️  Estado identificado: {state_code}")
            else:
                print(f"  ⚠️  Estado NÃO identificado")
            
            # Ler a aba
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
                print(f"  📋 Shape: {df.shape[0]} linhas x {df.shape[1]} colunas")
                print(f"  📋 Colunas: {df.columns.tolist()}")
                print()
                
                # Mostrar primeiras linhas
                print(f"  📄 Primeiras 5 linhas:")
                print(df.head(5).to_string())
                print()
                
                # Mostrar tipos das colunas
                print(f"  📊 Tipos das colunas:")
                for col in df.columns:
                    print(f"    {col}: {df[col].dtype}")
                print()
                
                # Tentar identificar colunas de data e variação
                date_col = None
                variation_col = None
                
                for col in df.columns:
                    col_str = str(col).lower()
                    if any(term in col_str for term in ['data', 'date', 'mês', 'mes', 'month', 'period', 'ano']):
                        if date_col is None:
                            date_col = col
                    if any(term in col_str for term in ['variação', 'variation', 'var', 'change', 'percent', '%']):
                        if variation_col is None:
                            variation_col = col
                
                # Se não encontrou, tentar identificar por tipo
                if variation_col is None:
                    for col in df.columns:
                        try:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                variation_col = col
                                break
                        except:
                            continue
                
                if date_col is None and len(df.columns) > 0:
                    date_col = df.columns[0]
                
                print(f"  🔍 Coluna de data sugerida: {date_col}")
                print(f"  🔍 Coluna de variação sugerida: {variation_col}")
                
                # Mostrar dados de exemplo
                if date_col and variation_col:
                    print(f"\n  📊 Dados de exemplo (data -> variação):")
                    sample_data = df[[date_col, variation_col]].head(10)
                    print(sample_data.to_string())
                
                # Tentar extrair dados
                extracted = 0
                if date_col and variation_col:
                    for idx_row, row in df.iterrows():
                        try:
                            date_val = row.get(date_col)
                            if pd.isna(date_val):
                                continue
                            
                            value = row.get(variation_col)
                            if pd.isna(value):
                                continue
                            
                            try:
                                float(value)
                                extracted += 1
                            except:
                                continue
                        except:
                            continue
                    
                    print(f"\n  ✅ Registros extraíveis: {extracted}")
                
                print("-" * 40)
                print()
                
            except Exception as e:
                print(f"  ❌ Erro ao ler aba: {e}")
                print()
        
        print("=" * 80)
        print("✅ Inspeção concluída!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro ao abrir arquivo: {e}")

def main():
    """Executa a inspeção."""
    # Caminho do arquivo
    file_path = PROJECT_ROOT / 'data' / 'raw' / 'fipezap_serieshistoricas.xlsx'
    
    inspect_fipezap_file(file_path)

if __name__ == "__main__":
    main()