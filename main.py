#!/usr/bin/env python
"""Main pipeline - FINAL VERSION - CORRECTED."""

import logging
from pathlib import Path
import pandas as pd
import yaml

# Create directories
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("data/raw").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

from src.extraction import DataExtractor
from src.database import DatabaseManager
from src.analysis import DefaultAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        logger.warning("config.yaml not found, using default configuration")
        return {
            'data': {
                'states': [
                    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
                    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
                    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
                ]
            },
            'database': {'path': 'data/credit_risk.db'},
            'analysis': {'output_dir': 'reports', 'export_csv': True}
        }

def main():
    config = load_config()
    
    # Get Brazilian states from config
    BRAZILIAN_STATES = config.get('data', {}).get('states', [])
    
    logger.info("=" * 60)
    logger.info("DEFAULT ANALYSIS - FINAL PIPELINE")
    logger.info(f"ONLY {len(BRAZILIAN_STATES)} BRAZILIAN STATES (NO BR)")
    logger.info("=" * 60)
    
    try:
        # 1. Extract
        logger.info("\n1. Extracting data...")
        extractor = DataExtractor('config.yaml')
        data = extractor.run_full_extraction_real()
        extractor.save_to_csv(data, 'real')
        
        # 2. Save to database - WITH AGGRESSIVE FILTERING
        logger.info("\n2. Saving to database...")
        db = DatabaseManager(config.get('database', {}).get('path', 'data/credit_risk.db'))
        db.reset_database()
        
        # ========== SCR - AGGRESSIVE FILTER ==========
        scr_data = data['scr_defaults'].copy()
        logger.info(f"   SCR before filter: {len(scr_data)} records")
        
        # Remove anything that's not a state
        scr_data = scr_data[scr_data['state_code'].isin(BRAZILIAN_STATES)]
        scr_data = scr_data[scr_data['state_code'] != 'BR']
        scr_data = scr_data[scr_data['state_code'].notna()]
        scr_data = scr_data[scr_data['state_code'] != '']
        
        # Remove duplicates
        scr_data = scr_data.drop_duplicates(subset=['state_code', 'month_date'])
        
        logger.info(f"   SCR after filter: {len(scr_data)} states")
        logger.info(f"   SCR states: {sorted(scr_data['state_code'].unique())}")
        
        # Insert SCR
        db.insert_data('scr_monthly', scr_data)
        logger.info(f"   ✅ SCR inserted: {len(scr_data):,} records")
        
        # ========== MACRO - AGGRESSIVE FILTER ==========
        logger.info("\n   Building macro_indicators...")
        
        # Start with income
        macro = data['income'].copy()
        macro = macro[macro['state_code'].isin(BRAZILIAN_STATES)]
        macro = macro[macro['state_code'] != 'BR']
        macro = macro[macro['state_code'].notna()]
        macro = macro[macro['state_code'] != '']
        
        logger.info(f"   Income: {len(macro)} states")
        
        # Add GINI
        if 'gini' in data and not data['gini'].empty:
            gini_data = data['gini'].copy()
            gini_data = gini_data[gini_data['state_code'].isin(BRAZILIAN_STATES)]
            gini_data = gini_data[gini_data['state_code'] != 'BR']
            macro = pd.merge(macro, gini_data[['state_code', 'gini_index']], 
                           on='state_code', how='left')
            logger.info(f"   GINI: {len(gini_data)} states")
        
        # Add Unemployment
        if 'unemployment' in data and not data['unemployment'].empty:
            unemp_data = data['unemployment'].copy()
            unemp_data = unemp_data[unemp_data['state_code'].isin(BRAZILIAN_STATES)]
            unemp_data = unemp_data[unemp_data['state_code'] != 'BR']
            macro = pd.merge(macro, unemp_data[['state_code', 'unemployment_rate']], 
                           on='state_code', how='left')
            logger.info(f"   Unemployment: {len(unemp_data)} states")
        
        # Add FipeZAP
        if 'rent' in data and not data['rent'].empty:
            rent_data = data['rent'].copy()
            rent_data = rent_data[rent_data['state_code'].isin(BRAZILIAN_STATES)]
            rent_data = rent_data[rent_data['state_code'] != 'BR']
            
            fipezap_cols = ['state_code', 'total_index', 'monthly_variation_pct', 
                           'variation_12m_pct', 'avg_price', 'rent_variation']
            available_cols = [col for col in fipezap_cols if col in rent_data.columns]
            macro = pd.merge(macro, rent_data[available_cols], 
                           on='state_code', how='left')
            logger.info(f"   FipeZAP: {len(rent_data)} states")
        
        # FINAL CHECK - ensure only 27 states
        macro = macro[macro['state_code'].isin(BRAZILIAN_STATES)]
        macro = macro.drop_duplicates(subset=['state_code'])
        
        logger.info(f"   Macro final: {len(macro)} states")
        logger.info(f"   Macro states: {sorted(macro['state_code'].unique())}")
        
        # Check if we have exactly 27 states
        if len(macro) != 27:
            logger.warning(f"   ⚠️ WARNING: Macro has {len(macro)} states, expected 27")
            missing = set(BRAZILIAN_STATES) - set(macro['state_code'].unique())
            if missing:
                logger.warning(f"   Missing states: {sorted(missing)}")
        
        # Insert Macro
        db.insert_data('macro_indicators', macro)
        logger.info(f"   ✅ Macro inserted: {len(macro):,} records")
        
        # ========== POST-INSERTION VERIFICATION ==========
        logger.info("\n   Verifying data in database...")
        
        # Check SCR
        scr_check = db.query_to_dataframe("SELECT DISTINCT state_code FROM scr_monthly")
        logger.info(f"   States in SCR: {len(scr_check)} - {sorted(scr_check['state_code'].tolist())}")
        
        # Check Macro
        macro_check = db.query_to_dataframe("SELECT DISTINCT state_code FROM macro_indicators")
        logger.info(f"   States in Macro: {len(macro_check)} - {sorted(macro_check['state_code'].tolist())}")
        
        # 3. Analyze
        logger.info("\n3. Running analysis...")
        analyzer = DefaultAnalyzer(db, config)
        results = analyzer.run_full_analysis()
        
        # 4. Export
        logger.info("\n4. Exporting results...")
        if results:
            output_dir = config.get('analysis', {}).get('output_dir', 'reports')
            analyzer.export_results(results, output_dir)
        
        # 5. Summary
        logger.info("\n" + "=" * 60)
        logger.info("RESULTS - REAL DATA (27 STATES)")
        logger.info("=" * 60)
        
        if 'state_medians' in results and not results['state_medians'].empty:
            logger.info(f"\n📊 Analysis of {len(results['state_medians'])} states:")
            logger.info("\nTop 5 - Highest default rates:")
            for _, row in results['state_medians'].head(5).iterrows():
                logger.info(f"   {row['state_code']}: {row['median_default_pct']:.2f}% (n={row['observations']})")
        
        if 'correlations' in results and not results['correlations'].empty:
            n_obs = results['correlations']['observations'].max() if 'observations' in results['correlations'].columns else '?'
            logger.info(f"\n🔗 Correlations with default (n={n_obs} states):")
            for _, row in results['correlations'].iterrows():
                logger.info(f"   {row['indicator']}: {row['correlation']:.4f} ({row['strength']})")
                logger.info(f"      p-value: {row['p_value']:.4f} | n: {row['observations']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Pipeline completed successfully!")
        logger.info(f"📁 Reports in: {config.get('analysis', {}).get('output_dir', 'reports')}/")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()