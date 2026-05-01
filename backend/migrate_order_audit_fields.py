#!/usr/bin/env python3
"""
数据库迁移脚本：添加订单异常字段、退款字段和审核日志表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

app = create_app()


def check_column_exists(table_name, column_name):
    result = db.session.execute(
        text(f"PRAGMA table_info({table_name})")
    )
    columns = [row[1] for row in result]
    return column_name in columns


def check_table_exists(table_name):
    result = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name}
    )
    return result.fetchone() is not None


def add_column_if_not_exists(table_name, column_def):
    column_name = column_def.split()[0]
    if not check_column_exists(table_name, column_name):
        try:
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
            db.session.commit()
            print(f"  ✓ 已添加列: {table_name}.{column_name}")
            return True
        except Exception as e:
            print(f"  ✗ 添加列失败: {table_name}.{column_name} - {e}")
            db.session.rollback()
            return False
    else:
        print(f"  - 列已存在: {table_name}.{column_name}")
        return True


def migrate():
    with app.app_context():
        print("="*60)
        print("数据库迁移脚本：添加订单异常字段、退款字段和审核日志表")
        print("="*60)
        
        print("\n【1/3】创建审核日志表...")
        print("-"*40)
        
        if not check_table_exists('audit_logs'):
            print("  正在创建 audit_logs 表...")
            try:
                db.session.execute(text("""
                    CREATE TABLE audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        admin_id INTEGER NOT NULL,
                        target_type VARCHAR(50) NOT NULL,
                        target_id INTEGER NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        reason VARCHAR(500),
                        before_data TEXT,
                        after_data TEXT,
                        created_at DATETIME
                    )
                """))
                db.session.commit()
                print("  ✓ 已创建 audit_logs 表")
            except Exception as e:
                print(f"  ✗ 创建表失败: {e}")
                db.session.rollback()
        else:
            print("  - audit_logs 表已存在")
        
        print("\n【2/3】为 orders 表添加异常订单字段...")
        print("-"*40)
        
        add_column_if_not_exists('orders', 'is_abnormal BOOLEAN DEFAULT 0')
        add_column_if_not_exists('orders', 'abnormal_reason TEXT')
        add_column_if_not_exists('orders', 'abnormal_reason_code VARCHAR(50) DEFAULT "other"')
        add_column_if_not_exists('orders', 'abnormal_time DATETIME')
        add_column_if_not_exists('orders', 'abnormal_resolved_at DATETIME')
        add_column_if_not_exists('orders', 'abnormal_resolved_by INTEGER')
        
        print("\n【3/3】为 orders 表添加退款字段...")
        print("-"*40)
        
        add_column_if_not_exists('orders', 'refund_status VARCHAR(20) DEFAULT "none"')
        add_column_if_not_exists('orders', 'refund_amount REAL DEFAULT 0.0')
        add_column_if_not_exists('orders', 'refund_reason TEXT')
        add_column_if_not_exists('orders', 'refund_approved_by INTEGER')
        add_column_if_not_exists('orders', 'refund_time DATETIME')
        
        print("\n" + "="*60)
        print("数据库迁移完成！")
        print("="*60)
        
        print("\n数据库表状态：")
        print("-"*40)
        
        tables_to_check = [
            ('orders', ['is_abnormal', 'abnormal_reason', 'abnormal_reason_code', 
                        'abnormal_time', 'abnormal_resolved_at', 'abnormal_resolved_by',
                        'refund_status', 'refund_amount', 'refund_reason', 
                        'refund_approved_by', 'refund_time']),
            ('audit_logs', None),
            ('reviews', ['is_read', 'read_at'])
        ]
        
        for table_name, columns in tables_to_check:
            if check_table_exists(table_name):
                if columns:
                    existing_cols = []
                    missing_cols = []
                    for col in columns:
                        if check_column_exists(table_name, col):
                            existing_cols.append(col)
                        else:
                            missing_cols.append(col)
                    
                    if missing_cols:
                        print(f"  ✗ {table_name} 表缺少列: {', '.join(missing_cols)}")
                    else:
                        print(f"  ✓ {table_name} 表所有列已就绪")
                else:
                    print(f"  ✓ {table_name} 表已存在")
            else:
                print(f"  ✗ {table_name} 表不存在")


if __name__ == '__main__':
    migrate()
