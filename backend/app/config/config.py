import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(basedir, '..', '..', '..'))

DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
DB_PATH = os.getenv('DB_PATH')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME', 'handicraft')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def _build_database_uri():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    db_type = DB_TYPE.lower()
    
    if db_type == 'sqlite':
        db_path = DB_PATH or os.path.join(project_root, 'handicraft.db')
        return f'sqlite:///{db_path}'
    
    if db_type == 'mysql':
        port = DB_PORT or '3306'
        if DB_USERNAME and DB_PASSWORD:
            return f'mysql+pymysql://{quote_plus(DB_USERNAME)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{port}/{DB_NAME}'
        elif DB_USERNAME:
            return f'mysql+pymysql://{quote_plus(DB_USERNAME)}@{DB_HOST}:{port}/{DB_NAME}'
        else:
            return f'mysql+pymysql://{DB_HOST}:{port}/{DB_NAME}'
    
    if db_type == 'postgresql':
        port = DB_PORT or '5432'
        if DB_USERNAME and DB_PASSWORD:
            return f'postgresql://{quote_plus(DB_USERNAME)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{port}/{DB_NAME}'
        elif DB_USERNAME:
            return f'postgresql://{quote_plus(DB_USERNAME)}@{DB_HOST}:{port}/{DB_NAME}'
        else:
            return f'postgresql://{DB_HOST}:{port}/{DB_NAME}'
    
    return 'sqlite:///' + os.path.join(project_root, 'handicraft.db')

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
    
    DB_TYPE = DB_TYPE
    DB_PATH = DB_PATH
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_NAME = DB_NAME
    DB_USERNAME = DB_USERNAME
    DB_PASSWORD = DB_PASSWORD
    
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() in ('true', '1', 't')
