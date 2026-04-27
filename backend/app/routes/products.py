from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.auth import login_required
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

def get_current_teacher_profile():
    user_id = g.get('user_id')
    if not user_id:
        return None
    profile = TeacherProfile.query.filter_by(user_id=user_id).first()
    return profile

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
                'user_id': product.teacher_profile.user_id,
                'real_name': product.teacher_profile.real_name,
                'nickname': product.teacher_profile.user.nickname if product.teacher_profile.user else None,
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
            'user_id': product.teacher_profile.user_id,
            'real_name': product.teacher_profile.real_name,
            'nickname': product.teacher_profile.user.nickname if product.teacher_profile.user else None,
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

@product_bp.route('/categories-with-hot', methods=['GET'])
def get_categories_with_hot_products():
    limit = request.args.get('limit', 3, type=int)
    
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    
    result = []
    for category in categories:
        category_dict = category.to_dict()
        
        products = Product.query.filter_by(
            status='active', 
            category_id=category.id
        ).order_by(
            Product.sales_count.desc(),
            Product.favorite_count.desc()
        ).limit(limit).all()
        
        product_list = []
        for product in products:
            product_dict = product.to_dict()
            product_list.append(product_dict)
        
        category_dict['hot_products'] = product_list
        result.append(category_dict)
    
    return jsonify(success(data=result))

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
                'user_id': product.teacher_profile.user_id,
                'real_name': product.teacher_profile.real_name,
                'nickname': product.teacher_profile.user.nickname if product.teacher_profile.user else None,
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
                'user_id': product.teacher_profile.user_id,
                'real_name': product.teacher_profile.real_name,
                'nickname': product.teacher_profile.user.nickname if product.teacher_profile.user else None,
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
                'user_id': product.teacher_profile.user_id,
                'real_name': product.teacher_profile.real_name,
                'nickname': product.teacher_profile.user.nickname if product.teacher_profile.user else None,
                'avatar': product.teacher_profile.user.avatar if product.teacher_profile.user else None
            }
        result.append(product_dict)
    
    return jsonify(success(data=result))

@product_bp.route('/my', methods=['GET'])
@login_required
def get_my_products():
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    pagination = Product.query.filter_by(
        teacher_id=teacher_profile.id
    ).order_by(Product.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )
    
    products = [p.to_dict() for p in pagination.items]
    
    return jsonify(success(data={
        'list': products,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next
    }))

@product_bp.route('', methods=['POST'])
@login_required
def create_product():
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    if 'title' not in data or not data.get('title'):
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='作品标题不能为空')), 400
    
    product = Product(
        teacher_id=teacher_profile.id,
        title=data.get('title'),
        description=data.get('description', ''),
        category_id=data.get('category_id'),
        price=float(data.get('price', 0)),
        original_price=float(data.get('original_price', 0)) if data.get('original_price') else float(data.get('price', 0)),
        stock=int(data.get('stock', 999)),
        status=data.get('status', 'active'),
        rating=5.0
    )
    
    if data.get('images'):
        product.images = data.get('images')
        if len(data.get('images')) > 0:
            product.cover_image = data.get('images')[0]
    
    if data.get('cover_image'):
        product.cover_image = data.get('cover_image')
    
    if data.get('tags'):
        product.tags = data.get('tags')
    
    db.session.add(product)
    db.session.commit()
    
    teacher_profile.product_count = (teacher_profile.product_count or 0) + 1
    db.session.commit()
    
    return jsonify(success(data=product.to_dict(), msg='作品创建成功'))

@product_bp.route('/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    product = Product.query.filter_by(id=product_id, teacher_id=teacher_profile.id).first()
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在或无权编辑')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    allowed_fields = [
        'title', 'description', 'category_id', 'price', 
        'original_price', 'stock', 'status', 'cover_image', 'rating'
    ]
    
    for field in data:
        if field in allowed_fields:
            if field in ['price', 'original_price']:
                setattr(product, field, float(data[field]))
            elif field in ['stock']:
                setattr(product, field, int(data[field]))
            else:
                setattr(product, field, data[field])
    
    if data.get('images'):
        product.images = data.get('images')
        if len(data.get('images')) > 0 and not data.get('cover_image'):
            product.cover_image = data.get('images')[0]
    
    if data.get('tags'):
        product.tags = data.get('tags')
    
    db.session.commit()
    
    return jsonify(success(data=product.to_dict(), msg='作品更新成功'))

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    product = Product.query.filter_by(id=product_id, teacher_id=teacher_profile.id).first()
    if not product:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='作品不存在或无权删除')), 404
    
    product.status = 'inactive'
    db.session.commit()
    
    return jsonify(success(msg='作品已删除'))
