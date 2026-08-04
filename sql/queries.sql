-- 1. Monthly Stratified Comparison: Most Indebted States (Ranked by Over 90)
SELECT 
    reference_month,
    state_code,
    ROUND(over_90_pct * 100, 2) AS over_90_delinquency_pct,
    ROUND(income_to_rent_ratio, 2) AS income_rent_index,
    indebtedness_rank
FROM analytical_master
WHERE reference_month = (SELECT MAX(reference_month) FROM analytical_master)
ORDER BY indebtedness_rank ASC;

-- 2. State-level Median Delinquency vs Income-to-Rent Ratio
SELECT 
    state_code,
    ROUND(AVG(over_30_pct) * 100, 2) AS median_over_30_pct,
    ROUND(AVG(over_60_pct) * 100, 2) AS median_over_60_pct,
    ROUND(AVG(over_90_pct) * 100, 2) AS median_over_90_pct,
    ROUND(AVG(income_to_rent_ratio), 2) AS avg_income_to_rent_index,
    ROUND(AVG(unemployment_rate) * 100, 2) AS avg_unemployment_pct
FROM analytical_master
GROUP BY state_code
ORDER BY median_over_90_pct DESC;