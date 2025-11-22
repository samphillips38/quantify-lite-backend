"""
Script to run database migrations.
This can be used in Railway's release phase or run manually.
"""
import os
import sys
from app import create_app
from flask_migrate import upgrade

def run_migrations():
    """Run database migrations."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Running database migrations...")
            upgrade()
            print("Migrations completed successfully!")
        except Exception as e:
            print(f"Error running migrations: {e}")
            # Don't fail if migrations can't run - the app will use create_all as fallback
            import traceback
            traceback.print_exc()
            sys.exit(0)  # Exit with 0 so Railway doesn't fail the deployment

if __name__ == '__main__':
    run_migrations()

