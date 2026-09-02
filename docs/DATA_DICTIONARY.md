# Data Dictionary - Credit Risk Vehicle Loans Analysis

## Database Schema

### 1. dim_state
Dimension table for Brazilian states.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| state_code | CHAR(2) | Primary key - State abbreviation | 'SP' |
| state_name | VARCHAR(100) | Full state name | 'São Paulo' |

### 2. scr_monthly
Monthly SCR data for vehicle loans.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Primary key (auto-increment) | 1 |
| state_code | CHAR(2) | Foreign key to dim_state | 'SP' |
| month_date | DATE | Reporting month | '2026-06-30' |
| default_rate_90 | DECIMAL(5,2) | Default rate for 90+ days (%) | 6.07 |

### 3. macro_indicators
Macroeconomic indicators by state.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Primary key (auto-increment) | 1 |
| state_code | CHAR(2) | Foreign key to dim_state | 'SP' |
| month_date | DATE | Reporting month | '2025-01-01' |
| median_income | DECIMAL(10,2) | Median monthly income (R$) | 2800.00 |
| gini_index | DECIMAL(4,3) | Gini coefficient | 0.4927 |
| unemployment_rate | DECIMAL(4,2) | Unemployment rate (%) | 5.99 |
| total_index | DECIMAL(10,2) | FipeZAP total index | 100.00 |
| monthly_variation_pct | DECIMAL(6,2) | Monthly variation (%) | 0.85 |
| variation_12m_pct | DECIMAL(6,2) | 12-month variation (%) | 8.20 |
| avg_price | DECIMAL(10,2) | Average price (R$/m²) | 8500.00 |
| rent_variation | DECIMAL(6,2) | Rent variation (12M %) | 8.20 |
| quarter | VARCHAR(10) | Quarter | '2025Q1' |

## Analysis Output Files

### 1. state_medians.csv
State-level default medians.

| Column | Description |
|--------|-------------|
| state_code | State abbreviation |
| observations | Number of months analyzed |
| avg_default_pct | Average default rate (%) |
| median_default_pct | Median default rate (%) |
| min_default_pct | Minimum default rate (%) |
| max_default_pct | Maximum default rate (%) |
| std_default_pct | Standard deviation |

### 2. correlations.csv
Correlation analysis results.

| Column | Description |
|--------|-------------|
| indicator | Indicator name |
| correlation | Pearson correlation coefficient |
| p_value | Statistical significance |
| strength | Correlation strength (Strong/Moderate/Weak/Very Weak) |
| significance | Significance level (***/**/*/Not Significant) |
| observations | Number of states analyzed |

### 3. monthly_rankings.csv
Monthly state rankings.

| Column | Description |
|--------|-------------|
| state_code | State abbreviation |
| months_ranked | Number of months in analysis |
| avg_rank | Average rank |
| avg_default_pct | Average default rate |
| times_in_top_3 | Count of months in top 3 |

### 4. trend_analysis.csv
Trend analysis results.

| Column | Description |
|--------|-------------|
| state_code | State abbreviation |
| avg_default | Average default rate |
| max_default | Maximum default rate |
| min_default | Minimum default rate |
| avg_pct_change | Average percentage change |
| trend_direction | Increasing/Stable/Decreasing |

### 5. outliers.csv
Outlier detection results.

| Column | Description |
|--------|-------------|
| state_code | State abbreviation |
| default_rate_90 | Default rate value |
| z_score | Z-score |
| is_outlier | Boolean flag |