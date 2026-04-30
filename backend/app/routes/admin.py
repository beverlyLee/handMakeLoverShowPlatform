from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from io import StringIO
import csv
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.database import db
from app.models import User, Product, Order, Category, Activity, Review, TeacherProfile, OrderItem, Like, ActivityRegistration, CRAFT_TYPES, ACTIVITY_TYPES

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
    'deleted': '已删除'
}

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

@admin_bp.route('/users/list', methods=['GET'])
@login_required
def get_users_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    role = request.args.get('role', '')
    sort = request.args.get('sort', 'newest')
    
    query = User.query
    
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.nickname.contains(keyword),
                User.phone.contains(keyword)
            )
        )
    
    if role:
        if role == 'teacher':
            query = query.filter(User._roles.contains('"teacher"'))
        elif role == 'customer':
            query = query.filter(User._roles.contains('"customer"'))
    
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
            user_dict['teacher_info'] = {
                'id': teacher_profile.id,
                'real_name': teacher_profile.real_name,
                'rating': teacher_profile.rating,
                'is_verified': teacher_profile.is_verified,
                'follower_count': teacher_profile.follower_count
            }
        users.append(user_dict)
    
    return jsonify(success(data={
        'list': users,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
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
            'total_products': Product.query.filter_by(user_id=user.id, status='active').count()
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
            Product.user_id == teacher_user.id,
            Product.created_at >= start,
            Product.created_at < end
        ).count()
        
        total_products = Product.query.filter_by(user_id=teacher_user.id, status='active').count()
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
            Product.user_id == teacher_user.id,
            Product.created_at >= start,
            Product.created_at < end
        ).count()
        
        total_products = Product.query.filter_by(user_id=teacher_user.id, status='active').count()
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
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Product.title.contains(keyword),
                Product.description.contains(keyword)
            )
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
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
        
        if p.user_id:
            teacher = User.query.get(p.user_id)
            if teacher:
                product_dict['teacher_name'] = teacher.nickname or teacher.username
        
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
        
        items = OrderItem.query.filter_by(order_id=order.id).all()
        order_dict['items'] = [item.to_dict() for item in items]
        order_dict['item_count'] = len(items)
        
        orders.append(order_dict)
    
    return jsonify(success(data={
        'list': orders,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages
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
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请提供新状态')), 400
    
    if new_status not in STATUS_NAMES:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='无效的订单状态')), 400
    
    old_status = order.status
    order.status = new_status
    
    if new_status == 'completed':
        order.complete_time = datetime.utcnow()
    elif new_status == 'cancelled':
        order.cancel_time = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=order.to_dict(), msg=f'订单状态已从{STATUS_NAMES.get(old_status, old_status)}更新为{STATUS_NAMES.get(new_status, new_status)}'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500

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
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    craft_type = request.args.get('craft_type', '')
    activity_type = request.args.get('activity_type', '')
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
    rating = request.args.get('rating', type=int)
    sort = request.args.get('sort', 'newest')
    
    query = Review.query
    
    if keyword:
        query = query.filter(
            db.or_(
                Review.content.contains(keyword),
                Review.reply.contains(keyword)
            )
        )
    
    if rating:
        query = query.filter(Review.rating == rating)
    
    if sort == 'newest':
        query = query.order_by(Review.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Review.created_at.asc())
    elif sort == 'rating_desc':
        query = query.order_by(Review.rating.desc())
    elif sort == 'rating_asc':
        query = query.order_by(Review.rating.asc())
    
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

@admin_bp.route('/reviews/<int:review_id>/reply', methods=['POST'])
@login_required
def reply_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='评价不存在')), 404
    
    data = request.get_json()
    reply = data.get('reply', '')
    
    review.reply = reply
    review.reply_time = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify(success(data=review.to_dict(), msg='回复成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'回复失败: {str(e)}')), 500

@admin_bp.route('/categories/list', methods=['GET'])
@login_required
def get_categories_list():
    categories = Category.query.filter(Category.status == 'active').order_by(Category.sort_order.asc()).all()
    
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
