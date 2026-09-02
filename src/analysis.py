"""Statistical analysis for vehicle default prediction."""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple, List
import logging
from pathlib import Path
from src.database import DatabaseManager

logger = logging.getLogger(__name__)

class DefaultAnalyzer:
    def __init__(self, db: DatabaseManager, config: Optional[Dict] = None):
        self.db = db
        self.results = {}
        self.config = config or {}
        
        # Get states from config or use default
        self.brazilian_states = self.config.get('data', {}).get('states', [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ])
        
        # Ensure we have exactly 27 states
        self.brazilian_states = list(set(self.brazilian_states))
        logger.info(f"Analyzer initialized with {len(self.brazilian_states)} states")
    
    def _filter_brazilian_states(self, df: pd.DataFrame, column: str = 'state_code') -> pd.DataFrame:
        """Filter DataFrame to include only Brazilian states (exclude BR)."""
        if df.empty:
            return df
        filtered = df[df[column].isin(self.brazilian_states)]
        logger.debug(f"Filtered from {len(df)} to {len(filtered)} rows")
        return filtered
    
    def _debug_merged_data(self, merged: pd.DataFrame) -> None:
        """Debug: Show details of merged data."""
        logger.info("\n🔍 DEBUG - Merged data:")
        logger.info(f"   Total rows: {len(merged)}")
        logger.info(f"   States: {sorted(merged['state_code'].unique())}")
        logger.info(f"   Columns: {merged.columns.tolist()}")
        
        # Check if BR is present
        if 'BR' in merged['state_code'].values:
            logger.error("   ❌ WARNING: BR found in data!")
            br_row = merged[merged['state_code'] == 'BR']
            logger.error(f"   BR data: {br_row.to_dict()}")
        else:
            logger.info("   ✅ BR not found in data")
        
        # Check number of states
        n_states = len(merged['state_code'].unique())
        logger.info(f"   Number of states: {n_states}")
        
        if n_states != 27:
            logger.warning(f"   ⚠️ Expected 27 states, found {n_states}")
    
    def run_full_analysis(self) -> Dict[str, pd.DataFrame]:
        """Run complete analysis pipeline."""
        logger.info("Running full analysis...")
        results = {}
        results['state_medians'] = self.calculate_state_medians()
        results['correlations'] = self.compute_correlation_matrix()
        results['monthly_rankings'] = self.identify_distressed_states()
        results['trend_analysis'] = self.analyze_trends()
        results['outliers'] = self.detect_outliers()
        
        # Filter out empty DataFrames
        results = {k: v for k, v in results.items() if not v.empty}
        logger.info(f"Analysis completed with {len(results)} results")
        return results
    
    def calculate_state_medians(self) -> pd.DataFrame:
        """Calculate median default rates by state."""
        states_placeholder = ','.join(["'{}'".format(s) for s in self.brazilian_states])
        
        query = f"""
        SELECT state_code, default_rate_90
        FROM scr_monthly
        WHERE default_rate_90 IS NOT NULL
          AND state_code IN ({states_placeholder})
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            return pd.DataFrame()
        
        results = []
        for state in df['state_code'].unique():
            data = df[df['state_code'] == state]['default_rate_90']
            if len(data) > 0:
                results.append({
                    'state_code': state,
                    'observations': len(data),
                    'avg_default_pct': round(data.mean(), 2),
                    'median_default_pct': round(data.median(), 2),
                    'min_default_pct': round(data.min(), 2),
                    'max_default_pct': round(data.max(), 2),
                    'std_default_pct': round(data.std(), 2)
                })
        
        result_df = pd.DataFrame(results)
        logger.info(f"Calculated medians for {len(result_df)} Brazilian states")
        return result_df.sort_values('median_default_pct', ascending=False)
    
    def compute_correlation_matrix(self) -> pd.DataFrame:
        """Compute correlations with ALL FipeZAP indicators."""
        logger.info("Computing correlations...")
        
        states_placeholder = ','.join(["'{}'".format(s) for s in self.brazilian_states])
        
        # Get default data - FORCE only Brazilian states
        default_query = f"""
        SELECT state_code, AVG(default_rate_90) as avg_default_rate
        FROM scr_monthly
        WHERE default_rate_90 IS NOT NULL
          AND state_code IN ({states_placeholder})
        GROUP BY state_code
        """
        default_df = self.db.query_to_dataframe(default_query)
        
        if default_df.empty:
            logger.warning("No default data available")
            return pd.DataFrame()
        
        logger.info(f"  Default data: {len(default_df)} Brazilian states")
        
        # Get macro data - FORCE only Brazilian states
        macro_query = f"""
        SELECT state_code, 
               median_income, 
               gini_index, 
               unemployment_rate,
               total_index,
               monthly_variation_pct,
               variation_12m_pct,
               avg_price,
               rent_variation
        FROM macro_indicators
        WHERE state_code IN ({states_placeholder})
        """
        macro_df = self.db.query_to_dataframe(macro_query)
        
        if macro_df.empty:
            logger.warning("No macro data available")
            return pd.DataFrame()
        
        logger.info(f"  Macro data: {len(macro_df)} Brazilian states")
        
        # Log states for debugging
        default_states = set(default_df['state_code'].tolist())
        macro_states = set(macro_df['state_code'].tolist())
        common_states = default_states & macro_states
        
        logger.info(f"  Common states: {len(common_states)}")
        
        # Check if we have all 27 states
        missing_states = set(self.brazilian_states) - common_states
        if missing_states:
            logger.warning(f"  Missing states: {sorted(missing_states)}")
        
        # Merge
        merged = pd.merge(default_df, macro_df, on='state_code', how='inner')
        
        # Final safety filter
        merged = merged[merged['state_code'].isin(self.brazilian_states)]
        
        if merged.empty:
            logger.warning("No matching states")
            return pd.DataFrame()
        
        logger.info(f"  Merged data: {len(merged)} Brazilian states")
        
        # Debug merged data
        self._debug_merged_data(merged)
        
        # Define indicators (no duplicates)
        indicators = [
            ('median_income', 'Median Income (R$)'),
            ('gini_index', 'Gini Index'),
            ('unemployment_rate', 'Unemployment Rate (%)'),
            ('total_index', 'FipeZAP - Total Index'),
            ('monthly_variation_pct', 'FipeZAP - Monthly Variation (%)'),
            ('variation_12m_pct', 'FipeZAP - 12M Variation (%)'),
            ('avg_price', 'FipeZAP - Avg Price (R$/m²)'),
            ('rent_variation', 'FipeZAP - Rent Variation (12M %)')
        ]
        
        correlations = []
        for col, label in indicators:
            if col in merged.columns and not merged[col].isna().all():
                clean = merged[['avg_default_rate', col]].dropna()
                if len(clean) > 2:
                    corr = clean['avg_default_rate'].corr(clean[col])
                    p_val = stats.pearsonr(clean['avg_default_rate'], clean[col])[1]
                    
                    correlations.append({
                        'indicator': label,
                        'correlation': round(corr, 4),
                        'p_value': round(p_val, 4),
                        'strength': self._interpret_correlation(corr),
                        'significance': self._interpret_significance(p_val),
                        'observations': len(clean)
                    })
                    logger.info(f"  {label}: r={corr:.4f}, p={p_val:.4f}, n={len(clean)}")
                else:
                    logger.warning(f"  {label}: insufficient data (n={len(clean)})")
            else:
                logger.warning(f"  {label}: column not found or all NaN")
        
        if not correlations:
            logger.warning("No correlations calculated")
            return pd.DataFrame()
        
        return pd.DataFrame(correlations).sort_values('correlation', ascending=False)
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            return 'Strong'
        elif abs_corr >= 0.4:
            return 'Moderate'
        elif abs_corr >= 0.2:
            return 'Weak'
        else:
            return 'Very Weak'
    
    def _interpret_significance(self, p: float) -> str:
        """Interpret p-value significance."""
        if p > 0.1:
            return 'Not Significant'
        elif p > 0.05:
            return 'Weakly Significant (*)'
        elif p > 0.01:
            return 'Significant (**)'
        else:
            return 'Highly Significant (***)'
    
    def identify_distressed_states(self) -> pd.DataFrame:
        """Identify states with highest default rates."""
        states_placeholder = ','.join(["'{}'".format(s) for s in self.brazilian_states])
        
        query = f"""
        WITH ranks AS (
            SELECT state_code, month_date, default_rate_90,
                   RANK() OVER (PARTITION BY month_date ORDER BY default_rate_90 DESC) as rank_90
            FROM scr_monthly
            WHERE default_rate_90 IS NOT NULL
              AND state_code IN ({states_placeholder})
        )
        SELECT state_code, 
               COUNT(*) as months_ranked,
               ROUND(AVG(rank_90), 1) as avg_rank,
               ROUND(AVG(default_rate_90), 2) as avg_default_pct,
               SUM(CASE WHEN rank_90 <= 3 THEN 1 ELSE 0 END) as times_in_top_3
        FROM ranks
        GROUP BY state_code
        HAVING months_ranked >= 3
        ORDER BY avg_rank ASC
        """
        
        result = self.db.query_to_dataframe(query)
        logger.info(f"Identified {len(result)} distressed states")
        return result
    
    def analyze_trends(self) -> pd.DataFrame:
        """Analyze default rate trends over time."""
        states_placeholder = ','.join(["'{}'".format(s) for s in self.brazilian_states])
        
        query = f"""
        SELECT strftime('%Y-%m', month_date) as month,
               state_code, default_rate_90
        FROM scr_monthly
        WHERE default_rate_90 IS NOT NULL
          AND state_code IN ({states_placeholder})
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            return pd.DataFrame()
        
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values(['state_code', 'month'])
        df['pct_change'] = df.groupby('state_code')['default_rate_90'].pct_change() * 100
        
        result = df.groupby('state_code').agg({
            'default_rate_90': ['mean', 'max', 'min'],
            'pct_change': ['mean']
        }).round(4)
        result.columns = ['avg_default', 'max_default', 'min_default', 'avg_pct_change']
        result = result.reset_index()
        result['trend_direction'] = result['avg_pct_change'].apply(
            lambda x: 'Increasing' if x > 0.5 else ('Decreasing' if x < -0.5 else 'Stable')
        )
        
        logger.info(f"Trend analysis completed for {len(result)} Brazilian states")
        return result
    
    def detect_outliers(self) -> pd.DataFrame:
        """Detect outliers using z-score method."""
        states_placeholder = ','.join(["'{}'".format(s) for s in self.brazilian_states])
        
        query = f"""
        SELECT state_code, default_rate_90 
        FROM scr_monthly 
        WHERE default_rate_90 IS NOT NULL
          AND state_code IN ({states_placeholder})
        """
        df = self.db.query_to_dataframe(query)
        if df.empty:
            return pd.DataFrame()
        
        z_scores = []
        for state in df['state_code'].unique():
            data = df[df['state_code'] == state]['default_rate_90']
            if len(data) > 1:
                mean = data.mean()
                std = data.std()
                if std > 0:
                    z_scores.extend(((data - mean) / std).tolist())
                else:
                    z_scores.extend([0] * len(data))
            else:
                z_scores.extend([0] * len(data))
        
        df['z_score'] = z_scores
        df['is_outlier'] = abs(df['z_score']) > 2
        outliers = df[df['is_outlier']]
        
        logger.info(f"Detected {len(outliers)} outliers in Brazilian states")
        return outliers
    
    def export_results(self, results: Dict[str, pd.DataFrame], output_dir: str = 'reports') -> None:
        """Export all results to CSV files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for name, df in results.items():
            if not df.empty:
                filepath = output_path / f"{name}.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Exported: {filepath} ({len(df)} rows)")