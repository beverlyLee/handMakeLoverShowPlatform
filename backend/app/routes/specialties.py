from flask import Blueprint, jsonify

from app.models.product import Category
from app.utils.response import success, error
from app.common.response_code import ResponseCode

specialty_bp = Blueprint('specialty', __name__, url_prefix='/api/specialties')

@specialty_bp.route('/', methods=['GET'])
def get_specialties():
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    data = [{
        'id': c.id,
        'name': c.name,
        'icon': c.icon,
        'sort_order': c.sort,
        'is_active': c.status == 'active'
    } for c in categories]
    return jsonify(success(data=data))

@specialty_bp.route('/grouped', methods=['GET'])
def get_specialties_grouped():
    categories = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    
    groups = {}
    for c in categories:
        group_name = '手工分类'
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append({
            'id': c.id,
            'name': c.name,
            'icon': c.icon,
            'sort_order': c.sort,
            'is_active': c.status == 'active'
        })
    
    return jsonify(success(data=groups))

@specialty_bp.route('/<int:id>', methods=['GET'])
def get_specialty(id):
    category = Category.query.get(id)
    if not category:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='分类不存在')), 404
    data = {
        'id': category.id,
        'name': category.name,
        'icon': category.icon,
        'sort_order': category.sort,
        'is_active': category.status == 'active'
    }
    return jsonify(success(data=data))