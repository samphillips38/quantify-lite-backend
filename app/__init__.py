from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Import and register blueprints here
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app 