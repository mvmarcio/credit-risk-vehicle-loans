-- Schema for credit risk vehicle loans database

-- States dimension
CREATE TABLE IF NOT EXISTS dim_state (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code CHAR(2) UNIQUE NOT NULL,
    state_name VARCHAR(100),
    region VARCHAR(50),
    population INTEGER
);

-- Insert all states
INSERT OR IGNORE INTO dim_state (state_code, state_name) VALUES
('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins');

-- SCR monthly data
CREATE TABLE IF NOT EXISTS scr_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code CHAR(2),
    month_date DATE NOT NULL,
    total_balance DECIMAL(15,2),
    default_rate_90 DECIMAL(5,2),
    default_rate_15_90 DECIMAL(5,2),
    default_rate_90_percent DECIMAL(5,2),
    FOREIGN KEY (state_code) REFERENCES dim_state(state_code),
    UNIQUE(state_code, month_date)
);

-- Macroeconomic indicators
CREATE TABLE macro_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code CHAR(2),
    month_date DATE,
    median_income DECIMAL(10,2),
    gini_index DECIMAL(4,3),
    unemployment_rate DECIMAL(4,2),
    rent_proxy DECIMAL(6,2),
    ipca_variation DECIMAL(5,2),
    igpm_variation DECIMAL(5,2),
    affordability_index DECIMAL(5,2),
    quarter VARCHAR(10),
    FOREIGN KEY (state_code) REFERENCES dim_state(state_code),
    UNIQUE(state_code, month_date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scr_state_date ON scr_monthly(state_code, month_date);
CREATE INDEX IF NOT EXISTS idx_scr_default ON scr_monthly(default_rate_90);
CREATE INDEX IF NOT EXISTS idx_macro_state_date ON macro_indicators(state_code, month_date);
CREATE INDEX IF NOT EXISTS idx_macro_affordability ON macro_indicators(affordability_index);