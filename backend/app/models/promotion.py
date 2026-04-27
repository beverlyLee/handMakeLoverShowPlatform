from datetime import datetime
from app.database import db
import json


class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    
    type = db.Column(db.String(20), nullable=False, default='fixed')
    value = db.Column(db.Float, nullable=False, default=0)
    discount = db.Column(db.Float, default=0)
    
    min_amount = db.Column(db.Float, default=0)
    max_discount = db.Column(db.Float)
    
    total_quantity = db.Column(db.Integer, default=1000)
    used_quantity = db.Column(db.Integer, default=0)
    limit_per_user = db.Column(db.Integer, default=1)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    _applicable_categories = db.Column('applicable_categories', db.Text)
    _applicable_products = db.Column('applicable_products', db.Text)
    
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_coupons = db.relationship('UserCoupon', backref='coupon', lazy='dynamic')

    TYPE_NAMES = {
        'fixed': '满减券',
        'percent': '折扣券',
        'free_shipping': '包邮券'
    }

    @property
    def applicable_categories(self):
        if self._applicable_categories:
            try:
                return json.loads(self._applicable_categories)
            except:
                return []
        return []

    @applicable_categories.setter
    def applicable_categories(self, value):
        if isinstance(value, list):
            self._applicable_categories = json.dumps(value, ensure_ascii=False)
        else:
            self._applicable_categories = value

    @property
    def applicable_products(self):
        if self._applicable_products:
            try:
                return json.loads(self._applicable_products)
            except:
                return []
        return []

    @applicable_products.setter
    def applicable_products(self, value):
        if isinstance(value, list):
            self._applicable_products = json.dumps(value, ensure_ascii=False)
        else:
            self._applicable_products = value

    @property
    def type_name(self):
        return self.TYPE_NAMES.get(self.type, self.type)

    @property
    def is_valid(self):
        if self.status != 'active':
            return False
        now = datetime.utcnow()
        if now < self.start_time or now > self.end_time:
            return False
        if self.used_quantity >= self.total_quantity:
            return False
        return True

    def can_apply(self, order_amount):
        if not self.is_valid:
            return False, '优惠券不可用'
        if order_amount < self.min_amount:
            return False, f'订单金额需满{self.min_amount}元才能使用'
        return True, None

    def calculate_discount(self, order_amount):
        if self.type == 'fixed':
            return min(self.value, order_amount)
        elif self.type == 'percent':
            discount = order_amount * (1 - self.discount)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        elif self.type == 'free_shipping':
            return 0
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'type_name': self.type_name,
            'value': self.value,
            'discount': self.discount,
            'min_amount': self.min_amount,
            'max_discount': self.max_discount,
            'total_quantity': self.total_quantity,
            'used_quantity': self.used_quantity,
            'limit_per_user': self.limit_per_user,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'applicable_categories': self.applicable_categories,
            'applicable_products': self.applicable_products,
            'status': self.status,
            'is_valid': self.is_valid,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Coupon {self.name}>'


class UserCoupon(db.Model):
    __tablename__ = 'user_coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    
    status = db.Column(db.String(20), default='unused')
    
    used_at = db.Column(db.DateTime)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'))
    
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    STATUS_NAMES = {
        'unused': '未使用',
        'used': '已使用',
        'expired': '已过期'
    }

    @property
    def status_name(self):
        return self.STATUS_NAMES.get(self.status, self.status)

    @property
    def is_valid(self):
        if self.status != 'unused':
            return False
        if self.coupon:
            return self.coupon.is_valid
        return False

    def to_dict(self, include_coupon=True):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'coupon_id': self.coupon_id,
            'status': self.status,
            'status_name': self.status_name,
            'is_valid': self.is_valid,
            'used_at': self.used_at.strftime('%Y-%m-%d %H:%M:%S') if self.used_at else None,
            'order_id': self.order_id,
            'received_at': self.received_at.strftime('%Y-%m-%d %H:%M:%S') if self.received_at else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_coupon and self.coupon:
            result['coupon'] = self.coupon.to_dict()
        
        return result

    def __repr__(self):
        return f'<UserCoupon user_id={self.user_id} coupon_id={self.coupon_id}>'
