from flask import Blueprint, jsonify, request, g
from datetime import datetime
from app.utils.response import success, error
from app.utils.jwt_utils import generate_token
from app.utils.password_utils import verify_password, generate_password_hash, validate_password_strength
from app.services.wechat_service import WeChatService
from app.services.user_service import UserService
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.database import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='code参数不能为空')), 400
    
    code = data.get('code')
    nickname = data.get('nickname')
    avatar = data.get('avatar')
    
    session_result = WeChatService.code2session(code)
    
    if 'errcode' in session_result and session_result['errcode'] != 0:
        errmsg = session_result.get('errmsg', '微信登录失败')
        return jsonify(error(code=ResponseCode.AUTH_FAILED, msg=errmsg)), 400
    
    openid = session_result.get('openid')
    session_key = session_result.get('session_key')
    
    user = UserService.get_user_by_openid(openid)
    is_new_user = False
    
    if user:
        UserService.update_user(user['id'], session_key=session_key)
    else:
        user = UserService.create_user(
            openid=openid,
            session_key=session_key,
            nickname=nickname,
            avatar=avatar
        )
        is_new_user = True
    
    token = generate_token(user['id'])
    
    user_info = UserService.get_user_public_info(user)
    
    return jsonify(success(data={
        'token': token,
        'user_info': user_info,
        'is_new_user': is_new_user
    }, msg='登录成功'))

@auth_bp.route('/register', methods=['POST'])
def register():
    return jsonify(success(msg='请使用微信登录接口进行注册'))

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    return jsonify(success(msg='登出成功'))

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user_id = g.get('user_id')
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    user_info = UserService.get_user_public_info(user)
    return jsonify(success(data=user_info))

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    user = UserService.update_user(
        user_id,
        nickname=data.get('nickname'),
        avatar=data.get('avatar'),
        phone=data.get('phone'),
        email=data.get('email'),
        gender=data.get('gender'),
        bio=data.get('bio')
    )
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    user_info = UserService.get_user_public_info(user)
    return jsonify(success(data=user_info, msg='用户信息更新成功'))

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='用户名和密码不能为空')), 400
    
    username = data.get('username')
    password = data.get('password')
    remember_me = data.get('remember_me', False)
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='账号不存在')), 404
    
    password_valid = False
    if user.password_hash:
        if user.password_salt:
            password_valid = verify_password(password, user.password_hash, user.password_salt)
        else:
            password_valid = verify_password(password, user.password_hash)
    else:
        if password == 'admin123':
            password_valid = True
    
    if not password_valid:
        return jsonify(error(code=ResponseCode.USER_PASSWORD_ERROR, msg='密码错误')), 401
    
    if 'admin' not in user.roles:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是管理员，无权限登录')), 403
    
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    
    expire_days = 7 if remember_me else None
    token = generate_token(user.id, expire_days=expire_days)
    user_info = UserService.get_user_public_info(user.to_dict())
    
    return jsonify(success(data={
        'token': token,
        'user_info': user_info
    }, msg='登录成功'))

@auth_bp.route('/admin/change-password', methods=['POST'])
@login_required
def admin_change_password():
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data or 'old_password' not in data or 'new_password' not in data or 'confirm_password' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='参数不完整')), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if new_password != confirm_password:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg='两次输入的新密码不一致')), 400
    
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return jsonify(error(code=ResponseCode.PARAM_ERROR, msg=error_msg)), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    password_valid = False
    if user.password_hash:
        if user.password_salt:
            password_valid = verify_password(old_password, user.password_hash, user.password_salt)
        else:
            password_valid = verify_password(old_password, user.password_hash)
    else:
        if old_password == 'admin123':
            password_valid = True
    
    if not password_valid:
        return jsonify(error(code=ResponseCode.USER_PASSWORD_ERROR, msg='旧密码错误')), 401
    
    new_pwd_data = generate_password_hash(new_password)
    user.password_hash = new_pwd_data['password_hash']
    user.password_salt = new_pwd_data['password_salt']
    
    try:
        db.session.commit()
        return jsonify(success(msg='密码修改成功，请重新登录'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'修改失败: {str(e)}')), 500

@auth_bp.route('/admin/profile', methods=['GET'])
@login_required
def get_admin_profile():
    user_id = g.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    user_dict = user.to_dict()
    
    return jsonify(success(data={
        'id': user_dict['id'],
        'username': user_dict['username'],
        'nickname': user_dict['nickname'],
        'avatar': user_dict['avatar'],
        'phone': user_dict['phone'],
        'email': user_dict['email'],
        'roles': user_dict['roles']
    }))

@auth_bp.route('/admin/profile', methods=['PUT'])
@login_required
def update_admin_profile():
    user_id = g.get('user_id')
    data = request.get_json()
    
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='用户不存在')), 404
    
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'phone' in data:
        user.phone = data['phone']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'email' in data:
        user.email = data['email']
    
    try:
        db.session.commit()
        user_dict = user.to_dict()
        return jsonify(success(data={
            'id': user_dict['id'],
            'username': user_dict['username'],
            'nickname': user_dict['nickname'],
            'avatar': user_dict['avatar'],
            'phone': user_dict['phone'],
            'email': user_dict['email'],
            'roles': user_dict['roles']
        }, msg='个人信息更新成功'))
    except Exception as e:
        db.session.rollback()
        return jsonify(error(code=ResponseCode.SYSTEM_ERROR, msg=f'更新失败: {str(e)}')), 500
