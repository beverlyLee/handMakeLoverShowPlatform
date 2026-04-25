from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    openid = db.Column(db.String(100), unique=True, nullable=True, index=True)
    unionid = db.Column(db.String(100), unique=True, nullable=True)
    session_key = db.Column(db.String(100), nullable=True)
    
    nickname = db.Column(db.String(50), nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='customer')
    bio = db.Column(db.Text, nullable=True)
    
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone,
            'email': self.email,
            'gender': self.gender,
            'role': self.role,
            'bio': self.bio,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }
    
    def to_public_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone,
            'email': self.email,
            'gender': self.gender,
            'role': self.role,
            'bio': self.bio,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }
