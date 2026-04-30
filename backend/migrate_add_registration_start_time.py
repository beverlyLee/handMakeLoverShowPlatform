#!/usr/bin/env python3
"""
数据库迁移脚本：添加 registration_start_time 列到 activities 表
"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config


def add_registration_start_time_column():
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    if db_path.startswith('/'):
        db_path = db_path
    else:
        db_path = os.path.join(os.path.dirname(__file__), db_path)
    
    print(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(activities)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 activities 表的列: {columns}")
        
        if 'registration_start_time' in columns:
            print("registration_start_time 列已存在，跳过迁移")
            return
        
        print("正在添加 registration_start_time 列...")
        cursor.execute("ALTER TABLE activities ADD COLUMN registration_start_time DATETIME")
        conn.commit()
        print("成功添加 registration_start_time 列!")
        
        print("\n正在更新现有数据（将 registration_deadline 前的时间设为开始时间）...")
        cursor.execute("""
            UPDATE activities 
            SET registration_start_time = 
                CASE 
                    WHEN created_at IS NOT NULL THEN created_at
                    ELSE '2026-01-01 00:00:00'
                END
            WHERE registration_start_time IS NULL
        """)
        conn.commit()
        
        updated_count = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"已更新 {updated_count} 条记录!")
        
        cursor.execute("PRAGMA table_info(activities)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\n更新后 activities 表的列: {columns}")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("\n数据库迁移完成!")


if __name__ == '__main__':
    add_registration_start_time_column()
