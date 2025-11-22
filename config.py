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

    # Email configuration - Using Resend API (Railway's recommended approach, works on all plans)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL') or os.environ.get('MAIL_USERNAME') or "samphillips38@gmail.com"
    
    # Legacy SMTP configuration (for local development fallback)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or "samphillips38@gmail.com"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or "gjkw qqyj ywwc xdcx"
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    MAIL_TIMEOUT = int(os.environ.get('MAIL_TIMEOUT') or 30)  # Timeout in seconds for SMTP operations
    
    # Add other configuration variables here, like API keys for financial data
    # e.g. SAVINGS_API_KEY = os.environ.get('SAVINGS_API_KEY') 