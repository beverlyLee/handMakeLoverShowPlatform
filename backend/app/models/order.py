from datetime import datetime, timedelta
from app.database import db
import json

PAY_METHODS = {
    'wechat': '微信支付',
    'alipay': '支付宝',
    'balance': '余额支付',
    'offline': '线下支付'
}

SHIPPING_METHODS = {
    'standard': '标准快递',
    'express': '特快专递',
    'sf': '顺丰速运',
    'jd': '京东物流',
    'zt': '中通快递',
    'yt': '圆通速递'
}

SHIPPING_COMPANIES = {
    'sf': '顺丰速运',
    'jd': '京东物流',
    'zt': '中通快递',
    'yt': '圆通速递',
    'yd': '韵达快递',
    'ems': 'EMS',
    'other': '其他'
}

REFUND_STATUS_PENDING = 'pending'
REFUND_STATUS_APPROVED = 'approved'
REFUND_STATUS_REJECTED = 'rejected'
REFUND_STATUS_COMPLETED = 'completed'

REFUND_STATUS_NAMES = {
    'pending': '待审核',
    'approved': '已同意',
    'rejected': '已拒绝',
    'completed': '退款完成'
}

ABNORMAL_REASONS = {
    'user_complaint': '用户投诉',
    'logistics_delay': '物流延迟',
    'quality_issue': '质量问题',
    'damaged_in_transit': '运输损坏',
    'wrong_item': '发错商品',
    'teacher_refusal': '老师拒单',
    'system_error': '系统异常',
    'other': '其他原因'
}


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
    
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'))
    user_coupon_id = db.Column(db.Integer, db.ForeignKey('user_coupons.id'))
    
    pay_method = db.Column(db.String(20))
    pay_time = db.Column(db.DateTime)
    
    shipping_method = db.Column(db.String(20), default='standard')
    shipping_company = db.Column(db.String(50))
    tracking_number = db.Column(db.String(50))
    
    estimated_arrival_days = db.Column(db.Integer, default=3)
    estimated_arrival_time = db.Column(db.DateTime)
    
    accept_time = db.Column(db.DateTime)
    start_making_time = db.Column(db.DateTime)
    complete_making_time = db.Column(db.DateTime)
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
    
    is_abnormal = db.Column(db.Boolean, default=False)
    abnormal_reason = db.Column(db.String(500))
    abnormal_reason_code = db.Column(db.String(50))
    abnormal_time = db.Column(db.DateTime)
    abnormal_resolved_at = db.Column(db.DateTime)
    abnormal_resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    refund_status = db.Column(db.String(20))
    refund_amount = db.Column(db.Float, default=0.0)
    refund_reason = db.Column(db.String(500))
    refund_time = db.Column(db.DateTime)
    refund_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    _refund_proofs = db.Column('refund_proofs', db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    logistics = db.relationship('Logistics', backref='order', uselist=False, lazy='select')
    user_coupon = db.relationship(
        'UserCoupon',
        foreign_keys=[user_coupon_id],
        uselist=False,
        lazy='select'
    )

    STATUS_NAMES = {
        'pending': '待付款',
        'pending_accept': '待接单',
        'accepted': '已接单',
        'in_progress': '制作中',
        'paid': '待发货',
        'shipped': '待收货',
        'delivered': '已送达',
        'completed': '已完成',
        'cancelled': '已取消',
        'rejected': '已拒绝',
        'deleted': '已删除'
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

    @property
    def pay_method_name(self):
        return PAY_METHODS.get(self.pay_method, self.pay_method or '')

    @property
    def shipping_method_name(self):
        return SHIPPING_METHODS.get(self.shipping_method, self.shipping_method or '')

    @property
    def refund_status_name(self):
        return REFUND_STATUS_NAMES.get(self.refund_status, self.refund_status or '')

    @property
    def abnormal_reason_name(self):
        if self.abnormal_reason_code:
            return ABNORMAL_REASONS.get(self.abnormal_reason_code, self.abnormal_reason_code)
        return None

    @property
    def refund_proofs(self):
        if self._refund_proofs:
            try:
                return json.loads(self._refund_proofs)
            except:
                return []
        return []

    @refund_proofs.setter
    def refund_proofs(self, value):
        if isinstance(value, list):
            self._refund_proofs = json.dumps(value, ensure_ascii=False)
        else:
            self._refund_proofs = value

    def calculate_estimated_arrival(self):
        if self.shipping_method == 'express' or self.shipping_method == 'sf':
            self.estimated_arrival_days = 2
        elif self.shipping_method == 'jd':
            self.estimated_arrival_days = 1
        else:
            self.estimated_arrival_days = 3
        
        if self.ship_time:
            self.estimated_arrival_time = self.ship_time + timedelta(days=self.estimated_arrival_days)

    @property
    def is_reviewed(self):
        from app.models.review import Review
        return db.session.query(Review).filter_by(order_id=self.id).first() is not None

    def to_dict(self, include_logistics=True, include_detail=True):
        customer_nickname = None
        if self.customer:
            customer_nickname = self.customer.nickname or self.customer.username
        
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'teacher_id': self.teacher_id,
            'status': self.status,
            'status_name': self.status_name,
            'is_reviewed': self.is_reviewed,
            'total_amount': self.total_amount,
            'discount_amount': self.discount_amount,
            'pay_amount': self.pay_amount,
            'shipping_fee': self.shipping_fee,
            'coupon_id': self.coupon_id,
            'user_coupon_id': self.user_coupon_id,
            'pay_method': self.pay_method,
            'pay_method_name': self.pay_method_name,
            'pay_time': self.pay_time.strftime('%Y-%m-%d %H:%M:%S') if self.pay_time else None,
            'accept_time': self.accept_time.strftime('%Y-%m-%d %H:%M:%S') if self.accept_time else None,
            'start_making_time': self.start_making_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_making_time else None,
            'complete_making_time': self.complete_making_time.strftime('%Y-%m-%d %H:%M:%S') if self.complete_making_time else None,
            'shipping_method': self.shipping_method,
            'shipping_method_name': self.shipping_method_name,
            'shipping_company': self.shipping_company,
            'tracking_number': self.tracking_number,
            'estimated_arrival_days': self.estimated_arrival_days,
            'estimated_arrival_time': self.estimated_arrival_time.strftime('%Y-%m-%d') if self.estimated_arrival_time else None,
            'ship_time': self.ship_time.strftime('%Y-%m-%d %H:%M:%S') if self.ship_time else None,
            'deliver_time': self.deliver_time.strftime('%Y-%m-%d %H:%M:%S') if self.deliver_time else None,
            'complete_time': self.complete_time.strftime('%Y-%m-%d %H:%M:%S') if self.complete_time else None,
            'cancel_time': self.cancel_time.strftime('%Y-%m-%d %H:%M:%S') if self.cancel_time else None,
            'cancel_reason': self.cancel_reason,
            'remark': self.remark,
            'customer_nickname': customer_nickname,
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
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'is_abnormal': self.is_abnormal,
            'abnormal_reason': self.abnormal_reason,
            'abnormal_reason_code': self.abnormal_reason_code,
            'abnormal_reason_name': self.abnormal_reason_name,
            'abnormal_time': self.abnormal_time.strftime('%Y-%m-%d %H:%M:%S') if self.abnormal_time else None,
            'abnormal_resolved_at': self.abnormal_resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.abnormal_resolved_at else None,
            'abnormal_resolved_by': self.abnormal_resolved_by,
            'refund_status': self.refund_status,
            'refund_status_name': self.refund_status_name,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason,
            'refund_time': self.refund_time.strftime('%Y-%m-%d %H:%M:%S') if self.refund_time else None,
            'refund_approved_by': self.refund_approved_by,
            'refund_proofs': self.refund_proofs
        }
        
        if include_detail:
            result['price_detail'] = {
                'product_amount': self.total_amount,
                'discount_amount': self.discount_amount,
                'shipping_fee': self.shipping_fee,
                'pay_amount': self.pay_amount
            }
        
        if include_logistics and self.logistics:
            result['logistics'] = self.logistics.to_dict()
        
        if self.user_coupon and self.user_coupon.coupon:
            result['coupon_info'] = {
                'id': self.user_coupon.coupon.id,
                'name': self.user_coupon.coupon.name,
                'type': self.user_coupon.coupon.type,
                'type_name': self.user_coupon.coupon.type_name,
                'value': self.user_coupon.coupon.value,
                'discount': self.user_coupon.coupon.discount,
                'discount_amount': self.discount_amount
            }
        
        return result

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


class Logistics(db.Model):
    __tablename__ = 'logistics'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id'), nullable=False, unique=True)
    
    shipping_company = db.Column(db.String(50))
    tracking_number = db.Column(db.String(50))
    shipping_method = db.Column(db.String(20), default='standard')
    
    status = db.Column(db.String(20), default='pending')
    
    shipped_at = db.Column(db.DateTime)
    estimated_arrival_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    sender_name = db.Column(db.String(50))
    sender_phone = db.Column(db.String(20))
    sender_address = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('LogisticsItem', backref='logistics', lazy='dynamic', cascade='all, delete-orphan', order_by='LogisticsItem.timestamp.asc()')

    STATUS_NAMES = {
        'pending': '待发货',
        'shipped': '已发货',
        'in_transit': '运输中',
        'delivering': '派送中',
        'delivered': '已签收',
        'returned': '已退回'
    }

    @property
    def status_name(self):
        return self.STATUS_NAMES.get(self.status, self.status)

    @property
    def shipping_method_name(self):
        return SHIPPING_METHODS.get(self.shipping_method, self.shipping_method or '')

    def to_dict(self, include_items=True):
        result = {
            'id': self.id,
            'order_id': self.order_id,
            'shipping_company': self.shipping_company,
            'tracking_number': self.tracking_number,
            'shipping_method': self.shipping_method,
            'shipping_method_name': self.shipping_method_name,
            'status': self.status,
            'status_name': self.status_name,
            'shipped_at': self.shipped_at.strftime('%Y-%m-%d %H:%M:%S') if self.shipped_at else None,
            'estimated_arrival_at': self.estimated_arrival_at.strftime('%Y-%m-%d') if self.estimated_arrival_at else None,
            'delivered_at': self.delivered_at.strftime('%Y-%m-%d %H:%M:%S') if self.delivered_at else None,
            'sender_name': self.sender_name,
            'sender_phone': self.sender_phone,
            'sender_address': self.sender_address,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_items:
            result['items'] = [item.to_dict() for item in self.items]
        
        return result

    def __repr__(self):
        return f'<Logistics order_id={self.order_id}>'


class LogisticsItem(db.Model):
    __tablename__ = 'logistics_items'
    
    id = db.Column(db.Integer, primary_key=True)
    logistics_id = db.Column(db.Integer, db.ForeignKey('logistics.id'), nullable=False)
    
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(200))
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'logistics_id': self.logistics_id,
            'status': self.status,
            'description': self.description,
            'location': self.location,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<LogisticsItem logistics_id={self.logistics_id}>'
