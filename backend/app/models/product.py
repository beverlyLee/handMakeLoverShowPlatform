from datetime import datetime
from app.database import db
import json

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    name_en = db.Column(db.String(100))
    icon = db.Column(db.String(500))
    description = db.Column(db.String(500))
    sort = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    product_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'icon': self.icon,
            'description': self.description,
            'sort': self.sort,
            'status': self.status,
            'product_count': self.product_count,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profiles.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    price = db.Column(db.Float, default=0.0)
    original_price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)
    
    _images = db.Column('images', db.Text)
    cover_image = db.Column(db.String(500))
    
    status = db.Column(db.String(20), default='active')
    sales_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=5.0)
    
    _tags = db.Column('tags', db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher_profile = db.relationship('TeacherProfile', backref='products', foreign_keys=[teacher_id])
    order_items = db.relationship('OrderItem', backref='product_ref', primaryjoin='Product.id == OrderItem.product_id', foreign_keys='OrderItem.product_id')

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

    def to_dict(self, include_teacher=False):
        result = {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'price': self.price,
            'original_price': self.original_price,
            'stock': self.stock,
            'images': self.images,
            'cover_image': self.cover_image,
            'status': self.status,
            'sales_count': self.sales_count,
            'favorite_count': self.favorite_count,
            'view_count': self.view_count,
            'rating': self.rating,
            'tags': self.tags,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_teacher and self.teacher_profile:
            result['teacher'] = {
                'id': self.teacher_profile.id,
                'teacher_id': self.teacher_profile.teacher_id,
                'real_name': self.teacher_profile.real_name,
                'avatar': self.teacher_profile.user.avatar if self.teacher_profile.user else None,
                'rating': self.teacher_profile.rating,
                'follower_count': self.teacher_profile.follower_count
            }
        
        return result

    def __repr__(self):
        return f'<Product {self.title}>'
