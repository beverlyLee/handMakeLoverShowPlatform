from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.response_code import ResponseCode
from app.common.auth import login_required
from app.models import Review, AppendReview, Order, Product, User, TeacherProfile, \
    PRODUCT_DETAIL_ITEMS, TEACHER_DETAIL_ITEMS, LOGISTICS_DETAIL_ITEMS
from app.database import db
from app.services.message_service import MessageService
from datetime import datetime
from sqlalchemy import func

review_bp = Blueprint('reviews', __name__)


def get_current_user():
    user_id = g.get('user_id', 1)
    return user_id


def get_user_nickname(user_id):
    user = User.query.get(user_id)
    if user:
        return user.nickname or user.username
    return None


def get_user_avatar(user_id):
    user = User.query.get(user_id)
    if user:
        return user.avatar
    return None


def get_user_role(user_id):
    user = User.query.get(user_id)
    if user:
        return user.current_role
    return None


def get_role_label(role):
    if role == 'teacher':
        return '老师'
    else:
        return '用户'


def get_teacher_profile(teacher_user_id):
    teacher_profile = TeacherProfile.query.filter_by(user_id=teacher_user_id).first()
    return teacher_profile


def update_product_rating(product_id):
    reviews = Review.query.filter_by(
        product_id=product_id,
        is_hidden=False
    ).all()
    
    if not reviews:
        return
    
    total_product_rating = 0.0
    count = 0
    for review in reviews:
        total_product_rating += review.product_rating
        count += 1
    
    if count > 0:
        avg_rating = round(total_product_rating / count, 1)
        product = Product.query.get(product_id)
        if product:
            product.rating = avg_rating
            db.session.commit()


def update_teacher_rating(teacher_user_id):
    reviews = Review.query.filter_by(
        teacher_id=teacher_user_id,
        is_hidden=False
    ).all()
    
    if not reviews:
        return
    
    total_teacher_rating = 0.0
    count = 0
    for review in reviews:
        total_teacher_rating += review.teacher_rating
        count += 1
    
    if count > 0:
        avg_rating = round(total_teacher_rating / count, 1)
        teacher_profile = get_teacher_profile(teacher_user_id)
        if teacher_profile:
            teacher_profile.rating = avg_rating
            db.session.commit()


def get_review_stats(query):
    reviews = query.all()
    stats = {
        'total': len(reviews),
        'avg_overall_rating': 0.0,
        'avg_product_rating': 0.0,
        'avg_teacher_rating': 0.0,
        'avg_logistics_rating': 0.0,
        'rating_distribution': {
            '5': 0, '4.5': 0, '4': 0, '3.5': 0, '3': 0,
            '2.5': 0, '2': 0, '1.5': 0, '1': 0, '0.5': 0
        },
        'good_count': 0,
        'medium_count': 0,
        'bad_count': 0,
        'has_image': 0,
        'has_reply': 0
    }
    
    if not reviews:
        return stats
    
    total_overall = 0.0
    total_product = 0.0
    total_teacher = 0.0
    total_logistics = 0.0
    count = 0
    
    for review in reviews:
        total_overall += review.overall_rating
        total_product += review.product_rating
        total_teacher += review.teacher_rating
        total_logistics += review.logistics_rating
        count += 1
        
        rating_key = str(review.overall_rating)
        if rating_key in stats['rating_distribution']:
            stats['rating_distribution'][rating_key] += 1
        
        if review.overall_rating >= 4.0:
            stats['good_count'] += 1
        elif review.overall_rating >= 2.0:
            stats['medium_count'] += 1
        else:
            stats['bad_count'] += 1
        
        if review.images and len(review.images) > 0:
            stats['has_image'] += 1
        
        if review.reply_content:
            stats['has_reply'] += 1
    
    if count > 0:
        stats['avg_overall_rating'] = round(total_overall / count, 1)
        stats['avg_product_rating'] = round(total_product / count, 1)
        stats['avg_teacher_rating'] = round(total_teacher / count, 1)
        stats['avg_logistics_rating'] = round(total_logistics / count, 1)
    
    return stats


def enrich_append_review(append_review, include_user=False):
    append_dict = append_review.to_dict(include_user=include_user)
    
    if include_user:
        nickname = get_user_nickname(append_review.user_id)
        avatar = get_user_avatar(append_review.user_id)
        role = get_user_role(append_review.user_id)
        role_label = get_role_label(role)
        append_dict['user_info'] = {
            'nickname': nickname,
            'avatar': avatar,
            'role': role,
            'role_label': role_label
        }
        append_dict['user_name'] = nickname
        append_dict['user_avatar'] = avatar
        append_dict['user_role'] = role
        append_dict['user_role_label'] = role_label
    
    return append_dict


def enrich_review(review, include_user=False, include_product=False, include_order=False, include_teacher=False, include_append_reviews=True):
    review_dict = review.to_dict(
        include_user=include_user,
        include_product=include_product,
        include_order=include_order,
        include_teacher=include_teacher
    )
    
    if include_user:
        if review.is_anonymous:
            review_dict['user_info'] = {
                'nickname': '匿名用户',
                'avatar': None,
                'role': 'customer',
                'role_label': '用户'
            }
            review_dict['user_name'] = '匿名用户'
            review_dict['user_avatar'] = None
            review_dict['user_role'] = 'customer'
            review_dict['user_role_label'] = '用户'
        else:
            nickname = get_user_nickname(review.user_id)
            avatar = get_user_avatar(review.user_id)
            role = get_user_role(review.user_id)
            role_label = get_role_label(role)
            review_dict['user_info'] = {
                'nickname': nickname,
                'avatar': avatar,
                'role': role,
                'role_label': role_label
            }
            review_dict['user_name'] = nickname
            review_dict['user_avatar'] = avatar
            review_dict['user_role'] = role
            review_dict['user_role_label'] = role_label
    
    if include_teacher:
        review_dict['teacher_info'] = {
            'nickname': get_user_nickname(review.teacher_id),
            'avatar': get_user_avatar(review.teacher_id)
        }
    
    if include_append_reviews:
        append_reviews = AppendReview.query.filter_by(
            review_id=review.id
        ).order_by(AppendReview.created_at.asc()).all()
        
        review_dict['append_reviews'] = [
            enrich_append_review(ar, include_user=True) for ar in append_reviews
        ]
    
    return review_dict


@review_bp.route('/detail-items', methods=['GET'])
def get_detail_items():
    return jsonify(success(data={
        'product_detail_items': PRODUCT_DETAIL_ITEMS,
        'teacher_detail_items': TEACHER_DETAIL_ITEMS,
        'logistics_detail_items': LOGISTICS_DETAIL_ITEMS
    }))


@review_bp.route('/', methods=['GET'])
@login_required
def get_reviews():
    user_id = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    product_id = request.args.get('product_id', None, type=int)
    teacher_id = request.args.get('teacher_id', None, type=int)
    order_id = request.args.get('order_id', None)
    user_id_filter = request.args.get('user_id', None, type=int)
    
    min_rating = request.args.get('min_rating', None, type=float)
    max_rating = request.args.get('max_rating', None, type=float)
    has_image = request.args.get('has_image', None, type=bool)
    has_reply = request.args.get('has_reply', None, type=bool)
    
    query = Review.query.filter_by(is_hidden=False)
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    
    if order_id:
        query = query.filter_by(order_id=order_id)
    
    if user_id_filter:
        query = query.filter_by(user_id=user_id_filter)
    
    if min_rating is not None:
        query = query.filter(Review.overall_rating >= min_rating)
    
    if max_rating is not None:
        query = query.filter(Review.overall_rating <= max_rating)
    
    if has_image is not None:
        if has_image:
            query = query.filter(Review._images.isnot(None))
        else:
            query = query.filter(
                (Review._images.is_(None)) | 
                (Review._images == '[]')
            )
    
    if has_reply is not None:
        if has_reply:
            query = query.filter(Review.reply_content.isnot(None))
        else:
            query = query.filter(Review.reply_content.is_(None))
    
    stats = get_review_stats(query)
    
    total = query.count()
    query = query.order_by(Review.created_at.desc())
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    reviews_list = []
    for review in paginated:
        reviews_list.append(enrich_review(
            review,
            include_user=True,
            include_product=True,
            include_order=True
        ))
    
    return jsonify(success(data={
        'list': reviews_list,
        'total': total,
        'page': page,
        'size': size,
        'stats': stats,
        'detail_items': {
            'product': PRODUCT_DETAIL_ITEMS,
            'teacher': TEACHER_DETAIL_ITEMS,
            'logistics': LOGISTICS_DETAIL_ITEMS
        }
    }))


@review_bp.route('/<int:review_id>', methods=['GET'])
@login_required
def get_review(review_id):
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    return jsonify(success(data=enrich_review(
        review,
        include_user=True,
        include_product=True,
        include_order=True
    )))


@review_bp.route('/order/<order_id>', methods=['GET'])
@login_required
def get_order_review(order_id):
    user_id = get_current_user()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id and order.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权查看此评价')), 403
    
    review = Review.query.filter_by(order_id=order_id).first()
    
    if not review:
        return jsonify(success(data={
            'has_review': False,
            'review': None,
            'order_info': order.to_dict(),
            'detail_items': {
                'product': PRODUCT_DETAIL_ITEMS,
                'teacher': TEACHER_DETAIL_ITEMS,
                'logistics': LOGISTICS_DETAIL_ITEMS
            }
        }))
    
    return jsonify(success(data={
        'has_review': True,
        'review': enrich_review(
            review,
            include_user=True,
            include_product=True,
            include_order=True
        ),
        'order_info': order.to_dict()
    }))


@review_bp.route('/', methods=['POST'])
@login_required
def create_review():
    user_id = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    order_id = data.get('order_id')
    if not order_id:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='订单ID不能为空')), 400
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    if order.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只能评价自己的订单')), 403
    
    if order.status != 'completed':
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='只能评价已完成的订单')), 400
    
    existing_review = Review.query.filter_by(order_id=order_id).first()
    if existing_review:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='该订单已评价过')), 400
    
    product_detail_ratings = data.get('product_detail_ratings', {})
    teacher_detail_ratings = data.get('teacher_detail_ratings', {})
    logistics_detail_ratings = data.get('logistics_detail_ratings', {})
    
    if len(product_detail_ratings) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请完成商品评价')), 400
    
    if len(teacher_detail_ratings) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请完成老师评价')), 400
    
    if len(logistics_detail_ratings) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请完成物流评价')), 400
    
    product_rating = Review.calculate_average_rating(
        product_detail_ratings,
        PRODUCT_DETAIL_ITEMS
    )
    teacher_rating = Review.calculate_average_rating(
        teacher_detail_ratings,
        TEACHER_DETAIL_ITEMS
    )
    logistics_rating = Review.calculate_average_rating(
        logistics_detail_ratings,
        LOGISTICS_DETAIL_ITEMS
    )
    overall_rating = Review.calculate_overall_rating(
        product_rating,
        teacher_rating,
        logistics_rating
    )
    
    order_item = None
    for item in order.items:
        order_item = item
        break
    
    product_id = order_item.product_id if order_item else None
    if not product_id:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单商品信息缺失')), 400
    
    product = Product.query.get(product_id)
    teacher_user_id = order.teacher_id or (product.teacher_profile.user_id if product and product.teacher_profile else None)
    
    if not teacher_user_id:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='老师信息缺失')), 400
    
    review = Review(
        order_id=order_id,
        user_id=user_id,
        product_id=product_id,
        teacher_id=teacher_user_id,
        overall_rating=overall_rating,
        product_rating=product_rating,
        teacher_rating=teacher_rating,
        logistics_rating=logistics_rating,
        content=data.get('content', ''),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    review.product_detail_ratings = product_detail_ratings
    review.teacher_detail_ratings = teacher_detail_ratings
    review.logistics_detail_ratings = logistics_detail_ratings
    review.images = data.get('images', [])
    
    db.session.add(review)
    db.session.commit()
    
    try:
        update_product_rating(product_id)
        update_teacher_rating(teacher_user_id)
    except Exception as e:
        print(f'更新评分统计失败: {e}')
    
    try:
        MessageService.send_review_notification(review, is_reply=False)
    except Exception as e:
        print(f'发送评价通知失败: {e}')
    
    return jsonify(success(
        data=enrich_review(review, include_user=True, include_product=True),
        msg='评价提交成功'
    ))


@review_bp.route('/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    user_id = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    if review.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只能修改自己的评价')), 403
    
    product_detail_ratings = data.get('product_detail_ratings')
    teacher_detail_ratings = data.get('teacher_detail_ratings')
    logistics_detail_ratings = data.get('logistics_detail_ratings')
    
    if product_detail_ratings is not None:
        review.product_detail_ratings = product_detail_ratings
        if len(product_detail_ratings) > 0:
            review.product_rating = Review.calculate_average_rating(
                product_detail_ratings,
                PRODUCT_DETAIL_ITEMS
            )
    
    if teacher_detail_ratings is not None:
        review.teacher_detail_ratings = teacher_detail_ratings
        if len(teacher_detail_ratings) > 0:
            review.teacher_rating = Review.calculate_average_rating(
                teacher_detail_ratings,
                TEACHER_DETAIL_ITEMS
            )
    
    if logistics_detail_ratings is not None:
        review.logistics_detail_ratings = logistics_detail_ratings
        if len(logistics_detail_ratings) > 0:
            review.logistics_rating = Review.calculate_average_rating(
                logistics_detail_ratings,
                LOGISTICS_DETAIL_ITEMS
            )
    
    if data.get('content') is not None:
        review.content = data.get('content')
    
    if data.get('images') is not None:
        review.images = data.get('images')
    
    if data.get('is_anonymous') is not None:
        review.is_anonymous = data.get('is_anonymous')
    
    if product_detail_ratings is not None or teacher_detail_ratings is not None or logistics_detail_ratings is not None:
        review.overall_rating = Review.calculate_overall_rating(
            review.product_rating,
            review.teacher_rating,
            review.logistics_rating
        )
    
    review.updated_at = datetime.utcnow()
    db.session.commit()
    
    try:
        update_product_rating(review.product_id)
        update_teacher_rating(review.teacher_id)
    except Exception as e:
        print(f'更新评分统计失败: {e}')
    
    return jsonify(success(
        data=enrich_review(review, include_user=True, include_product=True),
        msg='评价更新成功'
    ))


@review_bp.route('/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    user_id = get_current_user()
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    if review.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只能删除自己的评价')), 403
    
    product_id = review.product_id
    teacher_id = review.teacher_id
    order_id = review.order_id
    
    AppendReview.query.filter_by(review_id=review_id).delete()
    
    db.session.delete(review)
    db.session.commit()
    
    try:
        update_product_rating(product_id)
        update_teacher_rating(teacher_id)
    except Exception as e:
        print(f'更新评分统计失败: {e}')
    
    return jsonify(success(data=None, msg='评价删除成功'))


@review_bp.route('/<int:review_id>/reply', methods=['POST'])
@login_required
def reply_review(review_id):
    user_id = get_current_user()
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='回复内容不能为空')), 400
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    if review.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只有老师可以回复评价')), 403
    
    review.reply_content = data.get('content')
    review.reply_time = datetime.utcnow()
    review.reply_count = (review.reply_count or 0) + 1
    review.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    try:
        MessageService.send_review_notification(review, is_reply=True)
    except Exception as e:
        print(f'发送回复通知失败: {e}')
    
    return jsonify(success(data=enrich_review(review, include_user=True), msg='回复成功'))


@review_bp.route('/<int:review_id>/append', methods=['POST'])
@login_required
def append_review(review_id):
    user_id = get_current_user()
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='追加评论内容不能为空')), 400
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    append_review = AppendReview(
        review_id=review_id,
        user_id=user_id,
        content=data.get('content'),
        images=data.get('images', [])
    )
    
    db.session.add(append_review)
    db.session.commit()
    
    return jsonify(success(data=enrich_review(review, include_user=True), msg='追加评论成功'))


@review_bp.route('/append/<int:append_review_id>', methods=['DELETE'])
@login_required
def delete_append_review(append_review_id):
    user_id = get_current_user()
    
    append_review = AppendReview.query.get(append_review_id)
    
    if not append_review:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='追加评论不存在')), 404
    
    if append_review.user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只能删除自己的追加评论')), 403
    
    review_id = append_review.review_id
    
    db.session.delete(append_review)
    db.session.commit()
    
    review = Review.query.get(review_id)
    if review:
        return jsonify(success(data=enrich_review(review, include_user=True), msg='追加评论删除成功'))
    
    return jsonify(success(data=None, msg='追加评论删除成功'))


@review_bp.route('/product/<int:product_id>/stats', methods=['GET'])
def get_product_review_stats(product_id):
    query = Review.query.filter_by(
        product_id=product_id,
        is_hidden=False
    )
    stats = get_review_stats(query)
    
    return jsonify(success(data={
        'product_id': product_id,
        'stats': stats,
        'detail_items': {
            'product': PRODUCT_DETAIL_ITEMS,
            'teacher': TEACHER_DETAIL_ITEMS,
            'logistics': LOGISTICS_DETAIL_ITEMS
        }
    }))


@review_bp.route('/teacher/<int:teacher_user_id>/stats', methods=['GET'])
def get_teacher_review_stats(teacher_user_id):
    query = Review.query.filter_by(
        teacher_id=teacher_user_id,
        is_hidden=False
    )
    stats = get_review_stats(query)
    
    return jsonify(success(data={
        'teacher_user_id': teacher_user_id,
        'stats': stats
    }))


@review_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    min_rating = request.args.get('min_rating', None, type=float)
    max_rating = request.args.get('max_rating', None, type=float)
    has_image = request.args.get('has_image', None, type=bool)
    sort_by = request.args.get('sort_by', 'newest')
    
    query = Review.query.filter_by(
        product_id=product_id,
        is_hidden=False
    )
    
    if min_rating is not None:
        query = query.filter(Review.overall_rating >= min_rating)
    
    if max_rating is not None:
        query = query.filter(Review.overall_rating <= max_rating)
    
    if has_image is not None:
        if has_image:
            query = query.filter(Review._images.isnot(None))
        else:
            query = query.filter(
                (Review._images.is_(None)) | 
                (Review._images == '[]')
            )
    
    stats = get_review_stats(query)
    
    total = query.count()
    if sort_by == 'best':
        query = query.order_by(Review.overall_rating.desc(), Review.created_at.desc())
    else:
        query = query.order_by(Review.created_at.desc())
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    reviews_list = []
    for review in paginated:
        reviews_list.append(enrich_review(review, include_user=True))
    
    return jsonify(success(data={
        'list': reviews_list,
        'total': total,
        'page': page,
        'size': size,
        'stats': stats
    }))


@review_bp.route('/teacher/<int:teacher_user_id>', methods=['GET'])
def get_teacher_reviews(teacher_user_id):
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    min_rating = request.args.get('min_rating', None, type=float)
    max_rating = request.args.get('max_rating', None, type=float)
    has_image = request.args.get('has_image', None, type=bool)
    sort_by = request.args.get('sort_by', 'newest')
    
    query = Review.query.filter_by(
        teacher_id=teacher_user_id,
        is_hidden=False
    )
    
    if min_rating is not None:
        query = query.filter(Review.overall_rating >= min_rating)
    
    if max_rating is not None:
        query = query.filter(Review.overall_rating <= max_rating)
    
    if has_image is not None:
        if has_image:
            query = query.filter(Review._images.isnot(None))
        else:
            query = query.filter(
                (Review._images.is_(None)) | 
                (Review._images == '[]')
            )
    
    stats = get_review_stats(query)
    
    total = query.count()
    if sort_by == 'best':
        query = query.order_by(Review.overall_rating.desc(), Review.created_at.desc())
    else:
        query = query.order_by(Review.created_at.desc())
    paginated = query.offset((page - 1) * size).limit(size).all()
    
    reviews_list = []
    for review in paginated:
        reviews_list.append(enrich_review(
            review,
            include_user=True,
            include_product=True
        ))
    
    return jsonify(success(data={
        'list': reviews_list,
        'total': total,
        'page': page,
        'size': size,
        'stats': stats
    }))


@review_bp.route('/<int:review_id>', methods=['GET'])
@login_required
def get_review_by_id(review_id):
    user_id = get_current_user()
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    return jsonify(success(
        data=enrich_review(
            review,
            include_user=True,
            include_product=True,
            include_order=True,
            include_teacher=True
        )
    ))


@review_bp.route('/<int:review_id>/like', methods=['POST'])
@login_required
def like_review(review_id):
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    review.like_count = (review.like_count or 0) + 1
    review.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data={'like_count': review.like_count}, msg='点赞成功'))


@review_bp.route('/calculate-rating', methods=['POST'])
def calculate_rating():
    data = request.get_json() or {}
    
    product_detail_ratings = data.get('product_detail_ratings', {})
    teacher_detail_ratings = data.get('teacher_detail_ratings', {})
    logistics_detail_ratings = data.get('logistics_detail_ratings', {})
    
    product_rating = Review.calculate_average_rating(
        product_detail_ratings,
        PRODUCT_DETAIL_ITEMS
    )
    teacher_rating = Review.calculate_average_rating(
        teacher_detail_ratings,
        TEACHER_DETAIL_ITEMS
    )
    logistics_rating = Review.calculate_average_rating(
        logistics_detail_ratings,
        LOGISTICS_DETAIL_ITEMS
    )
    overall_rating = Review.calculate_overall_rating(
        product_rating,
        teacher_rating,
        logistics_rating
    )
    
    return jsonify(success(data={
        'product_rating': product_rating,
        'teacher_rating': teacher_rating,
        'logistics_rating': logistics_rating,
        'overall_rating': overall_rating
    }))


@review_bp.route('/<int:review_id>/read', methods=['POST'])
@login_required
def mark_review_read(review_id):
    user_id = get_current_user()
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    if review.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此评价')), 403
    
    review.is_read = True
    review.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(success(data=enrich_review(review, include_user=True, include_product=True), msg='已标记为已读'))


@review_bp.route('/batch-read', methods=['POST'])
@login_required
def mark_reviews_batch_read():
    user_id = get_current_user()
    data = request.get_json()
    
    if not data or not data.get('review_ids'):
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='评价ID列表不能为空')), 400
    
    review_ids = data.get('review_ids')
    
    if not isinstance(review_ids, list) or len(review_ids) == 0:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='评价ID列表不能为空')), 400
    
    count = Review.query.filter(
        Review.id.in_(review_ids),
        Review.teacher_id == user_id,
        Review.is_hidden == False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    }, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify(success(data={'marked_count': count}, msg=f'已标记 {count} 条评价为已读'))


@review_bp.route('/teacher/<int:teacher_user_id>/unread-stats', methods=['GET'])
@login_required
def get_teacher_unread_stats(teacher_user_id):
    user_id = get_current_user()
    
    if user_id != teacher_user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权查看此统计')), 403
    
    query = Review.query.filter_by(
        teacher_id=teacher_user_id,
        is_hidden=False
    )
    
    total = query.count()
    unread = query.filter_by(is_read=False).count()
    pending_reply = query.filter(Review.reply_content.is_(None)).count()
    
    return jsonify(success(data={
        'total': total,
        'unread': unread,
        'pending_reply': pending_reply
    }))


@review_bp.route('/<int:review_id>/reply', methods=['PUT'])
@login_required
def update_review_reply(review_id):
    user_id = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    review = Review.query.get(review_id)
    
    if not review or review.is_hidden:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='评价不存在')), 404
    
    if review.teacher_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='只有老师可以回复评价')), 403
    
    content = data.get('content')
    
    if content is None:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='回复内容不能为空')), 400
    
    if content == '':
        review.reply_content = None
        review.reply_time = None
        review.reply_count = max(0, (review.reply_count or 1) - 1)
    else:
        review.reply_content = content
        review.reply_time = datetime.utcnow()
        if not review.reply_content:
            review.reply_count = (review.reply_count or 0) + 1
    
    review.updated_at = datetime.utcnow()
    db.session.commit()
    
    if content and review.reply_content:
        try:
            MessageService.send_review_notification(review, is_reply=True)
        except Exception as e:
            print(f'发送回复通知失败: {e}')
    
    return jsonify(success(data=enrich_review(review, include_user=True), msg='回复已更新'))


@review_bp.route('/teacher/<int:teacher_user_id>/trend-stats', methods=['GET'])
@login_required
def get_teacher_trend_stats(teacher_user_id):
    user_id = get_current_user()
    
    if user_id != teacher_user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权查看此统计')), 403
    
    days = request.args.get('days', 30, type=int)
    days = min(max(days, 7), 90)
    
    from datetime import timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    reviews = Review.query.filter(
        Review.teacher_id == teacher_user_id,
        Review.is_hidden == False,
        Review.created_at >= start_date,
        Review.created_at <= end_date
    ).order_by(Review.created_at.asc()).all()
    
    daily_stats = {}
    for review in reviews:
        date_key = review.created_at.strftime('%Y-%m-%d')
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'date': date_key,
                'count': 0,
                'total_rating': 0.0,
                'avg_rating': 0.0,
                'good_count': 0,
                'medium_count': 0,
                'bad_count': 0
            }
        
        stat = daily_stats[date_key]
        stat['count'] += 1
        stat['total_rating'] += review.overall_rating
        
        if review.overall_rating >= 4.0:
            stat['good_count'] += 1
        elif review.overall_rating >= 2.0:
            stat['medium_count'] += 1
        else:
            stat['bad_count'] += 1
    
    trend_data = []
    for i in range(days):
        current_date = end_date - timedelta(days=i)
        date_key = current_date.strftime('%Y-%m-%d')
        
        if date_key in daily_stats:
            stat = daily_stats[date_key]
            stat['avg_rating'] = round(stat['total_rating'] / stat['count'], 1) if stat['count'] > 0 else 0.0
            trend_data.append(stat)
        else:
            trend_data.append({
                'date': date_key,
                'count': 0,
                'total_rating': 0.0,
                'avg_rating': 0.0,
                'good_count': 0,
                'medium_count': 0,
                'bad_count': 0
            })
    
    trend_data.reverse()
    
    overall_stats = get_review_stats(Review.query.filter_by(
        teacher_id=teacher_user_id,
        is_hidden=False
    ))
    
    return jsonify(success(data={
        'trend_data': trend_data,
        'overall_stats': overall_stats,
        'days': days
    }))
