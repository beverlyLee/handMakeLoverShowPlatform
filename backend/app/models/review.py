from datetime import datetime
from app.database import db
import json

PRODUCT_DETAIL_ITEMS = [
    {'key': 'craft_quality', 'label': '工艺质量', 'description': '手作工艺的精细程度'},
    {'key': 'material_quality', 'label': '材料质感', 'description': '使用材料的质感和品质'},
    {'key': 'design_appeal', 'label': '款式设计', 'description': '外观设计的美观程度'},
    {'key': 'practical_value', 'label': '实用价值', 'description': '产品的实用性和功能性'},
    {'key': 'packaging_quality', 'label': '包装精美', 'description': '包装的精美和保护程度'}
]

TEACHER_DETAIL_ITEMS = [
    {'key': 'teaching_patience', 'label': '教学耐心', 'description': '老师教学的耐心程度'},
    {'key': 'communication_timely', 'label': '沟通及时', 'description': '回复消息的及时性'},
    {'key': 'professional_level', 'label': '专业程度', 'description': '老师的专业技能水平'},
    {'key': 'service_attitude', 'label': '服务态度', 'description': '服务态度的友好程度'},
    {'key': 'after_sales_service', 'label': '售后服务', 'description': '售后问题处理能力'}
]

LOGISTICS_DETAIL_ITEMS = [
    {'key': 'delivery_speed', 'label': '配送速度', 'description': '物流配送的速度'},
    {'key': 'package_condition', 'label': '包裹完好', 'description': '包裹送达时的完好程度'},
    {'key': 'logistics_service', 'label': '物流服务', 'description': '快递员的服务态度'}
]


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    overall_rating = db.Column(db.Float, default=5.0)
    
    product_rating = db.Column(db.Float, default=5.0)
    _product_detail_ratings = db.Column('product_detail_ratings', db.Text)
    
    teacher_rating = db.Column(db.Float, default=5.0)
    _teacher_detail_ratings = db.Column('teacher_detail_ratings', db.Text)
    
    logistics_rating = db.Column(db.Float, default=5.0)
    _logistics_detail_ratings = db.Column('logistics_detail_ratings', db.Text)
    
    content = db.Column(db.Text)
    _images = db.Column('images', db.Text)
    
    is_anonymous = db.Column(db.Boolean, default=False)
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    reply_content = db.Column(db.Text)
    reply_time = db.Column(db.DateTime)
    
    is_reported = db.Column(db.Boolean, default=False)
    report_reason = db.Column(db.String(500))
    
    is_hidden = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = db.relationship('Order', backref='reviews', foreign_keys=[order_id])
    product = db.relationship('Product', backref='reviews', foreign_keys=[product_id])

    @property
    def product_detail_ratings(self):
        if self._product_detail_ratings:
            try:
                return json.loads(self._product_detail_ratings)
            except:
                return {}
        return {}

    @product_detail_ratings.setter
    def product_detail_ratings(self, value):
        if isinstance(value, dict):
            self._product_detail_ratings = json.dumps(value, ensure_ascii=False)
        else:
            self._product_detail_ratings = value

    @property
    def teacher_detail_ratings(self):
        if self._teacher_detail_ratings:
            try:
                return json.loads(self._teacher_detail_ratings)
            except:
                return {}
        return {}

    @teacher_detail_ratings.setter
    def teacher_detail_ratings(self, value):
        if isinstance(value, dict):
            self._teacher_detail_ratings = json.dumps(value, ensure_ascii=False)
        else:
            self._teacher_detail_ratings = value

    @property
    def logistics_detail_ratings(self):
        if self._logistics_detail_ratings:
            try:
                return json.loads(self._logistics_detail_ratings)
            except:
                return {}
        return {}

    @logistics_detail_ratings.setter
    def logistics_detail_ratings(self, value):
        if isinstance(value, dict):
            self._logistics_detail_ratings = json.dumps(value, ensure_ascii=False)
        else:
            self._logistics_detail_ratings = value

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

    @staticmethod
    def calculate_average_rating(detail_ratings, detail_items):
        if not detail_ratings:
            return 5.0
        total = 0.0
        count = 0
        for item in detail_items:
            key = item['key']
            if key in detail_ratings:
                rating = detail_ratings[key]
                if isinstance(rating, (int, float)) and 0 <= rating <= 5:
                    total += rating
                    count += 1
        if count == 0:
            return 5.0
        return round(total / count, 1)

    @staticmethod
    def calculate_overall_rating(product_rating, teacher_rating, logistics_rating):
        product_weight = 0.4
        teacher_weight = 0.35
        logistics_weight = 0.25
        
        overall = (product_rating * product_weight) + \
                  (teacher_rating * teacher_weight) + \
                  (logistics_rating * logistics_weight)
        return round(overall, 1)

    def to_dict(self, include_user=False, include_product=False, include_order=False, include_teacher=False):
        result = {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'teacher_id': self.teacher_id,
            
            'overall_rating': self.overall_rating,
            
            'product_rating': self.product_rating,
            'product_detail_ratings': self.product_detail_ratings,
            'product_detail_items': PRODUCT_DETAIL_ITEMS,
            
            'teacher_rating': self.teacher_rating,
            'teacher_detail_ratings': self.teacher_detail_ratings,
            'teacher_detail_items': TEACHER_DETAIL_ITEMS,
            
            'logistics_rating': self.logistics_rating,
            'logistics_detail_ratings': self.logistics_detail_ratings,
            'logistics_detail_items': LOGISTICS_DETAIL_ITEMS,
            
            'content': self.content,
            'images': self.images,
            'is_anonymous': self.is_anonymous,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'reply_content': self.reply_content,
            'reply': self.reply_content,
            'reply_time': self.reply_time.strftime('%Y-%m-%d %H:%M:%S') if self.reply_time else None,
            
            'is_reported': self.is_reported,
            'is_hidden': self.is_hidden,
            
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            
            'user_name': None,
            'user_avatar': None
        }
        
        if include_user and hasattr(self, 'user_info'):
            result['user_info'] = self.user_info
            if self.user_info:
                result['user_name'] = self.user_info.get('nickname')
                result['user_avatar'] = self.user_info.get('avatar')
        
        if include_product and self.product:
            result['product_info'] = {
                'id': self.product.id,
                'title': self.product.title,
                'cover_image': self.product.cover_image,
                'price': self.product.price
            }
        
        if include_order and self.order:
            result['order_info'] = {
                'id': self.order.id,
                'status': self.order.status,
                'status_name': self.order.status_name,
                'create_time': self.order.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.order.created_at else None
            }
        
        return result

    def __repr__(self):
        return f'<Review id={self.id}, order_id={self.order_id}>'
