import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app, jsonify, g
from app.models import User, db

def generate_token(user_id, expires_in=None):
    if expires_in is None:
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 24 * 60 * 60)
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def decode_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'code': 2002,
                'msg': '未登录，请先登录',
                'data': None
            }), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'code': 2003,
                'msg': '无效的Token格式',
                'data': None
            }), 401
        
        token = parts[1]
        payload = decode_token(token)
        
        if not payload:
            return jsonify({
                'code': 2003,
                'msg': 'Token已过期或无效',
                'data': None
            }), 401
        
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'code': 2003,
                'msg': '用户不存在',
                'data': None
            }), 401
        
        if user.status != 1:
            return jsonify({
                'code': 2003,
                'msg': '账户已被禁用',
                'data': None
            }), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    return getattr(g, 'current_user', None)
