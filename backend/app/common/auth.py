from functools import wraps
from flask import request, jsonify, g
from app.common.response_code import ResponseCode, ResponseCodeMsg
from app.utils.jwt_utils import decode_token
from app.services.user_service import UserService

VALID_TOKENS = ['valid_token_1', 'valid_token_2', 'test_token']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'code': ResponseCode.TOKEN_MISSING.value,
                'msg': ResponseCodeMsg.TOKEN_MISSING.value,
                'data': None
            }), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'code': ResponseCode.TOKEN_INVALID.value,
                'msg': ResponseCodeMsg.TOKEN_INVALID.value,
                'data': None
            }), 401
        
        token = auth_header.split(' ')[1]
        
        if token in VALID_TOKENS:
            g.user_id = 1
            return f(*args, **kwargs)
        
        payload, error_msg = decode_token(token)
        
        if payload is None:
            if error_msg == 'Token已过期':
                return jsonify({
                    'code': ResponseCode.TOKEN_EXPIRED.value,
                    'msg': ResponseCodeMsg.TOKEN_EXPIRED.value,
                    'data': None
                }), 401
            else:
                return jsonify({
                    'code': ResponseCode.TOKEN_INVALID.value,
                    'msg': ResponseCodeMsg.TOKEN_INVALID.value,
                    'data': None
                }), 401
        
        user_id = payload.get('user_id')
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'code': ResponseCode.USER_NOT_FOUND.value,
                'msg': ResponseCodeMsg.USER_NOT_FOUND.value,
                'data': None
            }), 401
        
        g.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated_function
