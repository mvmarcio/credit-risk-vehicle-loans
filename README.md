# Credit Risk Vehicle Loans Analysis

## Brazilian Auto Loan Delinquency & Macroeconomic Risk Analysis

## Executive Summary
This project analyzes state-level auto loan delinquency in Brazil (*Financiamento de Veículos*) across multiple overdue thresholds (**Over 30**, **Over 60**, and **Over 90** days) alongside macroeconomic drivers. By integrating data from Banco Central do Brasil (BACEN) and IBGE, this pipeline evaluates how income pressure, rental cost burden, unemployment, inequality, and inflation impact retail credit performance across Brazilian states.

## Key Metrics & Analysis
1. **Delinquency Rates:** Overdue balance ratios ($Over30 / Total Outstanding$, $Over60 / Total Outstanding$, $Over90 / Total Outstanding$).
2. **Rent-to-Income Purchasing Power Index:** 
   $$\text{Rent Index} = \frac{\text{Median Monthly Income}}{\text{Median Rent Value}}$$
3. **Macroeconomic Indicators:** Gini Coefficient (Inequality), Unemployment Rate (PNAD Continuous), and IGP-M / IPCA Housing component.
4. **Monthly Stratified Ranking:** Cross-sectional ranking of most indebted/delinquent states per month.

## Official Data Sources
* **BACEN (Banco Central do Brasil) - SCR (Sistema de Informações de Crédito):** Outstanding balance and non-performing loan (NPL) buckets per Brazilian state (UF).
* **IBGE - PNAD Contínua (via SIDRA API):** State-level median monthly income, unemployment rate, and Gini coefficient.
* **FIPE / IBGE IPCA:** State-level median rent metrics and housing inflation components.
* **FGV (Fundação Getulio Vargas):** IGP-M index monthly series.

