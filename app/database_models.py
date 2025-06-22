from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class OptimizationRecord(db.Model):
    __tablename__ = 'optimization_records'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Input data
    total_investment = db.Column(db.Float, nullable=False)
    earnings = db.Column(db.Float, nullable=True)
    isa_allowance_used = db.Column(db.Float, default=0.0)
    savings_goals_json = db.Column(db.Text, nullable=False)  # Storing as a JSON string
    
    # Results data
    status = db.Column(db.String(50), nullable=False)
    total_gross_interest = db.Column(db.Float, nullable=True)
    total_net_interest = db.Column(db.Float, nullable=True)
    net_effective_aer = db.Column(db.Float, nullable=True)
    tax_due = db.Column(db.Float, nullable=True)
    tax_band = db.Column(db.String(50), nullable=True)
    personal_savings_allowance = db.Column(db.Float, nullable=True)
    investments_json = db.Column(db.Text, nullable=True) # Storing as a JSON string
    
    # Metadata
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Feedback data
    recommend_rating = db.Column(db.Integer, nullable=True)
    satisfaction_rating = db.Column(db.Integer, nullable=True)
    feedback_text = db.Column(db.Text, nullable=True)
    
    # Metadata
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True) 