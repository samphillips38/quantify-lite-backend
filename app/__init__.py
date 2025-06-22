import os
from flask import Flask
from config import Config
from flask_cors import CORS
from .database_models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app)

    # Initialize database
    db.init_app(app)

    # Import and register blueprints here
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app 