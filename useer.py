from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(100), nullable=False)
    military_id = db.Column(db.String(50), unique=True, nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='soldier')  # admin, commander, officer, soldier
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'rank': self.rank,
            'unit': self.unit,
            'military_id': self.military_id,
            'join_date': self.join_date.strftime('%Y-%m-%d'),
            'role': self.role,
            'status': self.status
        }
