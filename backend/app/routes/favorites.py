from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.database import db
from app.models import Like, Product, User, TeacherProfile
from app.services.message_service import MessageService

favorite_bp = Blueprint('favorites', __name__)

@favorite_bp.route('/like', methods=['POST'])
@login_required
def toggle_like():
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='缺少产品ID参数')), 400
    
    user_id = g.get('user_id')
    product_id = data.get('product_id')
    
    product = Product.query.get(product_id)
    if not product or product.status != 'active':
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在或已下架')), 404
    
    existing_like = Like.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        product.like_count = (product.like_count or 0) - 1
        is_liked = False
    else:
        new_like = Like(user_id=user_id, product_id=product_id)
        db.session.add(new_like)
        product.like_count = (product.like_count or 0) + 1
        is_liked = True
    
    product.update_heat_score()
    db.session.commit()
    
    if is_liked and product.teacher_profile:
        liker_user = User.query.get(user_id)
        teacher_profile = product.teacher_profile
        teacher_user = User.query.get(teacher_profile.user_id)
        
        if liker_user and teacher_user:
            try:
                MessageService.send_like_notification(liker_user, product, teacher_user)
            except Exception as e:
                print(f"发送点赞通知失败: {e}")
    
    return jsonify(success(data={
        'is_liked': is_liked,
        'like_count': product.like_count,
        'heat_score': product.heat_score,
        'popularity_score': product.popularity_score
    }, msg='点赞成功' if is_liked else '取消点赞成功'))

@favorite_bp.route('/like/<int:product_id>', methods=['GET'])
@login_required
def check_like_status(product_id):
    user_id = g.get('user_id')
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    existing_like = Like.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    return jsonify(success(data={
        'product_id': product_id,
        'is_liked': existing_like is not None,
        'like_count': product.like_count or 0
    }))

@favorite_bp.route('/like/count/<int:product_id>', methods=['GET'])
def get_like_count(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    return jsonify(success(data={
        'product_id': product_id,
        'like_count': product.like_count or 0
    }))

@favorite_bp.route('/like/my', methods=['GET'])
@login_required
def get_my_likes():
    user_id = g.get('user_id')
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    query = Like.query.filter_by(user_id=user_id).order_by(Like.created_at.desc())
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    likes = []
    for like in pagination.items:
        like_dict = like.to_dict()
        
        if like.product:
            product_dict = like.product.to_dict()
            if like.product.teacher_profile:
                product_dict['teacher'] = {
                    'id': like.product.teacher_profile.id,
                    'teacher_id': like.product.teacher_profile.teacher_id,
                    'user_id': like.product.teacher_profile.user_id,
                    'real_name': like.product.teacher_profile.real_name,
                    'nickname': like.product.teacher_profile.user.nickname if like.product.teacher_profile.user else None,
                    'avatar': like.product.teacher_profile.user.avatar if like.product.teacher_profile.user else None,
                    'rating': like.product.teacher_profile.rating
                }
            like_dict['product'] = product_dict
        
        likes.append(like_dict)
    
    return jsonify(success(data={
        'list': likes,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next
    }))

@favorite_bp.route('/like/batch-check', methods=['POST'])
@login_required
def batch_check_like_status():
    data = request.get_json()
    if not data or 'product_ids' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='缺少产品ID列表参数')), 400
    
    user_id = g.get('user_id')
    product_ids = data.get('product_ids', [])
    
    if not isinstance(product_ids, list):
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='产品ID列表参数格式错误')), 400
    
    likes = Like.query.filter(
        Like.user_id == user_id,
        Like.product_id.in_(product_ids)
    ).all()
    
    liked_product_ids = [like.product_id for like in likes]
    
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    like_counts = {p.id: p.like_count or 0 for p in products}
    
    result = []
    for product_id in product_ids:
        result.append({
            'product_id': product_id,
            'is_liked': product_id in liked_product_ids,
            'like_count': like_counts.get(product_id, 0)
        })
    
    return jsonify(success(data=result))