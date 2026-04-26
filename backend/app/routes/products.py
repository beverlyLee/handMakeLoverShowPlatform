from flask import Blueprint, jsonify, request
from app.utils.response import success, error
from app.common.response_code import ResponseCode
from app.database import db
from app.models import Product, Category, TeacherProfile

product_bp = Blueprint('products', __name__)

SORT_OPTIONS = {
    'default': Product.created_at.desc(),
    'price_asc': Product.price.asc(),
    'price_desc': Product.price.desc(),
    'sales': Product.sales_count.desc(),
    'popular': Product.favorite_count.desc(),
    'newest': Product.created_at.desc()
}

@product_bp.route('', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    category_id = request.args.get('category', None, type=int)
    keyword = request.args.get('keyword', None, type=str)
    sort = request.args.get('sort', 'default', type=str)
    teacher_id = request.args.get('teacher_id', None, type=int)
    status = request.args.get('status', 'active', type=str)
    
    query = Product.query
    
    if status:
        query = query.filter(Product.status == status)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if teacher_id:
        query = query.filter(Product.teacher_id == teacher_id)
    
    if keyword:
        query = query.filter(
            db.or_(
                Product.title.contains(keyword),
                Product.description.contains(keyword)
            )
        )
    
    order_by = SORT_OPTIONS.get(sort, SORT_OPTIONS['default'])
    query = query.order_by(order_by)
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    products = []
    for product in pagination.items:
        product_dict = product.to_dict()
        if product.teacher_profile:
            product_dict['teacher'] = {
                'id': product.teacher_profile.id,
                'teacher_id': product.teacher_profile.teacher_id,
                'real_name': product.teacher_profile.real_name,
                'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None,
                'rating': product.teacher_profile.rating
            }
        products.append(product_dict)
    
    return jsonify(success(data={
        'list': products,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }))

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在')), 404
    
    product.view_count = (product.view_count or 0) + 1
    db.session.commit()
    
    product_dict = product.to_dict()
    
    if product.teacher_profile:
        product_dict['teacher'] = {
            'id': product.teacher_profile.id,
            'teacher_id': product.teacher_profile.teacher_id,
            'real_name': product.teacher_profile.real_name,
            'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None,
            'rating': product.teacher_profile.rating,
            'follower_count': product.teacher_profile.follower_count,
            'product_count': product.teacher_profile.product_count,
            'intro': product.teacher_profile.intro,
            'specialties': product.teacher_profile.specialties
        }
    
    if product.category:
        product_dict['category'] = product.category.to_dict()
    
    return jsonify(success(data=product_dict))

@product_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    
    category_list = [cat.to_dict() for cat in categories]
    
    return jsonify(success(data=category_list))

@product_bp.route('/hot', methods=['GET'])
def get_hot_products():
    limit = request.args.get('limit', 10, type=int)
    
    products = Product.query.filter_by(status='active').order_by(
        Product.sales_count.desc(),
        Product.favorite_count.desc()
    ).limit(limit).all()
    
    result = []
    for product in products:
        product_dict = product.to_dict()
        if product.teacher_profile:
            product_dict['teacher'] = {
                'id': product.teacher_profile.id,
                'teacher_id': product.teacher_profile.teacher_id,
                'real_name': product.teacher_profile.real_name,
                'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None
            }
        result.append(product_dict)
    
    return jsonify(success(data=result))

@product_bp.route('/new', methods=['GET'])
def get_new_products():
    limit = request.args.get('limit', 10, type=int)
    
    products = Product.query.filter_by(status='active').order_by(
        Product.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for product in products:
        product_dict = product.to_dict()
        if product.teacher_profile:
            product_dict['teacher'] = {
                'id': product.teacher_profile.id,
                'teacher_id': product.teacher_profile.teacher_id,
                'real_name': product.teacher_profile.real_name,
                'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None
            }
        result.append(product_dict)
    
    return jsonify(success(data=result))

@product_bp.route('/recommend', methods=['GET'])
def get_recommend_products():
    limit = request.args.get('limit', 10, type=int)
    
    products = Product.query.filter_by(status='active').order_by(
        Product.rating.desc(),
        Product.favorite_count.desc()
    ).limit(limit).all()
    
    result = []
    for product in products:
        product_dict = product.to_dict()
        if product.teacher_profile:
            product_dict['teacher'] = {
                'id': product.teacher_profile.id,
                'teacher_id': product.teacher_profile.teacher_id,
                'real_name': product.teacher_profile.real_name,
                'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None
            }
        result.append(product_dict)
    
    return jsonify(success(data=result))
