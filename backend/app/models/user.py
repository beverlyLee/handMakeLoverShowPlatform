from datetime import datetime
from app.database import db
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80))
    avatar = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    gender = db.Column(db.Integer, default=0)
    password_hash = db.Column(db.String(256))
    bio = db.Column(db.String(500))
    
    _roles = db.Column('roles', db.Text, default='["customer"]')
    current_role = db.Column(db.String(20), default='customer')
    
    openid = db.Column(db.String(100), unique=True)
    unionid = db.Column(db.String(100))
    session_key = db.Column(db.String(100))
    
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders_as_customer = db.relationship('Order', foreign_keys='Order.user_id', backref='customer', lazy='dynamic')
    orders_as_teacher = db.relationship('Order', foreign_keys='Order.teacher_id', backref='teacher', lazy='dynamic')

    @property
    def roles(self):
        if self._roles:
            try:
                return json.loads(self._roles)
            except:
                return ['customer']
        return ['customer']

    @roles.setter
    def roles(self, value):
        if isinstance(value, list):
            self._roles = json.dumps(value, ensure_ascii=False)
        else:
            self._roles = value

    @property
    def is_teacher(self):
        return 'teacher' in self.roles

    @property
    def is_customer(self):
        return 'customer' in self.roles

    @property
    def has_multiple_roles(self):
        return len(self.roles) > 1

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone,
            'email': self.email,
            'gender': self.gender,
            'role': self.current_role,
            'roles': self.roles,
            'current_role': self.current_role,
            'bio': self.bio,
            'is_teacher': self.is_teacher,
            'is_customer': self.is_customer,
            'has_multiple_roles': self.has_multiple_roles,
            'teacher_info': self.teacher_profile.to_dict() if self.teacher_profile else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(50))
    city = db.Column(db.String(50))
    district = db.Column(db.String(50))
    detail = db.Column(db.String(200), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'detail': self.detail,
            'is_default': self.is_default,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Address {self.id}>'


class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    teacher_id = db.Column(db.String(50), unique=True, nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    
    _specialties = db.Column('specialties', db.Text)
    intro = db.Column(db.String(1000))
    experience_years = db.Column(db.Integer, default=0)
    
    studio_name = db.Column(db.String(100))
    studio_address = db.Column(db.String(200))
    _studio_images = db.Column('studio_images', db.Text)
    _work_photos = db.Column('work_photos', db.Text)
    
    _certifications = db.Column('certifications', db.Text)
    bio = db.Column(db.String(1000))
    
    rating = db.Column(db.Float, default=5.0)
    student_count = db.Column(db.Integer, default=0)
    product_count = db.Column(db.Integer, default=0)
    order_count = db.Column(db.Integer, default=0)
    follower_count = db.Column(db.Integer, default=0)
    
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def specialties(self):
        if self._specialties:
            try:
                return json.loads(self._specialties)
            except:
                return []
        return []

    @specialties.setter
    def specialties(self, value):
        if isinstance(value, list):
            self._specialties = json.dumps(value, ensure_ascii=False)
        else:
            self._specialties = value

    @property
    def studio_images(self):
        if self._studio_images:
            try:
                return json.loads(self._studio_images)
            except:
                return []
        return []

    @studio_images.setter
    def studio_images(self, value):
        if isinstance(value, list):
            self._studio_images = json.dumps(value, ensure_ascii=False)
        else:
            self._studio_images = value

    @property
    def work_photos(self):
        if self._work_photos:
            try:
                return json.loads(self._work_photos)
            except:
                return []
        return []

    @work_photos.setter
    def work_photos(self, value):
        if isinstance(value, list):
            self._work_photos = json.dumps(value, ensure_ascii=False)
        else:
            self._work_photos = value

    @property
    def certifications(self):
        if self._certifications:
            try:
                return json.loads(self._certifications)
            except:
                return []
        return []

    @certifications.setter
    def certifications(self, value):
        if isinstance(value, list):
            self._certifications = json.dumps(value, ensure_ascii=False)
        else:
            self._certifications = value

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'teacher_id': self.teacher_id,
            'real_name': self.real_name,
            'id_card': self.id_card,
            'phone': self.phone,
            'specialties': self.specialties,
            'intro': self.intro,
            'experience_years': self.experience_years,
            'studio_name': self.studio_name,
            'studio_address': self.studio_address,
            'studio_images': self.studio_images,
            'work_photos': self.work_photos,
            'certifications': self.certifications,
            'bio': self.bio,
            'rating': self.rating,
            'student_count': self.student_count,
            'product_count': self.product_count,
            'order_count': self.order_count,
            'follower_count': self.follower_count,
            'verified': self.is_verified,
            'is_verified': self.is_verified,
            'verify_time': self.verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.verified_at else None,
            'verified_at': self.verified_at.strftime('%Y-%m-%d %H:%M:%S') if self.verified_at else None,
            'apply_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<TeacherProfile {self.teacher_id}>'
