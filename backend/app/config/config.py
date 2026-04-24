import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    PORT = int(os.getenv('PORT', 5001))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///handicraft.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    WECHAT_APPID = os.getenv('WECHAT_APPID', '')
    WECHAT_SECRET = os.getenv('WECHAT_SECRET', '')
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60
