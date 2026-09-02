"""
Script para validar os dados do SCR.data - Foco em 30/06/2026 (Cross-section).
Valida com dados oficiais do BACEN para PF - Veículos.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Dados oficiais do BACEN - 30/06/2026 (PF - Veículos)
# Fonte: https://www.bcb.gov.br/estabilidadefinanceira/scrdata
DADOS_OFICIAIS = {
    'Brasil': {
        'carteira_ativa': 403_923_493_654.08,
        'inadimplencia_pct': 6.77,
        'ativo_problematico_pct': 8.68,
    }
}

# Submodalidades EXATAS de veículos
SUB_MODALIDADES_VEICULOS = [
    'AQUISIÇÃO DE BENS - VEÍCULOS AUTOMOTORES',
    'ARRENDAMENTO FINANCEIRO DE VEÍCULOS AUTOMOTORES'
]

def carregar_scr_junho() -> pd.DataFrame:
    """
    Carrega apenas o arquivo de 30/06/2026 do SCR.data.
    """
    # Caminho do arquivo
    base_dir = Path("files/scrdata_2026")
    
    if not base_dir.exists():
        base_dir = Path("C:/Users/user/Documents/Projects/credit-risk-vehicle-loans/files/scrdata_2026")
    
    arquivo = base_dir / "scrdata_202606.csv"
    
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
    
    logger.info(f"  Carregando: {arquivo.name}")
    
    try:
        df = pd.read_csv(
            arquivo,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
            low_memory=False,
        )
        
        logger.info(f"  Total de registros: {len(df):,}")
        
        # Converter data
        if "data_base" in df.columns:
            df["data_base"] = pd.to_datetime(df["data_base"], format="%Y-%m-%d", errors="coerce")
            
            # Filtrar apenas 30/06/2026
            df = df[df["data_base"] == "2026-06-30"]
            logger.info(f"  Registros em 30/06/2026: {len(df):,}")
        else:
            logger.warning("  ⚠️ Coluna 'data_base' não encontrada")
            return df
        
        if df.empty:
            logger.warning("  ⚠️ Nenhum dado encontrado para 30/06/2026")
            return df
        
        # Tratamento numérico
        colunas_financeiras = [
            "a_vencer_ate_90_dias", "a_vencer_de_91_ate_360_dias",
            "a_vencer_de_361_ate_1080_dias", "a_vencer_de_1081_ate_1800_dias",
            "a_vencer_de_1801_ate_5400_dias", "a_vencer_acima_de_5400_dias",
            "carteira_a_vencer", "vencido_de_15_ate_90_dias",
            "vencido_acima_de_90_dias", "carteira_vencida",
            "carteira_ativa", "carteira_inadimplencia", "ativo_problematico"
        ]
        for col in colunas_financeiras:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        
        # Indicadores de crédito
        denominador = df["carteira_ativa"].replace(0, np.nan)
        df["taxa_inadimplencia"] = df["carteira_inadimplencia"] / denominador
        df["taxa_ativo_problematico"] = df["ativo_problematico"] / denominador
        df["taxa_carteira_vencida"] = df["carteira_vencida"] / denominador
        
        return df
        
    except Exception as e:
        logger.error(f"  ❌ Erro ao carregar: {e}")
        raise

def validar_scr_junho():
    """
    Valida os dados do SCR.data para 30/06/2026 (cross-section).
    """
    logger.info("=" * 60)
    logger.info("VALIDANDO SCR.DATA - 30/06/2026 (CROSS-SECTION)")
    logger.info("=" * 60)
    
    # 1. Carregar dados
    logger.info("\n1. CARREGANDO DADOS")
    logger.info("-" * 40)
    
    try:
        df = carregar_scr_junho()
    except Exception as e:
        logger.error(f"  ❌ Erro ao carregar: {e}")
        return
    
    if df.empty:
        logger.error("  ❌ Nenhum dado encontrado para 30/06/2026")
        return
    
    # ========== DIAGNÓSTICO - SUBMODALIDADES PF ==========
    logger.info("\n1.5. DIAGNÓSTICO - SUBMODALIDADES PF")
    logger.info("-" * 40)
    
    # Filtrar apenas PF
    if 'cliente' in df.columns:
        cliente_pf = df['cliente'].astype(str).str.upper().str.contains(
            'PESSOA FISICA|PESSOA FÍSICA|PF', 
            case=False, na=False
        )
        df_pf = df[cliente_pf]
        logger.info(f"  Total PF: {len(df_pf):,} registros")
        
        # Mostrar submodalidades PF (top 15)
        if 'submodalidade' in df_pf.columns:
            submods_pf = df_pf['submodalidade'].value_counts().head(15)
            logger.info(f"\n  Principais submodalidades PF:")
            for submod, count in submods_pf.items():
                ativa = df_pf[df_pf['submodalidade'] == submod]['carteira_ativa'].sum()
                pct = (ativa / df_pf['carteira_ativa'].sum()) * 100
                logger.info(f"    {submod}: {count:,} registros, R$ {ativa/1e9:,.2f} Bi ({pct:.1f}%)")
    
    # 2. FILTRAR: PF + Veículos (submodalidades EXATAS)
    logger.info("\n2. FILTRANDO PF + VEÍCULOS (submodalidades EXATAS)")
    logger.info("-" * 40)
    
    # Filtro PF
    if 'cliente' in df.columns:
        cliente_pf = df['cliente'].astype(str).str.upper().str.contains(
            'PESSOA FISICA|PESSOA FÍSICA|PF', 
            case=False, na=False
        )
        df = df[cliente_pf]
        logger.info(f"  Após filtro PF: {len(df):,} registros")
    
    # Filtro Veículos - APENAS as submodalidades EXATAS
    if 'submodalidade' in df.columns:
        # Criar máscara para as duas submodalidades exatas
        mascara = df['submodalidade'].astype(str).str.upper().isin(
            [s.upper() for s in SUB_MODALIDADES_VEICULOS]
        )
        df = df[mascara]
        logger.info(f"  Após filtro submodalidades EXATAS: {len(df):,} registros")
        
        # Mostrar submodalidades após o filtro
        if not df.empty:
            submods = df['submodalidade'].value_counts()
            logger.info(f"\n  Submodalidades incluídas:")
            for submod, count in submods.items():
                ativa = df[df['submodalidade'] == submod]['carteira_ativa'].sum()
                logger.info(f"    {submod}: {count:,} registros, R$ {ativa/1e9:,.2f} Bi")
        else:
            logger.warning("  ⚠️ Nenhum registro encontrado para as submodalidades especificadas!")
            logger.info(f"  Submodalidades disponíveis: {df['submodalidade'].unique()[:10]}")
            return
    else:
        logger.error("  ❌ Coluna 'submodalidade' não encontrada")
        return
    
    if df.empty:
        logger.error("  ❌ Nenhum dado após os filtros!")
        return
    
    # 3. VALIDAR TOTAL BRASIL
    logger.info("\n3. VALIDAÇÃO - TOTAL BRASIL (PF + Veículos)")
    logger.info("-" * 40)
    
    total_ativa = df['carteira_ativa'].sum()
    total_inad = df['carteira_inadimplencia'].sum()
    total_ativo_prob = df['ativo_problematico'].sum()
    total_vencido = df['vencido_acima_de_90_dias'].sum()
    
    taxa_inad = (total_inad / total_ativa) * 100 if total_ativa > 0 else 0
    taxa_ativo_prob = (total_ativo_prob / total_ativa) * 100 if total_ativa > 0 else 0
    taxa_vencido = (total_vencido / total_ativa) * 100 if total_ativa > 0 else 0
    
    logger.info(f"\n  📊 Total Brasil - PF + Veículos (30/06/2026):")
    logger.info(f"    Carteira Ativa: R$ {total_ativa:,.2f} (R$ {total_ativa/1e9:,.2f} Bi)")
    logger.info(f"    Inadimplência: R$ {total_inad:,.2f} (R$ {total_inad/1e9:,.2f} Bi)")
    logger.info(f"    Ativo Problemático: R$ {total_ativo_prob:,.2f} (R$ {total_ativo_prob/1e9:,.2f} Bi)")
    logger.info(f"    Vencido > 90 dias: R$ {total_vencido:,.2f} (R$ {total_vencido/1e9:,.2f} Bi)")
    logger.info(f"    Taxa de Inadimplência: {taxa_inad:.2f}%")
    logger.info(f"    Taxa de Ativo Problemático: {taxa_ativo_prob:.2f}%")
    logger.info(f"    Taxa de Vencido > 90 dias: {taxa_vencido:.2f}%")
    
    # Comparar com dados oficiais
    logger.info(f"\n  🔍 Comparação com dados oficiais do BACEN:")
    logger.info(f"    Oficial - Carteira Ativa: R$ {DADOS_OFICIAIS['Brasil']['carteira_ativa']:,.2f} (R$ {DADOS_OFICIAIS['Brasil']['carteira_ativa']/1e9:,.2f} Bi)")
    logger.info(f"    Calculado: R$ {total_ativa:,.2f} (R$ {total_ativa/1e9:,.2f} Bi)")
    
    diff_ativa = total_ativa - DADOS_OFICIAIS['Brasil']['carteira_ativa']
    diff_pct = (diff_ativa / DADOS_OFICIAIS['Brasil']['carteira_ativa']) * 100
    
    logger.info(f"    Diferença: R$ {diff_ativa:,.2f} ({diff_pct:.2f}%)")
    
    if abs(diff_pct) < 1:
        logger.info(f"    ✅ VALIDADO - Carteira Ativa dentro da margem de erro")
    else:
        logger.warning(f"    ⚠️  ATENÇÃO - Diferença significativa ({diff_pct:.2f}%)")
    
    # 4. Agregar por estado
    logger.info("\n4. AGREGAÇÃO POR ESTADO")
    logger.info("-" * 40)
    
    # Identificar coluna de estado
    uf_col = None
    for col in ['uf', 'estado', 'state', 'UF', 'Estado']:
        if col in df.columns:
            uf_col = col
            break
    
    if uf_col is None:
        logger.error("  ❌ Coluna de estado não encontrada")
        return
    
    # Agregar
    agregado = df.groupby(uf_col).agg({
        'carteira_ativa': 'sum',
        'carteira_inadimplencia': 'sum',
        'vencido_acima_de_90_dias': 'sum',
        'ativo_problematico': 'sum'
    }).reset_index()
    
    # Renomear coluna de estado
    agregado = agregado.rename(columns={uf_col: 'uf'})
    
    # Calcular taxas
    agregado['taxa_inadimplencia'] = (agregado['carteira_inadimplencia'] / agregado['carteira_ativa']) * 100
    agregado['taxa_ativo_problematico'] = (agregado['ativo_problematico'] / agregado['carteira_ativa']) * 100
    agregado['taxa_vencido_acima_90'] = (agregado['vencido_acima_de_90_dias'] / agregado['carteira_ativa']) * 100
    
    # Ordenar por carteira ativa
    agregado = agregado.sort_values('carteira_ativa', ascending=False)
    
    logger.info(f"  Total estados: {len(agregado)}")
    
    # 5. Mostrar resultados por estado
    logger.info("\n5. RESULTADOS POR ESTADO - 30/06/2026")
    logger.info("-" * 40)
    
    logger.info("  📊 Agregação por Estado (PF + Veículos):")
    logger.info("  " + "-" * 110)
    logger.info(f"  {'UF':<5} {'Carteira Ativa':>20} {'Inadimplência':>18} {'Taxa Inad':>10} {'Taxa AP':>10} {'Vencido >90':>18}")
    logger.info("  " + "-" * 110)
    
    for _, row in agregado.iterrows():
        uf = row['uf']
        ativa = row['carteira_ativa']
        inad = row['carteira_inadimplencia']
        taxa_inad = row['taxa_inadimplencia']
        taxa_ap = row['taxa_ativo_problematico']
        vencido = row['vencido_acima_de_90_dias']
        
        ativa_str = f"R$ {ativa/1e9:,.2f} Bi"
        inad_str = f"R$ {inad/1e9:,.2f} Bi"
        vencido_str = f"R$ {vencido/1e9:,.2f} Bi"
        
        logger.info(f"  {uf:<5} {ativa_str:>20} {inad_str:>18} {taxa_inad:>9.2f}% {taxa_ap:>9.2f}% {vencido_str:>18}")
    
    # 6. Salvar resultados
    logger.info("\n6. SALVANDO RESULTADOS")
    logger.info("-" * 40)
    
    output_dir = Path("reports/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar agregação
    output_file = output_dir / "scr_aggregation_20260630.csv"
    agregado.to_csv(output_file, index=False)
    logger.info(f"  ✅ Agregação salva em: {output_file}")
    
    # Salvar relatório
    report_file = output_dir / "validation_report_20260630.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("RELATÓRIO DE VALIDAÇÃO - SCR.DATA\n")
        f.write("30/06/2026 (CROSS-SECTION)\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"TOTAL BRASIL:\n")
        f.write(f"  Carteira Ativa: R$ {total_ativa:,.2f}\n")
        f.write(f"  Inadimplência: {taxa_inad:.2f}%\n")
        f.write(f"  Ativo Problemático: {taxa_ativo_prob:.2f}%\n\n")
        f.write(f"OFICIAL BACEN:\n")
        f.write(f"  Carteira Ativa: R$ {DADOS_OFICIAIS['Brasil']['carteira_ativa']:,.2f}\n")
        f.write(f"  Diferença: {diff_pct:.2f}%\n\n")
        f.write("ESTADOS:\n")
        for _, row in agregado.iterrows():
            f.write(f"{row['uf']}: {row['taxa_inadimplencia']:.2f}% | AP: {row['taxa_ativo_problematico']:.2f}%\n")
    
    logger.info(f"  ✅ Relatório salvo em: {report_file}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ VALIDAÇÃO CONCLUÍDA!")
    logger.info("=" * 60)
    
    # 7. Resumo para correlação
    logger.info("\n📊 RESUMO PARA CORRELAÇÃO (CROSS-SECTION)")
    logger.info("-" * 40)
    logger.info(f"  Estados disponíveis: {len(agregado)}")
    logger.info(f"  Estados: {sorted(agregado['uf'].tolist())}")
    logger.info(f"  Taxa de inadimplência média: {agregado['taxa_inadimplencia'].mean():.2f}%")

def main():
    """Função principal."""
    validar_scr_junho()

if __name__ == "__main__":
    main()