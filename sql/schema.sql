PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS bacen_scr_state (
    reference_month DATE NOT NULL,
    state_code CHAR(2) NOT NULL,
    outstanding_balance DECIMAL(15, 2) NOT NULL,
    over_30_balance DECIMAL(15, 2) NOT NULL,
    over_60_balance DECIMAL(15, 2) NOT NULL,
    over_90_balance DECIMAL(15, 2) NOT NULL,
    PRIMARY KEY (reference_month, state_code)
);

CREATE TABLE IF NOT EXISTS macro_indicators_state (
    reference_month DATE NOT NULL,
    state_code CHAR(2) NOT NULL,
    median_income DECIMAL(10, 2),
    median_rent DECIMAL(10, 2),
    unemployment_rate DECIMAL(5, 4),
    gini_index DECIMAL(5, 4),
    igpm_variation DECIMAL(6, 4),
    PRIMARY KEY (reference_month, state_code)
);

CREATE TABLE IF NOT EXISTS analytical_master (
    reference_month DATE NOT NULL,
    state_code CHAR(2) NOT NULL,
    over_30_pct DECIMAL(6, 4),
    over_60_pct DECIMAL(6, 4),
    over_90_pct DECIMAL(6, 4),
    income_to_rent_ratio DECIMAL(8, 4),
    unemployment_rate DECIMAL(5, 4),
    gini_index DECIMAL(5, 4),
    igpm_variation DECIMAL(6, 4),
    indebtedness_rank INT,
    PRIMARY KEY (reference_month, state_code)
);
