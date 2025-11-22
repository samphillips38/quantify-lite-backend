"""
Database migration script that works for both SQLite (dev) and PostgreSQL (production).
This script adds missing columns to existing tables (optimization_records, feedback).
Note: New tables (like email_requests) are automatically created by db.create_all() in app/__init__.py.
Can be run manually or as part of Railway's release phase.
"""
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def get_database_url():
    """Get database URL from environment or config."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # Fallback to local SQLite for development
        from pathlib import Path
        db_path = Path(__file__).parent / 'dev.sqlite'
        database_url = f"sqlite:///{db_path}"
    
    # Heroku/Railway use postgres://, but SQLAlchemy prefers postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url

def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_column_sqlite(engine, table_name, column_name, column_type='REAL'):
    """Add a column to a SQLite table."""
    with engine.connect() as conn:
        try:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()
            return True
        except OperationalError as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                return False  # Column already exists
            raise

def add_column_postgresql(engine, table_name, column_name, column_type='REAL'):
    """Add a column to a PostgreSQL table."""
    with engine.connect() as conn:
        try:
            # For VARCHAR types, use TEXT in PostgreSQL
            pg_type = 'TEXT' if 'VARCHAR' in column_type.upper() else column_type
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {pg_type}"))
            conn.commit()
            return True
        except (OperationalError, ProgrammingError) as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                return False  # Column already exists
            raise

def migrate_database():
    """Run database migration to add missing columns."""
    database_url = get_database_url()
    is_sqlite = database_url.startswith('sqlite')
    
    print(f"Connecting to database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    engine = create_engine(database_url)
    
    # Migrate optimization_records table
    table_name = 'optimization_records'
    columns_to_add = [
        ('tax_rate', 'REAL'),
        ('tax_free_allowance_remaining', 'REAL'),
        ('other_savings_income', 'REAL'),
        ('equivalent_pre_tax_rate', 'REAL'),
        ('session_id', 'VARCHAR(36)'),
        ('batch_id', 'VARCHAR(36)'),
    ]
    
    added_columns = []
    skipped_columns = []
    
    # Check if table exists
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' does not exist. It will be created by db.create_all() on first run.")
    else:
        for column_name, column_type in columns_to_add:
            if column_exists(engine, table_name, column_name):
                print(f"Column '{column_name}' already exists. Skipping.")
                skipped_columns.append(column_name)
            else:
                print(f"Adding column '{column_name}' ({column_type})...")
                try:
                    if is_sqlite:
                        success = add_column_sqlite(engine, table_name, column_name, column_type)
                    else:
                        success = add_column_postgresql(engine, table_name, column_name, column_type)
                    
                    if success:
                        added_columns.append(column_name)
                        print(f"Successfully added column '{column_name}'!")
                    else:
                        skipped_columns.append(column_name)
                        print(f"Column '{column_name}' already exists (detected during add).")
                except Exception as e:
                    print(f"Error adding column '{column_name}': {e}")
                    import traceback
                    traceback.print_exc()
    
    # Migrate feedback table
    feedback_table_name = 'feedback'
    feedback_columns_to_add = [
        ('session_id', 'VARCHAR(36)'),
        ('batch_id', 'VARCHAR(36)'),
    ]
    
    feedback_added_columns = []
    feedback_skipped_columns = []
    
    if feedback_table_name not in inspector.get_table_names():
        print(f"Table '{feedback_table_name}' does not exist. It will be created by db.create_all() on first run.")
    else:
        for column_name, column_type in feedback_columns_to_add:
            if column_exists(engine, feedback_table_name, column_name):
                print(f"Column '{column_name}' already exists in '{feedback_table_name}'. Skipping.")
                feedback_skipped_columns.append(column_name)
            else:
                print(f"Adding column '{column_name}' ({column_type}) to '{feedback_table_name}'...")
                try:
                    if is_sqlite:
                        success = add_column_sqlite(engine, feedback_table_name, column_name, column_type)
                    else:
                        success = add_column_postgresql(engine, feedback_table_name, column_name, column_type)
                    
                    if success:
                        feedback_added_columns.append(column_name)
                        print(f"Successfully added column '{column_name}' to '{feedback_table_name}'!")
                    else:
                        feedback_skipped_columns.append(column_name)
                        print(f"Column '{column_name}' already exists in '{feedback_table_name}' (detected during add).")
                except Exception as e:
                    print(f"Error adding column '{column_name}' to '{feedback_table_name}': {e}")
                    import traceback
                    traceback.print_exc()
    
    if added_columns or feedback_added_columns:
        total_added = len(added_columns) + len(feedback_added_columns)
        print(f"\n✓ Successfully added {total_added} column(s)")
        if added_columns:
            print(f"  - optimization_records: {', '.join(added_columns)}")
        if feedback_added_columns:
            print(f"  - feedback: {', '.join(feedback_added_columns)}")
    if skipped_columns or feedback_skipped_columns:
        total_skipped = len(skipped_columns) + len(feedback_skipped_columns)
        print(f"⊘ Skipped {total_skipped} column(s) (already exist)")
        if skipped_columns:
            print(f"  - optimization_records: {', '.join(skipped_columns)}")
        if feedback_skipped_columns:
            print(f"  - feedback: {', '.join(feedback_skipped_columns)}")
    if not added_columns and not skipped_columns and not feedback_added_columns and not feedback_skipped_columns:
        print("\n✓ All columns already exist. Database is up to date.")
    
    print("Migration complete!")

if __name__ == '__main__':
    migrate_database()

