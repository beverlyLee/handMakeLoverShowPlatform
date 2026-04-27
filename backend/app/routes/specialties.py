from flask import Blueprint, jsonify

from app.models.specialty import Specialty
from app.utils.response import success, error
from app.common.response_code import ResponseCode

specialty_bp = Blueprint('specialty', __name__, url_prefix='/api/specialties')

@specialty_bp.route('/', methods=['GET'])
def get_specialties():
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.sort_order).all()
    data = [s.to_dict() for s in specialties]
    return jsonify(success(data=data))

@specialty_bp.route('/grouped', methods=['GET'])
def get_specialties_grouped():
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.sort_order).all()
    
    groups = {}
    for s in specialties:
        category = s.category or '其他'
        if category not in groups:
            groups[category] = []
        groups[category].append(s.to_dict())
    
    return jsonify(success(data=groups))

@specialty_bp.route('/<int:id>', methods=['GET'])
def get_specialty(id):
    specialty = Specialty.query.get(id)
    if not specialty:
        return jsonify(error(code=ResponseCode.NOT_FOUND, msg='擅长领域不存在')), 404
    return jsonify(success(data=specialty.to_dict()))