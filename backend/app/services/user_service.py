from datetime import datetime
import copy
from app.data.mock_data import mock_user

users = {}
next_user_id = 2

def init_users():
    global users, next_user_id
    user_with_openid = copy.deepcopy(mock_user)
    user_with_openid['openid'] = 'oTestOpenid123456'
    user_with_openid['unionid'] = None
    user_with_openid['session_key'] = 'mock_session_key_test_code_1'
    user_with_openid['update_time'] = '2024-01-15 10:30:00'
    users[1] = user_with_openid
    users['oTestOpenid123456'] = user_with_openid

init_users()

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id):
        return users.get(user_id)
    
    @staticmethod
    def get_user_by_openid(openid):
        return users.get(openid)
    
    @staticmethod
    def create_user(openid, session_key, nickname=None, avatar=None, unionid=None):
        global next_user_id, users
        
        user = {
            'id': next_user_id,
            'openid': openid,
            'unionid': unionid,
            'session_key': session_key,
            'username': f'wx_{openid[-8:]}',
            'nickname': nickname or '微信用户',
            'avatar': avatar or 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=default%20user%20avatar&image_size=square',
            'phone': None,
            'email': None,
            'gender': 0,
            'role': 'customer',
            'bio': '',
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        users[next_user_id] = user
        users[openid] = user
        next_user_id += 1
        
        return user
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = users.get(user_id)
        if not user:
            return None
        
        allowed_fields = ['nickname', 'avatar', 'phone', 'email', 'gender', 'bio', 'session_key']
        for field in kwargs:
            if field in allowed_fields:
                user[field] = kwargs[field]
        
        user['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'openid' in user:
            users[user['openid']] = user
        
        return user
    
    @staticmethod
    def get_user_public_info(user):
        if not user:
            return None
        
        public_info = {
            'id': user.get('id'),
            'username': user.get('username'),
            'nickname': user.get('nickname'),
            'avatar': user.get('avatar'),
            'phone': user.get('phone'),
            'email': user.get('email'),
            'gender': user.get('gender'),
            'role': user.get('role'),
            'bio': user.get('bio'),
            'create_time': user.get('create_time')
        }
        
        return public_info
