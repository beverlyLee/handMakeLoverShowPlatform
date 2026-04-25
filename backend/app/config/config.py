import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(basedir, '..', '..', '..'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    PORT = int(os.getenv('PORT', 5001))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    WECHAT_APPID = os.getenv('WECHAT_APPID', 'your-wechat-appid')
    WECHAT_SECRET = os.getenv('WECHAT_SECRET', 'your-wechat-secret')
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRE_HOURS', 72))
    
    USE_DATABASE = os.getenv('USE_DATABASE', 'True').lower() in ('true', '1', 't')
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(project_root, 'handicraft.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() in ('true', '1', 't')
