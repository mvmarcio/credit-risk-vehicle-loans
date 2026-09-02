-- queries/analysis_queries.sql

-- 1. State-level median default rates (90 days)
WITH state_medians AS (
    SELECT 
        state_code,
        AVG(default_rate_90) as avg_default_90,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY default_rate_90) 
            OVER (PARTITION BY state_code) as median_default_90
    FROM scr_monthly
    WHERE month_date >= '2024-01-01'
)
SELECT DISTINCT
    state_code,
    ROUND(median_default_90, 4) as median_default_90_pct,
    ROUND(avg_default_90, 4) as avg_default_90_pct
FROM state_medians
ORDER BY median_default_90_pct DESC;

-- 2. Correlation matrix (Spearman)
SELECT 
    'Income' as indicator,
    ROUND(CORR(m.median_income, s.default_rate_90), 4) as correlation_default_90
FROM macro_indicators m
JOIN scr_monthly s ON m.state_code = s.state_code AND m.month_date = s.month_date
UNION ALL
SELECT 
    'GINI',
    ROUND(CORR(m.gini_index, s.default_rate_90), 4)
FROM macro_indicators m
JOIN scr_monthly s ON m.state_code = s.state_code AND m.month_date = s.month_date
UNION ALL
SELECT 
    'Unemployment',
    ROUND(CORR(m.unemployment_rate, s.default_rate_90), 4)
FROM macro_indicators m
JOIN scr_monthly s ON m.state_code = s.state_code AND m.month_date = s.month_date
UNION ALL
SELECT 
    'Median Rent',
    ROUND(CORR(m.median_rent, s.default_rate_90), 4)
FROM macro_indicators m
JOIN scr_monthly s ON m.state_code = s.state_code AND m.month_date = s.month_date
UNION ALL
SELECT 
    'Affordability Index',
    ROUND(CORR(m.affordability_index, s.default_rate_90), 4)
FROM macro_indicators m
JOIN scr_monthly s ON m.state_code = s.state_code AND m.month_date = s.month_date;

-- 3. Monthly ranking - most overdue states
WITH monthly_ranks AS (
    SELECT 
        state_code,
        month_date,
        default_rate_90,
        RANK() OVER (PARTITION BY month_date ORDER BY default_rate_90 DESC) as rank_90
    FROM scr_monthly
    WHERE month_date >= '2024-01-01'
)
SELECT 
    strftime('%Y-%m', month_date) as month,
    state_code,
    ROUND(default_rate_90 * 100, 2) as default_pct,
    rank_90
FROM monthly_ranks
WHERE rank_90 <= 5
ORDER BY month_date DESC, rank_90;

-- 4. Affordability impact analysis
SELECT 
    CASE 
        WHEN affordability_index < 3 THEN 'Severe Burden'
        WHEN affordability_index < 5 THEN 'Moderate Burden'
        WHEN affordability_index < 7 THEN 'Mild Burden'
        ELSE 'Affordable'
    END as affordability_category,
    COUNT(*) as observations,
    ROUND(AVG(default_rate_90) * 100, 2) as avg_default_pct,
    ROUND(MEDIAN(default_rate_90) * 100, 2) as median_default_pct
FROM scr_monthly s
JOIN macro_indicators m ON s.state_code = m.state_code AND s.month_date = m.month_date
WHERE s.month_date >= '2024-01-01'
GROUP BY affordability_category
ORDER BY avg_default_pct DESC;