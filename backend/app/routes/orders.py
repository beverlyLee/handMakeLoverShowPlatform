from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.response_code import ResponseCode
from app.common.auth import login_required
from app.models import Order, OrderItem, User, TeacherProfile, UserCoupon, Coupon, Review
from app.database import db
from app.services.user_service import UserService
from app.services.message_service import MessageService
from datetime import datetime, timedelta

order_bp = Blueprint('orders', __name__)

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

def get_current_user():
    user_id = g.get('user_id', 1)
    user_dict = UserService.get_user_by_id(user_id)
    return user_dict, user_id

def build_query(user_id=None, teacher_id=None, status=None, role='customer', is_reviewed=None):
    query = Order.query.filter(Order.status != 'deleted')
    
    if role == 'customer' and user_id:
        query = query.filter_by(user_id=user_id)
    
    if role == 'teacher' and teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if is_reviewed is not None:
        if is_reviewed:
            query = query.filter(Order.reviews.any())
        else:
            query = query.filter(~Order.reviews.any())
    
    return query

def get_order_stats_from_query(query):
    orders = query.all()
    stats = {
        'total': len(orders),
        'pending': 0,
        'pending_accept': 0,
        'accepted': 0,
        'in_progress': 0,
        'paid': 0,
        'shipped': 0,
        'delivered': 0,
        'completed': 0,
        'cancelled': 0,
        'rejected': 0,
        'total_amount': 0,
        'today_orders': 0,
        'today_amount': 0,
        'today_complete_making': 0,
        'today_shipped': 0,
        'today_income': 0,
        'month_income': 0,
        'in_progress_and_shipped': 0
    }
    
    today = datetime.utcnow().date()
    current_month = today.month
    current_year = today.year
    
    for order in orders:
        stats[order.status] = stats.get(order.status, 0) + 1
        if order.status in ['pending_accept', 'in_progress', 'paid', 'shipped', 'delivered', 'completed']:
            stats['total_amount'] += order.pay_amount
        
        if order.created_at and order.created_at.date() == today:
            stats['today_orders'] += 1
        
        if order.complete_making_time and order.complete_making_time.date() == today:
            stats['today_complete_making'] += 1
        
        if order.ship_time and order.ship_time.date() == today:
            stats['today_shipped'] += 1
        
        if order.complete_time and order.complete_time.date() == today:
            stats['today_income'] += order.pay_amount
        
        if order.complete_time and order.complete_time.month == current_month and order.complete_time.year == current_year:
            stats['month_income'] += order.pay_amount
        
        if order.status in ['pending_accept', 'in_progress', 'paid', 'shipped', 'delivered', 'completed'] and order.created_at and order.created_at.date() == today:
            stats['today_amount'] += order.pay_amount
    
    stats['in_progress_and_shipped'] = stats['in_progress'] + stats['shipped']
    stats['in_progress_pending_ship'] = stats['in_progress'] + stats['paid']
    
    return stats

@order_bp.route('/', methods=['GET'])
@login_required
def get_orders():
    user_dict, user_id = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', None)
    role = request.args.get('role', 'customer')
    is_reviewed = request.args.get('is_reviewed', None, type=int)
    
    filter_user_id = request.args.get('user_id', None, type=int)
    filter_teacher_id = request.args.get('teacher_id', None, type=int)
    
    if role == 'customer' and filter_user_id is None:
        filter_user_id = user_id
    
    if role == 'teacher' and filter_teacher_id is None:
        filter_teacher_id = user_id
    
    if is_reviewed is not None:
        is_reviewed = bool(is_reviewed)
    
    query = build_query(
        user_id=filter_user_id,
        teacher_id=filter_teacher_id,
        status=status,
        role=role,
        is_reviewed=is_reviewed
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
    is_reviewed = request.args.get('is_reviewed', None, type=int)
    
    query = Order.query.filter_by(teacher_id=teacher_id).filter(Order.status != 'deleted')
    
    if status:
        if ',' in status:
            status_list = [s.strip() for s in status.split(',')]
            query = query.filter(Order.status.in_(status_list))
        else:
            query = query.filter_by(status=status)
    
    if is_reviewed is not None:
        is_reviewed = bool(is_reviewed)
        if is_reviewed:
            query = query.filter(Order.reviews.any())
        else:
            query = query.filter(~Order.reviews.any())
    
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
    
    query = Order.query.filter_by(teacher_id=teacher_id).filter(Order.status != 'deleted')
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
    
    required_fields = ['items']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    teacher_user_id = data.get('teacher_user_id')
    teacher_profile_id = data.get('teacher_id')
    
    if not teacher_user_id and not teacher_profile_id:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='teacher_id 或 teacher_user_id 不能为空')), 400
    
    if teacher_profile_id and not teacher_user_id:
        teacher_profile = TeacherProfile.query.get(teacher_profile_id)
        if teacher_profile:
            teacher_user_id = teacher_profile.user_id
        else:
            return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    order_id = f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    items = data.get('items', [])
    total_amount = 0
    for item in items:
        total_amount += item.get('price', 0) * item.get('quantity', 1)
    
    discount_amount = 0
    shipping_fee = data.get('shipping_fee', 0)
    pay_method = data.get('pay_method')
    shipping_method = data.get('shipping_method', 'standard')
    
    user_coupon = None
    user_coupon_id = data.get('user_coupon_id')
    coupon_id = data.get('coupon_id')
    
    if user_coupon_id:
        user_coupon = UserCoupon.query.filter_by(
            id=user_coupon_id,
            user_id=user_id,
            status='unused'
        ).first()
    elif coupon_id:
        user_coupon = UserCoupon.query.filter_by(
            user_id=user_id,
            coupon_id=coupon_id,
            status='unused'
        ).first()
    
    if user_coupon and user_coupon.coupon:
        coupon = user_coupon.coupon
        can_apply, reason = coupon.can_apply(total_amount)
        if can_apply:
            discount_amount = coupon.calculate_discount(total_amount)
    
    pay_amount = max(total_amount - discount_amount + shipping_fee, 0)
    
    order = Order(
        id=order_id,
        user_id=user_id,
        teacher_id=teacher_user_id,
        status='pending',
        total_amount=total_amount,
        discount_amount=discount_amount,
        pay_amount=pay_amount,
        shipping_fee=shipping_fee,
        pay_method=pay_method,
        shipping_method=shipping_method,
        coupon_id=user_coupon.coupon_id if user_coupon else None,
        user_coupon_id=user_coupon.id if user_coupon else None,
        remark=data.get('remark', '')
    )
    
    if shipping_method in ['express', 'sf']:
        order.estimated_arrival_days = 2
    elif shipping_method == 'jd':
        order.estimated_arrival_days = 1
    else:
        order.estimated_arrival_days = 3
    
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
    
    if user_coupon:
        user_coupon.status = 'used'
        user_coupon.used_at = datetime.utcnow()
        user_coupon.order_id = order_id
        db.session.add(user_coupon)
    
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
    
    order.pay_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    order.status = 'pending_accept'
    
    db.session.commit()
    
    try:
        MessageService.send_order_pay_notification(order)
    except Exception as e:
        print(f'发送订单支付通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='支付成功，等待老师接单'))

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
    
    try:
        MessageService.send_order_cancel_notification(order, cancel_reason, is_teacher=False)
    except Exception as e:
        print(f'发送订单取消通知失败: {e}')
    
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
    
    try:
        MessageService.send_order_complete_notification(order)
    except Exception as e:
        print(f'发送订单完成通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='确认收货成功'))


@order_bp.route('/<order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status not in ['completed', 'cancelled']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有已完成或已取消的订单可以删除，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.user_id != user_id and order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权删除此订单')), 403
    
    order.status = 'deleted'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=None, msg='订单已删除'))


@order_bp.route('/<order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status != 'pending_accept':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有待接单状态可以接单，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    data = request.get_json() or {}
    action = data.get('action', 'start_making')  # 'start_making', 'ship'
    
    order.accept_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    if action == 'ship':
        order.status = 'paid'
        msg = '已进入待发货状态'
    else:
        order.status = 'in_progress'
        order.start_making_time = datetime.utcnow()
        msg = '已开始制作'
    
    db.session.commit()
    
    try:
        MessageService.send_order_accept_notification(order, action)
    except Exception as e:
        print(f'发送订单接单通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg=msg))


@order_bp.route('/<order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status != 'pending_accept':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有待接单状态可以拒单，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    data = request.get_json() or {}
    reject_reason = data.get('reject_reason', '')
    
    if not reject_reason:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请填写拒单理由')), 400
    
    order.status = 'rejected'
    order.reject_time = datetime.utcnow()
    order.reject_reason = reject_reason
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    try:
        MessageService.send_order_reject_notification(order, reject_reason)
    except Exception as e:
        print(f'发送订单拒单通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='拒单成功'))


@order_bp.route('/<order_id>/ship', methods=['POST'])
@login_required
def ship_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status not in ['in_progress', 'paid']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有制作中或待发货状态可以发货，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    data = request.get_json() or {}
    shipping_company = data.get('shipping_company', '')
    tracking_number = data.get('tracking_number', '')
    shipping_method = data.get('shipping_method', 'standard')
    estimated_arrival_days = data.get('estimated_arrival_days', 3)
    
    if not tracking_number:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请填写物流单号')), 400
    
    order.status = 'shipped'
    order.shipping_company = shipping_company
    order.tracking_number = tracking_number
    order.shipping_method = shipping_method
    order.estimated_arrival_days = estimated_arrival_days
    order.ship_time = datetime.utcnow()
    
    if order.ship_time:
        order.estimated_arrival_time = order.ship_time + timedelta(days=estimated_arrival_days)
    
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    try:
        MessageService.send_ship_notification(order)
    except Exception as e:
        print(f'发送订单发货通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='发货成功'))


@order_bp.route('/<order_id>/logistics', methods=['GET'])
@login_required
def get_order_logistics(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id and order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权查看此订单')), 403
    
    logistics_info = {
        'order_id': order.id,
        'status': order.status,
        'status_name': STATUS_NAMES.get(order.status, order.status),
        'shipping_company': order.shipping_company,
        'tracking_number': order.tracking_number,
        'shipping_method': order.shipping_method,
        'ship_time': order.ship_time.strftime('%Y-%m-%d %H:%M:%S') if order.ship_time else None,
        'estimated_arrival_time': order.estimated_arrival_time.strftime('%Y-%m-%d') if order.estimated_arrival_time else None,
        'tracking_items': []
    }
    
    if order.logistics and order.logistics.items:
        logistics_info['tracking_items'] = [item.to_dict() for item in order.logistics.items]
    
    return jsonify(success(data=logistics_info))


@order_bp.route('/<order_id>/start-making', methods=['POST'])
@login_required
def start_making_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status not in ['pending_accept', 'paid']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有待接单或待发货状态可以开始制作，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    if order.status == 'pending_accept':
        order.accept_time = datetime.utcnow()
    
    order.status = 'in_progress'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    try:
        MessageService.send_order_accept_notification(order, 'start_making')
    except Exception as e:
        print(f'发送订单开始制作通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='已开始制作'))


@order_bp.route('/<order_id>/complete-making', methods=['POST'])
@login_required
def complete_making_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.status != 'in_progress':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg=f'只有制作中状态可以标记制作完成，当前状态: {STATUS_NAMES.get(order.status)}')), 400
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    order.status = 'paid'
    order.complete_making_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    try:
        MessageService.send_making_complete_notification(order)
    except Exception as e:
        print(f'发送订单制作完成通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='制作完成，已进入待发货状态'))


@order_bp.route('/<order_id>/edit', methods=['PUT'])
@login_required
def edit_order(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    can_edit_all = order.status == 'pending'
    can_edit_address = order.status in ['pending_accept', 'in_progress', 'paid']
    
    if not can_edit_all and not can_edit_address:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='当前订单状态不可修改')), 400
    
    data = request.get_json() or {}
    
    if can_edit_all:
        if 'total_amount' in data:
            order.total_amount = data['total_amount']
        if 'discount_amount' in data:
            order.discount_amount = data['discount_amount']
        if 'shipping_fee' in data:
            order.shipping_fee = data['shipping_fee']
        if 'pay_amount' in data:
            order.pay_amount = data['pay_amount']
        if 'remark' in data:
            order.remark = data['remark']
        if 'shipping_method' in data:
            order.shipping_method = data['shipping_method']
        
        if 'items' in data:
            for item in order.items:
                db.session.delete(item)
            
            for item_data in data['items']:
                order_item = OrderItem(
                    order_id=order_id,
                    product_id=item_data.get('product_id'),
                    product_title=item_data.get('product_title', ''),
                    product_image=item_data.get('product_image'),
                    price=item_data.get('price', 0),
                    original_price=item_data.get('original_price', item_data.get('price', 0)),
                    quantity=item_data.get('quantity', 1),
                    total_price=item_data.get('total_price') or (item_data.get('price', 0) * item_data.get('quantity', 1))
                )
                db.session.add(order_item)
        
        new_total_amount = order.total_amount
        new_discount_amount = order.discount_amount
        new_shipping_fee = order.shipping_fee
        new_pay_amount = max(new_total_amount - new_discount_amount + new_shipping_fee, 0)
        
        if 'pay_amount' not in data:
            order.pay_amount = new_pay_amount
    
    if can_edit_all or can_edit_address:
        if 'address' in data:
            address = data['address']
            if 'name' in address:
                order.address_name = address['name']
            if 'phone' in address:
                order.address_phone = address['phone']
            if 'province' in address:
                order.address_province = address['province']
            if 'city' in address:
                order.address_city = address['city']
            if 'district' in address:
                order.address_district = address['district']
            if 'detail' in address:
                order.address_detail = address['detail']
    
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='订单修改成功'))


@order_bp.route('/<order_id>/refund', methods=['POST'])
@login_required
def apply_refund(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    if order.refund_status in ['pending', 'approved']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='已有退款申请正在处理中')), 400
    
    can_refund_statuses = ['pending_accept', 'in_progress', 'paid', 'shipped', 'delivered']
    if order.status not in can_refund_statuses:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='当前订单状态不支持退款申请')), 400
    
    data = request.get_json() or {}
    refund_reason = data.get('refund_reason', '')
    refund_proofs = data.get('refund_proofs', [])
    refund_amount = data.get('refund_amount')
    
    if not refund_reason or len(refund_reason.strip()) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请填写退款理由')), 400
    
    if len(refund_reason) > 200:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='退款理由不能超过200个字符')), 400
    
    if refund_proofs and len(refund_proofs) > 3:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='退款凭证最多上传3张')), 400
    
    if refund_amount is not None:
        if refund_amount <= 0 or refund_amount > order.pay_amount:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=f'退款金额必须大于0且不超过订单金额¥{order.pay_amount}')), 400
        order.refund_amount = refund_amount
    else:
        order.refund_amount = order.pay_amount
    
    order.refund_status = 'pending'
    order.refund_reason = refund_reason
    order.refund_proofs = refund_proofs if isinstance(refund_proofs, list) else []
    order.refund_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    try:
        MessageService.send_refund_notification(order, 'pending', order.refund_amount, refund_reason)
    except Exception as e:
        print(f'发送退款申请通知失败: {e}')
    
    return jsonify(success(data=order.to_dict(), msg='退款申请已提交'))


@order_bp.route('/<order_id>/refund', methods=['GET'])
@login_required
def get_refund_detail(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id and order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权查看此订单')), 403
    
    refund_info = {
        'order_id': order.id,
        'refund_status': order.refund_status,
        'refund_status_name': order.refund_status_name,
        'refund_amount': order.refund_amount,
        'refund_reason': order.refund_reason,
        'refund_proofs': order.refund_proofs,
        'refund_time': order.refund_time.strftime('%Y-%m-%d %H:%M:%S') if order.refund_time else None,
        'pay_amount': order.pay_amount,
        'status': order.status,
        'status_name': order.status_name
    }
    
    return jsonify(success(data=refund_info))


@order_bp.route('/<order_id>/refund/cancel', methods=['POST'])
@login_required
def cancel_refund(order_id):
    user_dict, user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    if order.refund_status != 'pending':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='只有待审核状态的退款可以取消')), 400
    
    order.refund_status = None
    order.refund_reason = None
    order.refund_proofs = []
    order.refund_time = None
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(success(data=order.to_dict(), msg='退款申请已取消'))
