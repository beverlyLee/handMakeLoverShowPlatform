from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.utils.jwt_utils import generate_token
from app.services.wechat_service import WeChatService
from app.services.user_service import UserService
from app.common.auth import login_required
from app.common.response_code import ResponseCode

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
        UserService.update_user(user.id, session_key=session_key)
    else:
        user = UserService.create_user(
            openid=openid,
            session_key=session_key,
            nickname=nickname,
            avatar=avatar
        )
        is_new_user = True
    
    token = generate_token(user.id)
    
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
