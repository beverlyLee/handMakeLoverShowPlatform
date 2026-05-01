from datetime import datetime
from app.database import db
import json


CRAFT_TYPES = ['编织', '陶艺', '刺绣', '皮具', '木艺', '纸艺', '花艺', '烘焙', '其他']
ACTIVITY_TYPES = ['线下体验', '线上课程', '讲座', '工作坊', '手工市集', '其他']


class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profiles.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    craft_type = db.Column(db.String(50), default='其他')
    activity_type = db.Column(db.String(50), default='其他')
    
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    registration_start_time = db.Column(db.DateTime)
    registration_deadline = db.Column(db.DateTime)
    
    location = db.Column(db.String(200))
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    
    price = db.Column(db.Float, default=0.0)
    original_price = db.Column(db.Float, default=0.0)
    
    max_participants = db.Column(db.Integer, default=999)
    current_participants = db.Column(db.Integer, default=0)
    
    _images = db.Column('images', db.Text)
    cover_image = db.Column(db.String(500))
    
    _tags = db.Column('tags', db.Text)
    
    status = db.Column(db.String(20), default='active')
    
    view_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)
    registration_count = db.Column(db.Integer, default=0)
    
    verify_status = db.Column(db.String(20), default='pending')
    verify_time = db.Column(db.DateTime)
    verify_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reject_reason = db.Column(db.String(500))
    
    is_official = db.Column(db.Boolean, default=False)
    process = db.Column(db.Text)
    registration_method = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher_profile = db.relationship('TeacherProfile', backref='activities', foreign_keys=[teacher_id])
    registrations = db.relationship('ActivityRegistration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def images(self):
        if self._images:
            try:
                return json.loads(self._images)
            except:
                return []
        return []

    @images.setter
    def images(self, value):
        if isinstance(value, list):
            self._images = json.dumps(value, ensure_ascii=False)
        else:
            self._images = value

    @property
    def tags(self):
        if self._tags:
            try:
                return json.loads(self._tags)
            except:
                return []
        return []

    @tags.setter
    def tags(self, value):
        if isinstance(value, list):
            self._tags = json.dumps(value, ensure_ascii=False)
        else:
            self._tags = value

    @property
    def is_registration_open(self):
        if self.status != 'active':
            return False
        if self.registration_start_time and datetime.utcnow() < self.registration_start_time:
            return False
        if self.registration_deadline and datetime.utcnow() > self.registration_deadline:
            return False
        if self.current_participants >= self.max_participants:
            return False
        return True

    @property
    def computed_status(self):
        now = datetime.utcnow()
        if self.verify_status != 'approved':
            return 'pending_review'
        if not self.start_time or not self.end_time:
            return 'not_started'
        if now < self.start_time:
            return 'not_started'
        elif self.start_time <= now <= self.end_time:
            return 'in_progress'
        else:
            return 'ended'

    def to_dict(self, include_teacher=False):
        result = {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_user_id': self.teacher_profile.user_id if self.teacher_profile else None,
            'title': self.title,
            'description': self.description,
            'craft_type': self.craft_type,
            'activity_type': self.activity_type,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'registration_start_time': self.registration_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.registration_start_time else None,
            'registration_deadline': self.registration_deadline.strftime('%Y-%m-%d %H:%M:%S') if self.registration_deadline else None,
            'location': self.location,
            'address': self.address,
            'city': self.city,
            'price': self.price,
            'original_price': self.original_price,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'images': self.images,
            'cover_image': self.cover_image,
            'tags': self.tags,
            'status': self.status,
            'view_count': self.view_count,
            'favorite_count': self.favorite_count,
            'registration_count': self.registration_count,
            'is_registration_open': self.is_registration_open,
            'verify_status': self.verify_status,
            'verify_time': self.verify_time.strftime('%Y-%m-%d %H:%M:%S') if self.verify_time else None,
            'verify_admin_id': self.verify_admin_id,
            'reject_reason': self.reject_reason,
            'is_official': self.is_official,
            'process': self.process,
            'registration_method': self.registration_method,
            'computed_status': self.computed_status,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_teacher and self.teacher_profile:
            result['teacher'] = {
                'id': self.teacher_profile.id,
                'teacher_id': self.teacher_profile.teacher_id,
                'user_id': self.teacher_profile.user_id,
                'real_name': self.teacher_profile.real_name,
                'avatar': self.teacher_profile.user.avatar if self.teacher_profile.user else None,
                'rating': self.teacher_profile.rating,
                'follower_count': self.teacher_profile.follower_count
            }
        
        return result

    def __repr__(self):
        return f'<Activity {self.title}>'


class ActivityRegistration(db.Model):
    __tablename__ = 'activity_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    remark = db.Column(db.String(500))
    
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='activity_registrations')

    def to_dict(self):
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'remark': self.remark,
            'status': self.status,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'contact_name': self.name,
            'contact_phone': self.phone,
            'special_requests': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'number_of_people': 1
        }

    def __repr__(self):
        return f'<ActivityRegistration {self.id}>'
