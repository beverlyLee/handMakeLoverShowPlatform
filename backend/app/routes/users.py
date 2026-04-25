from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.models.user import User
from app.models.address import Address
from app.services.user_service import UserService
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.extensions import db

user_bp = Blueprint('users', __name__)

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_user_profile():
    user_id = g.get('user_id')
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return jsonify(success(data=UserService.get_user_public_info(user)))

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_user_profile():
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    update_data = {}
    allowed_fields = ['username', 'nickname', 'avatar', 'phone', 'email', 'gender', 'bio']
    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]
    
    if not update_data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='没有可更新的字段')), 400
    
    user = UserService.update_user(user_id, **update_data)
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    return jsonify(success(data=UserService.get_user_public_info(user), msg='用户信息更新成功'))

@user_bp.route('/role', methods=['PUT'])
@login_required
def switch_role():
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data or 'role' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='角色参数不能为空')), 400
    
    role = data.get('role')
    if role not in ['customer', 'teacher']:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='角色类型不正确，只能是 customer 或 teacher')), 400
    
    user = UserService.update_user(user_id, role=role)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    return jsonify(success(data=UserService.get_user_public_info(user), msg='角色切换成功'))

@user_bp.route('/address', methods=['GET'])
@login_required
def get_address_list():
    user_id = g.get('user_id')
    addresses = Address.query.filter_by(user_id=user_id).order_by(Address.is_default.desc(), Address.create_time.desc()).all()
    return jsonify(success(data=[addr.to_dict() for addr in addresses]))

@user_bp.route('/address', methods=['POST'])
@login_required
def create_address():
    user_id = g.get('user_id')
    data = request.get_json()
    
    required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    is_default = data.get('is_default', False)
    if is_default:
        Address.query.filter_by(user_id=user_id).update({'is_default': False})
        db.session.commit()
    
    address = Address(
        user_id=user_id,
        name=data.get('name'),
        phone=data.get('phone'),
        province=data.get('province'),
        city=data.get('city'),
        district=data.get('district'),
        detail=data.get('detail'),
        is_default=is_default
    )
    db.session.add(address)
    db.session.commit()
    
    return jsonify(success(data=address.to_dict(), msg='地址添加成功'))

@user_bp.route('/address/<int:address_id>', methods=['PUT'])
@login_required
def update_address(address_id):
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    allowed_fields = ['name', 'phone', 'province', 'city', 'district', 'detail', 'is_default']
    for field in data:
        if field in allowed_fields:
            setattr(address, field, data[field])
    
    is_default = data.get('is_default')
    if is_default:
        Address.query.filter(Address.user_id == user_id, Address.id != address_id).update({'is_default': False})
        db.session.commit()
    
    db.session.commit()
    return jsonify(success(data=address.to_dict(), msg='地址更新成功'))

@user_bp.route('/address/<int:address_id>', methods=['DELETE'])
@login_required
def delete_address(address_id):
    user_id = g.get('user_id')
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    db.session.delete(address)
    db.session.commit()
    
    return jsonify(success(msg='地址删除成功'))

@user_bp.route('/address/<int:address_id>/default', methods=['PUT'])
@login_required
def set_default_address(address_id):
    user_id = g.get('user_id')
    
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    Address.query.filter_by(user_id=user_id).update({'is_default': False})
    address.is_default = True
    db.session.commit()
    
    return jsonify(success(msg='默认地址设置成功'))

@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(success(data=[UserService.get_user_public_info(user) for user in users]))

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return jsonify(success(data=UserService.get_user_public_info(user)))

@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    current_user_id = g.get('user_id')
    if current_user_id != user_id:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权限修改其他用户信息')), 403
    return update_user_profile()
