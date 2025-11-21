"""
Script to add missing columns to optimization_records table.
Run this once to fix the database schema.
"""
import sqlite3
import os
from pathlib import Path

# Get the database path
db_path = Path(__file__).parent / 'dev.sqlite'

if not db_path.exists():
    print(f"Database file not found at {db_path}")
    exit(1)

print(f"Connecting to database at {db_path}")

# Define all columns that should exist in the optimization_records table
# Format: (column_name, column_type, nullable)
required_columns = {
    'id': ('INTEGER', False),
    'timestamp': ('DATETIME', True),
    'total_investment': ('REAL', False),
    'earnings': ('REAL', True),
    'isa_allowance_used': ('REAL', True),
    'savings_goals_json': ('TEXT', False),
    'status': ('VARCHAR(50)', False),
    'total_gross_interest': ('REAL', True),
    'total_net_interest': ('REAL', True),
    'net_effective_aer': ('REAL', True),
    'tax_due': ('REAL', True),
    'tax_band': ('VARCHAR(50)', True),
    'personal_savings_allowance': ('REAL', True),
    'tax_rate': ('REAL', True),
    'tax_free_allowance_remaining': ('REAL', True),
    'investments_json': ('TEXT', True),
    'user_agent': ('VARCHAR(500)', True),
    'ip_address': ('VARCHAR(45)', True),
}

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(optimization_records)")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    print(f"Existing columns: {list(existing_columns.keys())}")
    
    # Check and add missing columns
    added_columns = []
    for column_name, (column_type, nullable) in required_columns.items():
        if column_name not in existing_columns:
            print(f"Adding missing column '{column_name}' ({column_type})...")
            # SQLite doesn't support all column types, so we'll use REAL for numeric and TEXT for text
            sqlite_type = 'REAL' if 'REAL' in column_type or 'INTEGER' in column_type else 'TEXT'
            cursor.execute(f"ALTER TABLE optimization_records ADD COLUMN {column_name} {sqlite_type}")
            added_columns.append(column_name)
        else:
            print(f"Column '{column_name}' already exists.")
    
    if added_columns:
        conn.commit()
        print(f"\nSuccessfully added {len(added_columns)} column(s): {', '.join(added_columns)}")
    else:
        print("\nAll required columns already exist. No changes needed.")
    
    conn.close()
    print("Database update complete.")
    
except Exception as e:
    print(f"Error updating database: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

