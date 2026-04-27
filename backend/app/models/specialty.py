from datetime import datetime
from app.database import db
import json

class Specialty(db.Model):
    __tablename__ = 'specialties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    icon = db.Column(db.String(100))
    category = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'category': self.category,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }
    
    @staticmethod
    def init_default_specialties():
        specialties_data = [
            {'name': '棒针编织', 'icon': '🧶', 'category': '编织', 'sort_order': 1},
            {'name': '钩针编织', 'icon': '🧶', 'category': '编织', 'sort_order': 2},
            {'name': '编织', 'icon': '🧶', 'category': '编织', 'sort_order': 3},
            {'name': '陶艺', 'icon': '🏺', 'category': '陶艺', 'sort_order': 10},
            {'name': '拉坯', 'icon': '🏺', 'category': '陶艺', 'sort_order': 11},
            {'name': '釉上彩', 'icon': '🎨', 'category': '陶艺', 'sort_order': 12},
            {'name': '皮革工艺', 'icon': '👜', 'category': '皮革', 'sort_order': 20},
            {'name': '刺绣', 'icon': '🧵', 'category': '布艺', 'sort_order': 30},
            {'name': '纸艺', 'icon': '📄', 'category': '纸艺', 'sort_order': 40},
            {'name': '珠串', 'icon': '💎', 'category': '珠串', 'sort_order': 50},
            {'name': '木艺', 'icon': '🪵', 'category': '木艺', 'sort_order': 60},
            {'name': '布艺', 'icon': '🧵', 'category': '布艺', 'sort_order': 31},
            {'name': '手工皂', 'icon': '🧼', 'category': '手工', 'sort_order': 70},
            {'name': '蜡烛', 'icon': '🕯️', 'category': '手工', 'sort_order': 71},
            {'name': '押花', 'icon': '🌸', 'category': '手工', 'sort_order': 72},
            {'name': '热缩片', 'icon': '🔬', 'category': '手工', 'sort_order': 73},
            {'name': '滴胶', 'icon': '💧', 'category': '手工', 'sort_order': 74},
            {'name': '黏土', 'icon': '🟠', 'category': '手工', 'sort_order': 75}
        ]
        
        for data in specialties_data:
            existing = Specialty.query.filter_by(name=data['name']).first()
            if not existing:
                specialty = Specialty(**data)
                db.session.add(specialty)
        
        db.session.commit()
        print('擅长领域数据初始化完成')