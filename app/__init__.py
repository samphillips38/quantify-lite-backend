from flask import Flask
from config import Config
from flask_cors import CORS
from .database_models import db
from flask_migrate import Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize database
    db.init_app(app)
    from . import database_models
    migrate = Migrate(app, db)

    # Import and register blueprints here
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app 