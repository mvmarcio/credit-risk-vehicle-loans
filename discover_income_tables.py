import sidrapy
import pandas as pd

# Tabelas históricas e ativas da PNADC para Rendimento Habitual por UF
income_tables_to_test = ["6588", "6589", "6590", "7358", "7359"]

print("INSPECIONANDO TABELAS DE RENDIMENTO NO IBGE SIDRA...\n")

for table in income_tables_to_test:
    print(f"--- TESTANDO TABELA SIDRA {table} ---")
    try:
        df = sidrapy.get_table(
            table_code=table,
            territorial_level="3",
            ibge_territorial_code="all",
            period="last 1"
        )
        if isinstance(df, pd.DataFrame) and len(df) > 1:
            # Pega códigos D3C (Código) e D3N (Descrição) das variáveis presentes na tabela
            vars_found = df[['D3C', 'D3N']].drop_duplicates()
            print(f"✓ Tabela {table} ATIVA! Variáveis encontradas:")
            print(vars_found.to_string(index=False))
            print("\nPrimeiras linhas do retorno:")
            print(df[['D1N', 'D3N', 'V']].iloc[1:6].to_string(index=False))
            print("="*60 + "\n")
        else:
            print(f"✗ Tabela {table} sem dados ou retorno vazio.\n")
    except Exception as e:
        print(f"✗ Erro na Tabela {table}: {e}\n")