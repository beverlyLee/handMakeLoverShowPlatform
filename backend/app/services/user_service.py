from datetime import datetime
from app.extensions import db
from app.models.user import User

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_openid(openid):
        return User.query.filter_by(openid=openid).first()
    
    @staticmethod
    def create_user(openid, session_key, nickname=None, avatar=None, unionid=None):
        user = User(
            openid=openid,
            unionid=unionid,
            session_key=session_key,
            username=f'wx_{openid[-8:]}',
            nickname=nickname or '微信用户',
            avatar=avatar or 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=default%20user%20avatar&image_size=square',
            phone=None,
            email=None,
            gender=0,
            role='customer',
            bio=''
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return None
        
        allowed_fields = ['username', 'nickname', 'avatar', 'phone', 'email', 'gender', 'bio', 'session_key', 'role']
        for field in kwargs:
            if field in allowed_fields and kwargs[field] is not None:
                setattr(user, field, kwargs[field])
        
        db.session.commit()
        return user
    
    @staticmethod
    def get_user_public_info(user):
        if not user:
            return None
        
        return user.to_public_dict()
