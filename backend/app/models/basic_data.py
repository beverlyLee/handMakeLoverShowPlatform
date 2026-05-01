from datetime import datetime
from app.database import db
import json


class ActivityType(db.Model):
    __tablename__ = 'activity_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    craft_type_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    sort = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    craft_type = db.relationship('Category', backref='activity_types')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'craft_type_id': self.craft_type_id,
            'craft_type_name': self.craft_type.name if self.craft_type else None,
            'sort': self.sort,
            'status': self.status,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<ActivityType {self.name}>'


class SystemConfig(db.Model):
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(500))
    group = db.Column(db.String(50), default='general')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'group': self.group,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<SystemConfig {self.key}>'
