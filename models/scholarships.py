from . import db
from datetime import datetime

class Scholarship(db.Model):
    __tablename__ = 'scholarship'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quota = db.Column(db.Integer, default=0)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='open') # open, checking, interview, announce
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Relationships
    criteria = db.relationship('Criterion', backref='scholarship', lazy=True)
    applications = db.relationship('Application', backref='scholarship', lazy=True)

class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.String, primary_key=True) # เช่น APP2026-001
    student_id = db.Column(db.String(20), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'), nullable=False)
    status = db.Column(db.String(20), default='รอตรวจสอบ')
    total_score = db.Column(db.Integer, default=0)
    is_scored = db.Column(db.Boolean, default=False)

class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'))
    name = db.Column(db.String(100))
    max_score = db.Column(db.Integer)