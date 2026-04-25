from datetime import datetime
from app.database import db
import json

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.String(50), primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    status = db.Column(db.String(20), default='pending')
    
    total_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    pay_amount = db.Column(db.Float, default=0.0)
    shipping_fee = db.Column(db.Float, default=0.0)
    
    pay_method = db.Column(db.String(20))
    pay_time = db.Column(db.DateTime)
    
    ship_time = db.Column(db.DateTime)
    deliver_time = db.Column(db.DateTime)
    complete_time = db.Column(db.DateTime)
    cancel_time = db.Column(db.DateTime)
    cancel_reason = db.Column(db.String(200))
    
    remark = db.Column(db.String(500))
    
    address_name = db.Column(db.String(50))
    address_phone = db.Column(db.String(20))
    address_province = db.Column(db.String(50))
    address_city = db.Column(db.String(50))
    address_district = db.Column(db.String(50))
    address_detail = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    STATUS_NAMES = {
        'pending': '待付款',
        'paid': '待发货',
        'shipped': '待收货',
        'delivered': '已送达',
        'completed': '已完成',
        'cancelled': '已取消'
    }

    @property
    def address(self):
        return {
            'name': self.address_name,
            'phone': self.address_phone,
            'province': self.address_province,
            'city': self.address_city,
            'district': self.address_district,
            'detail': self.address_detail
        }

    @property
    def status_name(self):
        return self.STATUS_NAMES.get(self.status, self.status)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'teacher_id': self.teacher_id,
            'status': self.status,
            'status_name': self.status_name,
            'total_amount': self.total_amount,
            'discount_amount': self.discount_amount,
            'pay_amount': self.pay_amount,
            'shipping_fee': self.shipping_fee,
            'pay_method': self.pay_method,
            'pay_time': self.pay_time.strftime('%Y-%m-%d %H:%M:%S') if self.pay_time else None,
            'ship_time': self.ship_time.strftime('%Y-%m-%d %H:%M:%S') if self.ship_time else None,
            'deliver_time': self.deliver_time.strftime('%Y-%m-%d %H:%M:%S') if self.deliver_time else None,
            'complete_time': self.complete_time.strftime('%Y-%m-%d %H:%M:%S') if self.complete_time else None,
            'cancel_time': self.cancel_time.strftime('%Y-%m-%d %H:%M:%S') if self.cancel_time else None,
            'cancel_reason': self.cancel_reason,
            'remark': self.remark,
            'address': {
                'name': self.address_name,
                'phone': self.address_phone,
                'province': self.address_province,
                'city': self.address_city,
                'district': self.address_district,
                'detail': self.address_detail
            },
            'items': [item.to_dict() for item in self.items],
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'), nullable=False)
    
    product_id = db.Column(db.Integer, nullable=False)
    product_title = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(500))
    
    price = db.Column(db.Float, default=0.0)
    original_price = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_title': self.product_title,
            'product_image': self.product_image,
            'price': self.price,
            'original_price': self.original_price,
            'quantity': self.quantity,
            'total_price': self.total_price or (self.price * self.quantity)
        }

    def __repr__(self):
        return f'<OrderItem {self.id}>'
