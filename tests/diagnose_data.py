"""
Simple diagnostic script.
"""

import sqlite3
import pandas as pd
from pathlib import Path

def diagnose():
    print("=" * 80)
    print("DATA DIAGNOSTIC - SIMPLE")
    print("=" * 80)
    
    db_path = Path("data/credit_risk.db")
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Check SCR
        scr = pd.read_sql_query("SELECT DISTINCT state_code, COUNT(*) as count FROM scr_monthly GROUP BY state_code", conn)
        print(f"\nSCR states: {len(scr)}")
        print(scr)
        
        # Check Macro
        macro = pd.read_sql_query("SELECT DISTINCT state_code, COUNT(*) as count FROM macro_indicators GROUP BY state_code", conn)
        print(f"\nMacro states: {len(macro)}")
        print(macro)
        
        # Check common states
        scr_set = set(scr['state_code'].tolist())
        macro_set = set(macro['state_code'].tolist())
        common = scr_set & macro_set
        
        print(f"\nCommon states: {len(common)}")
        print(f"Common: {sorted(common)}")
        
        # Check rent_variation
        rent = pd.read_sql_query("SELECT state_code, rent_variation FROM macro_indicators WHERE rent_variation IS NOT NULL", conn)
        print(f"\nFipeZAP data: {len(rent)} records")
        if not rent.empty:
            print(rent)
        else:
            print("❌ No FipeZAP data found!")
        
        # Check correlations file
        reports_dir = Path("reports")
        if reports_dir.exists():
            files = list(reports_dir.glob("*.csv"))
            print(f"\nReports: {len(files)} files")
            for f in files:
                size = f.stat().st_size
                print(f"  - {f.name} ({size} bytes)")
            
            if (reports_dir / "correlations.csv").exists():
                corr = pd.read_csv(reports_dir / "correlations.csv")
                print(f"\ncorrelations.csv:")
                print(corr)
            else:
                print("\n❌ correlations.csv NOT found!")
        else:
            print("\n❌ reports/ directory not found!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose()