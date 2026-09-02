"""SQLite database operations."""

import sqlite3
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/credit_risk.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.cursor = None
    
    def connect(self) -> None:
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def reset_database(self) -> None:
        logger.info("Resetting database...")
        self.connect()
        try:
            self.cursor.execute("DROP TABLE IF EXISTS macro_indicators")
            self.cursor.execute("DROP TABLE IF EXISTS scr_monthly")
            self.cursor.execute("DROP TABLE IF EXISTS dim_state")
            self.connection.commit()
            self._create_tables()
            self.connection.commit()
            logger.info("Database reset completed")
        except Exception as e:
            logger.error(f"Failed to reset: {e}")
            raise
    
    def _create_tables(self) -> None:
        # States
        self.cursor.execute("""
            CREATE TABLE dim_state (
                state_code CHAR(2) PRIMARY KEY,
                state_name VARCHAR(100)
            )
        """)
        
        states = [
            ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
            ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
            ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
            ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
            ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
            ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
            ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
        ]
        
        for code, name in states:
            self.cursor.execute(
                "INSERT OR IGNORE INTO dim_state (state_code, state_name) VALUES (?, ?)",
                (code, name)
            )
        
        # SCR
        self.cursor.execute("""
            CREATE TABLE scr_monthly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_code CHAR(2),
                month_date DATE NOT NULL,
                default_rate_90 DECIMAL(5,2),
                FOREIGN KEY (state_code) REFERENCES dim_state(state_code),
                UNIQUE(state_code, month_date)
            )
        """)
        
        # Macro
        self.cursor.execute("""
            CREATE TABLE macro_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_code CHAR(2),
                month_date DATE,
                median_income DECIMAL(10,2),
                gini_index DECIMAL(4,3),
                unemployment_rate DECIMAL(4,2),
                total_index DECIMAL(10,2),
                monthly_variation_pct DECIMAL(6,2),
                variation_12m_pct DECIMAL(6,2),
                avg_price DECIMAL(10,2),
                rent_variation DECIMAL(6,2),
                quarter VARCHAR(10),
                FOREIGN KEY (state_code) REFERENCES dim_state(state_code),
                UNIQUE(state_code, month_date)
            )
        """)
        
        self.cursor.execute("CREATE INDEX idx_scr_state_date ON scr_monthly(state_code, month_date)")
        self.cursor.execute("CREATE INDEX idx_macro_state_date ON macro_indicators(state_code, month_date)")
        logger.info("Tables created")
    
    def insert_data(self, table: str, df: pd.DataFrame) -> None:
        if df.empty:
            raise ValueError(f"Cannot insert empty DataFrame into {table}")
        
        self.connect()
        try:
            self.cursor.execute(f"PRAGMA table_info({table})")
            existing = [row[1] for row in self.cursor.fetchall()]
            
            valid = [col for col in df.columns if col in existing]
            if not valid:
                raise ValueError(f"No valid columns for {table}")
            
            df_filtered = df[valid]
            
            count = self.get_table_count(table)
            if count == 0:
                df_filtered.to_sql(table, self.connection, if_exists='replace', index=False)
            else:
                df_filtered.to_sql(table, self.connection, if_exists='append', index=False)
            
            self.connection.commit()
            logger.info(f"Inserted {len(df_filtered)} rows into {table}")
        except Exception as e:
            logger.error(f"Failed to insert: {e}")
            raise
    
    def query_to_dataframe(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        self.connect()
        try:
            return pd.read_sql_query(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def get_columns(self, table: str) -> List[str]:
        self.connect()
        try:
            self.cursor.execute(f"PRAGMA table_info({table})")
            return [row[1] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_table_count(self, table: str) -> int:
        self.connect()
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            return self.cursor.fetchone()[0]
        except:
            return 0
    
    def debug_table_contents(self, table: str) -> None:
        """Debug: Show table contents."""
        try:
            query = f"SELECT DISTINCT state_code, COUNT(*) as count FROM {table} GROUP BY state_code ORDER BY state_code"
            df = self.query_to_dataframe(query)
            logger.info(f"\n📊 Table {table} contents:")
            for _, row in df.iterrows():
                logger.info(f"   {row['state_code']}: {row['count']} records")
            logger.info(f"   Total: {len(df)} distinct states")
        except Exception as e:
            logger.error(f"Debug error: {e}")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()