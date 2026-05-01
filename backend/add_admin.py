#!/usr/bin/env python3
"""
添加管理员账号到现有数据库
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models import User
from app.utils.password_utils import hash_password
from app.config import Config

def add_admin():
    app = create_app(Config)
    
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("管理员账号已存在")
            print(f"用户名: {admin.username}")
            print(f"角色: {admin.roles}")
            return
        
        password = 'admin123'
        password_hash, password_salt = hash_password(password)
        
        admin = User(
            username='admin',
            nickname='系统管理员',
            avatar='https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=system%20admin%20avatar&image_size=square',
            email='admin@handmade.com',
            password_hash=password_hash,
            password_salt=password_salt,
            roles=['admin', 'customer'],
            current_role='admin',
            bio='系统管理员，负责平台日常运维'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("="*50)
        print("管理员账号创建成功！")
        print("="*50)
        print(f"用户名: admin")
        print(f"密码: {password}")
        print(f"角色: {admin.roles}")
        print("="*50)

if __name__ == '__main__':
    add_admin()
