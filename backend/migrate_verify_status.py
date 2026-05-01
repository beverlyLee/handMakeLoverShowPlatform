#!/usr/bin/env python3
"""
数据库迁移脚本：添加审核状态字段和审核日志表
"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.config import Config


def add_columns_and_tables():
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
        print("\n【1/5】检查 products 表...")
        print("-"*40)
        
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 products 表的列: {columns}")
        
        product_columns_to_add = [
            ('verify_status', "VARCHAR(20) DEFAULT 'pending'"),
            ('verify_time', 'DATETIME'),
            ('verify_admin_id', 'INTEGER'),
            ('reject_reason', 'VARCHAR(500)'),
            ('is_online', 'BOOLEAN DEFAULT 0')
        ]
        
        for col_name, col_def in product_columns_to_add:
            if col_name not in columns:
                print(f"正在添加列: products.{col_name}")
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")
                conn.commit()
                print(f"  ✓ 已添加列: products.{col_name}")
            else:
                print(f"  - 列已存在: products.{col_name}")
        
        print("\n更新现有产品的默认值...")
        cursor.execute("UPDATE products SET verify_status = 'pending' WHERE verify_status IS NULL")
        cursor.execute("UPDATE products SET is_online = 0 WHERE is_online IS NULL")
        conn.commit()
        print(f"  ✓ 已更新默认值")
        
        print("\n【2/5】检查 activities 表...")
        print("-"*40)
        
        cursor.execute("PRAGMA table_info(activities)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前 activities 表的列: {columns}")
        
        activity_columns_to_add = [
            ('verify_status', "VARCHAR(20) DEFAULT 'pending'"),
            ('verify_time', 'DATETIME'),
            ('verify_admin_id', 'INTEGER'),
            ('reject_reason', 'VARCHAR(500)'),
            ('is_official', 'BOOLEAN DEFAULT 0'),
            ('process', 'TEXT'),
            ('registration_method', 'VARCHAR(500)')
        ]
        
        for col_name, col_def in activity_columns_to_add:
            if col_name not in columns:
                print(f"正在添加列: activities.{col_name}")
                cursor.execute(f"ALTER TABLE activities ADD COLUMN {col_name} {col_def}")
                conn.commit()
                print(f"  ✓ 已添加列: activities.{col_name}")
            else:
                print(f"  - 列已存在: activities.{col_name}")
        
        print("\n更新现有活动的默认值...")
        cursor.execute("UPDATE activities SET verify_status = 'pending' WHERE verify_status IS NULL")
        cursor.execute("UPDATE activities SET is_official = 0 WHERE is_official IS NULL")
        conn.commit()
        print(f"  ✓ 已更新默认值")
        
        print("\n【3/5】创建 audit_logs 表...")
        print("-"*40)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                target_type VARCHAR(50) NOT NULL,
                target_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                reason VARCHAR(500),
                before_data TEXT,
                after_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("  ✓ 已创建 audit_logs 表")
        
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  audit_logs 表的列: {columns}")
        
        print("\n【4/5】为现有已上架产品设置默认状态...")
        print("-"*40)
        
        cursor.execute("UPDATE products SET verify_status = 'approved' WHERE status = 'active'")
        cursor.execute("UPDATE products SET is_online = 1 WHERE status = 'active'")
        conn.commit()
        updated_count = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"  ✓ 已为 {updated_count} 个已上架产品设置审核通过状态")
        
        print("\n【5/5】为现有活动设置默认状态...")
        print("-"*40)
        
        cursor.execute("UPDATE activities SET verify_status = 'approved' WHERE status = 'active'")
        conn.commit()
        updated_count = cursor.execute("SELECT changes()").fetchone()[0]
        print(f"  ✓ 已为 {updated_count} 个活动设置审核通过状态")
        
        print("\n" + "="*60)
        print("数据库迁移完成！")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM activities")
        activity_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        audit_log_count = cursor.fetchone()[0]
        
        print(f"产品总数: {product_count}")
        print(f"活动总数: {activity_count}")
        print(f"审核日志数: {audit_log_count}")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    add_columns_and_tables()
