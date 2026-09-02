"""
Script para testar a extração dos dados do FipeZAP.
Independente do pipeline principal.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def test_fipezap_extraction():
    """
    Testa diferentes estratégias para extrair dados do FipeZAP.
    """
    print("=" * 80)
    print("🧪 TESTE DE EXTRAÇÃO FIPEZAP")
    print("=" * 80)
    
    file_path = Path("data/raw/fipezap_serieshistoricas.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return
    
    print(f"✅ Arquivo encontrado: {file_path}")
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
    
    try:
        xl = pd.ExcelFile(file_path)
        all_data = []
        states_found = set()
        
        skip_sheets = ['Resumo', 'Aux', 'Índice FipeZAP']
        
        for sheet_name in xl.sheet_names:
            if sheet_name in skip_sheets:
                continue
            
            # Encontrar estado
            state_code = None
            sheet_clean = sheet_name.replace(' ', '').replace('-', '').replace('_', '')
            for city, code in city_state_map.items():
                if city.lower() in sheet_clean.lower():
                    state_code = code
                    break
            
            if not state_code:
                continue
            
            states_found.add(state_code)
            print(f"\n📊 Processando: {sheet_name} -> {state_code}")
            
            # Ler a planilha
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
            
            if df.empty:
                print(f"  ⚠️ Planilha vazia")
                continue
            
            print(f"  Shape: {df.shape}")
            print(f"  Colunas: {df.columns.tolist()[:10]}...")
            
            # Estratégia 1: Encontrar linha de dados
            data_start_row = None
            for idx, row in df.iterrows():
                first_col = row.iloc[0] if len(row) > 0 else None
                if isinstance(first_col, pd.Timestamp):
                    data_start_row = idx
                    break
                elif isinstance(first_col, str) and first_col.startswith('2008-'):
                    data_start_row = idx
                    break
            
            if data_start_row is None:
                data_start_row = 3
            
            print(f"  Linha de dados: {data_start_row}")
            
            # Extrair dados a partir da linha encontrada
            data_df = df.iloc[data_start_row:].copy()
            data_df = data_df.reset_index(drop=True)
            
            # Encontrar colunas de locação
            rent_columns = []
            for idx, row in df.iterrows():
                for col_idx, val in enumerate(row):
                    if isinstance(val, str) and ('Locação' in val or 'loca' in val.lower()):
                        rent_columns.append(col_idx)
                    if isinstance(val, str) and ('Preços de locação' in val):
                        rent_columns.append(col_idx)
            
            if not rent_columns:
                # Baseado na inspeção, as colunas de locação são 16-20
                rent_columns = list(range(16, 21))
            
            print(f"  Colunas de locação: {rent_columns}")
            
            # Encontrar coluna de variação
            variation_col = None
            for col in rent_columns:
                if col < len(df.columns):
                    header_val = df.iloc[1, col] if len(df) > 1 else None
                    if isinstance(header_val, str) and ('Var.' in header_val or 'mensal' in header_val):
                        variation_col = col
                        break
            
            if variation_col is None and rent_columns:
                variation_col = rent_columns[0]
            
            print(f"  Coluna de variação: {variation_col}")
            
            if variation_col is None:
                print(f"  ⚠️ Não foi possível encontrar coluna de variação")
                continue
            
            # Extrair dados
            extracted = 0
            for idx, row in data_df.iterrows():
                try:
                    date_val = row.iloc[0] if len(row) > 0 else None
                    if pd.isna(date_val):
                        continue
                    
                    # Converter data
                    if isinstance(date_val, pd.Timestamp):
                        month_date = date_val.strftime('%Y-%m-01')
                    elif isinstance(date_val, datetime):
                        month_date = date_val.strftime('%Y-%m-01')
                    elif isinstance(date_val, str):
                        try:
                            parsed = pd.to_datetime(date_val, dayfirst=True)
                            month_date = parsed.strftime('%Y-%m-01')
                        except:
                            continue
                    else:
                        continue
                    
                    # Pegar valor
                    value = row.iloc[variation_col] if variation_col < len(row) else None
                    if pd.isna(value):
                        continue
                    
                    # Converter para float
                    try:
                        if isinstance(value, str):
                            value = value.replace('%', '').replace(',', '.').strip()
                            value_float = float(value)
                        else:
                            value_float = float(value)
                        
                        # Validar valor
                        if -50 < value_float < 50:
                            all_data.append({
                                'state_code': state_code,
                                'month_date': month_date,
                                'rent_variation': round(value_float, 2)
                            })
                            extracted += 1
                    except (ValueError, TypeError):
                        continue
                        
                except Exception as e:
                    continue
            
            print(f"  ✅ Extraídos: {extracted} registros")
        
        print("\n" + "=" * 80)
        print("📊 RESULTADO DA EXTRAÇÃO")
        print("=" * 80)
        
        if not all_data:
            print("❌ Nenhum dado foi extraído!")
            print("\n🔍 Possíveis problemas:")
            print("  1. Estrutura do Excel é diferente do esperado")
            print("  2. Colunas de locação estão em posições diferentes")
            print("  3. Os dados estão em formato diferente")
            print("\n💡 Sugestão: Rode o script de inspeção primeiro!")
            return
        
        result_df = pd.DataFrame(all_data)
        print(f"✅ Total de registros extraídos: {len(result_df)}")
        print(f"✅ Estados encontrados: {sorted(result_df['state_code'].unique())}")
        print(f"✅ Período: {result_df['month_date'].min()} a {result_df['month_date'].max()}")
        
        print("\n📊 Estatísticas por estado:")
        for state in sorted(result_df['state_code'].unique()):
            state_data = result_df[result_df['state_code'] == state]
            print(f"  {state}: {len(state_data)} registros, média: {state_data['rent_variation'].mean():.2f}")
        
        print("\n📊 Amostra dos dados:")
        print(result_df.head(20).to_string())
        
        # Salvar resultado
        output_file = Path("data/raw/fipezap_extracted.csv")
        result_df.to_csv(output_file, index=False)
        print(f"\n💾 Dados salvos em: {output_file}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fipezap_extraction()