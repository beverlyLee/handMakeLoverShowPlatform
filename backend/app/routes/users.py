from flask import Blueprint, jsonify, request
from app.utils.response import success, error
from app.data.mock_data import mock_user, mock_addresses
from app.common.auth import login_required
from app.common.response_code import ResponseCode
import copy

user_bp = Blueprint('users', __name__)

current_user = copy.deepcopy(mock_user)
current_addresses = copy.deepcopy(mock_addresses)
next_address_id = 3

@user_bp.route('/profile', methods=['GET'])
def get_user_profile():
    return jsonify(success(data=current_user))

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_user_profile():
    global current_user
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    allowed_fields = ['nickname', 'avatar', 'phone', 'email', 'gender', 'bio']
    for field in data:
        if field in allowed_fields:
            current_user[field] = data[field]
    
    return jsonify(success(data=current_user, msg='用户信息更新成功'))

@user_bp.route('/role', methods=['PUT'])
@login_required
def switch_role():
    global current_user
    data = request.get_json()
    
    if not data or 'role' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='角色参数不能为空')), 400
    
    role = data.get('role')
    if role not in ['customer', 'teacher']:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='角色类型不正确，只能是 customer 或 teacher')), 400
    
    current_user['role'] = role
    return jsonify(success(data=current_user, msg='角色切换成功'))

@user_bp.route('/address', methods=['GET'])
def get_address_list():
    return jsonify(success(data=current_addresses))

@user_bp.route('/address', methods=['POST'])
@login_required
def create_address():
    global current_addresses, next_address_id
    data = request.get_json()
    
    required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    is_default = data.get('is_default', False)
    if is_default:
        for addr in current_addresses:
            addr['is_default'] = False
    
    new_address = {
        'id': next_address_id,
        'user_id': 1,
        'name': data.get('name'),
        'phone': data.get('phone'),
        'province': data.get('province'),
        'city': data.get('city'),
        'district': data.get('district'),
        'detail': data.get('detail'),
        'is_default': is_default,
        'create_time': '2026-04-24 10:30:00'
    }
    
    current_addresses.append(new_address)
    next_address_id += 1
    
    return jsonify(success(data=new_address, msg='地址添加成功'))

@user_bp.route('/address/<int:address_id>', methods=['PUT'])
@login_required
def update_address(address_id):
    global current_addresses
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    address = None
    for addr in current_addresses:
        if addr['id'] == address_id:
            address = addr
            break
    
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    allowed_fields = ['name', 'phone', 'province', 'city', 'district', 'detail', 'is_default']
    for field in data:
        if field in allowed_fields:
            address[field] = data[field]
    
    if data.get('is_default'):
        for addr in current_addresses:
            if addr['id'] != address_id:
                addr['is_default'] = False
    
    return jsonify(success(data=address, msg='地址更新成功'))

@user_bp.route('/address/<int:address_id>', methods=['DELETE'])
@login_required
def delete_address(address_id):
    global current_addresses
    
    address = None
    for i, addr in enumerate(current_addresses):
        if addr['id'] == address_id:
            address = addr
            del current_addresses[i]
            break
    
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    return jsonify(success(msg='地址删除成功'))

@user_bp.route('/address/<int:address_id>/default', methods=['PUT'])
@login_required
def set_default_address(address_id):
    global current_addresses
    
    address = None
    for addr in current_addresses:
        if addr['id'] == address_id:
            address = addr
            break
    
    if not address:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='地址不存在')), 404
    
    for addr in current_addresses:
        addr['is_default'] = (addr['id'] == address_id)
    
    return jsonify(success(msg='默认地址设置成功'))

@user_bp.route('/', methods=['GET'])
def get_users():
    return jsonify(success(data=[current_user]))

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    if user_id != 1:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return jsonify(success(data=current_user))

@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if user_id != 1:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    return update_user_profile()
