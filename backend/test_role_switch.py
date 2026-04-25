from flask import Flask, jsonify, request
from flask_cors import CORS

mock_users = [
    {
        'id': 1,
        'username': 'handmade_lover',
        'nickname': '手作爱好者',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20crafts%20lover%20avatar&image_size=square',
        'phone': '138****8888',
        'email': 'handmade@example.com',
        'gender': 1,
        'role': 'customer',
        'bio': '热爱手作，喜欢制作各种手工制品',
        'create_time': '2024-01-15 10:30:00'
    },
    {
        'id': 2,
        'username': 'craft_master',
        'nickname': '手作大师',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar&image_size=square',
        'phone': '139****9999',
        'email': 'craftmaster@example.com',
        'gender': 2,
        'role': 'teacher',
        'bio': '资深手作老师，擅长编织、陶艺等多种手作技艺',
        'create_time': '2023-06-20 09:15:00'
    },
    {
        'id': 3,
        'username': 'diy_enthusiast',
        'nickname': 'DIY达人',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=diy%20enthusiast%20avatar&image_size=square',
        'phone': '137****7777',
        'email': 'diylover@example.com',
        'gender': 0,
        'role': 'customer',
        'bio': '喜欢尝试各种DIY项目，享受动手创造的乐趣',
        'create_time': '2024-03-10 14:45:00'
    }
]

import copy
current_users = copy.deepcopy(mock_users)

VALID_ROLES = ['customer', 'teacher']
ROLE_NAMES = {
    'customer': '客户',
    'teacher': '手作老师'
}

class ResponseCode:
    SUCCESS = 0
    ERROR = 1
    PARAM_ERROR = 1001
    PARAM_MISSING = 1002
    PARAM_INVALID = 1003
    USER_NOT_FOUND = 3001

class ResponseCodeMsg:
    SUCCESS = "操作成功"
    ERROR = "操作失败"
    PARAM_ERROR = "参数错误"
    PARAM_MISSING = "参数缺失"
    PARAM_INVALID = "参数无效"
    USER_NOT_FOUND = "用户不存在"

def success(data=None, msg=ResponseCodeMsg.SUCCESS):
    return {
        'code': ResponseCode.SUCCESS,
        'msg': msg,
        'data': data
    }

def error(code=ResponseCode.ERROR, msg=None, data=None):
    if msg is None:
        msg = ResponseCodeMsg.ERROR
    return {
        'code': code,
        'msg': msg,
        'data': data
    }

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Role Switch API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'switch_role': 'POST /api/role-switch/switch',
            'get_users': 'GET /api/role-switch/users',
            'get_user': 'GET /api/role-switch/users/<user_id>',
            'get_roles': 'GET /api/role-switch/roles'
        }
    })

@app.route('/api/role-switch/switch', methods=['POST'])
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

@app.route('/api/role-switch/users', methods=['GET'])
def get_all_users():
    return jsonify(success(data=current_users))

@app.route('/api/role-switch/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = None
    for u in current_users:
        if u['id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    return jsonify(success(data=user))

@app.route('/api/role-switch/roles', methods=['GET'])
def get_available_roles():
    return jsonify(success(data={
        'roles': VALID_ROLES,
        'role_names': ROLE_NAMES
    }))

if __name__ == '__main__':
    print('=' * 60)
    print('角色切换API服务已启动')
    print('=' * 60)
    print('服务地址: http://localhost:5002')
    print()
    print('可用接口:')
    print('  POST http://localhost:5002/api/role-switch/switch')
    print('       - 切换用户角色')
    print('       - 请求参数: {"user_id": 1, "target_role": "teacher"}')
    print()
    print('  GET  http://localhost:5002/api/role-switch/users')
    print('       - 获取所有用户列表')
    print()
    print('  GET  http://localhost:5002/api/role-switch/users/<user_id>')
    print('       - 获取指定用户信息')
    print()
    print('  GET  http://localhost:5002/api/role-switch/roles')
    print('       - 获取可用角色列表')
    print()
    print('  GET  http://localhost:5002/')
    print('       - 服务健康检查')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5002, debug=True)
