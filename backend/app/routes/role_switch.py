from flask import Blueprint, jsonify, request
from app.utils.response import success, error
from app.data.mock_data import mock_users
from app.common.response_code import ResponseCode
import copy

role_switch_bp = Blueprint('role_switch', __name__)

current_users = copy.deepcopy(mock_users)

VALID_ROLES = ['customer', 'teacher']
ROLE_NAMES = {
    'customer': '客户',
    'teacher': '手作老师'
}

@role_switch_bp.route('/switch', methods=['POST'])
def switch_role():
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    user_id = data.get('user_id')
    target_role = data.get('target_role')
    
    if user_id is None:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='user_id 参数不能为空')), 400
    
    if target_role is None:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='target_role 参数不能为空')), 400
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='user_id 必须是整数')), 400
    
    if target_role not in VALID_ROLES:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg=f'target_role 只能是 {VALID_ROLES}')), 400
    
    user = None
    for u in current_users:
        if u['id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    original_role = user['role']
    
    if original_role == target_role:
        return jsonify(success(data={
            'user_id': user_id,
            'original_role': original_role,
            'original_role_name': ROLE_NAMES.get(original_role, original_role),
            'current_role': target_role,
            'current_role_name': ROLE_NAMES.get(target_role, target_role),
            'message': '用户角色未变更，已是目标角色'
        }, msg='角色切换成功'))
    
    user['role'] = target_role
    
    return jsonify(success(data={
        'user_id': user_id,
        'original_role': original_role,
        'original_role_name': ROLE_NAMES.get(original_role, original_role),
        'current_role': target_role,
        'current_role_name': ROLE_NAMES.get(target_role, target_role),
        'message': f'用户角色已从 {ROLE_NAMES.get(original_role, original_role)} 切换为 {ROLE_NAMES.get(target_role, target_role)}'
    }, msg='角色切换成功'))

@role_switch_bp.route('/users', methods=['GET'])
def get_all_users():
    return jsonify(success(data=current_users))

@role_switch_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = None
    for u in current_users:
        if u['id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    return jsonify(success(data=user))

@role_switch_bp.route('/roles', methods=['GET'])
def get_available_roles():
    return jsonify(success(data={
        'roles': VALID_ROLES,
        'role_names': ROLE_NAMES
    }))
