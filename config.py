import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # Add other configuration variables here, like API keys for financial data
    # e.g. SAVINGS_API_KEY = os.environ.get('SAVINGS_API_KEY') 