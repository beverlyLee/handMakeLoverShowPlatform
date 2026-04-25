import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.config.config import Config

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(
        payload,
        Config.JWT_SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM
    )
    return token

def decode_token(token):
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token已过期'
    except jwt.InvalidTokenError:
        return None, 'Token无效'
    except Exception as e:
        return None, str(e)
