from datetime import datetime
import requests
from flask import Blueprint, request, jsonify, current_app, g
from app.models import User, db
from app.utils import generate_token, login_required, get_current_user

auth_bp = Blueprint('auth', __name__)

def get_wechat_session(code):
    appid = current_app.config.get('WECHAT_APPID')
    secret = current_app.config.get('WECHAT_SECRET')
    
    if not appid or not secret:
        return None, '微信小程序配置未设置'
    
    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'errcode' in data and data['errcode'] != 0:
            return None, data.get('errmsg', '微信登录失败')
        
        return data, None
    except Exception as e:
        return None, f'请求微信API失败: {str(e)}'

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'msg': '请求参数错误',
            'data': None
        }), 400
    
    login_type = data.get('loginType', 'wechat')
    
    if login_type == 'phone':
        phone = data.get('phone')
        code = data.get('code')
        
        if not phone or not code:
            return jsonify({
                'code': 400,
                'msg': '请输入手机号和验证码',
                'data': None
            }), 400
        
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            return jsonify({
                'code': 0,
                'data': {
                    'needRegister': True,
                    'phone': phone
                }
            })
        
        if user.status != 1:
            return jsonify({
                'code': 403,
                'msg': '账户已被禁用',
                'data': None
            }), 403
        
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        token = generate_token(user.id)
        
        return jsonify({
            'code': 0,
            'data': {
                'needRegister': False,
                'token': token,
                'user': user.to_dict()
            }
        })
    
    else:
        code = data.get('code')
        
        if not code:
            return jsonify({
                'code': 400,
                'msg': '缺少登录凭证',
                'data': None
            }), 400
        
        session_data, error = get_wechat_session(code)
        
        if error:
            return jsonify({
                'code': 500,
                'msg': error,
                'data': None
            }), 500
        
        openid = session_data.get('openid')
        session_key = session_data.get('session_key')
        unionid = session_data.get('unionid')
        
        if not openid:
            return jsonify({
                'code': 500,
                'msg': '获取微信用户信息失败',
                'data': None
            }), 500
        
        user = User.query.filter_by(openid=openid).first()
        
        if not user:
            return jsonify({
                'code': 0,
                'data': {
                    'needRegister': True,
                    'openid': openid,
                    'sessionKey': session_key,
                    'unionid': unionid
                }
            })
        
        if user.status != 1:
            return jsonify({
                'code': 403,
                'msg': '账户已被禁用',
                'data': None
            }), 403
        
        if unionid and not user.unionid:
            user.unionid = unionid
        
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        token = generate_token(user.id)
        
        return jsonify({
            'code': 0,
            'data': {
                'needRegister': False,
                'token': token,
                'user': user.to_dict()
            }
        })

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'msg': '请求参数错误',
            'data': None
        }), 400
    
    phone = data.get('phone')
    code = data.get('code')
    openid = data.get('openid')
    nickname = data.get('nickname')
    avatar = data.get('avatar')
    
    if not phone:
        return jsonify({
            'code': 400,
            'msg': '请输入手机号',
            'data': None
        }), 400
    
    if not code:
        return jsonify({
            'code': 400,
            'msg': '请输入验证码',
            'data': None
        }), 400
    
    existing_user = User.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({
            'code': 400,
            'msg': '该手机号已注册',
            'data': None
        }), 400
    
    if openid:
        existing_openid = User.query.filter_by(openid=openid).first()
        if existing_openid:
            return jsonify({
                'code': 400,
                'msg': '该微信账号已绑定其他手机号',
                'data': None
            }), 400
    
    user = User(
        phone=phone,
        openid=openid,
        nickname=nickname or f'用户{phone[-4:]}',
        avatar=avatar or '',
        status=1,
        last_login_at=datetime.utcnow()
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        
        token = generate_token(user.id)
        
        return jsonify({
            'code': 0,
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'注册失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    return jsonify({
        'code': 0,
        'msg': '登出成功',
        'data': None
    })

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = get_current_user()
    return jsonify({
        'code': 0,
        'data': user.to_dict()
    })

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 400,
            'msg': '请求参数错误',
            'data': None
        }), 400
    
    allowed_fields = ['nickname', 'avatar', 'gender']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    try:
        db.session.commit()
        return jsonify({
            'code': 0,
            'data': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'更新失败: {str(e)}',
            'data': None
        }), 500
