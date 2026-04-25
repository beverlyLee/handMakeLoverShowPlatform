from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.response_code import ResponseCode
from app.common.auth import login_required
from app.models import Order, OrderItem, User
from app.database import db
from app.services.user_service import UserService
from datetime import datetime

order_bp = Blueprint('orders', __name__)

STATUS_NAMES = {
    'pending': '待付款',
    'paid': '待发货',
    'shipped': '待收货',
    'delivered': '已送达',
    'completed': '已完成',
    'cancelled': '已取消'
}

def get_current_user():
    user_id = g.get('user_id', 1)
    user_dict = UserService.get_user_by_id(user_id)
    return user_dict, user_id

def build_query(user_id=None, teacher_id=None, status=None, role='customer'):
    query = Order.query
    
    if role == 'customer' and user_id:
        query = query.filter_by(user_id=user_id)
    
    if role == 'teacher' and teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    
    if status:
        query = query.filter_by(status=status)
    
    return query

def get_order_stats_from_query(query):
    orders = query.all()
    stats = {
        'total': len(orders),
        'pending': 0,
        'paid': 0,
        'shipped': 0,
        'delivered': 0,
        'completed': 0,
        'cancelled': 0,
        'total_amount': 0,
        'today_orders': 0,
        'today_amount': 0
    }
    
    today = datetime.utcnow().date()
    
    for order in orders:
        stats[order.status] = stats.get(order.status, 0) + 1
        if order.status in ['paid', 'shipped', 'delivered', 'completed']:
            stats['total_amount'] += order.pay_amount
        
        if order.created_at and order.created_at.date() == today:
            stats['today_orders'] += 1
            if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                stats['today_amount'] += order.pay_amount
    
    return stats

@order_bp.route('/', methods=['GET'])
@login_required
def get_orders():
    user_dict, user_id = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', None)
    role = request.args.get('role', 'customer')
    
    filter_user_id = request.args.get('user_id', None, type=int)
    filter_teacher_id = request.args.get('teacher_id', None, type=int)
    
    if role == 'customer' and filter_user_id is None:
        filter_user_id = user_id
    
    if role == 'teacher' and filter_teacher_id is None:
        filter_teacher_id = user_id
    
    query = build_query(
        user_id=filter_user_id,
        teacher_id=filter_teacher_id,
        status=status,
        role=role
    )
    
    stats = get_order_stats_from_query(query)
    
    total = query.count()
    query = query.order_by(Order.created_at.desc())
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    orders_list = []
    for order in paginated:
        order_dict = order.to_dict()
        orders_list.append(order_dict)
    
    return jsonify(success(data={
        'list': orders_list,
        'orders': orders_list,
        'total': total,
        'page': page,
        'size': size,
        'stats': stats,
        'status_names': STATUS_NAMES
    }))

@order_bp.route('/teacher', methods=['GET'])
@login_required
def get_teacher_orders():
    user_dict, user_id = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', None)
    teacher_id = request.args.get('teacher_id', user_id, type=int)
    
    query = Order.query.filter_by(teacher_id=teacher_id)
    
    if status:
        query = query.filter_by(status=status)
    
    stats = get_order_stats_from_query(query)
    
    total = query.count()
    query = query.order_by(Order.created_at.desc())
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    orders_list = []
    for order in paginated:
        order_dict = order.to_dict()
        orders_list.append(order_dict)
    
    return jsonify(success(data={
        'list': orders_list,
        'orders': orders_list,
        'total': total,
        'page': page,
        'size': size,
        'stats': stats,
        'status_names': STATUS_NAMES
    }))

@order_bp.route('/teacher/stats', methods=['GET'])
@login_required
def get_teacher_order_stats():
    user_dict, user_id = get_current_user()
    teacher_id = request.args.get('teacher_id', user_id, type=int)
    
    query = Order.query.filter_by(teacher_id=teacher_id)
    stats = get_order_stats_from_query(query)
    
    recent_query = query.order_by(Order.created_at.desc()).limit(5)
    recent_orders = [o.to_dict() for o in recent_query.all()]
    
    return jsonify(success(data={
        'stats': stats,
        'recent_orders': recent_orders,
        'status_names': STATUS_NAMES
    }))

@order_bp.route('/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    return jsonify(success(data=order.to_dict()))

@order_bp.route('/', methods=['POST'])
@login_required
def create_order():
    user_dict, user_id = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    required_fields = ['teacher_id', 'items']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    order_id = f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    items = data.get('items', [])
    total_amount = 0
    for item in items:
        total_amount += item.get('price', 0) * item.get('quantity', 1)
    
    order = Order(
        id=order_id,
        user_id=user_id,
        teacher_id=data.get('teacher_id'),
        status='pending',
        total_amount=total_amount,
        pay_amount=total_amount,
        remark=data.get('remark', '')
    )
    
    address = data.get('address', {})
    if address:
        order.address_name = address.get('name')
        order.address_phone = address.get('phone')
        order.address_province = address.get('province')
        order.address_city = address.get('city')
        order.address_district = address.get('district')
        order.address_detail = address.get('detail')
    
    db.session.add(order)
    
    for item_data in items:
        order_item = OrderItem(
            order_id=order_id,
            product_id=item_data.get('product_id'),
            product_title=item_data.get('product_title', ''),
            product_image=item_data.get('product_image'),
            price=item_data.get('price', 0),
            original_price=item_data.get('original_price', item_data.get('price', 0)),
            quantity=item_data.get('quantity', 1),
            total_price=item_data.get('price', 0) * item_data.get('quantity', 1)
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='订单创建成功'))

@order_bp.route('/<order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    if 'remark' in data:
        order.remark = data.get('remark')
    
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='订单更新成功'))

@order_bp.route('/<order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='状态参数不能为空')), 400
    
    status = data.get('status')
    valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'completed', 'cancelled']
    
    if status not in valid_statuses:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg=f'状态值无效，只能是: {valid_statuses}')), 400
    
    original_status = order.status
    
    if status == 'paid':
        order.pay_time = datetime.utcnow()
    elif status == 'shipped':
        order.ship_time = datetime.utcnow()
    elif status == 'delivered':
        order.deliver_time = datetime.utcnow()
    elif status == 'completed':
        order.complete_time = datetime.utcnow()
    elif status == 'cancelled':
        order.cancel_time = datetime.utcnow()
        order.cancel_reason = data.get('cancel_reason', '')
    
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg=f'订单状态已从 {STATUS_NAMES.get(original_status)} 更新为 {STATUS_NAMES.get(status)}'))

@order_bp.route('/<order_id>/pay', methods=['POST'])
@login_required
def pay_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status != 'pending':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'订单状态不是待付款，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权支付此订单')), 403
    
    order.status = 'paid'
    order.pay_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='支付成功'))

@order_bp.route('/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status not in ['pending']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有待付款订单可以取消，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权取消此订单')), 403
    
    data = request.get_json() or {}
    cancel_reason = data.get('cancel_reason', '用户主动取消')
    
    order.status = 'cancelled'
    order.cancel_time = datetime.utcnow()
    order.cancel_reason = cancel_reason
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='订单已取消'))

@order_bp.route('/<order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status not in ['shipped', 'delivered']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有待收货或已送达订单可以确认，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权确认此订单')), 403
    
    order.status = 'completed'
    order.complete_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='确认收货成功'))
