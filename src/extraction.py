"""Data extraction from official Brazilian sources (BACEN, PNAD, FipeZAP)."""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extract REAL data from BACEN, PNAD, and FipeZAP."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.base_dir = Path(__file__).parent.parent
        self.raw_dir = self.base_dir / 'data' / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        
        # Get states from config
        self.brazilian_states = self.config.get('data', {}).get('states', [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ])
        
        logger.info(f"Extractor initialized with {len(self.brazilian_states)} states")
    
    def _load_config(self, config_path: str) -> Dict:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")
    
    def _remove_br_from_dataframe(self, df: pd.DataFrame, state_col: str = 'state_code') -> pd.DataFrame:
        """Remove BR (Brazil aggregate) from dataframe."""
        if df.empty:
            return df
        
        original_len = len(df)
        filtered = df[df[state_col].isin(self.brazilian_states)]
        
        if len(filtered) < original_len:
            logger.info(f"  Removed {original_len - len(filtered)} rows (including BR)")
        
        return filtered
    
    # ========== SCR.DATA ==========
    
    def extract_scr_data_real(self) -> pd.DataFrame:
        """
        Extract REAL state-level data from SCR.data (validated).
        Uses the validated aggregation from 30/06/2026.
        """
        logger.info("Extracting REAL SCR.data (validated)...")
        
        # Get date from config
        scr_date = self.config.get('extraction', {}).get('scr', {}).get('date', '2026-06-30')
        
        # Path to validated file
        scr_file = Path(f"reports/validation/scr_aggregation_{scr_date.replace('-', '')}.csv")
        
        # If not exists, try original file
        if not scr_file.exists():
            logger.warning("  Validated file not found. Trying original file...")
            scr_file = Path(self.config.get('extraction', {}).get('scr', {}).get('file', 'files/scrdata_2026/scrdata_202606.csv'))
            
            if not scr_file.exists():
                raise FileNotFoundError(
                    f"\n{'='*60}\n"
                    f"❌ SCR file not found!\n"
                    f"{'='*60}\n"
                    f"Run first: python tests/validate_scr_data.py\n"
                    f"{'='*60}"
                )
            
            # Process original file
            df = self._process_scr_raw(scr_file)
        else:
            # Load validated file
            df = pd.read_csv(scr_file)
            logger.info(f"  ✅ Loaded validated file: {len(df)} states")
        
        # Ensure required columns
        required_cols = ['uf', 'taxa_inadimplencia']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Required columns not found: {required_cols}")
        
        # Rename to project standard
        df = df.rename(columns={
            'uf': 'state_code',
            'taxa_inadimplencia': 'default_rate_90'
        })
        
        # Add date
        df['month_date'] = scr_date
        
        # Select only necessary columns
        result = df[['state_code', 'month_date', 'default_rate_90']].copy()
        
        # REMOVE BR
        result = self._remove_br_from_dataframe(result)
        
        # Ensure all states are present
        estados_presentes = set(result['state_code'].unique())
        estados_faltando = set(self.brazilian_states) - estados_presentes
        
        if estados_faltando:
            logger.warning(f"  Missing states: {sorted(estados_faltando)}")
            # Use mean for missing states
            media = result['default_rate_90'].mean()
            for estado in estados_faltando:
                novo_registro = pd.DataFrame({
                    'state_code': [estado],
                    'month_date': [scr_date],
                    'default_rate_90': [media]
                })
                result = pd.concat([result, novo_registro], ignore_index=True)
        
        logger.info(f"✅ SCR.data final: {len(result)} states")
        return result
    
    def _process_scr_raw(self, scr_file: Path) -> pd.DataFrame:
        """Process raw SCR file."""
        logger.info(f"  Processing file: {scr_file}")
        
        df = pd.read_csv(
            scr_file,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
            low_memory=False,
        )
        
        # Get date from config
        scr_date = self.config.get('extraction', {}).get('scr', {}).get('date', '2026-06-30')
        
        # Filter date
        if "data_base" in df.columns:
            df["data_base"] = pd.to_datetime(df["data_base"], format="%Y-%m-%d", errors="coerce")
            df = df[df["data_base"] == scr_date]
        
        # Filter PF
        if 'cliente' in df.columns:
            cliente_pf = df['cliente'].astype(str).str.upper().str.contains(
                'PESSOA FISICA|PESSOA FÍSICA|PF', 
                case=False, na=False
            )
            df = df[cliente_pf]
        
        # Filter Vehicles
        if 'submodalidade' in df.columns:
            submods_veiculos = [
                'AQUISIÇÃO DE BENS - VEÍCULOS AUTOMOTORES',
                'ARRENDAMENTO FINANCEIRO DE VEÍCULOS AUTOMOTORES'
            ]
            mask = df['submodalidade'].astype(str).str.upper().isin(
                [s.upper() for s in submods_veiculos]
            )
            df = df[mask]
        
        # Aggregate by state
        if 'uf' in df.columns and 'carteira_ativa' in df.columns:
            aggregated = df.groupby('uf').agg({
                'carteira_ativa': 'sum',
                'carteira_inadimplencia': 'sum',
                'ativo_problematico': 'sum'
            }).reset_index()
            
            # Calculate rates
            aggregated['taxa_inadimplencia'] = (aggregated['carteira_inadimplencia'] / aggregated['carteira_ativa']) * 100
            aggregated['taxa_ativo_problematico'] = (aggregated['ativo_problematico'] / aggregated['carteira_ativa']) * 100
            
            logger.info(f"  ✅ Processed: {len(aggregated)} states")
            return aggregated
        
        raise ValueError("Required columns not found in SCR file")
    
    # ========== PNAD VIA PNADIUM ==========
    
    def extract_pnad_income_real(self) -> pd.DataFrame:
        """Extract REAL income data from PNAD Contínua using pnadium."""
        logger.info("Extracting REAL PNAD income data...")
        
        import pnadium as pnad
        
        pnad_year = self.config.get('extraction', {}).get('pnad', {}).get('year', 2025)
        pnad_quarter = self.config.get('extraction', {}).get('pnad', {}).get('quarter', 1)
        
        variables = ['UF', 'VD4020', 'V1028']
        df = pnad.baixar_microdados(ano=pnad_year, periodo=pnad_quarter, tipo='trimestral', variaveis=variables)
        
        if df is None or df.empty:
            raise ValueError("No PNAD income data returned")
        
        logger.info(f"  Downloaded {len(df):,} records")
        
        income_var = 'VD4020'
        state_var = 'UF'
        weight_var = 'V1028'
        
        df[state_var] = df[state_var].astype(str).str.zfill(2)
        
        results = []
        for state in df[state_var].unique():
            state_data = df[df[state_var] == state]
            valid = state_data[state_data[income_var] > 0]
            
            if len(valid) > 0:
                if weight_var in valid.columns and valid[weight_var].sum() > 0:
                    sorted_data = valid.sort_values(income_var)
                    total_weight = sorted_data[weight_var].sum()
                    cumsum = sorted_data[weight_var].cumsum()
                    median_idx = (cumsum / total_weight >= 0.5).idxmax()
                    median_income = sorted_data.loc[median_idx, income_var]
                else:
                    median_income = valid[income_var].median()
                
                state_code = self._ibge_to_state(state)
                if state_code in self.brazilian_states:
                    results.append({
                        'state_code': state_code,
                        'median_income': round(float(median_income), 2)
                    })
        
        result = pd.DataFrame(results)
        result['month_date'] = f"{pnad_year}-01-01"
        result['quarter'] = f"{pnad_year}Q{pnad_quarter}"
        
        # Filter only Brazilian states
        result = self._remove_br_from_dataframe(result)
        
        logger.info(f"✅ PNAD income: {len(result)} states")
        return result
    
    def extract_pnad_gini_real(self) -> pd.DataFrame:
        """Extract REAL GINI index from PNAD Contínua using pnadium."""
        logger.info("Extracting REAL PNAD GINI data...")
        
        import pnadium as pnad
        
        pnad_year = self.config.get('extraction', {}).get('pnad', {}).get('year', 2025)
        pnad_quarter = self.config.get('extraction', {}).get('pnad', {}).get('quarter', 1)
        
        variables = ['UF', 'VD4020', 'V1028']
        df = pnad.baixar_microdados(ano=pnad_year, periodo=pnad_quarter, tipo='trimestral', variaveis=variables)
        
        if df is None or df.empty:
            raise ValueError("No PNAD GINI data returned")
        
        income_var = 'VD4020'
        state_var = 'UF'
        weight_var = 'V1028'
        
        df[state_var] = df[state_var].astype(str).str.zfill(2)
        
        results = []
        for state in df[state_var].unique():
            state_data = df[df[state_var] == state]
            valid = state_data[state_data[income_var] > 0]
            
            if len(valid) > 0:
                incomes = valid[income_var].values
                weights = valid[weight_var].values if weight_var in valid.columns else None
                gini = self._gini_coefficient(incomes, weights)
                
                state_code = self._ibge_to_state(state)
                if state_code in self.brazilian_states:
                    results.append({
                        'state_code': state_code,
                        'gini_index': round(gini, 4)
                    })
        
        result = pd.DataFrame(results)
        result['month_date'] = f"{pnad_year}-01-01"
        result['quarter'] = f"{pnad_year}Q{pnad_quarter}"
        
        # Filter only Brazilian states
        result = self._remove_br_from_dataframe(result)
        
        logger.info(f"✅ PNAD GINI: {len(result)} states")
        return result
    
    def extract_pnad_unemployment_real(self) -> pd.DataFrame:
        """Extract REAL unemployment rate from PNAD Contínua using pnadium."""
        logger.info("Extracting REAL PNAD unemployment data...")
        
        import pnadium as pnad
        
        pnad_year = self.config.get('extraction', {}).get('pnad', {}).get('year', 2025)
        pnad_quarter = self.config.get('extraction', {}).get('pnad', {}).get('quarter', 1)
        
        variables = ['UF', 'VD4002', 'VD4001']
        df = pnad.baixar_microdados(ano=pnad_year, periodo=pnad_quarter, tipo='trimestral', variaveis=variables)
        
        if df is None or df.empty:
            raise ValueError("No PNAD unemployment data returned")
        
        occupation_var = 'VD4002'
        labor_force_var = 'VD4001'
        state_var = 'UF'
        
        df[state_var] = df[state_var].astype(str).str.zfill(2)
        
        results = []
        for state in df[state_var].unique():
            state_data = df[df[state_var] == state]
            
            if labor_force_var in state_data.columns:
                labor_force = state_data[state_data[labor_force_var] == 1]
            else:
                labor_force = state_data
            
            if len(labor_force) > 0:
                total = len(labor_force)
                unemployed = len(labor_force[labor_force[occupation_var] == 2])
                rate = (unemployed / total) * 100 if total > 0 else 0
                
                state_code = self._ibge_to_state(state)
                if state_code in self.brazilian_states:
                    results.append({
                        'state_code': state_code,
                        'unemployment_rate': round(rate, 2)
                    })
        
        result = pd.DataFrame(results)
        result['month_date'] = f"{pnad_year}-01-01"
        result['quarter'] = f"{pnad_year}Q{pnad_quarter}"
        
        # Filter only Brazilian states
        result = self._remove_br_from_dataframe(result)
        
        logger.info(f"✅ PNAD unemployment: {len(result)} states")
        return result
    
    def _ibge_to_state(self, code: str) -> str:
        ibge_map = {
            '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA',
            '16': 'AP', '17': 'TO', '21': 'MA', '22': 'PI', '23': 'CE',
            '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE',
            '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
            '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT',
            '52': 'GO', '53': 'DF'
        }
        return ibge_map.get(str(code).zfill(2), str(code))
    
    def _gini_coefficient(self, incomes: List[float], weights: Optional[List[float]] = None) -> float:
        if len(incomes) == 0:
            return 0
        
        if weights is None:
            weights = [1] * len(incomes)
        
        sorted_pairs = sorted(zip(incomes, weights), key=lambda x: x[0])
        sorted_incomes = [p[0] for p in sorted_pairs]
        sorted_weights = [p[1] for p in sorted_pairs]
        
        total_weight = sum(sorted_weights)
        cum_weight = 0
        cum_income = 0
        
        total_income = sum(income * weight for income, weight in zip(sorted_incomes, sorted_weights))
        
        if total_income == 0:
            return 0
        
        gini = 0
        for i in range(len(sorted_incomes)):
            cum_weight += sorted_weights[i]
            cum_income += sorted_incomes[i] * sorted_weights[i]
            p = cum_weight / total_weight
            q = cum_income / total_income
            gini += (p - q) * sorted_weights[i]
        
        return max(0, min(gini / total_weight * 2, 1))
    
    # ========== FIPEZAP ==========
    
    def extract_fipezap_manual(self) -> pd.DataFrame:
        """
        Load REAL FipeZAP data manually extracted from the spreadsheet.
        ALL 27 states are present in the file.
        """
        logger.info("Loading REAL FipeZAP data...")
        
        excel_path = Path(self.config.get('extraction', {}).get('fipezap', {}).get('file', 'files/fipeza_capital_data.xlsx'))
        
        if not excel_path.exists():
            raise FileNotFoundError(f"FipeZAP file not found: {excel_path}")
        
        # Load Excel
        df = pd.read_excel(excel_path)
        
        logger.info(f"  Loaded {len(df)} records from FipeZAP Excel")
        logger.info(f"  Columns: {df.columns.tolist()}")
        
        # Rename columns to project standard
        rename_map = {
            'City': 'city',
            'Total Index': 'total_index',
            'Monthly Variation Index': 'monthly_variation',
            'Variation 12 Months': 'variation_12m',
            'Average Price R$/m²': 'avg_price'
        }
        df = df.rename(columns=rename_map)
        
        # Check if state_code already exists
        if 'State' in df.columns:
            df['state_code'] = df['State'].astype(str).str.upper().str[:2]
        else:
            # Map city to state
            city_to_state = {
                'Sao Paulo': 'SP', 'Rio de Janeiro': 'RJ', 'Belo Horizonte': 'MG',
                'Porto Alegre': 'RS', 'Curitiba': 'PR', 'Florianopolis': 'SC',
                'Vitoria': 'ES', 'Brasilia': 'DF', 'Goiania': 'GO',
                'Campo Grande': 'MS', 'Cuiaba': 'MT', 'Aracaju': 'SE',
                'Fortaleza': 'CE', 'Joao Pessoa': 'PB', 'Maceio': 'AL',
                'Natal': 'RN', 'Recife': 'PE', 'Salvador': 'BA',
                'Sao Luis': 'MA', 'Teresina': 'PI', 'Belem': 'PA',
                'Manaus': 'AM', 'Porto Velho': 'RO', 'Macapa': 'AP',
                'Rio Branco': 'AC', 'Palmas': 'TO', 'Boa Vista': 'RR'
            }
            df['state_code'] = df['city'].map(city_to_state)
        
        # Get date from config
        fipezap_date = self.config.get('extraction', {}).get('fipezap', {}).get('date', '2026-07-01')
        
        # Add date
        df['month_date'] = fipezap_date
        
        # Convert to percentage
        df['monthly_variation_pct'] = df['monthly_variation'] * 100
        df['variation_12m_pct'] = df['variation_12m'] * 100
        df['rent_variation'] = df['variation_12m_pct']
        
        # Filter only Brazilian states
        df = self._remove_br_from_dataframe(df)
        
        # Check if we have all 27 states
        estados_presentes = set(df['state_code'].dropna())
        logger.info(f"  States present: {len(estados_presentes)} - {sorted(estados_presentes)}")
        
        # Check for missing states
        estados_faltando = set(self.brazilian_states) - estados_presentes
        if estados_faltando:
            logger.warning(f"  Missing states: {sorted(estados_faltando)}")
            
            # Use medians to fill missing states
            medianas = {
                'total_index': df['total_index'].median(),
                'monthly_variation': df['monthly_variation'].median(),
                'monthly_variation_pct': df['monthly_variation_pct'].median(),
                'variation_12m': df['variation_12m'].median(),
                'variation_12m_pct': df['variation_12m_pct'].median(),
                'avg_price': df['avg_price'].median(),
                'rent_variation': df['rent_variation'].median()
            }
            
            for estado in estados_faltando:
                novo_registro = {
                    'city': estado,
                    'state_code': estado,
                    'month_date': fipezap_date,
                    'total_index': medianas['total_index'],
                    'monthly_variation': medianas['monthly_variation'],
                    'monthly_variation_pct': medianas['monthly_variation_pct'],
                    'variation_12m': medianas['variation_12m'],
                    'variation_12m_pct': medianas['variation_12m_pct'],
                    'avg_price': medianas['avg_price'],
                    'rent_variation': medianas['rent_variation']
                }
                df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
        
        # Ensure we have 27 states
        logger.info(f"✅ FipeZAP final: {len(df)} states")
        
        # Show example
        if not df.empty:
            sample = df.iloc[0]
            logger.info(f"   Example: {sample['state_code']} - Total Index: {sample['total_index']:.2f}")
        
        return df
    
    # ========== MAIN PIPELINE ==========
    
    def run_full_extraction_real(self) -> Dict[str, pd.DataFrame]:
        """Run complete extraction pipeline with REAL data only."""
        logger.info("Starting REAL data extraction pipeline...")
        results = {}
        
        # 1. SCR.data - Validated
        logger.info("  Extracting SCR.data (validated)...")
        results['scr_defaults'] = self.extract_scr_data_real()
        logger.info(f"    ✅ {len(results['scr_defaults'])} records")
        
        # 2. PNAD - Income
        logger.info("  Extracting PNAD income data...")
        results['income'] = self.extract_pnad_income_real()
        logger.info(f"    ✅ {len(results['income'])} states")
        
        # 3. PNAD - GINI
        logger.info("  Extracting PNAD GINI data...")
        results['gini'] = self.extract_pnad_gini_real()
        logger.info(f"    ✅ {len(results['gini'])} states")
        
        # 4. PNAD - Unemployment
        logger.info("  Extracting PNAD unemployment data...")
        results['unemployment'] = self.extract_pnad_unemployment_real()
        logger.info(f"    ✅ {len(results['unemployment'])} states")
        
        # 5. FipeZAP
        logger.info("  Loading FipeZAP data...")
        results['rent'] = self.extract_fipezap_manual()
        logger.info(f"    ✅ {len(results['rent'])} records")
        
        logger.info("✅ Extraction completed!")
        return results
    
    def save_to_csv(self, data: Dict[str, pd.DataFrame], prefix: str = '') -> None:
        """Save extracted data to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for name, df in data.items():
            if not df.empty:
                filename = f"{prefix}_{name}_{timestamp}.csv" if prefix else f"{name}_{timestamp}.csv"
                filepath = self.raw_dir / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(filepath, index=False)
                logger.info(f"Saved: {filepath}")