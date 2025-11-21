import os
import sys
from flask import Flask
from config import Config
from flask_cors import CORS
from flask_migrate import Migrate
from .database_models import db

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)

    # Import and register blueprints here
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # Try to run database migration script first (for adding missing columns)
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrate_database.py')],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"Migration script output: {result.stdout}")
                print(f"Migration script errors: {result.stderr}")
        except Exception as e:
            print(f"Could not run migration script: {e}")
        
        # Always run create_all as a fallback (creates tables if they don't exist)
        db.create_all()

    return app 