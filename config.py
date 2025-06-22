import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # Heroku/Railway use postgres://, but SQLAlchemy prefers postgresql://
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Fallback to a local SQLite database for local development
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev.sqlite')}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add other configuration variables here, like API keys for financial data
    # e.g. SAVINGS_API_KEY = os.environ.get('SAVINGS_API_KEY') 