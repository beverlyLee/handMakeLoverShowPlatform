from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from io import StringIO
import csv
import json
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.database import db
from app.models import User, Product, Order, Category, Activity, Review, TeacherProfile, OrderItem, Like, ActivityRegistration, CRAFT_TYPES, ACTIVITY_TYPES, ActivityType, SystemConfig, AuditLog, REFUND_STATUS_NAMES, ABNORMAL_REASONS, RefundProgress
from app.models.order import (
    REFUND_STATUS_PENDING, REFUND_STATUS_APPROVED, REFUND_STATUS_PROCESSING,
    REFUND_STATUS_COMPLETED, REFUND_STATUS_REJECTED, REFUND_STATUS_ABNORMAL,
    REFUND_STEP_APPLY, REFUND_STEP_AUDIT, REFUND_STEP_PROCESS, REFUND_STEP_COMPLETE
)
from app.models.message import Message, Conversation, MESSAGE_TYPES, ANNOUNCEMENT_SUBTYPES, RECIPIENT_TYPES
from app.services.message_service import MessageService

admin_bp = Blueprint('admin', __name__)

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
    'deleted': '已删除',
    'refunding': '退款中'
}

def parse_datetime(datetime_str):
    if not datetime_str:
        return None
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None

def get_date_range(period, start_date=None, end_date=None):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            return start, end
        except:
            pass
    
    if period == 'week':
        start = today_start - timedelta(days=today_start.weekday())
        end = start + timedelta(days=7)
    elif period == 'month':
        start = today_start.replace(day=1)
        next_month = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year + 1, month=1, day=1)
        end = next_month
    elif period == 'quarter':
        quarter = (today_start.month - 1) // 3
        start = today_start.replace(month=quarter * 3 + 1, day=1)
        end = start.replace(month=start.month + 3, day=1) if start.month <= 9 else start.replace(year=start.year + 1, month=1, day=1)
    elif period == 'year':
        start = today_start.replace(month=1, day=1)
        end = start.replace(year=start.year + 1, month=1, day=1)
    else:
        start = today_start - timedelta(days=6)
        end = today_start + timedelta(days=1)
    
    return start, end

def generate_csv(data, headers, filename):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    output.seek(0)
    return output.getvalue()

@admin_bp.route('/stats', methods=['GET'])
@login_required
def get_admin_stats():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    total_users = User.query.count()
    today_users = User.query.filter(User.created_at >= today_start).count()
    week_users = User.query.filter(User.created_at >= week_start).count()
    month_users = User.query.filter(User.created_at >= month_start).count()
    
    total_products = Product.query.filter(Product.status == 'active').count()
    today_products = Product.query.filter(
        Product.created_at >= today_start,
        Product.status == 'active'
    ).count()
    
    statuses = ['pending', 'pending_accept', 'accepted', 'in_progress', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'rejected']
    status_counts = {}
    for status in statuses:
        status_counts[status] = Order.query.filter(Order.status == status).count()
    
    total_orders = Order.query.filter(Order.status != 'deleted').count()
    today_orders = Order.query.filter(
        Order.created_at >= today_start,
        Order.status != 'deleted'
    ).count()
    
    month_orders = Order.query.filter(
        Order.created_at >= month_start,
        Order.status != 'deleted'
    ).count()
    
    completed_orders = Order.query.filter(Order.status == 'completed').all()
    total_revenue = sum(order.pay_amount for order in completed_orders) if completed_orders else 0
    today_completed = Order.query.filter(
        Order.status == 'completed',
        Order.complete_time >= today_start
    ).all()
    today_revenue = sum(order.pay_amount for order in today_completed) if today_completed else 0
    
    month_completed = Order.query.filter(
        Order.status == 'completed',
        Order.complete_time >= month_start
    ).all()
    month_revenue = sum(order.pay_amount for order in month_completed) if month_completed else 0
    
    pending_accept = status_counts.get('pending_accept', 0)
    in_progress = status_counts.get('in_progress', 0)
    paid = status_counts.get('paid', 0)
    
    total_teachers = TeacherProfile.query.count()
    total_categories = Category.query.filter(Category.status == 'active').count()
    total_activities = Activity.query.filter(Activity.status == 'active').count()
    total_reviews = Review.query.count()
    
    daily_trend = []
    for i in range(6, -1, -1):
        date_start = today_start - timedelta(days=i)
        date_end = date_start + timedelta(days=1)
        
        day_users = User.query.filter(
            User.created_at >= date_start,
            User.created_at < date_end
        ).count()
        
        day_orders = Order.query.filter(
            Order.created_at >= date_start,
            Order.created_at < date_end,
            Order.status != 'deleted'
        ).count()
        
        day_completed = Order.query.filter(
            Order.status == 'completed',
            Order.complete_time >= date_start,
            Order.complete_time < date_end
        ).all()
        day_revenue = sum(order.pay_amount for order in day_completed) if day_completed else 0
        
        daily_trend.append({
            'date': date_start.strftime('%Y-%m-%d'),
            'users': day_users,
            'orders': day_orders,
            'revenue': round(day_revenue, 2)
        })
    
    recent_query = Order.query.filter(Order.status != 'deleted').order_by(Order.created_at.desc()).limit(10)
    recent_orders = []
    for order in recent_query.all():
        order_dict = order.to_dict()
        customer = User.query.get(order.user_id)
        if customer:
            order_dict['customer_nickname'] = customer.nickname
        recent_orders.append(order_dict)
    
    return jsonify(success(data={
        'users': {
            'total': total_users,
            'today': today_users,
            'week': week_users,
            'month': month_users
        },
        'products': {
            'total': total_products,
            'today': today_products
        },
        'orders': {
            'total': total_orders,
            'today': today_orders,
            'month': month_orders,
            'pending': status_counts.get('pending_accept', 0) + status_counts.get('in_progress', 0) + status_counts.get('paid', 0)
        },
        'revenue': {
            'total': round(total_revenue, 2),
            'today': round(today_revenue, 2),
            'month': round(month_revenue, 2)
        },
        'status_counts': status_counts,
        'stats': {
            'totalOrders': total_orders,
            'total_amount': round(total_revenue, 2),
            'today_orders': today_orders,
            'today_amount': round(today_revenue, 2),
            'pending_accept': pending_accept,
            'in_progress': in_progress,
            'paid': paid,
            'month_income': round(month_revenue, 2),
            'pending': status_counts.get('pending', 0),
            'accepted': status_counts.get('accepted', 0),
            'shipped': status_counts.get('shipped', 0),
            'delivered': status_counts.get('delivered', 0),
            'completed': status_counts.get('completed', 0),
            'cancelled': status_counts.get('cancelled', 0),
            'rejected': status_counts.get('rejected', 0)
        },
        'recent_orders': recent_orders,
        'summary': {
            'teachers': total_teachers,
            'categories': total_categories,
            'activities': total_activities,
            'reviews': total_reviews
        },
        'daily_trend': daily_trend
    }))

@admin_bp.route('/users/stats', methods=['GET'])
@login_required
def get_user_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    total_users = User.query.count()
    today_users = User.query.filter(User.created_at >= today_start).count()
    week_users = User.query.filter(User.created_at >= week_start).count()
    month_users = User.query.filter(User.created_at >= month_start).count()
    
    period_users = User.query.filter(
        User.created_at >= start,
        User.created_at < end
    ).count()
    
    total_teachers = TeacherProfile.query.count()
    verified_teachers = TeacherProfile.query.filter(
        TeacherProfile.is_verified == True
    ).count()
    
    active_users = User.query.filter(
        User.last_login_at >= week_start
    ).count()
    
    period_roles = {
        'customer': 0,
        'teacher': 0
    }
    period_users_query = User.query.filter(
        User.created_at >= start,
        User.created_at < end
    ).all()
    
    for user in period_users_query:
        if 'teacher' in user.roles:
            period_roles['teacher'] += 1
        else:
            period_roles['customer'] += 1
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            day_users = User.query.filter(
                User.created_at >= current,
                User.created_at < next_day
            ).count()
            
            day_active = User.query.filter(
                User.last_login_at >= current,
                User.last_login_at < next_day
            ).count()
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'new_users': day_users,
                'active_users': day_active
            })
            current = next_day
    
    return jsonify(success(data={
        'total': total_users,
        'today': today_users,
        'week': week_users,
        'month': month_users,
        'period_total': period_users,
        'teachers': {
            'total': total_teachers,
            'verified': verified_teachers
        },
        'active_users': active_users,
        'period_roles': period_roles,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_detail(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    user_dict = user.to_dict()
    
    teacher_profile = TeacherProfile.query.filter_by(user_id=user.id).first()
    if teacher_profile:
        user_dict['teacher_info'] = {
            'id': teacher_profile.id,
            'real_name': teacher_profile.real_name,
            'rating': teacher_profile.rating,
            'is_verified': teacher_profile.is_verified,
            'follower_count': teacher_profile.follower_count,
            'total_orders': Order.query.filter_by(teacher_id=user.id, status='completed').count(),
            'total_products': Product.query.filter_by(teacher_id=teacher_profile.id, status='active').count()
        }
    
    user_dict['order_count'] = Order.query.filter_by(user_id=user.id).count()
    user_dict['review_count'] = Review.query.filter_by(user_id=user.id).count()
    user_dict['like_count'] = Like.query.filter_by(user_id=user.id).count()
    
    return jsonify(success(data=user_dict))

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'username' in data:
        existing = User.query.filter(
            User.username == data['username'],
            User.id != user_id
        ).first()
        if existing:
            return jsonify(error(code=ResponseCode.USER_EXISTS, msg='用户名已存在')), 400
        user.username = data['username']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    if 'gender' in data:
        user.gender = data['gender']
    if 'bio' in data:
        user.bio = data['bio']
    if 'current_role' in data:
        user.current_role = data['current_role']
    if 'status' in data:
        user.status = data['status']
    
    try:
        db.session.commit()
        return jsonify(success(data=user.to_dict(), msg='更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/users/stats/export', methods=['GET'])
@login_required
def export_user_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    users = User.query.filter(
        User.created_at >= start,
        User.created_at < end
    ).order_by(User.created_at.desc()).all()
    
    headers = ['ID', '用户名', '昵称', '手机号', '邮箱', '角色', '注册时间', '最后登录时间']
    data = []
    
    for user in users:
        data.append([
            user.id,
            user.username or '',
            user.nickname or '',
            user.phone or '',
            user.email or '',
            '老师' if 'teacher' in user.roles else '普通用户',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
            user.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_at else ''
        ])
    
    csv_content = generate_csv(data, headers, 'user_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'user_stats_{datetime.now().strftime("%Y%m%d")}.csv',
        'total': len(data)
    }))

@admin_bp.route('/teachers/stats', methods=['GET'])
@login_required
def get_teacher_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    total_teachers = TeacherProfile.query.count()
    verified_teachers = TeacherProfile.query.filter_by(is_verified=True).count()
    new_teachers = TeacherProfile.query.filter(
        TeacherProfile.created_at >= start,
        TeacherProfile.created_at < end
    ).count()
    
    teachers = TeacherProfile.query.all()
    teacher_ranking = []
    
    for teacher in teachers:
        teacher_user = User.query.get(teacher.user_id)
        if not teacher_user:
            continue
        
        period_orders = Order.query.filter(
            Order.teacher_id == teacher_user.id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.status != 'deleted'
        ).count()
        
        period_completed = Order.query.filter(
            Order.teacher_id == teacher_user.id,
            Order.complete_time >= start,
            Order.complete_time < end,
            Order.status == 'completed'
        ).all()
        period_revenue = sum(o.pay_amount for o in period_completed) if period_completed else 0
        
        period_products = Product.query.filter(
            Product.teacher_id == teacher.id,
            Product.created_at >= start,
            Product.created_at < end
        ).count()
        
        total_products = Product.query.filter_by(teacher_id=teacher.id, status='active').count()
        total_orders = Order.query.filter_by(teacher_id=teacher_user.id, status='completed').count()
        
        teacher_ranking.append({
            'teacher_id': teacher.id,
            'user_id': teacher.user_id,
            'nickname': teacher_user.nickname or teacher_user.username,
            'avatar': teacher_user.avatar,
            'real_name': teacher.real_name,
            'rating': teacher.rating,
            'is_verified': teacher.is_verified,
            'follower_count': teacher.follower_count,
            'period_orders': period_orders,
            'period_revenue': round(period_revenue, 2),
            'period_products': period_products,
            'total_products': total_products,
            'total_orders': total_orders
        })
    
    teacher_ranking.sort(key=lambda x: x['period_orders'], reverse=True)
    
    for i, t in enumerate(teacher_ranking):
        t['rank'] = i + 1
    
    total_period_orders = sum(t['period_orders'] for t in teacher_ranking)
    total_period_revenue = sum(t['period_revenue'] for t in teacher_ranking)
    total_period_products = sum(t['period_products'] for t in teacher_ranking)
    
    return jsonify(success(data={
        'summary': {
            'total_teachers': total_teachers,
            'verified_teachers': verified_teachers,
            'new_teachers': new_teachers,
            'period_orders': total_period_orders,
            'period_revenue': round(total_period_revenue, 2),
            'period_products': total_period_products
        },
        'ranking': teacher_ranking[:50],
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))

@admin_bp.route('/teachers/stats/export', methods=['GET'])
@login_required
def export_teacher_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    teachers = TeacherProfile.query.all()
    
    headers = ['排名', '老师ID', '昵称', '真实姓名', '是否认证', '评分', '粉丝数', '周期订单数', '周期收入', '周期作品数', '总作品数', '总订单数']
    data = []
    
    teacher_list = []
    for teacher in teachers:
        teacher_user = User.query.get(teacher.user_id)
        if not teacher_user:
            continue
        
        period_orders = Order.query.filter(
            Order.teacher_id == teacher_user.id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.status != 'deleted'
        ).count()
        
        period_completed = Order.query.filter(
            Order.teacher_id == teacher_user.id,
            Order.complete_time >= start,
            Order.complete_time < end,
            Order.status == 'completed'
        ).all()
        period_revenue = sum(o.pay_amount for o in period_completed) if period_completed else 0
        
        period_products = Product.query.filter(
            Product.teacher_id == teacher.id,
            Product.created_at >= start,
            Product.created_at < end
        ).count()
        
        total_products = Product.query.filter_by(teacher_id=teacher.id, status='active').count()
        total_orders = Order.query.filter_by(teacher_id=teacher_user.id, status='completed').count()
        
        teacher_list.append({
            'teacher': teacher,
            'user': teacher_user,
            'period_orders': period_orders,
            'period_revenue': period_revenue,
            'period_products': period_products,
            'total_products': total_products,
            'total_orders': total_orders
        })
    
    teacher_list.sort(key=lambda x: x['period_orders'], reverse=True)
    
    for i, t in enumerate(teacher_list):
        data.append([
            i + 1,
            t['teacher'].id,
            t['user'].nickname or t['user'].username,
            t['teacher'].real_name or '',
            '是' if t['teacher'].is_verified else '否',
            t['teacher'].rating or 0,
            t['teacher'].follower_count or 0,
            t['period_orders'],
            round(t['period_revenue'], 2),
            t['period_products'],
            t['total_products'],
            t['total_orders']
        ])
    
    csv_content = generate_csv(data, headers, 'teacher_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'teacher_stats_{datetime.now().strftime("%Y%m%d")}.csv',
        'total': len(data)
    }))

@admin_bp.route('/products/stats', methods=['GET'])
@login_required
def get_product_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    total_products = Product.query.filter(Product.status == 'active').count()
    inactive_products = Product.query.filter(Product.status != 'active').count()
    
    period_products = Product.query.filter(
        Product.created_at >= start,
        Product.created_at < end
    ).count()
    
    total_likes = Like.query.count()
    total_reviews = Review.query.count()
    
    categories = Category.query.filter(Category.status == 'active').all()
    category_stats = []
    
    for cat in categories:
        product_count = Product.query.filter(
            Product.category_id == cat.id,
            Product.status == 'active'
        ).count()
        
        period_count = Product.query.filter(
            Product.category_id == cat.id,
            Product.created_at >= start,
            Product.created_at < end
        ).count()
        
        category_products = Product.query.filter_by(category_id=cat.id, status='active').all()
        total_cat_likes = 0
        total_cat_reviews = 0
        
        for p in category_products:
            total_cat_likes += Like.query.filter_by(product_id=p.id).count()
            total_cat_reviews += Review.query.filter_by(product_id=p.id).count()
        
        category_stats.append({
            'id': cat.id,
            'name': cat.name,
            'product_count': product_count,
            'period_count': period_count,
            'total_likes': total_cat_likes,
            'total_reviews': total_cat_reviews
        })
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            
            day_products = Product.query.filter(
                Product.created_at >= current,
                Product.created_at < next_day
            ).count()
            
            day_sales = 0
            day_orders = Order.query.filter(
                Order.created_at >= current,
                Order.created_at < next_day,
                Order.status != 'deleted'
            ).all()
            
            for order in day_orders:
                items = OrderItem.query.filter_by(order_id=order.id).all()
                day_sales += len(items)
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'new_products': day_products,
                'sales_volume': day_sales
            })
            current = next_day
    
    return jsonify(success(data={
        'summary': {
            'total_active': total_products,
            'total_inactive': inactive_products,
            'period_new': period_products,
            'total_likes': total_likes,
            'total_reviews': total_reviews
        },
        'categories': category_stats,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))

@admin_bp.route('/products/stats/export', methods=['GET'])
@login_required
def export_product_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    
    headers = ['ID', '商品名称', '分类', '价格', '库存', '销量', '评分', '状态', '点赞数', '评价数', '创建时间']
    data = []
    
    for product in products:
        category = Category.query.get(product.category_id)
        likes = Like.query.filter_by(product_id=product.id).count()
        reviews = Review.query.filter_by(product_id=product.id).count()
        
        data.append([
            product.id,
            product.title,
            category.name if category else '未分类',
            product.price or 0,
            product.stock or 0,
            product.sales_count or 0,
            product.rating or 0,
            '上架' if product.status == 'active' else '下架',
            likes,
            reviews,
            product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
        ])
    
    csv_content = generate_csv(data, headers, 'product_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'product_stats_{datetime.now().strftime("%Y%m%d")}.csv',
        'total': len(data)
    }))

@admin_bp.route('/products/list', methods=['GET'])
@login_required
def get_products_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    product_id = request.args.get('product_id', '')
    teacher_id = request.args.get('teacher_id', '')
    category_id = request.args.get('category', type=int)
    verify_status = request.args.get('verify_status', '')
    is_online = request.args.get('is_online', type=bool)
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query
    
    query = query.filter(Product.status != 'inactive')
    
    if keyword:
        query = query.filter(
            db.or_(
                Product.title.contains(keyword),
                Product.description.contains(keyword)
            )
        )
    
    if product_id:
        try:
            query = query.filter(Product.id == int(product_id))
        except ValueError:
            pass
    
    if teacher_id:
        try:
            query = query.filter(Product.teacher_id == int(teacher_id))
        except ValueError:
            pass
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if verify_status:
        query = query.filter(Product.verify_status == verify_status)
    
    if is_online is not None:
        query = query.filter(Product.is_online == is_online)
    
    if status:
        query = query.filter(Product.status == status)
    
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'sales':
        query = query.order_by(Product.sales_count.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    products = []
    for p in pagination.items:
        product_dict = p.to_dict()
        category = Category.query.get(p.category_id)
        if category:
            product_dict['category_name'] = category.name
        
        product_dict['likes_count'] = Like.query.filter_by(product_id=p.id).count()
        product_dict['reviews_count'] = Review.query.filter_by(product_id=p.id).count()
        
        if p.teacher_profile and p.teacher_profile.user:
            product_dict['teacher_name'] = p.teacher_profile.user.nickname or p.teacher_profile.user.username
        
        products.append(product_dict)
    
    return jsonify(success(data={
        'list': products,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))

@admin_bp.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product_detail(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='商品不存在')), 404
    
    product_dict = product.to_dict()
    
    category = Category.query.get(product.category_id)
    if category:
        product_dict['category_name'] = category.name
    
    product_dict['likes_count'] = Like.query.filter_by(product_id=product.id).count()
    product_dict['reviews_count'] = Review.query.filter_by(product_id=product.id).count()
    
    reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).limit(10).all()
    product_dict['recent_reviews'] = [r.to_dict() for r in reviews]
    
    return jsonify(success(data=product_dict))

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='商品不存在')), 404
    
    data = request.get_json()
    
    if 'title' in data:
        product.title = data['title']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'original_price' in data:
        product.original_price = data['original_price']
    if 'stock' in data:
        product.stock = data['stock']
    if 'status' in data:
        product.status = data['status']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'cover_image' in data:
        product.cover_image = data['cover_image']
    if 'images' in data:
        product.images = data['images']
    if 'rating' in data:
        product.rating = data['rating']
    
    try:
        db.session.commit()
        return jsonify(success(data=product.to_dict(), msg='更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/orders/stats', methods=['GET'])
@login_required
def get_order_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    statuses = ['pending', 'pending_accept', 'accepted', 'in_progress', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'rejected']
    status_counts = {}
    for status in statuses:
        status_counts[status] = Order.query.filter(Order.status == status).count()
    
    period_status_counts = {}
    for status in statuses:
        period_status_counts[status] = Order.query.filter(
            Order.status == status,
            Order.created_at >= start,
            Order.created_at < end
        ).count()
    
    period_orders = Order.query.filter(
        Order.created_at >= start,
        Order.created_at < end,
        Order.status != 'deleted'
    ).count()
    
    period_completed = Order.query.filter(
        Order.status == 'completed',
        Order.complete_time >= start,
        Order.complete_time < end
    ).all()
    period_revenue = sum(o.pay_amount for o in period_completed) if period_completed else 0
    
    period_cancelled = Order.query.filter(
        Order.status == 'cancelled',
        Order.created_at >= start,
        Order.created_at < end
    ).count()
    
    period_rejected = Order.query.filter(
        Order.status == 'rejected',
        Order.created_at >= start,
        Order.created_at < end
    ).count()
    
    total_orders = Order.query.filter(Order.status != 'deleted').count()
    completed_orders = Order.query.filter(Order.status == 'completed').all()
    total_revenue = sum(o.pay_amount for o in completed_orders) if completed_orders else 0
    
    total_cancelled = status_counts.get('cancelled', 0) + status_counts.get('rejected', 0)
    refund_rate = (period_cancelled + period_rejected) / period_orders * 100 if period_orders > 0 else 0
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            
            day_orders = Order.query.filter(
                Order.created_at >= current,
                Order.created_at < next_day,
                Order.status != 'deleted'
            ).count()
            
            day_completed = Order.query.filter(
                Order.status == 'completed',
                Order.complete_time >= current,
                Order.complete_time < next_day
            ).all()
            day_revenue = sum(o.pay_amount for o in day_completed) if day_completed else 0
            
            day_cancelled = Order.query.filter(
                Order.status.in_(['cancelled', 'rejected']),
                Order.created_at >= current,
                Order.created_at < next_day
            ).count()
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'order_count': day_orders,
                'revenue': round(day_revenue, 2),
                'cancelled_count': day_cancelled
            })
            current = next_day
    
    return jsonify(success(data={
        'summary': {
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'total_cancelled': total_cancelled,
            'period_orders': period_orders,
            'period_revenue': round(period_revenue, 2),
            'period_cancelled': period_cancelled + period_rejected,
            'refund_rate': round(refund_rate, 2)
        },
        'status_counts': status_counts,
        'period_status_counts': period_status_counts,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))

@admin_bp.route('/orders/stats/export', methods=['GET'])
@login_required
def export_order_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    orders = Order.query.filter(
        Order.created_at >= start,
        Order.created_at < end
    ).order_by(Order.created_at.desc()).all()
    
    headers = ['订单号', '用户', '订单状态', '商品金额', '优惠金额', '运费', '实付金额', '支付方式', '下单时间', '支付时间']
    data = []
    
    for order in orders:
        customer = User.query.get(order.user_id)
        data.append([
            order.id,
            customer.nickname or customer.username if customer else '',
            STATUS_NAMES.get(order.status, order.status),
            order.total_amount or 0,
            order.discount_amount or 0,
            order.shipping_fee or 0,
            order.pay_amount or 0,
            order.pay_method_name or '',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
            order.pay_time.strftime('%Y-%m-%d %H:%M:%S') if order.pay_time else ''
        ])
    
    csv_content = generate_csv(data, headers, 'order_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'order_stats_{datetime.now().strftime("%Y%m%d")}.csv',
        'total': len(data)
    }))

@admin_bp.route('/orders/list', methods=['GET'])
@login_required
def get_orders_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    user_id = request.args.get('user_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    is_abnormal = request.args.get('is_abnormal', type=bool)
    refund_status = request.args.get('refund_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort = request.args.get('sort', 'newest')
    
    query = Order.query.filter(Order.status != 'deleted')
    
    if keyword:
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                Order.id.contains(keyword),
                Order.user_id.in_(user_ids)
            )
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    if teacher_id:
        query = query.filter(Order.teacher_id == teacher_id)
    
    if is_abnormal is not None:
        query = query.filter(Order.is_abnormal == is_abnormal)
    
    if refund_status:
        query = query.filter(Order.refund_status == refund_status)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end)
        except ValueError:
            pass
    
    if sort == 'newest':
        query = query.order_by(Order.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Order.created_at.asc())
    elif sort == 'amount_desc':
        query = query.order_by(Order.pay_amount.desc())
    elif sort == 'amount_asc':
        query = query.order_by(Order.pay_amount.asc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    orders = []
    for order in pagination.items:
        order_dict = order.to_dict()
        
        customer = User.query.get(order.user_id)
        if customer:
            order_dict['customer_nickname'] = customer.nickname or customer.username
            order_dict['customer_avatar'] = customer.avatar
        
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                order_dict['teacher_nickname'] = teacher.nickname or teacher.username
                order_dict['teacher_avatar'] = teacher.avatar
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        order_dict['items'] = [item.to_dict() for item in items]
        order_dict['item_count'] = len(items)
        
        orders.append(order_dict)
    
    return jsonify(success(data={
        'list': orders,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'status_names': STATUS_NAMES,
        'refund_status_names': REFUND_STATUS_NAMES,
        'abnormal_reasons': ABNORMAL_REASONS
    }))

@admin_bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order_detail(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    order_dict = order.to_dict()
    
    customer = User.query.get(order.user_id)
    if customer:
        order_dict['customer'] = customer.to_dict()
    
    if order.teacher_id:
        teacher = User.query.get(order.teacher_id)
        if teacher:
            order_dict['teacher'] = teacher.to_dict()
    
    items = OrderItem.query.filter_by(order_id=order.id).all()
    order_dict['items'] = [item.to_dict() for item in items]
    
    review = Review.query.filter_by(order_id=order.id).first()
    if review:
        order_dict['review'] = review.to_dict()
    
    return jsonify(success(data=order_dict))

@admin_bp.route('/orders/<order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    new_status = data.get('status')
    reason = data.get('reason', '')
    
    if not new_status:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请提供新状态')), 400
    
    if new_status not in STATUS_NAMES:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的订单状态')), 400
    
    if new_status == 'cancelled':
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='取消订单理由至少需要10个字符')), 400
    
    old_status = order.status
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.status = new_status
    
    if new_status == 'completed':
        order.complete_time = datetime.utcnow()
    elif new_status == 'cancelled':
        order.cancel_time = datetime.utcnow()
        order.cancel_reason = reason
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action=f'status_change_{old_status}_to_{new_status}',
            reason=reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=order.to_dict(), msg=f'订单状态已从{STATUS_NAMES.get(old_status, old_status)}更新为{STATUS_NAMES.get(new_status, new_status)}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/abnormal', methods=['POST'])
@login_required
def mark_order_abnormal(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    reason = data.get('reason', '')
    reason_code = data.get('reason_code', 'other')
    
    if not reason or len(reason.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='异常订单理由至少需要10个字符')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.is_abnormal = True
    order.abnormal_reason = reason
    order.abnormal_reason_code = reason_code
    order.abnormal_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='mark_abnormal',
            reason=reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=order.to_dict(), msg='订单已标记为异常'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/resolve-abnormal', methods=['POST'])
@login_required
def resolve_abnormal_order(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    if not order.is_abnormal:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单不是异常订单')), 400
    
    data = request.get_json()
    resolution = data.get('resolution', '')
    action = data.get('action', '')
    
    if not resolution or len(resolution.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='处理方案至少需要10个字符')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.is_abnormal = False
    order.abnormal_resolved_at = datetime.utcnow()
    order.abnormal_resolved_by = admin_id
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action=f'resolve_abnormal_{action}',
            reason=resolution,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=order.to_dict(), msg='异常订单已处理'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/update-logistics', methods=['PUT'])
@login_required
def update_order_logistics(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    shipping_company = data.get('shipping_company', '')
    tracking_number = data.get('tracking_number', '')
    reason = data.get('reason', '')
    
    if not shipping_company or not tracking_number:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请提供快递公司和物流单号')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.shipping_company = shipping_company
    order.tracking_number = tracking_number
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='update_logistics',
            reason=reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=order.to_dict(), msg='物流信息已更新'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/refund', methods=['POST'])
@login_required
def process_order_refund(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    refund_status = data.get('refund_status', '')
    refund_amount = data.get('refund_amount', order.pay_amount)
    reason = data.get('reason', '')
    
    valid_refund_statuses = ['pending', 'approved', 'rejected', 'completed']
    if refund_status not in valid_refund_statuses:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的退款状态')), 400
    
    if refund_status in ['approved', 'rejected']:
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='退款处理理由至少需要10个字符')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.refund_status = refund_status
    order.refund_amount = refund_amount
    order.refund_reason = reason
    order.refund_approved_by = admin_id
    order.refund_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action=f'refund_{refund_status}',
            reason=reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=order.to_dict(), msg='退款状态已更新'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/export', methods=['GET'])
@login_required
def export_orders():
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    user_id = request.args.get('user_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    is_abnormal = request.args.get('is_abnormal', type=bool)
    refund_status = request.args.get('refund_status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    export_fields = request.args.get('fields', 'id,customer_nickname,status,pay_amount,create_time')
    fields = export_fields.split(',') if export_fields else []
    
    query = Order.query.filter(Order.status != 'deleted')
    
    if keyword:
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                Order.id.contains(keyword),
                Order.user_id.in_(user_ids)
            )
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    if teacher_id:
        query = query.filter(Order.teacher_id == teacher_id)
    
    if is_abnormal is not None:
        query = query.filter(Order.is_abnormal == is_abnormal)
    
    if refund_status:
        query = query.filter(Order.refund_status == refund_status)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end)
        except ValueError:
            pass
    
    query = query.order_by(Order.created_at.desc())
    orders = query.all()
    
    all_available_fields = {
        'id': '订单号',
        'customer_nickname': '用户昵称',
        'teacher_nickname': '老师昵称',
        'status_name': '订单状态',
        'pay_amount': '实付金额',
        'total_amount': '商品金额',
        'discount_amount': '优惠金额',
        'shipping_fee': '运费',
        'pay_method_name': '支付方式',
        'is_abnormal': '是否异常',
        'refund_status_name': '退款状态',
        'refund_amount': '退款金额',
        'create_time': '下单时间',
        'pay_time': '支付时间',
        'ship_time': '发货时间',
        'complete_time': '完成时间'
    }
    
    selected_fields = []
    headers = []
    for field in fields:
        if field in all_available_fields:
            selected_fields.append(field)
            headers.append(all_available_fields[field])
    
    if not selected_fields:
        selected_fields = ['id', 'customer_nickname', 'status_name', 'pay_amount', 'create_time']
        headers = ['订单号', '用户昵称', '订单状态', '实付金额', '下单时间']
    
    data = []
    for order in orders:
        order_dict = order.to_dict()
        
        customer = User.query.get(order.user_id)
        if customer:
            order_dict['customer_nickname'] = customer.nickname or customer.username
        
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                order_dict['teacher_nickname'] = teacher.nickname or teacher.username
        
        row = []
        for field in selected_fields:
            if field == 'is_abnormal':
                value = '是' if order_dict.get(field) else '否'
            else:
                value = order_dict.get(field, '')
            row.append(value)
        data.append(row)
    
    csv_content = generate_csv(data, headers, 'orders.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'orders_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
        'total': len(data),
        'available_fields': all_available_fields
    }))

@admin_bp.route('/activities/stats', methods=['GET'])
@login_required
def get_activity_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    total_activities = Activity.query.filter(Activity.status == 'active').count()
    
    period_activities = Activity.query.filter(
        Activity.created_at >= start,
        Activity.created_at < end
    ).count()
    
    total_registrations = ActivityRegistration.query.count()
    
    period_registrations = ActivityRegistration.query.filter(
        ActivityRegistration.created_at >= start,
        ActivityRegistration.created_at < end
    ).count()
    
    total_views = db.session.query(db.func.sum(Activity.view_count)).scalar() or 0
    
    craft_type_stats = {}
    for craft_type in CRAFT_TYPES:
        craft_type_stats[craft_type] = Activity.query.filter(
            Activity.craft_type == craft_type,
            Activity.status == 'active'
        ).count()
    
    activity_type_stats = {}
    for act_type in ACTIVITY_TYPES:
        activity_type_stats[act_type] = Activity.query.filter(
            Activity.activity_type == act_type,
            Activity.status == 'active'
        ).count()
    
    top_activities = Activity.query.filter(
        Activity.status == 'active'
    ).order_by(
        Activity.registration_count.desc(),
        Activity.view_count.desc()
    ).limit(10).all()
    
    top_list = []
    for act in top_activities:
        teacher = User.query.get(act.teacher_id)
        top_list.append({
            'id': act.id,
            'title': act.title,
            'cover_image': act.cover_image,
            'craft_type': act.craft_type,
            'activity_type': act.activity_type,
            'price': act.price,
            'view_count': act.view_count,
            'registration_count': act.registration_count,
            'max_participants': act.max_participants,
            'teacher_name': teacher.nickname or teacher.username if teacher else '',
            'start_time': act.start_time.strftime('%Y-%m-%d %H:%M') if act.start_time else None
        })
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            
            day_activities = Activity.query.filter(
                Activity.created_at >= current,
                Activity.created_at < next_day
            ).count()
            
            day_registrations = ActivityRegistration.query.filter(
                ActivityRegistration.created_at >= current,
                ActivityRegistration.created_at < next_day
            ).count()
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'new_activities': day_activities,
                'registrations': day_registrations
            })
            current = next_day
    
    return jsonify(success(data={
        'summary': {
            'total_activities': total_activities,
            'period_activities': period_activities,
            'total_registrations': total_registrations,
            'period_registrations': period_registrations,
            'total_views': total_views
        },
        'craft_types': craft_type_stats,
        'activity_types': activity_type_stats,
        'top_activities': top_list,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))

@admin_bp.route('/activities/stats/export', methods=['GET'])
@login_required
def export_activity_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    activities = Activity.query.filter(
        Activity.created_at >= start,
        Activity.created_at < end
    ).order_by(Activity.created_at.desc()).all()
    
    headers = ['ID', '活动名称', '手工类型', '活动类型', '价格', '浏览量', '报名人数', '最大人数', '状态', '开始时间', '结束时间', '创建时间']
    data = []
    
    for act in activities:
        teacher = User.query.get(act.teacher_id)
        data.append([
            act.id,
            act.title,
            act.craft_type or '',
            act.activity_type or '',
            act.price or 0,
            act.view_count or 0,
            act.registration_count or 0,
            act.max_participants or 0,
            '上架' if act.status == 'active' else '下架',
            act.start_time.strftime('%Y-%m-%d %H:%M') if act.start_time else '',
            act.end_time.strftime('%Y-%m-%d %H:%M') if act.end_time else '',
            act.created_at.strftime('%Y-%m-%d %H:%M:%S') if act.created_at else ''
        ])
    
    csv_content = generate_csv(data, headers, 'activity_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'activity_stats_{datetime.now().strftime("%Y%m%d")}.csv',
        'total': len(data)
    }))

@admin_bp.route('/activities/list', methods=['GET'])
@login_required
def get_activities_list():
    from datetime import datetime
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    craft_type = request.args.get('craft_type', '')
    activity_type = request.args.get('activity_type', '')
    publisher_type = request.args.get('publisher_type', '')
    computed_status = request.args.get('computed_status', '')
    sort = request.args.get('sort', 'newest')
    
    query = Activity.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Activity.title.contains(keyword),
                Activity.description.contains(keyword)
            )
        )
    
    if status:
        query = query.filter(Activity.status == status)
    
    if craft_type:
        query = query.filter(Activity.craft_type == craft_type)
    
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    
    if publisher_type == 'official':
        query = query.filter(Activity.is_official == True)
    elif publisher_type == 'teacher':
        query = query.filter(Activity.is_official == False)
    
    now = datetime.utcnow()
    if computed_status == 'pending_review':
        query = query.filter(Activity.verify_status == 'pending')
    elif computed_status == 'not_started':
        query = query.filter(Activity.verify_status == 'approved').filter(
            db.or_(
                Activity.start_time == None,
                Activity.start_time > now
            )
        )
    elif computed_status == 'in_progress':
        query = query.filter(Activity.verify_status == 'approved').filter(
            Activity.start_time <= now
        ).filter(
            db.or_(
                Activity.end_time == None,
                Activity.end_time >= now
            )
        )
    elif computed_status == 'ended':
        query = query.filter(Activity.verify_status == 'approved').filter(
            Activity.end_time < now
        )
    
    if sort == 'newest':
        query = query.order_by(Activity.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Activity.created_at.asc())
    elif sort == 'popular':
        query = query.order_by(Activity.registration_count.desc())
    elif sort == 'views':
        query = query.order_by(Activity.view_count.desc())
    elif sort == 'price_asc':
        query = query.order_by(Activity.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Activity.price.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    activities = []
    for act in pagination.items:
        act_dict = act.to_dict()
        
        teacher = User.query.get(act.teacher_id)
        if teacher:
            act_dict['teacher_name'] = teacher.nickname or teacher.username
            act_dict['teacher_avatar'] = teacher.avatar
        
        activities.append(act_dict)
    
    return jsonify(success(data={
        'list': activities,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))

@admin_bp.route('/activities/<int:activity_id>', methods=['GET'])
@login_required
def get_activity_detail(activity_id):
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='活动不存在')), 404
    
    act_dict = activity.to_dict()
    
    teacher = User.query.get(activity.teacher_id)
    if teacher:
        act_dict['teacher'] = teacher.to_dict()
    
    registrations = ActivityRegistration.query.filter_by(activity_id=activity.id).order_by(ActivityRegistration.created_at.desc()).all()
    act_dict['registrations'] = []
    
    for reg in registrations:
        reg_dict = reg.to_dict()
        user = User.query.get(reg.user_id)
        if user:
            reg_dict['user_nickname'] = user.nickname or user.username
            reg_dict['user_avatar'] = user.avatar
        act_dict['registrations'].append(reg_dict)
    
    return jsonify(success(data=act_dict))

@admin_bp.route('/activities/<int:activity_id>', methods=['PUT'])
@login_required
def update_activity(activity_id):
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='活动不存在')), 404
    
    data = request.get_json()
    
    if 'title' in data:
        activity.title = data['title']
    if 'description' in data:
        activity.description = data['description']
    if 'price' in data:
        activity.price = data['price']
    if 'original_price' in data:
        activity.original_price = data['original_price']
    if 'max_participants' in data:
        activity.max_participants = data['max_participants']
    if 'status' in data:
        activity.status = data['status']
    if 'craft_type' in data:
        activity.craft_type = data['craft_type']
    if 'activity_type' in data:
        activity.activity_type = data['activity_type']
    if 'location' in data:
        activity.location = data['location']
    if 'address' in data:
        activity.address = data['address']
    if 'city' in data:
        activity.city = data['city']
    if 'cover_image' in data:
        activity.cover_image = data['cover_image']
    if 'images' in data:
        activity.images = data['images']
    if 'tags' in data:
        activity.tags = data['tags']
    
    try:
        db.session.commit()
        return jsonify(success(data=activity.to_dict(), msg='更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/reviews/list', methods=['GET'])
@login_required
def get_reviews_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    rating = request.args.get('rating', type=float)
    product_id = request.args.get('product_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    order_id = request.args.get('order_id', '')
    user_id = request.args.get('user_id', type=int)
    is_read = request.args.get('is_read', type=bool)
    has_reply = request.args.get('has_reply', type=bool)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort = request.args.get('sort', 'newest')
    
    query = Review.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Review.content.contains(keyword),
                Review.reply_content.contains(keyword)
            )
        )
    
    if rating is not None:
        query = query.filter(Review.overall_rating == rating)
    
    if product_id:
        query = query.filter(Review.product_id == product_id)
    
    if teacher_id:
        query = query.filter(Review.teacher_id == teacher_id)
    
    if order_id:
        query = query.filter(Review.order_id == order_id)
    
    if user_id:
        query = query.filter(Review.user_id == user_id)
    
    if is_read is not None:
        query = query.filter(Review.is_read == is_read)
    
    if has_reply is not None:
        if has_reply:
            query = query.filter(Review.reply_content.isnot(None))
        else:
            query = query.filter(Review.reply_content.is_(None))
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Review.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Review.created_at < end)
        except ValueError:
            pass
    
    if sort == 'newest':
        query = query.order_by(Review.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Review.created_at.asc())
    elif sort == 'rating_desc':
        query = query.order_by(Review.overall_rating.desc())
    elif sort == 'rating_asc':
        query = query.order_by(Review.overall_rating.asc())
    elif sort == 'unread_first':
        query = query.order_by(Review.is_read.asc(), Review.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    reviews = []
    for review in pagination.items:
        rev_dict = review.to_dict()
        
        user = User.query.get(review.user_id)
        if user:
            rev_dict['user_nickname'] = user.nickname or user.username
            rev_dict['user_avatar'] = user.avatar
        
        product = Product.query.get(review.product_id)
        if product:
            rev_dict['product_title'] = product.title
            rev_dict['product_image'] = product.cover_image
        
        order = Order.query.get(review.order_id)
        if order:
            rev_dict['order_id'] = order.id
            rev_dict['order_status'] = order.status
            rev_dict['order_status_name'] = order.status_name
        
        teacher = User.query.get(review.teacher_id)
        if teacher:
            rev_dict['teacher_nickname'] = teacher.nickname or teacher.username
        
        reviews.append(rev_dict)
    
    return jsonify(success(data={
        'list': reviews,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/reviews/<int:review_id>/mark-read', methods=['POST'])
@login_required
def mark_review_read(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='评价不存在')), 404
    
    review.is_read = True
    review.read_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=review.to_dict(), msg='已标记为已读'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    admin_id = g.get('user_id', 1)
    review = Review.query.get(review_id)
    if not review:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='评价不存在')), 404
    
    old_review_data = json.dumps(review.to_dict(), ensure_ascii=False)
    
    review.is_hidden = True
    review.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='review',
            target_id=review_id,
            action='delete_malicious',
            reason='管理员删除恶意评价',
            before_data=old_review_data,
            after_data=json.dumps(review.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=review.to_dict(), msg='评价已删除'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/reviews/<int:review_id>/reply', methods=['POST', 'PUT'])
@login_required
def admin_reply_review(review_id):
    admin_id = g.get('user_id', 1)
    review = Review.query.get(review_id)
    if not review:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='评价不存在')), 404
    
    data = request.get_json()
    reply_content = data.get('content', '')
    is_undo = data.get('is_undo', False)
    
    if is_undo:
        if not review.reply_content:
            return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该评价暂无回复，无法撤销')), 400
        
        old_reply_data = json.dumps(review.to_dict(), ensure_ascii=False)
        
        review.reply_content = None
        review.reply_time = None
        review.reply_role = None
        review.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            audit_log = AuditLog(
                admin_id=admin_id,
                target_type='review',
                target_id=review_id,
                action='undo_reply',
                reason='管理员撤销回复',
                before_data=old_reply_data,
                after_data=json.dumps(review.to_dict(), ensure_ascii=False)
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify(success(data=review.to_dict(), msg='回复已撤销'))
        except Exception as e:
            db.session.rollback()
            return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500
    
    if not reply_content or len(reply_content.strip()) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='回复内容不能为空')), 400
    
    if len(reply_content) > 200:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='回复内容不能超过200个字符')), 400
    
    old_review_data = json.dumps(review.to_dict(), ensure_ascii=False)
    
    review.reply_content = reply_content
    review.reply_time = datetime.utcnow()
    review.reply_role = 'admin'
    review.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='review',
            target_id=review_id,
            action='admin_reply',
            reason=f'管理员代老师回复: {reply_content[:50]}...' if len(reply_content) > 50 else f'管理员代老师回复: {reply_content}',
            before_data=old_review_data,
            after_data=json.dumps(review.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify(success(data=review.to_dict(), msg='回复成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500

@admin_bp.route('/categories/list', methods=['GET'])
@login_required
def get_categories_list():
    categories = Category.query.filter(Category.status == 'active').order_by(Category.sort.asc()).all()
    
    category_list = []
    for cat in categories:
        cat_dict = cat.to_dict()
        cat_dict['product_count'] = Product.query.filter_by(category_id=cat.id, status='active').count()
        category_list.append(cat_dict)
    
    return jsonify(success(data=category_list))

@admin_bp.route('/users/roles/<int:user_id>', methods=['PUT'])
@login_required
def update_user_roles(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    roles = data.get('roles', [])
    current_role = data.get('current_role')
    
    if not isinstance(roles, list):
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='roles必须是数组')), 400
    
    user.roles = roles
    if current_role:
        user.current_role = current_role
    
    try:
        db.session.commit()
        return jsonify(success(data=user.to_dict(), msg='角色更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 100, type=int)
    status = request.args.get('status', '')
    
    query = Category.query
    
    if status:
        query = query.filter(Category.status == status)
    
    query = query.order_by(Category.sort.asc(), Category.id.asc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    categories = []
    for cat in pagination.items:
        cat_dict = cat.to_dict()
        cat_dict['product_count'] = Product.query.filter_by(category_id=cat.id, status='active').count()
        cat_dict['activity_count'] = Activity.query.filter_by(craft_type=cat.name, status='active').count()
        categories.append(cat_dict)
    
    return jsonify(success(data={
        'list': categories,
        'total': pagination.total,
        'page': page,
        'size': size
    }))

@admin_bp.route('/categories/all', methods=['GET'])
@login_required
def get_all_categories():
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    category_list = [cat.to_dict() for cat in categories]
    return jsonify(success(data=category_list))

@admin_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='分类不存在')), 404
    
    cat_dict = category.to_dict()
    cat_dict['product_count'] = Product.query.filter_by(category_id=category.id, status='active').count()
    cat_dict['activity_count'] = Activity.query.filter_by(craft_type=category.name, status='active').count()
    
    return jsonify(success(data=cat_dict))

@admin_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='分类名称不能为空')), 400
    
    name = data.get('name')
    
    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify(error(code=ResponseCode.DATA_EXISTS, msg='分类名称已存在')), 400
    
    category = Category(
        name=name,
        icon=data.get('icon', ''),
        description=data.get('description', ''),
        sort=data.get('sort', 0),
        status=data.get('status', 'active')
    )
    
    try:
        db.session.add(category)
        db.session.commit()
        return jsonify(success(data=category.to_dict(), msg='分类创建成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'创建失败: {str(e)}')), 500

@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='分类不存在')), 404
    
    data = request.get_json()
    
    if 'name' in data:
        existing = Category.query.filter(
            Category.name == data['name'],
            Category.id != category_id
        ).first()
        if existing:
            return jsonify(error(code=ResponseCode.DATA_EXISTS, msg='分类名称已存在')), 400
        category.name = data['name']
    
    if 'icon' in data:
        category.icon = data['icon']
    if 'description' in data:
        category.description = data['description']
    if 'sort' in data:
        category.sort = data['sort']
    if 'status' in data:
        category.status = data['status']
    
    try:
        db.session.commit()
        return jsonify(success(data=category.to_dict(), msg='分类更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='分类不存在')), 404
    
    product_count = Product.query.filter_by(category_id=category_id, status='active').count()
    if product_count > 0:
        return jsonify(error(code=ResponseCode.DATA_DELETE_FAILED, msg=f'该分类下有{product_count}个作品，无法删除')), 400
    
    activity_count = Activity.query.filter_by(craft_type=category.name, status='active').count()
    if activity_count > 0:
        return jsonify(error(code=ResponseCode.DATA_DELETE_FAILED, msg=f'该分类下有{activity_count}个活动，无法删除')), 400
    
    activity_type_count = ActivityType.query.filter_by(craft_type_id=category_id, status='active').count()
    if activity_type_count > 0:
        return jsonify(error(code=ResponseCode.DATA_DELETE_FAILED, msg=f'该分类下关联了{activity_type_count}个活动类型，无法删除')), 400
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify(success(msg='分类删除成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500

@admin_bp.route('/activity-types', methods=['GET'])
@login_required
def get_activity_types():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 100, type=int)
    status = request.args.get('status', '')
    craft_type_id = request.args.get('craft_type_id', type=int)
    
    query = ActivityType.query
    
    if status:
        query = query.filter(ActivityType.status == status)
    if craft_type_id:
        query = query.filter(ActivityType.craft_type_id == craft_type_id)
    
    query = query.order_by(ActivityType.sort.asc(), ActivityType.id.asc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    activity_types = []
    for at in pagination.items:
        at_dict = at.to_dict()
        at_dict['activity_count'] = Activity.query.filter_by(activity_type=at.name, status='active').count()
        activity_types.append(at_dict)
    
    return jsonify(success(data={
        'list': activity_types,
        'total': pagination.total,
        'page': page,
        'size': size
    }))

@admin_bp.route('/activity-types/all', methods=['GET'])
@login_required
def get_all_activity_types():
    craft_type_id = request.args.get('craft_type_id', type=int)
    
    query = ActivityType.query.filter_by(status='active')
    if craft_type_id:
        query = query.filter(ActivityType.craft_type_id == craft_type_id)
    
    activity_types = query.order_by(ActivityType.sort.asc()).all()
    type_list = [at.to_dict() for at in activity_types]
    return jsonify(success(data=type_list))

@admin_bp.route('/activity-types/<int:type_id>', methods=['GET'])
@login_required
def get_activity_type(type_id):
    activity_type = ActivityType.query.get(type_id)
    if not activity_type:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动类型不存在')), 404
    
    at_dict = activity_type.to_dict()
    at_dict['activity_count'] = Activity.query.filter_by(activity_type=activity_type.name, status='active').count()
    
    return jsonify(success(data=at_dict))

@admin_bp.route('/activity-types', methods=['POST'])
@login_required
def create_activity_type():
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='活动类型名称不能为空')), 400
    
    name = data.get('name')
    
    existing = ActivityType.query.filter_by(name=name).first()
    if existing:
        return jsonify(error(code=ResponseCode.DATA_EXISTS, msg='活动类型名称已存在')), 400
    
    activity_type = ActivityType(
        name=name,
        description=data.get('description', ''),
        craft_type_id=data.get('craft_type_id'),
        sort=data.get('sort', 0),
        status=data.get('status', 'active')
    )
    
    try:
        db.session.add(activity_type)
        db.session.commit()
        return jsonify(success(data=activity_type.to_dict(), msg='活动类型创建成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'创建失败: {str(e)}')), 500

@admin_bp.route('/activity-types/<int:type_id>', methods=['PUT'])
@login_required
def update_activity_type(type_id):
    activity_type = ActivityType.query.get(type_id)
    if not activity_type:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动类型不存在')), 404
    
    data = request.get_json()
    
    if 'name' in data:
        existing = ActivityType.query.filter(
            ActivityType.name == data['name'],
            ActivityType.id != type_id
        ).first()
        if existing:
            return jsonify(error(code=ResponseCode.DATA_EXISTS, msg='活动类型名称已存在')), 400
        activity_type.name = data['name']
    
    if 'description' in data:
        activity_type.description = data['description']
    if 'craft_type_id' in data:
        activity_type.craft_type_id = data['craft_type_id']
    if 'sort' in data:
        activity_type.sort = data['sort']
    if 'status' in data:
        activity_type.status = data['status']
    
    try:
        db.session.commit()
        return jsonify(success(data=activity_type.to_dict(), msg='活动类型更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

@admin_bp.route('/activity-types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_activity_type(type_id):
    activity_type = ActivityType.query.get(type_id)
    if not activity_type:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动类型不存在')), 404
    
    activity_count = Activity.query.filter_by(activity_type=activity_type.name, status='active').count()
    if activity_count > 0:
        return jsonify(error(code=ResponseCode.DATA_DELETE_FAILED, msg=f'该活动类型下有{activity_count}个活动，无法删除')), 400
    
    try:
        db.session.delete(activity_type)
        db.session.commit()
        return jsonify(success(msg='活动类型删除成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500

@admin_bp.route('/system-configs', methods=['GET'])
@login_required
def get_system_configs():
    group = request.args.get('group', '')
    
    query = SystemConfig.query
    if group:
        query = query.filter(SystemConfig.group == group)
    
    configs = query.order_by(SystemConfig.group.asc(), SystemConfig.id.asc()).all()
    
    config_dict = {}
    for config in configs:
        if config.group not in config_dict:
            config_dict[config.group] = []
        config_dict[config.group].append(config.to_dict())
    
    return jsonify(success(data=config_dict))

@admin_bp.route('/system-configs/save', methods=['POST'])
@login_required
def save_system_configs():
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='配置数据不能为空')), 400
    
    try:
        for key, value in data.items():
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = value
            else:
                config = SystemConfig(
                    key=key,
                    value=value,
                    group='general'
                )
                db.session.add(config)
        
        db.session.commit()
        return jsonify(success(msg='配置已同步'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'保存失败: {str(e)}')), 500

@admin_bp.route('/system-configs/<int:config_id>', methods=['PUT'])
@login_required
def update_system_config(config_id):
    config = SystemConfig.query.get(config_id)
    if not config:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='配置不存在')), 404
    
    data = request.get_json()
    
    if 'value' in data:
        config.value = data['value']
    if 'description' in data:
        config.description = data['description']
    if 'group' in data:
        config.group = data['group']
    
    try:
        db.session.commit()
        return jsonify(success(data=config.to_dict(), msg='配置更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500


@admin_bp.route('/users/list', methods=['GET'])
@login_required
def get_users_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    user_id = request.args.get('user_id', type=int)
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    
    query = User.query
    
    if user_id:
        query = query.filter(User.id == user_id)
    
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.nickname.contains(keyword),
                User.phone.contains(keyword)
            )
        )
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(User.created_at >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(User.created_at < end)
        except:
            pass
    
    if role:
        if role == 'teacher':
            query = query.filter(User._roles.contains('"teacher"'))
        elif role == 'customer':
            query = query.filter(User._roles.contains('"customer"'))
    
    if status:
        if status == 'active':
            query = query.filter(User.is_active == True)
        elif status == 'inactive':
            query = query.filter(User.is_active == False)
    
    if sort == 'newest':
        query = query.order_by(User.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort == 'active':
        query = query.order_by(User.last_login_at.desc().nullslast())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    users = []
    for user in pagination.items:
        user_dict = user.to_dict()
        teacher_profile = TeacherProfile.query.filter_by(user_id=user.id).first()
        if teacher_profile:
            user_dict['teacher_info'] = teacher_profile.to_dict()
        users.append(user_dict)
    
    return jsonify(success(data={
        'list': users,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@login_required
def update_user_status(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    data = request.get_json()
    is_active = data.get('is_active')
    
    if is_active is None:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='状态参数不能为空')), 400
    
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=user.to_dict(), msg=f'用户已{"启用" if is_active else "禁用"}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/users/<int:user_id>/likes', methods=['GET'])
@login_required
def get_user_likes(user_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    query = Like.query.filter_by(user_id=user_id).order_by(Like.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    likes = []
    for like in pagination.items:
        like_dict = like.to_dict()
        product = Product.query.get(like.product_id)
        if product:
            like_dict['product_title'] = product.title
            like_dict['product_image'] = product.cover_image
            like_dict['product_price'] = product.price
        likes.append(like_dict)
    
    return jsonify(success(data={
        'list': likes,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/users/<int:user_id>/orders', methods=['GET'])
@login_required
def get_user_orders(user_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', '')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    query = Order.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    orders = []
    for order in pagination.items:
        order_dict = order.to_dict()
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                order_dict['teacher_nickname'] = teacher.nickname or teacher.username
        orders.append(order_dict)
    
    return jsonify(success(data={
        'list': orders,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'status_names': STATUS_NAMES
    }))


@admin_bp.route('/users/<int:user_id>/reviews', methods=['GET'])
@login_required
def get_user_reviews(user_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    query = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    reviews = []
    for review in pagination.items:
        rev_dict = review.to_dict()
        product = Product.query.get(review.product_id)
        if product:
            rev_dict['product_title'] = product.title
            rev_dict['product_image'] = product.cover_image
        teacher = User.query.get(review.teacher_id)
        if teacher:
            rev_dict['teacher_nickname'] = teacher.nickname or teacher.username
        reviews.append(rev_dict)
    
    return jsonify(success(data={
        'list': reviews,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/teachers/pending', methods=['GET'])
@login_required
def get_pending_teachers():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    query = TeacherProfile.query.filter_by(verify_status='pending').order_by(TeacherProfile.created_at.asc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    teachers = []
    for tp in pagination.items:
        teacher_dict = tp.to_dict()
        user = User.query.get(tp.user_id)
        if user:
            teacher_dict['user_info'] = {
                'id': user.id,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'phone': user.phone,
                'create_time': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            }
        teachers.append(teacher_dict)
    
    return jsonify(success(data={
        'list': teachers,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/teachers/<int:teacher_id>/verify', methods=['POST'])
@login_required
def verify_teacher(teacher_id):
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    data = request.get_json()
    action = data.get('action')
    reason = data.get('reason', '')
    
    if action == 'approve':
        tp.is_verified = True
        tp.verify_status = 'approved'
        tp.verified_at = datetime.utcnow()
        tp.reject_reason = None
        
        user = User.query.get(tp.user_id)
        if user and 'teacher' not in user.roles:
            roles = user.roles
            roles.append('teacher')
            user.roles = roles
        
        message = '老师审核通过'
    elif action == 'reject':
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='拒绝理由不能少于10个字')), 400
        
        tp.is_verified = False
        tp.verify_status = 'rejected'
        tp.reject_reason = reason
        tp.verified_at = None
        
        message = '老师审核已拒绝'
    else:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的操作类型')), 400
    
    tp.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=tp.to_dict(), msg=message))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/teachers/list', methods=['GET'])
@login_required
def get_teachers_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    teacher_id = request.args.get('teacher_id', type=int) or request.args.get('id', type=int)
    keyword = request.args.get('keyword', '') or request.args.get('name', '')
    specialty = request.args.get('specialty', '')
    verify_status = request.args.get('verify_status', '')
    sort = request.args.get('sort', 'newest')
    
    query = TeacherProfile.query
    
    if teacher_id:
        query = query.filter(TeacherProfile.id == teacher_id)
    
    if keyword:
        user_ids = []
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.phone.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                TeacherProfile.real_name.contains(keyword),
                TeacherProfile.user_id.in_(user_ids)
            )
        )
    
    if specialty:
        query = query.filter(TeacherProfile._specialties.contains(specialty))
    
    if verify_status:
        query = query.filter(TeacherProfile.verify_status == verify_status)
    
    if sort == 'newest':
        query = query.order_by(TeacherProfile.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(TeacherProfile.created_at.asc())
    elif sort == 'rating':
        query = query.order_by(TeacherProfile.rating.desc())
    elif sort == 'orders':
        query = query.order_by(TeacherProfile.order_count.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    teachers = []
    for tp in pagination.items:
        teacher_dict = tp.to_dict()
        user = User.query.get(tp.user_id)
        if user:
            teacher_dict['user_info'] = {
                'id': user.id,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'phone': user.phone,
                'is_active': user.is_active,
                'create_time': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            }
        teachers.append(teacher_dict)
    
    return jsonify(success(data={
        'list': teachers,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/teachers/<int:teacher_id>', methods=['GET'])
@login_required
def get_teacher_detail(teacher_id):
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    teacher_dict = tp.to_dict()
    user = User.query.get(tp.user_id)
    if user:
        teacher_dict['user_info'] = {
            'id': user.id,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'phone': user.phone,
            'email': user.email,
            'gender': user.gender,
            'is_active': user.is_active,
            'create_time': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
        }
    
    product_count = Product.query.filter_by(teacher_id=tp.id, status='active').count()
    order_count = Order.query.filter_by(teacher_id=tp.user_id).count()
    review_count = Review.query.filter_by(teacher_id=tp.user_id).count()
    
    teacher_dict['stats'] = {
        'product_count': product_count,
        'order_count': order_count,
        'review_count': review_count
    }
    
    return jsonify(success(data=teacher_dict))


@admin_bp.route('/teachers/<int:teacher_id>', methods=['PUT'])
@login_required
def update_teacher(teacher_id):
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    data = request.get_json()
    
    if 'real_name' in data:
        tp.real_name = data['real_name']
    if 'phone' in data:
        tp.phone = data['phone']
    if 'intro' in data:
        tp.intro = data['intro']
    if 'bio' in data:
        tp.bio = data['bio']
    if 'specialties' in data:
        tp.specialties = data['specialties']
    if 'studio_name' in data:
        tp.studio_name = data['studio_name']
    if 'studio_address' in data:
        tp.studio_address = data['studio_address']
    if 'experience_years' in data:
        tp.experience_years = int(data['experience_years']) if data['experience_years'] else 0
    
    tp.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=tp.to_dict(), msg='老师信息更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500


@admin_bp.route('/teachers/<int:teacher_id>/check-pending-orders', methods=['GET'])
@login_required
def check_teacher_pending_orders(teacher_id):
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    pending_statuses = ['pending', 'pending_accept', 'accepted', 'in_progress', 'paid', 'shipped']
    pending_orders = Order.query.filter(
        Order.teacher_id == tp.user_id,
        Order.status.in_(pending_statuses)
    ).all()
    
    pending_count = len(pending_orders)
    
    return jsonify(success(data={
        'has_pending_orders': pending_count > 0,
        'pending_count': pending_count,
        'pending_orders': [
            {
                'id': o.id,
                'status': o.status,
                'status_name': o.status_name,
                'create_time': o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else None
            } for o in pending_orders
        ]
    }))


@admin_bp.route('/teachers/<int:teacher_id>/status', methods=['PUT'])
@login_required
def update_teacher_status(teacher_id):
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    data = request.get_json()
    is_active = data.get('is_active')
    
    if is_active is None:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='状态参数不能为空')), 400
    
    if not is_active:
        pending_statuses = ['pending', 'pending_accept', 'accepted', 'in_progress', 'paid', 'shipped']
        pending_orders = Order.query.filter(
            Order.teacher_id == tp.user_id,
            Order.status.in_(pending_statuses)
        ).count()
        
        if pending_orders > 0:
            return jsonify(error(
                code=ResponseCode.OPERATION_FAILED,
                msg=f'该老师有{pending_orders}个未完成订单，暂时无法禁用'
            )), 400
    
    tp.is_active = is_active
    tp.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=tp.to_dict(), msg=f'老师已{"启用" if is_active else "禁用"}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/teachers/<int:teacher_id>/products', methods=['GET'])
@login_required
def get_teacher_products(teacher_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', '')
    
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    query = Product.query.filter_by(teacher_id=tp.id)
    
    if status:
        query = query.filter(Product.status == status)
    
    query = query.order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    products = []
    for product in pagination.items:
        product_dict = product.to_dict()
        product_dict['likes_count'] = Like.query.filter_by(product_id=product.id).count()
        product_dict['reviews_count'] = Review.query.filter_by(product_id=product.id).count()
        products.append(product_dict)
    
    return jsonify(success(data={
        'list': products,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/teachers/<int:teacher_id>/orders', methods=['GET'])
@login_required
def get_teacher_orders(teacher_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    status = request.args.get('status', '')
    
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    query = Order.query.filter_by(teacher_id=tp.user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    orders = []
    for order in pagination.items:
        order_dict = order.to_dict()
        customer = User.query.get(order.user_id)
        if customer:
            order_dict['customer_nickname'] = customer.nickname or customer.username
            order_dict['customer_avatar'] = customer.avatar
        orders.append(order_dict)
    
    return jsonify(success(data={
        'list': orders,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'status_names': STATUS_NAMES
    }))


@admin_bp.route('/teachers/<int:teacher_id>/reviews', methods=['GET'])
@login_required
def get_teacher_reviews(teacher_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    query = Review.query.filter_by(teacher_id=tp.user_id).order_by(Review.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    reviews = []
    for review in pagination.items:
        rev_dict = review.to_dict()
        user = User.query.get(review.user_id)
        if user:
            rev_dict['user_nickname'] = user.nickname or user.username
            rev_dict['user_avatar'] = user.avatar
        product = Product.query.get(review.product_id)
        if product:
            rev_dict['product_title'] = product.title
            rev_dict['product_image'] = product.cover_image
        reviews.append(rev_dict)
    
    return jsonify(success(data={
        'list': reviews,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/teachers/<int:teacher_id>/likes', methods=['GET'])
@login_required
def get_teacher_likes(teacher_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    tp = TeacherProfile.query.get(teacher_id)
    if not tp:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息不存在')), 404
    
    teacher_products = Product.query.filter_by(teacher_id=tp.id).all()
    product_ids = [p.id for p in teacher_products]
    
    if not product_ids:
        return jsonify(success(data={
            'list': [],
            'total': 0,
            'page': page,
            'size': size,
            'total_pages': 0,
            'stats': {
                'total_likes': 0,
                'total_products': 0,
                'product_likes': []
            }
        }))
    
    query = Like.query.filter(Like.product_id.in_(product_ids)).order_by(Like.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    likes = []
    for like in pagination.items:
        like_dict = like.to_dict()
        user = User.query.get(like.user_id)
        if user:
            like_dict['user_nickname'] = user.nickname or user.username
            like_dict['user_avatar'] = user.avatar
        product = Product.query.get(like.product_id)
        if product:
            like_dict['product_title'] = product.title
            like_dict['product_image'] = product.cover_image
        likes.append(like_dict)
    
    total_likes = Like.query.filter(Like.product_id.in_(product_ids)).count()
    
    product_likes_stats = db.session.query(
        Product.id,
        Product.title,
        Product.cover_image,
        db.func.count(Like.id).label('like_count')
    ).outerjoin(
        Like, Product.id == Like.product_id
    ).filter(
        Product.id.in_(product_ids)
    ).group_by(
        Product.id, Product.title, Product.cover_image
    ).order_by(
        db.desc('like_count')
    ).all()
    
    product_likes = []
    for pl in product_likes_stats:
        product_likes.append({
            'product_id': pl.id,
            'product_title': pl.title,
            'product_image': pl.cover_image,
            'like_count': pl.like_count or 0
        })
    
    return jsonify(success(data={
        'list': likes,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'stats': {
            'total_likes': total_likes,
            'total_products': len(product_ids),
            'product_likes': product_likes
        }
    }))


@admin_bp.route('/specialties/all', methods=['GET'])
@login_required
def get_all_specialties():
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    specialty_list = [{
        'id': c.id,
        'name': c.name,
        'icon': c.icon,
        'sort_order': c.sort,
        'is_active': c.status == 'active'
    } for c in categories]
    return jsonify(success(data=specialty_list))


def create_audit_log(admin_id, target_type, target_id, action, reason=None, before_data=None, after_data=None):
    from app.models import AuditLog
    import json
    
    audit_log = AuditLog(
        admin_id=admin_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        reason=reason,
        before_data=json.dumps(before_data, ensure_ascii=False) if before_data else None,
        after_data=json.dumps(after_data, ensure_ascii=False) if after_data else None
    )
    db.session.add(audit_log)
    db.session.commit()
    return audit_log


@admin_bp.route('/products/pending-review', methods=['GET'])
@login_required
def get_pending_review_products():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '', type=str)
    
    query = Product.query.filter(Product.verify_status == 'pending')
    
    if keyword:
        query = query.filter(
            db.or_(
                Product.title.contains(keyword),
                Product.description.contains(keyword)
            )
        )
    
    query = query.order_by(Product.created_at.asc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    products = []
    for p in pagination.items:
        product_dict = p.to_dict(include_teacher=True)
        if p.teacher_profile and p.teacher_profile.user:
            product_dict['teacher_name'] = p.teacher_profile.user.nickname or p.teacher_profile.user.username
        products.append(product_dict)
    
    return jsonify(success(data={
        'list': products,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/products/<int:product_id>/review', methods=['POST'])
@login_required
def review_product(product_id):
    admin_id = g.get('user_id')
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    if product.verify_status != 'pending':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该作品已审核，无需重复审核')), 400
    
    data = request.get_json()
    action = data.get('action')
    reason = data.get('reason', '')
    
    before_data = product.to_dict()
    
    if action == 'approve':
        product.verify_status = 'approved'
        product.verify_time = datetime.utcnow()
        product.verify_admin_id = admin_id
        product.reject_reason = None
        product.is_online = True
        message = '作品审核通过'
        
    elif action == 'reject':
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='拒绝理由不能少于10个字')), 400
        
        product.verify_status = 'rejected'
        product.verify_time = datetime.utcnow()
        product.verify_admin_id = admin_id
        product.reject_reason = reason
        product.is_online = False
        message = '作品审核已拒绝'
    else:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的操作类型')), 400
    
    try:
        db.session.commit()
        
        after_data = product.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='product',
            target_id=product_id,
            action=action,
            reason=reason,
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=product.to_dict(), msg=message))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/products/<int:product_id>/online', methods=['POST'])
@login_required
def set_product_online(product_id):
    admin_id = g.get('user_id')
    data = request.get_json()
    is_online = data.get('is_online', True)
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    if product.verify_status != 'approved':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='仅已审核通过的作品才能上下架')), 400
    
    before_data = product.to_dict()
    product.is_online = is_online
    
    try:
        db.session.commit()
        
        after_data = product.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='product',
            target_id=product_id,
            action='online' if is_online else 'offline',
            before_data=before_data,
            after_data=after_data
        )
        
        status_text = '上架' if is_online else '下架'
        return jsonify(success(data=product.to_dict(), msg=f'作品已{status_text}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/products/<int:product_id>/admin-edit', methods=['PUT'])
@login_required
def admin_edit_product(product_id):
    admin_id = g.get('user_id')
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    if product.verify_status != 'approved':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='仅已审核通过的作品才能编辑')), 400
    
    if not product.is_online:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='仅已上架的作品才能编辑')), 400
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    before_data = product.to_dict()
    
    errors = []
    
    if 'price' in data:
        price = data.get('price')
        if not isinstance(price, (int, float)) or price <= 0:
            errors.append('价格必须是大于0的数字')
        else:
            product.price = float(price)
    
    if 'title' in data and data.get('title'):
        product.title = data.get('title')
    
    if 'description' in data:
        product.description = data.get('description')
    
    if 'category_id' in data:
        product.category_id = data.get('category_id')
    
    if 'images' in data:
        images = data.get('images')
        if images and isinstance(images, list):
            product.images = images
            if len(images) > 0 and not data.get('cover_image'):
                product.cover_image = images[0]
    
    if 'cover_image' in data:
        product.cover_image = data.get('cover_image')
    
    if errors:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='; '.join(errors))), 400
    
    try:
        db.session.commit()
        
        after_data = product.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='product',
            target_id=product_id,
            action='edit',
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=product.to_dict(), msg='作品更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500


@admin_bp.route('/products/<int:product_id>/admin-delete', methods=['DELETE'])
@login_required
def admin_delete_product(product_id):
    admin_id = g.get('user_id')
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    order_count = OrderItem.query.filter_by(product_id=product_id).count()
    if order_count > 0:
        return jsonify(error(
            code=ResponseCode.DATA_DELETE_FAILED,
            msg=f'该作品有{order_count}个关联订单，无法删除'
        )), 400
    
    review_count = Review.query.filter_by(product_id=product_id).count()
    if review_count > 0:
        return jsonify(error(
            code=ResponseCode.DATA_DELETE_FAILED,
            msg=f'该作品有{review_count}个关联评价，无法删除'
        )), 400
    
    like_count = Like.query.filter_by(product_id=product_id).count()
    if like_count > 0:
        return jsonify(error(
            code=ResponseCode.DATA_DELETE_FAILED,
            msg=f'该作品有{like_count}个关联点赞，无法删除'
        )), 400
    
    before_data = product.to_dict()
    
    try:
        db.session.delete(product)
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='product',
            target_id=product_id,
            action='delete',
            before_data=before_data
        )
        
        return jsonify(success(msg='作品已删除'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500


@admin_bp.route('/activities/pending-review', methods=['GET'])
@login_required
def get_pending_review_activities():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '', type=str)
    
    query = Activity.query.filter(Activity.verify_status == 'pending')
    
    if keyword:
        query = query.filter(
            db.or_(
                Activity.title.contains(keyword),
                Activity.description.contains(keyword)
            )
        )
    
    query = query.order_by(Activity.created_at.asc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    activities = []
    for act in pagination.items:
        act_dict = act.to_dict(include_teacher=True)
        if act.teacher_profile and act.teacher_profile.user:
            act_dict['teacher_name'] = act.teacher_profile.user.nickname or act.teacher_profile.user.username
        activities.append(act_dict)
    
    return jsonify(success(data={
        'list': activities,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/activities/<int:activity_id>/review', methods=['POST'])
@login_required
def review_activity(activity_id):
    admin_id = g.get('user_id')
    
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在')), 404
    
    if activity.verify_status != 'pending':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该活动已审核，无需重复审核')), 400
    
    data = request.get_json()
    action = data.get('action')
    reason = data.get('reason', '')
    
    before_data = activity.to_dict()
    
    if action == 'approve':
        activity.verify_status = 'approved'
        activity.verify_time = datetime.utcnow()
        activity.verify_admin_id = admin_id
        activity.reject_reason = None
        message = '活动审核通过'
        
    elif action == 'reject':
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='拒绝理由不能少于10个字')), 400
        
        activity.verify_status = 'rejected'
        activity.verify_time = datetime.utcnow()
        activity.verify_admin_id = admin_id
        activity.reject_reason = reason
        activity.status = 'inactive'
        message = '活动审核已拒绝'
    else:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的操作类型')), 400
    
    try:
        db.session.commit()
        
        after_data = activity.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='activity',
            target_id=activity_id,
            action=action,
            reason=reason,
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=activity.to_dict(), msg=message))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/activities/official-create', methods=['POST'])
@login_required
def create_official_activity():
    admin_id = g.get('user_id')
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    title = data.get('title', '').strip()
    if not title or len(title) < 5:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='活动标题不能少于5个字')), 400
    
    images = data.get('images', [])
    if not images or len(images) < 1:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='请至少上传1张活动图片')), 400
    
    activity = Activity(
        teacher_id=1,
        title=title,
        description=data.get('description', ''),
        craft_type=data.get('craft_type', '其他'),
        activity_type=data.get('activity_type', '其他'),
        start_time=parse_datetime(data.get('start_time')),
        end_time=parse_datetime(data.get('end_time')),
        registration_start_time=parse_datetime(data.get('registration_start_time')),
        registration_deadline=parse_datetime(data.get('registration_deadline')),
        location=data.get('location'),
        address=data.get('address'),
        city=data.get('city'),
        price=float(data.get('price', 0)),
        original_price=float(data.get('original_price', 0)) if data.get('original_price') else float(data.get('price', 0)),
        max_participants=int(data.get('max_participants', 999)),
        current_participants=0,
        process=process,
        registration_method=data.get('registration_method'),
        status='active',
        verify_status='approved',
        verify_time=datetime.utcnow(),
        verify_admin_id=admin_id,
        is_official=True,
        view_count=0,
        favorite_count=0,
        registration_count=0
    )
    
    if images and isinstance(images, list):
        activity.images = images
        if len(images) > 0:
            activity.cover_image = images[0]
    
    if data.get('cover_image'):
        activity.cover_image = data.get('cover_image')
    
    if data.get('tags'):
        activity.tags = data.get('tags')
    
    try:
        db.session.add(activity)
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='activity',
            target_id=activity.id,
            action='official_create',
            after_data=activity.to_dict()
        )
        
        return jsonify(success(data=activity.to_dict(), msg='官方活动创建成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'创建失败: {str(e)}')), 500


@admin_bp.route('/activities/<int:activity_id>/admin-edit', methods=['PUT'])
@login_required
def admin_edit_activity(activity_id):
    admin_id = g.get('user_id')
    
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在')), 404
    
    if activity.verify_status != 'approved':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='仅已审核通过的活动才能编辑')), 400
    
    now = datetime.utcnow()
    if activity.end_time and activity.end_time < now:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='活动已结束，无法编辑')), 400
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    before_data = activity.to_dict()
    
    if 'title' in data:
        activity.title = data.get('title')
    if 'description' in data:
        activity.description = data.get('description')
    if 'craft_type' in data:
        activity.craft_type = data.get('craft_type')
    if 'activity_type' in data:
        activity.activity_type = data.get('activity_type')
    if 'start_time' in data:
        activity.start_time = parse_datetime(data.get('start_time'))
    if 'end_time' in data:
        activity.end_time = parse_datetime(data.get('end_time'))
    if 'registration_start_time' in data:
        activity.registration_start_time = parse_datetime(data.get('registration_start_time'))
    if 'registration_deadline' in data:
        activity.registration_deadline = parse_datetime(data.get('registration_deadline'))
    if 'location' in data:
        activity.location = data.get('location')
    if 'address' in data:
        activity.address = data.get('address')
    if 'city' in data:
        activity.city = data.get('city')
    if 'price' in data:
        activity.price = float(data.get('price'))
    if 'original_price' in data:
        activity.original_price = float(data.get('original_price'))
    if 'max_participants' in data:
        activity.max_participants = int(data.get('max_participants'))
    if 'process' in data:
        activity.process = data.get('process')
    if 'registration_method' in data:
        activity.registration_method = data.get('registration_method')
    if 'cover_image' in data:
        activity.cover_image = data.get('cover_image')
    
    if 'images' in data:
        images = data.get('images')
        if images and isinstance(images, list):
            activity.images = images
            if len(images) > 0 and not data.get('cover_image'):
                activity.cover_image = images[0]
    
    if 'tags' in data:
        activity.tags = data.get('tags')
    
    try:
        db.session.commit()
        
        after_data = activity.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='activity',
            target_id=activity_id,
            action='edit',
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=activity.to_dict(), msg='活动更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500


@admin_bp.route('/activities/<int:activity_id>/admin-delete', methods=['DELETE'])
@login_required
def admin_delete_activity(activity_id):
    admin_id = g.get('user_id')
    
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在')), 404
    
    registration_count = ActivityRegistration.query.filter_by(activity_id=activity_id).count()
    if registration_count > 0:
        return jsonify(error(
            code=ResponseCode.DATA_DELETE_FAILED,
            msg=f'该活动已有{registration_count}人报名，无法删除'
        )), 400
    
    before_data = activity.to_dict()
    
    try:
        db.session.delete(activity)
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='activity',
            target_id=activity_id,
            action='delete',
            before_data=before_data
        )
        
        return jsonify(success(msg='活动已删除'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500


@admin_bp.route('/activities/<int:activity_id>/stats', methods=['GET'])
@login_required
def get_activity_detail_stats(activity_id):
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在')), 404
    
    registrations = ActivityRegistration.query.filter_by(activity_id=activity_id).order_by(
        ActivityRegistration.created_at.desc()
    ).all()
    
    registration_list = []
    for reg in registrations:
        reg_dict = reg.to_dict()
        user = User.query.get(reg.user_id)
        if user:
            reg_dict['user_nickname'] = user.nickname or user.username
            reg_dict['user_avatar'] = user.avatar
        registration_list.append(reg_dict)
    
    return jsonify(success(data={
        'activity': activity.to_dict(),
        'registration_count': len(registration_list),
        'view_count': activity.view_count,
        'registrations': registration_list
    }))


@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
def get_audit_logs():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    target_type = request.args.get('target_type', '', type=str)
    action = request.args.get('action', '', type=str)
    
    from app.models import AuditLog
    
    query = AuditLog.query
    
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if action:
        query = query.filter(AuditLog.action == action)
    
    query = query.order_by(AuditLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    logs = []
    for log in pagination.items:
        log_dict = log.to_dict()
        admin = User.query.get(log.admin_id)
        if admin:
            log_dict['admin_nickname'] = admin.nickname or admin.username
        logs.append(log_dict)
    
    return jsonify(success(data={
        'list': logs,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/messages/list', methods=['GET'])
@login_required
def get_admin_messages():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    msg_type = request.args.get('type', '')
    subtype = request.args.get('subtype', '')
    recipient_type = request.args.get('recipient_type', '')
    is_read = request.args.get('is_read', type=bool)
    is_announcement = request.args.get('is_announcement', type=bool)
    is_expired = request.args.get('is_expired', type=bool)
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort = request.args.get('sort', 'newest')
    
    query = Message.query
    
    if msg_type and msg_type in MESSAGE_TYPES:
        query = query.filter(Message.type == msg_type)
    
    if subtype:
        query = query.filter(Message.subtype == subtype)
    
    if recipient_type:
        query = query.filter(Message.recipient_type == recipient_type)
    
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)
    
    if is_announcement is not None:
        query = query.filter(Message.is_announcement == is_announcement)
    
    if is_expired is not None:
        if is_expired:
            query = query.filter(Message.expire_time < datetime.utcnow())
        else:
            query = query.filter(
                db.or_(
                    Message.expire_time == None,
                    Message.expire_time >= datetime.utcnow()
                )
            )
    
    if keyword:
        query = query.filter(
            db.or_(
                Message.title.contains(keyword),
                Message.content.contains(keyword)
            )
        )
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Message.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Message.created_at < end)
        except ValueError:
            pass
    
    if sort == 'newest':
        query = query.order_by(Message.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Message.created_at.asc())
    elif sort == 'expire_asc':
        query = query.order_by(Message.expire_time.asc().nullslast())
    elif sort == 'expire_desc':
        query = query.order_by(Message.expire_time.desc().nullslast())
    
    total = query.count()
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    messages = []
    for msg in pagination.items:
        msg_dict = msg.to_dict()
        
        user = User.query.get(msg.user_id)
        if user:
            msg_dict['user_nickname'] = user.nickname or user.username
            msg_dict['user_avatar'] = user.avatar
        
        messages.append(msg_dict)
    
    return jsonify(success(data={
        'list': messages,
        'total': total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'message_types': MESSAGE_TYPES,
        'announcement_subtypes': ANNOUNCEMENT_SUBTYPES,
        'recipient_types': RECIPIENT_TYPES
    }))


@admin_bp.route('/messages/<int:message_id>', methods=['GET'])
@login_required
def get_admin_message_detail(message_id):
    message = Message.query.get(message_id)
    if not message:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='消息不存在')), 404
    
    msg_dict = message.to_dict()
    
    user = User.query.get(message.user_id)
    if user:
        msg_dict['user_info'] = {
            'id': user.id,
            'nickname': user.nickname or user.username,
            'avatar': user.avatar
        }
    
    return jsonify(success(data=msg_dict))


@admin_bp.route('/messages/announcements', methods=['POST'])
@login_required
def create_announcement():
    admin_id = g.get('user_id', 1)
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    subtype = data.get('subtype', 'system')
    recipient_type = data.get('recipient_type', 'all')
    target_user_ids = data.get('target_user_ids', [])
    expire_time_str = data.get('expire_time')
    
    if not title or len(title) < 5:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='公告标题不能少于5个字')), 400
    
    if not content or len(content) < 20:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='公告内容不能少于20个字')), 400
    
    expire_time = None
    if expire_time_str:
        expire_time = parse_datetime(expire_time_str)
    
    target_users = []
    
    if recipient_type == 'all':
        target_users = User.query.filter(User.is_active == True).all()
    elif recipient_type == 'customer':
        target_users = User.query.filter(
            User.is_active == True,
            User._roles.contains('"customer"')
        ).all()
    elif recipient_type == 'teacher':
        target_users = User.query.filter(
            User.is_active == True,
            User._roles.contains('"teacher"')
        ).all()
    elif recipient_type == 'specific' and target_user_ids:
        if not isinstance(target_user_ids, list):
            target_user_ids = []
        target_users = User.query.filter(
            User.id.in_(target_user_ids),
            User.is_active == True
        ).all()
    
    if not target_users:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='没有找到匹配的接收用户')), 400
    
    try:
        now = datetime.utcnow()
        messages_created = []
        
        for user in target_users:
            message = Message(
                user_id=user.id,
                type='announcement',
                subtype=subtype,
                title=title,
                content=content,
                sender='管理员',
                recipient_type=recipient_type,
                recipient_role='customer' if recipient_type == 'customer' else ('teacher' if recipient_type == 'teacher' else 'customer'),
                target_user_ids=[u.id for u in target_users] if recipient_type == 'specific' else [],
                expire_time=expire_time,
                is_announcement=True,
                is_read=False,
                created_at=now,
                updated_at=now
            )
            db.session.add(message)
            messages_created.append(message)
        
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='announcement',
            target_id=messages_created[0].id if messages_created else 0,
            action='create',
            reason=f'发布公告: {title[:50]}...' if len(title) > 50 else f'发布公告: {title}',
            after_data={
                'title': title,
                'subtype': subtype,
                'recipient_type': recipient_type,
                'recipient_count': len(target_users),
                'expire_time': expire_time_str
            }
        )
        
        return jsonify(success(data={
            'message_count': len(messages_created),
            'title': title,
            'recipient_type': recipient_type,
            'recipient_count': len(target_users)
        }, msg='公告发布成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'发布失败: {str(e)}')), 500


@admin_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_admin_message(message_id):
    admin_id = g.get('user_id', 1)
    
    message = Message.query.get(message_id)
    if not message:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='消息不存在')), 404
    
    before_data = message.to_dict()
    
    try:
        db.session.delete(message)
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='message',
            target_id=message_id,
            action='delete',
            before_data=before_data
        )
        
        return jsonify(success(msg='消息已删除'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500


@admin_bp.route('/messages/batch-delete', methods=['POST'])
@login_required
def batch_delete_admin_messages():
    admin_id = g.get('user_id', 1)
    
    data = request.get_json()
    if not data or 'message_ids' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='message_ids参数不能为空')), 400
    
    message_ids = data.get('message_ids', [])
    if not isinstance(message_ids, list) or len(message_ids) == 0:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='message_ids必须是非空数组')), 400
    
    try:
        deleted_count = Message.query.filter(Message.id.in_(message_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        create_audit_log(
            admin_id=admin_id,
            target_type='message',
            target_id=message_ids[0] if message_ids else 0,
            action='batch_delete',
            reason=f'批量删除{deleted_count}条消息'
        )
        
        return jsonify(success(data={'deleted_count': deleted_count}, msg=f'已删除{deleted_count}条消息'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'删除失败: {str(e)}')), 500


@admin_bp.route('/messages/stats', methods=['GET'])
@login_required
def get_message_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    msg_type = request.args.get('type', '')
    is_announcement = request.args.get('is_announcement', type=bool)
    
    start, end = get_date_range(period, start_date, end_date)
    
    query = Message.query.filter(
        Message.created_at >= start,
        Message.created_at < end
    )
    
    if msg_type:
        query = query.filter(Message.type == msg_type)
    
    if is_announcement is not None:
        query = query.filter(Message.is_announcement == is_announcement)
    
    total = query.count()
    read_count = query.filter(Message.is_read == True).count()
    unread_count = total - read_count
    
    type_stats = {}
    for msg_type_val, type_name in MESSAGE_TYPES.items():
        type_count = Message.query.filter(
            Message.type == msg_type_val,
            Message.created_at >= start,
            Message.created_at < end
        ).count()
        type_stats[msg_type_val] = {
            'name': type_name,
            'count': type_count
        }
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            
            day_query = Message.query.filter(
                Message.created_at >= current,
                Message.created_at < next_day
            )
            
            day_total = day_query.count()
            day_read = day_query.filter(Message.is_read == True).count()
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'total': day_total,
                'read': day_read,
                'unread': day_total - day_read
            })
            current = next_day
    
    return jsonify(success(data={
        'summary': {
            'total': total,
            'read': read_count,
            'unread': unread_count,
            'read_rate': round(read_count / total * 100, 2) if total > 0 else 0
        },
        'type_stats': type_stats,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))


@admin_bp.route('/messages/stats/export', methods=['GET'])
@login_required
def export_message_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    msg_type = request.args.get('type', '')
    
    start, end = get_date_range(period, start_date, end_date)
    
    query = Message.query.filter(
        Message.created_at >= start,
        Message.created_at < end
    )
    
    if msg_type:
        query = query.filter(Message.type == msg_type)
    
    query = query.order_by(Message.created_at.desc())
    messages = query.all()
    
    headers = ['ID', '消息类型', '子类型', '标题', '接收用户', '发送者', '是否已读', '是否公告', '是否过期', '创建时间']
    data = []
    
    for msg in messages:
        user = User.query.get(msg.user_id)
        user_name = user.nickname or user.username if user else '-'
        
        data.append([
            msg.id,
            MESSAGE_TYPES.get(msg.type, msg.type),
            ANNOUNCEMENT_SUBTYPES.get(msg.subtype, msg.subtype) if msg.subtype else '-',
            msg.title,
            user_name,
            msg.sender or '系统',
            '是' if msg.is_read else '否',
            '是' if msg.is_announcement else '否',
            '是' if (msg.expire_time and datetime.utcnow() > msg.expire_time) else '否',
            msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else '-'
        ])
    
    csv_content = generate_csv(data, headers, 'message_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'message_stats_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
        'total': len(data)
    }))


@admin_bp.route('/messages/conversations', methods=['GET'])
@login_required
def get_admin_conversations():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    from app.models.message import Conversation
    
    query = Conversation.query
    
    if keyword:
        user_ids = []
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        if user_ids:
            query = query.filter(
                db.or_(
                    Conversation.user1_id.in_(user_ids),
                    Conversation.user2_id.in_(user_ids)
                )
            )
    
    query = query.order_by(Conversation.updated_at.desc())
    total = query.count()
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    conversations = []
    for conv in pagination.items:
        conv_dict = conv.to_dict()
        
        user1 = User.query.get(conv.user1_id)
        user2 = User.query.get(conv.user2_id)
        
        if user1:
            conv_dict['user1_info'] = {
                'id': user1.id,
                'nickname': user1.nickname or user1.username,
                'avatar': user1.avatar
            }
        if user2:
            conv_dict['user2_info'] = {
                'id': user2.id,
                'nickname': user2.nickname or user2.username,
                'avatar': user2.avatar
            }
        
        conversations.append(conv_dict)
    
    return jsonify(success(data={
        'list': conversations,
        'total': total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/refunds/list', methods=['GET'])
@login_required
def get_refund_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    refund_status = request.args.get('refund_status', '')
    is_abnormal = request.args.get('is_abnormal', type=bool)
    keyword = request.args.get('keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    sort = request.args.get('sort', 'newest')
    
    query = Order.query.filter(
        Order.refund_status.in_(['pending', 'approved', 'processing', 'completed'])
    )
    
    if refund_status:
        query = query.filter(Order.refund_status == refund_status)
    
    if is_abnormal is not None:
        query = query.filter(Order.is_abnormal == is_abnormal)
    
    if keyword:
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                Order.id.contains(keyword),
                Order.user_id.in_(user_ids)
            )
        )
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.refund_time >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.refund_time < end)
        except ValueError:
            pass
    
    if sort == 'newest':
        query = query.order_by(Order.refund_time.desc(), Order.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Order.refund_time.asc().nullslast(), Order.created_at.asc())
    elif sort == 'amount_desc':
        query = query.order_by(Order.refund_amount.desc())
    
    total = query.count()
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    refunds = []
    for order in pagination.items:
        refund_dict = order.to_dict()
        
        customer = User.query.get(order.user_id)
        if customer:
            refund_dict['customer_nickname'] = customer.nickname or customer.username
            refund_dict['customer_avatar'] = customer.avatar
        
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                refund_dict['teacher_nickname'] = teacher.nickname or teacher.username
                refund_dict['teacher_avatar'] = teacher.avatar
        
        if order.created_at:
            hours_since_created = (datetime.utcnow() - order.created_at).total_seconds() / 3600
            refund_dict['is_teacher_overdue'] = order.status == 'pending_accept' and hours_since_created > 24
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        refund_dict['items'] = [item.to_dict() for item in items]
        
        refunds.append(refund_dict)
    
    return jsonify(success(data={
        'list': refunds,
        'total': total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'refund_status_names': REFUND_STATUS_NAMES,
        'abnormal_reasons': ABNORMAL_REASONS
    }))


@admin_bp.route('/refunds/pending', methods=['GET'])
@login_required
def get_pending_refunds():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = Order.query.filter(
        Order.refund_status == 'pending',
        Order.is_abnormal == False
    )
    
    if keyword:
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                Order.id.contains(keyword),
                Order.user_id.in_(user_ids)
            )
        )
    
    query = query.order_by(Order.created_at.desc())
    total = query.count()
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    refunds = []
    for order in pagination.items:
        refund_dict = order.to_dict()
        
        customer = User.query.get(order.user_id)
        if customer:
            refund_dict['customer_nickname'] = customer.nickname or customer.username
            refund_dict['customer_avatar'] = customer.avatar
        
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                refund_dict['teacher_nickname'] = teacher.nickname or teacher.username
        
        if order.created_at:
            hours_since_created = (datetime.utcnow() - order.created_at).total_seconds() / 3600
            refund_dict['is_teacher_overdue'] = hours_since_created > 24
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        refund_dict['items'] = [item.to_dict() for item in items]
        
        refunds.append(refund_dict)
    
    return jsonify(success(data={
        'list': refunds,
        'total': total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
    }))


@admin_bp.route('/refunds/abnormal', methods=['GET'])
@login_required
def get_abnormal_refunds():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    abnormal_reason_code = request.args.get('abnormal_reason_code', '')
    
    query = Order.query.filter(
        db.or_(
            db.and_(
                Order.refund_status.isnot(None),
                Order.refund_status != '',
                Order.is_abnormal == True
            ),
            db.and_(
                Order.refund_status.in_(['approved', 'rejected']),
                Order.is_abnormal == False,
                Order.status.in_(['pending', 'pending_accept', 'accepted', 'in_progress', 'paid', 'shipped', 'delivered'])
            )
        )
    )
    
    if keyword:
        users = User.query.filter(
            db.or_(
                User.nickname.contains(keyword),
                User.username.contains(keyword)
            )
        ).all()
        user_ids = [u.id for u in users]
        
        query = query.filter(
            db.or_(
                Order.id.contains(keyword),
                Order.user_id.in_(user_ids)
            )
        )
    
    if abnormal_reason_code:
        query = query.filter(Order.abnormal_reason_code == abnormal_reason_code)
    
    query = query.order_by(Order.abnormal_time.desc().nullslast(), Order.created_at.desc())
    total = query.count()
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    refunds = []
    for order in pagination.items:
        refund_dict = order.to_dict()
        
        customer = User.query.get(order.user_id)
        if customer:
            refund_dict['customer_nickname'] = customer.nickname or customer.username
            refund_dict['customer_avatar'] = customer.avatar
        
        if order.teacher_id:
            teacher = User.query.get(order.teacher_id)
            if teacher:
                refund_dict['teacher_nickname'] = teacher.nickname or teacher.username
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        refund_dict['items'] = [item.to_dict() for item in items]
        
        refunds.append(refund_dict)
    
    return jsonify(success(data={
        'list': refunds,
        'total': total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'abnormal_reasons': ABNORMAL_REASONS
    }))


@admin_bp.route('/refunds/<order_id>/audit', methods=['POST'])
@login_required
def audit_refund(order_id):
    admin_id = g.get('user_id', 1)
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.refund_status not in ['pending', 'approved']:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该退款不在可审核状态')), 400
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    action = data.get('action')
    reason = data.get('reason', '')
    refund_amount = data.get('refund_amount', order.pay_amount or 0)
    
    if action not in ['approve', 'reject']:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的操作类型')), 400
    
    if action == 'reject':
        if not reason or len(reason.strip()) < 10:
            return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='拒绝理由不能少于10个字')), 400
    
    if refund_amount <= 0 or refund_amount > order.pay_amount:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=f'退款金额必须大于0且不超过订单金额{order.pay_amount}')), 400
    
    before_data = order.to_dict()
    old_status = order.refund_status
    
    try:
        if action == 'approve':
            order.refund_status = 'approved'
            order.status = 'refunding'
            order.refund_amount = refund_amount
            order.refund_approved_by = admin_id
            order.refund_time = datetime.utcnow()
            message = '退款已同意'
            
            try:
                MessageService.send_refund_notification(
                    order, 'approved', refund_amount, '管理员已同意退款申请'
                )
            except Exception as e:
                print(f'发送退款通知失败: {e}')
        
        elif action == 'reject':
            order.refund_status = 'rejected'
            order.refund_amount = 0
            order.refund_reason = reason
            order.refund_approved_by = admin_id
            order.refund_time = datetime.utcnow()
            message = '退款已拒绝'
            
            try:
                MessageService.send_refund_notification(
                    order, 'rejected', 0, reason
                )
            except Exception as e:
                print(f'发送退款通知失败: {e}')
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        after_data = order.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='refund',
            target_id=order.id if isinstance(order.id, int) else 0,
            action=action,
            reason=reason,
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=order.to_dict(), msg=message))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/refunds/<order_id>/force-handle', methods=['POST'])
@login_required
def force_handle_refund(order_id):
    admin_id = g.get('user_id', 1)
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    target_status = data.get('target_status')
    reason = data.get('reason', '')
    order_status = data.get('order_status')
    
    if not reason or len(reason.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='处理理由不能少于10个字')), 400
    
    valid_refund_statuses = ['approved', 'rejected', 'completed']
    valid_order_statuses = ['cancelled', 'completed', 'refunding']
    
    if target_status and target_status not in valid_refund_statuses:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=f'无效的退款状态，可选值: {valid_refund_statuses}')), 400
    
    if order_status and order_status not in valid_order_statuses:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=f'无效的订单状态，可选值: {valid_order_statuses}')), 400
    
    before_data = order.to_dict()
    
    try:
        if target_status:
            order.refund_status = target_status
            order.refund_approved_by = admin_id
            order.refund_time = datetime.utcnow()
        
        if order_status:
            order.status = order_status
            if order_status == 'completed':
                order.complete_time = datetime.utcnow()
            elif order_status == 'cancelled':
                order.cancel_time = datetime.utcnow()
                order.cancel_reason = reason
        
        if not order.is_abnormal:
            order.is_abnormal = True
            order.abnormal_reason = reason
            order.abnormal_reason_code = 'system_error'
            order.abnormal_time = datetime.utcnow()
        
        order.abnormal_resolved_at = datetime.utcnow()
        order.abnormal_resolved_by = admin_id
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        after_data = order.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='refund',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='force_handle',
            reason=reason,
            before_data=before_data,
            after_data=after_data
        )
        
        try:
            from app.models.message import Message
            message_title = '退款处理通知'
            message_content = f'您的订单 {order.id} 退款状态已由管理员更新。\n\n'
            message_content += f'处理说明：{reason}\n'
            if target_status:
                message_content += f'退款状态：{REFUND_STATUS_NAMES.get(target_status, target_status)}\n'
            if order_status:
                message_content += f'订单状态：{STATUS_NAMES.get(order_status, order_status)}\n'
            
            MessageService.send_announcement(
                user_id=order.user_id,
                subtype='refund',
                title=message_title,
                content=message_content,
                related_id=order.id,
                related_type='order',
                sender='管理员',
                recipient_role='customer'
            )
        except Exception as e:
            print(f'发送退款处理通知失败: {e}')
        
        return jsonify(success(data=order.to_dict(), msg='异常退款已处理'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'处理失败: {str(e)}')), 500


@admin_bp.route('/refunds/<order_id>/mark-abnormal', methods=['POST'])
@login_required
def mark_refund_as_abnormal(order_id):
    admin_id = g.get('user_id', 1)
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    reason = data.get('reason', '')
    reason_code = data.get('reason_code', 'system_error')
    
    if not reason or len(reason.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='标记异常理由不能少于10个字')), 400
    
    before_data = order.to_dict()
    
    try:
        order.is_abnormal = True
        order.abnormal_reason = reason
        order.abnormal_reason_code = reason_code
        order.abnormal_time = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        after_data = order.to_dict()
        create_audit_log(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='mark_abnormal',
            reason=reason,
            before_data=before_data,
            after_data=after_data
        )
        
        return jsonify(success(data=order.to_dict(), msg='订单已标记为异常'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/refunds/stats', methods=['GET'])
@login_required
def get_refund_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    query = Order.query.filter(
        Order.refund_status.isnot(None),
        Order.refund_status != '',
        Order.refund_time >= start,
        Order.refund_time < end
    )
    
    total = query.count()
    
    status_stats = {}
    for status, name in REFUND_STATUS_NAMES.items():
        count = Order.query.filter(
            Order.refund_status == status,
            Order.refund_time >= start,
            Order.refund_time < end
        ).count()
        status_stats[status] = {
            'name': name,
            'count': count
        }
    
    total_amount = db.session.query(
        db.func.sum(Order.refund_amount)
    ).filter(
        Order.refund_status.in_(['approved', 'completed']),
        Order.refund_time >= start,
        Order.refund_time < end
    ).scalar() or 0
    
    abnormal_count = Order.query.filter(
        Order.refund_status.isnot(None),
        Order.refund_status != '',
        Order.is_abnormal == True,
        Order.refund_time >= start,
        Order.refund_time < end
    ).count()
    
    daily_data = []
    if (end - start).days <= 30:
        current = start
        while current < end:
            next_day = current + timedelta(days=1)
            
            day_query = Order.query.filter(
                Order.refund_time >= current,
                Order.refund_time < next_day,
                Order.refund_status.isnot(None),
                Order.refund_status != ''
            )
            
            day_total = day_query.count()
            day_approved = day_query.filter(Order.refund_status.in_(['approved', 'completed'])).count()
            day_amount = db.session.query(
                db.func.sum(Order.refund_amount)
            ).filter(
                Order.refund_status.in_(['approved', 'completed']),
                Order.refund_time >= current,
                Order.refund_time < next_day
            ).scalar() or 0
            
            daily_data.append({
                'date': current.strftime('%Y-%m-%d'),
                'total': day_total,
                'approved': day_approved,
                'amount': round(day_amount, 2)
            })
            current = next_day
    
    return jsonify(success(data={
        'summary': {
            'total': total,
            'approved': status_stats.get('approved', {}).get('count', 0) + status_stats.get('completed', {}).get('count', 0),
            'rejected': status_stats.get('rejected', {}).get('count', 0),
            'pending': status_stats.get('pending', {}).get('count', 0),
            'total_amount': round(total_amount, 2),
            'abnormal_count': abnormal_count
        },
        'status_stats': status_stats,
        'daily_data': daily_data,
        'period_start': start.strftime('%Y-%m-%d'),
        'period_end': (end - timedelta(days=1)).strftime('%Y-%m-%d')
    }))


@admin_bp.route('/refunds/stats/export', methods=['GET'])
@login_required
def export_refund_stats():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    refund_status = request.args.get('refund_status', '')
    
    start, end = get_date_range(period, start_date, end_date)
    
    query = Order.query.filter(
        Order.refund_status.isnot(None),
        Order.refund_status != '',
        Order.refund_time >= start,
        Order.refund_time < end
    )
    
    if refund_status:
        query = query.filter(Order.refund_status == refund_status)
    
    query = query.order_by(Order.refund_time.desc())
    refunds = query.all()
    
    headers = ['订单号', '用户', '老师', '订单金额', '退款金额', '退款状态', '是否异常', '申请时间', '处理时间']
    data = []
    
    for order in refunds:
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id)
        
        data.append([
            order.id,
            customer.nickname or customer.username if customer else '-',
            teacher.nickname or teacher.username if teacher else '-',
            order.pay_amount or 0,
            order.refund_amount or 0,
            REFUND_STATUS_NAMES.get(order.refund_status, order.refund_status),
            '是' if order.is_abnormal else '否',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '-',
            order.refund_time.strftime('%Y-%m-%d %H:%M:%S') if order.refund_time else '-'
        ])
    
    csv_content = generate_csv(data, headers, 'refund_stats.csv')
    
    return jsonify(success(data={
        'csv_content': csv_content,
        'filename': f'refund_stats_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
        'total': len(data)
    }))


@admin_bp.route('/orders/<order_id>/refund/official-intervene', methods=['POST'])
@login_required
def official_intervene_refund(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    if not order.refund_status or order.refund_status == '':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单没有退款申请')), 400
    
    if order.refund_status == REFUND_STATUS_COMPLETED:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该退款已完成，无需官方介入')), 400
    
    data = request.get_json() or {}
    intervene_reason = data.get('reason', '')
    
    if not intervene_reason or len(intervene_reason.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='介入理由至少需要10个字符')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.is_abnormal = True
    order.abnormal_reason = f'官方介入：{intervene_reason}'
    order.abnormal_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    refund_progress = RefundProgress(
        order_id=order.id,
        step='official_intervene',
        operator_id=admin_id,
        operator_type='admin',
        description='官方介入退款处理',
        reason=intervene_reason
    )
    db.session.add(refund_progress)
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='official_intervene_refund',
            reason=intervene_reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        try:
            MessageService.send_system_notification(
                order.user_id,
                '退款官方介入通知',
                f'您的订单 {order.id} 的退款申请已被官方介入处理。介入原因：{intervene_reason}。请耐心等待处理结果。',
                related_id=order.id,
                related_type='order'
            )
        except Exception as e:
            print(f'发送官方介入通知失败: {e}')
        
        return jsonify(success(data=order.to_dict(), msg='已标记为官方介入'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/refund/force-refund', methods=['POST'])
@login_required
def force_process_refund(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    if not order.refund_status or order.refund_status == '':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单没有退款申请')), 400
    
    if order.refund_status == REFUND_STATUS_COMPLETED:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该退款已完成')), 400
    
    data = request.get_json() or {}
    refund_amount = data.get('refund_amount', order.refund_amount or order.pay_amount)
    reason = data.get('reason', '管理员强制退款')
    
    if refund_amount <= 0 or refund_amount > order.pay_amount:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=f'退款金额必须大于0且不超过订单金额¥{order.pay_amount}')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.refund_status = REFUND_STATUS_COMPLETED
    order.refund_amount = refund_amount
    order.refund_approved_by = admin_id
    order.refund_audit_time = datetime.utcnow()
    order.refund_audit_by = admin_id
    order.refund_audit_reason = reason
    order.refund_process_time = datetime.utcnow()
    order.refund_complete_time = datetime.utcnow()
    order.status = 'cancelled'
    order.is_abnormal = False
    order.updated_at = datetime.utcnow()
    
    refund_progress_audit = RefundProgress(
        order_id=order.id,
        step=REFUND_STEP_AUDIT,
        status='approved',
        operator_id=admin_id,
        operator_type='admin',
        description='管理员审核通过退款',
        reason=reason,
        refund_amount=refund_amount
    )
    db.session.add(refund_progress_audit)
    
    refund_progress_complete = RefundProgress(
        order_id=order.id,
        step=REFUND_STEP_COMPLETE,
        status='completed',
        operator_id=admin_id,
        operator_type='admin',
        description='管理员强制完成退款',
        reason=reason,
        refund_amount=refund_amount
    )
    db.session.add(refund_progress_complete)
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='force_refund',
            reason=reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        try:
            MessageService.send_refund_notification(order, 'completed', refund_amount, reason)
        except Exception as e:
            print(f'发送强制退款通知失败: {e}')
        
        return jsonify(success(data=order.to_dict(), msg='强制退款成功，订单已标记为退款完成'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/refund/mark-abnormal', methods=['POST'])
@login_required
def mark_refund_abnormal(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    if not order.refund_status or order.refund_status == '':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单没有退款申请')), 400
    
    if order.refund_status == REFUND_STATUS_COMPLETED:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该退款已完成')), 400
    
    data = request.get_json() or {}
    abnormal_reason = data.get('reason', '')
    
    if not abnormal_reason or len(abnormal_reason.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='异常理由至少需要10个字符')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.refund_status = REFUND_STATUS_ABNORMAL
    order.refund_abnormal_reason = abnormal_reason
    order.refund_abnormal_time = datetime.utcnow()
    order.is_abnormal = True
    order.abnormal_reason = abnormal_reason
    order.abnormal_time = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    refund_progress = RefundProgress(
        order_id=order.id,
        step='abnormal',
        status='abnormal',
        operator_id=admin_id,
        operator_type='admin',
        description='标记为退款异常',
        reason=abnormal_reason
    )
    db.session.add(refund_progress)
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action='mark_refund_abnormal',
            reason=abnormal_reason,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        try:
            MessageService.send_system_notification(
                order.user_id,
                '退款异常通知',
                f'您的订单 {order.id} 的退款申请出现异常。异常原因：{abnormal_reason}。请联系客服或重新提交退款申请。',
                related_id=order.id,
                related_type='order'
            )
        except Exception as e:
            print(f'发送退款异常通知失败: {e}')
        
        return jsonify(success(data=order.to_dict(), msg='已标记为退款异常'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500


@admin_bp.route('/orders/<order_id>/refund/resolve-abnormal', methods=['POST'])
@login_required
def resolve_refund_abnormal(order_id):
    admin_id = g.get('user_id', 1)
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    if order.refund_status != REFUND_STATUS_ABNORMAL:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单不是退款异常状态')), 400
    
    data = request.get_json() or {}
    resolution = data.get('resolution', '')
    action = data.get('action', '')
    
    if not resolution or len(resolution.strip()) < 10:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='处理方案至少需要10个字符')), 400
    
    if action not in ['reset_to_pending', 'reject', 'approve']:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的操作类型')), 400
    
    old_order_data = json.dumps(order.to_dict(), ensure_ascii=False)
    
    order.refund_abnormal_resolved_at = datetime.utcnow()
    order.refund_abnormal_resolved_by = admin_id
    order.is_abnormal = False
    order.abnormal_resolved_at = datetime.utcnow()
    order.abnormal_resolved_by = admin_id
    
    if action == 'reset_to_pending':
        order.refund_status = REFUND_STATUS_PENDING
        status_desc = '待审核'
    elif action == 'reject':
        order.refund_status = REFUND_STATUS_REJECTED
        order.refund_audit_time = datetime.utcnow()
        order.refund_audit_by = admin_id
        order.refund_audit_reason = resolution
        if order.original_status_before_refund:
            order.status = order.original_status_before_refund
        status_desc = '已拒绝'
    else:
        order.refund_status = REFUND_STATUS_COMPLETED
        order.refund_audit_time = datetime.utcnow()
        order.refund_audit_by = admin_id
        order.refund_audit_reason = resolution
        order.refund_process_time = datetime.utcnow()
        order.refund_complete_time = datetime.utcnow()
        order.status = 'cancelled'
        status_desc = '已完成'
    
    order.updated_at = datetime.utcnow()
    
    refund_progress = RefundProgress(
        order_id=order.id,
        step='resolve_abnormal',
        status=action,
        operator_id=admin_id,
        operator_type='admin',
        description=f'管理员解决退款异常，状态变更为：{status_desc}',
        reason=resolution
    )
    db.session.add(refund_progress)
    
    try:
        db.session.commit()
        
        audit_log = AuditLog(
            admin_id=admin_id,
            target_type='order',
            target_id=order.id if isinstance(order.id, int) else 0,
            action=f'resolve_refund_abnormal_{action}',
            reason=resolution,
            before_data=old_order_data,
            after_data=json.dumps(order.to_dict(), ensure_ascii=False)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        try:
            MessageService.send_system_notification(
                order.user_id,
                '退款异常处理通知',
                f'您的订单 {order.id} 的退款异常已处理。处理方案：{resolution}。当前退款状态：{status_desc}。',
                related_id=order.id,
                related_type='order'
            )
        except Exception as e:
            print(f'发送退款异常处理通知失败: {e}')
        
        return jsonify(success(data=order.to_dict(), msg=f'退款异常已解决，状态变更为：{status_desc}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'操作失败: {str(e)}')), 500
