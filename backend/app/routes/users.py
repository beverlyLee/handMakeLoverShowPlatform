from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.services.user_service import UserService
from app.models import Order, OrderItem, Review
from app.database import db
from datetime import datetime, timedelta

user_bp = Blueprint('users', __name__)

ROLE_NAMES = {
    'customer': '普通用户',
    'teacher': '手作老师'
}

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

def get_order_stats(user_id, role):
    if role == 'teacher':
        orders = Order.query.filter_by(teacher_id=user_id).all()
    else:
        orders = Order.query.filter_by(user_id=user_id).all()
    
    stats = {
        'total': len(orders),
        'pending': 0,
        'paid': 0,
        'shipped': 0,
        'delivered': 0,
        'completed': 0,
        'cancelled': 0,
        'total_amount': 0
    }
    
    for order in orders:
        stats[order.status] = stats.get(order.status, 0) + 1
        if order.status in ['paid', 'shipped', 'delivered', 'completed']:
            stats['total_amount'] += order.pay_amount
    
    return stats

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_user_profile():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return jsonify(success(data=user_dict))

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_user_profile():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    user_dict = UserService.update_user(user_id, **data)
    return jsonify(success(data=user_dict, msg='用户信息更新成功'))

@user_bp.route('/roles', methods=['GET'])
@login_required
def get_user_roles():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    roles = user_dict.get('roles', ['customer'])
    current_role = user_dict.get('current_role', 'customer')
    
    return jsonify(success(data={
        'roles': roles,
        'current_role': current_role,
        'can_switch': len(roles) > 1,
        'role_names': ROLE_NAMES
    }))

@user_bp.route('/role', methods=['PUT'])
@login_required
def switch_role():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='角色参数不能为空')), 400
    
    target_role = data.get('role')
    if target_role not in ['customer', 'teacher']:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='角色类型不正确，只能是 customer 或 teacher')), 400
    
    result = UserService.switch_role(user_id, target_role)
    user_dict, error_msg, original_role = result
    
    if error_msg:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg=error_msg)), 403
    
    if original_role == target_role:
        return jsonify(success(data={
            'user': user_dict,
            'original_role': original_role,
            'original_role_name': ROLE_NAMES.get(original_role),
            'current_role': target_role,
            'current_role_name': ROLE_NAMES.get(target_role),
            'message': '用户角色未变更，已是目标角色'
        }, msg='角色切换成功'))
    
    return jsonify(success(data={
        'user': user_dict,
        'original_role': original_role,
        'original_role_name': ROLE_NAMES.get(original_role),
        'current_role': target_role,
        'current_role_name': ROLE_NAMES.get(target_role),
        'message': f'用户角色已从 {ROLE_NAMES.get(original_role)} 切换为 {ROLE_NAMES.get(target_role)}'
    }, msg='角色切换成功'))

@user_bp.route('/teacher/verify', methods=['POST'])
@login_required
def verify_teacher_identity():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    required_fields = ['real_name', 'id_card', 'phone']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    existing_profile = UserService.get_teacher_profile(user_id)
    if existing_profile:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='您已经是手作老师身份')), 400
    
    teacher_info = UserService.verify_teacher_identity(user_id, data)
    user_dict = UserService.get_user_by_id(user_id)
    
    return jsonify(success(data={
        'teacher_info': teacher_info,
        'user': user_dict
    }, msg='手作老师身份验证成功'))

@user_bp.route('/teacher/apply', methods=['POST'])
@login_required
def apply_teacher():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    required_fields = ['real_name', 'id_card', 'phone', 'specialties']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    existing_profile = UserService.get_teacher_profile(user_id)
    if existing_profile:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='您已经是手作老师身份')), 400
    
    teacher_info = UserService.create_teacher_profile(user_id, data)
    user_dict = UserService.get_user_by_id(user_id)
    
    return jsonify(success(data={
        'teacher_info': teacher_info,
        'user': user_dict,
        'message': '恭喜您成功入驻成为手作老师！'
    }, msg='入驻成功'))

@user_bp.route('/teacher/info', methods=['GET'])
@login_required
def get_teacher_info():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    teacher_info = UserService.get_teacher_profile(user_id)
    if not teacher_info:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    return jsonify(success(data=teacher_info))

@user_bp.route('/teacher/info', methods=['PUT'])
@login_required
def update_teacher_info():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    teacher_info = UserService.get_teacher_profile(user_id)
    if not teacher_info:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    updated_teacher = UserService.update_teacher_profile(user_id, data)
    
    return jsonify(success(data=updated_teacher, msg='老师资料更新成功'))

@user_bp.route('/teacher/stats', methods=['GET'])
@login_required
def get_teacher_order_stats():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    stats = get_order_stats(user_id, 'teacher')
    
    return jsonify(success(data={
        'stats': stats,
        'status_names': STATUS_NAMES
    }))

@user_bp.route('/address', methods=['GET'])
@login_required
def get_address_list():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    addresses = UserService.get_addresses_by_user(user_id)
    return jsonify(success(data={
        'list': addresses,
        'addresses': addresses,
        'total': len(addresses)
    }))

@user_bp.route('/address/<int:address_id>', methods=['GET'])
@login_required
def get_address_detail(address_id):
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    address = UserService.get_address_by_id(address_id, user_id)
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    return jsonify(success(data=address))

@user_bp.route('/address', methods=['POST'])
@login_required
def create_address():
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    
    required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    new_address = UserService.create_address(user_id, data)
    
    return jsonify(success(data=new_address, msg='地址添加成功'))

@user_bp.route('/address/<int:address_id>', methods=['PUT'])
@login_required
def update_address(address_id):
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    address = UserService.update_address(address_id, user_id, data)
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    return jsonify(success(data=address, msg='地址更新成功'))

@user_bp.route('/address/<int:address_id>', methods=['DELETE'])
@login_required
def delete_address(address_id):
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    is_success = UserService.delete_address(address_id, user_id)
    if not is_success:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    return jsonify(success(msg='地址删除成功'))

@user_bp.route('/address/<int:address_id>/default', methods=['PUT'])
@login_required
def set_default_address(address_id):
    user_dict, user_id = get_current_user()
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    is_success = UserService.set_default_address(address_id, user_id)
    if not is_success:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    return jsonify(success(msg='默认地址设置成功'))

@user_bp.route('/', methods=['GET'])
def get_users():
    from app.models import User
    users = User.query.limit(10).all()
    return jsonify(success(data=[u.to_dict() for u in users]))

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user_dict = UserService.get_user_by_id(user_id)
    if not user_dict:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return jsonify(success(data=user_dict))

@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user_dict, current_user_id = get_current_user()
    if user_id != current_user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权修改其他用户信息')), 403
    
    return update_user_profile()


@user_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
def get_teacher_public_info(teacher_id):
    from app.models import TeacherProfile
    
    teacher = TeacherProfile.query.get(teacher_id)
    if not teacher:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师不存在')), 404
    
    teacher_dict = teacher.to_dict()
    
    if teacher.user:
        teacher_dict['user_info'] = {
            'id': teacher.user.id,
            'nickname': teacher.user.nickname,
            'avatar': teacher.user.avatar,
            'phone': teacher.user.phone
        }
    
    return jsonify(success(data=teacher_dict))


@user_bp.route('/teacher/<int:teacher_id>/order-stats', methods=['GET'])
def get_teacher_public_order_stats(teacher_id):
    from app.models import TeacherProfile, Order
    
    teacher = TeacherProfile.query.get(teacher_id)
    if not teacher:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师不存在')), 404
    
    orders_query = Order.query.filter_by(teacher_id=teacher.user_id)
    all_orders = orders_query.all()
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)
    seven_days_ago = today_start - timedelta(days=7)
    
    stats = {
        'total': len(all_orders),
        'pending': 0,
        'paid': 0,
        'shipped': 0,
        'delivered': 0,
        'completed': 0,
        'cancelled': 0,
        'pending_accept': 0,
        'accepted': 0,
        'in_progress': 0,
        'rejected': 0,
        'total_amount': 0
    }
    
    paid_amounts = []
    completed_count = 0
    cancelled_count = 0
    total_effective_count = 0
    
    today_orders_count = 0
    today_orders_amount = 0
    week_orders_count = 0
    week_orders_amount = 0
    month_orders_count = 0
    month_orders_amount = 0
    thirty_days_orders_count = 0
    thirty_days_orders_amount = 0
    
    daily_trend_data = {}
    for i in range(7):
        date_key = (today_start - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_trend_data[date_key] = {'count': 0, 'amount': 0}
    
    for order in all_orders:
        stats[order.status] = stats.get(order.status, 0) + 1
        
        if order.status in ['paid', 'shipped', 'delivered', 'completed']:
            stats['total_amount'] += order.pay_amount
            paid_amounts.append(order.pay_amount)
            total_effective_count += 1
        
        if order.status == 'completed':
            completed_count += 1
        elif order.status == 'cancelled':
            cancelled_count += 1
        
        order_date = order.created_at
        if order_date:
            order_date_key = order_date.strftime('%Y-%m-%d')
            
            if order_date >= today_start:
                today_orders_count += 1
                if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                    today_orders_amount += order.pay_amount
            
            if order_date >= week_start:
                week_orders_count += 1
                if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                    week_orders_amount += order.pay_amount
            
            if order_date >= month_start:
                month_orders_count += 1
                if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                    month_orders_amount += order.pay_amount
            
            if order_date >= thirty_days_ago:
                thirty_days_orders_count += 1
                if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                    thirty_days_orders_amount += order.pay_amount
            
            if order_date_key in daily_trend_data:
                daily_trend_data[order_date_key]['count'] += 1
                if order.status in ['paid', 'shipped', 'delivered', 'completed']:
                    daily_trend_data[order_date_key]['amount'] += order.pay_amount
    
    stats['today_orders_count'] = today_orders_count
    stats['today_orders_amount'] = round(today_orders_amount, 2)
    stats['week_orders_count'] = week_orders_count
    stats['week_orders_amount'] = round(week_orders_amount, 2)
    stats['month_orders_count'] = month_orders_count
    stats['month_orders_amount'] = round(month_orders_amount, 2)
    stats['thirty_days_orders_count'] = thirty_days_orders_count
    stats['thirty_days_orders_amount'] = round(thirty_days_orders_amount, 2)
    
    stats['completion_rate'] = round(completed_count / total_effective_count * 100, 1) if total_effective_count > 0 else 0
    stats['cancellation_rate'] = round(cancelled_count / (total_effective_count + cancelled_count) * 100, 1) if (total_effective_count + cancelled_count) > 0 else 0
    stats['avg_order_value'] = round(stats['total_amount'] / total_effective_count, 2) if total_effective_count > 0 else 0
    stats['avg_daily_amount_30days'] = round(thirty_days_orders_amount / 30, 2)
    stats['max_order_value'] = round(max(paid_amounts), 2) if paid_amounts else 0
    stats['min_order_value'] = round(min(paid_amounts), 2) if paid_amounts else 0
    
    pending_orders = {
        'pending_accept': stats.get('pending_accept', 0),
        'accepted': stats.get('accepted', 0),
        'in_progress': stats.get('in_progress', 0),
        'paid': stats.get('paid', 0),
        'shipped': stats.get('shipped', 0),
        'total_pending': stats.get('pending_accept', 0) + stats.get('accepted', 0) + stats.get('in_progress', 0) + stats.get('paid', 0) + stats.get('shipped', 0)
    }
    
    daily_trend = []
    for i in range(6, -1, -1):
        date_key = (today_start - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_data = daily_trend_data.get(date_key, {'count': 0, 'amount': 0})
        daily_trend.append({
            'date': date_key,
            'count': daily_data['count'],
            'amount': round(daily_data['amount'], 2)
        })
    
    pending_reviews_count = Review.query.filter_by(
        teacher_id=teacher.user_id,
        is_hidden=False,
        is_read=False
    ).count()
    
    pending_reply_count = Review.query.filter(
        Review.teacher_id == teacher.user_id,
        Review.is_hidden == False,
        Review.reply_content.is_(None)
    ).count()
    
    recent_query = orders_query.order_by(Order.created_at.desc()).limit(10)
    recent_orders = []
    for order in recent_query.all():
        order_dict = {
            'id': order.id,
            'status': order.status,
            'status_name': order.status_name,
            'total_amount': order.total_amount,
            'pay_amount': order.pay_amount,
            'create_time': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else None,
            'items': []
        }
        for item in order.items:
            order_dict['items'].append({
                'product_title': item.product_title,
                'product_image': item.product_image,
                'price': item.price,
                'quantity': item.quantity
            })
        recent_orders.append(order_dict)
    
    return jsonify(success(data={
        'stats': stats,
        'pending_orders': pending_orders,
        'daily_trend': daily_trend,
        'pending_reviews_count': pending_reviews_count,
        'pending_reply_count': pending_reply_count,
        'recent_orders': recent_orders,
        'status_names': STATUS_NAMES
    }))
