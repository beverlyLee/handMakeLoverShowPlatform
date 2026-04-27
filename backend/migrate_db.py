import os
import sys
import json
from datetime import datetime
from app import create_app
from app.database import db
from sqlalchemy import text
from app.models import (
    User, Address, TeacherProfile, Order, OrderItem, 
    Category, Product, Specialty, Coupon, UserCoupon,
    Logistics, LogisticsItem
)

app = create_app()

MOCK_DATA_DIR = os.path.join(os.path.dirname(__file__), 'mock-data')

def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d')
        except:
            try:
                return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
            except:
                return None

def load_json_file(filename):
    filepath = os.path.join(MOCK_DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def check_column_exists(table_name, column_name):
    result = db.session.execute(
        text(f"PRAGMA table_info({table_name})")
    )
    columns = [row[1] for row in result]
    return column_name in columns

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

def check_table_exists(table_name):
    result = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name}
    )
    return result.fetchone() is not None

def migrate():
    with app.app_context():
        print("="*60)
        print("数据库迁移脚本")
        print("="*60)
        
        print("\n【1/3】创建新表...")
        print("-"*40)
        
        new_tables = ['coupons', 'user_coupons', 'logistics', 'logistics_items']
        for table in new_tables:
            if not check_table_exists(table):
                print(f"  创建表: {table}")
            else:
                print(f"  表已存在: {table}")
        
        db.create_all()
        db.session.commit()
        print("  ✓ 新表创建完成")
        
        print("\n【2/3】为已有表添加新字段...")
        print("-"*40)
        
        print("\n正在检查 orders 表:")
        
        add_column_if_not_exists('orders', 'coupon_id INTEGER')
        add_column_if_not_exists('orders', 'user_coupon_id INTEGER')
        add_column_if_not_exists('orders', 'pay_method VARCHAR(20)')
        add_column_if_not_exists('orders', 'shipping_method VARCHAR(20)')
        add_column_if_not_exists('orders', 'shipping_company VARCHAR(50)')
        add_column_if_not_exists('orders', 'tracking_number VARCHAR(50)')
        add_column_if_not_exists('orders', 'estimated_arrival_days INTEGER')
        add_column_if_not_exists('orders', 'estimated_arrival_time DATETIME')
        
        print("\n为已有订单设置默认值...")
        try:
            result1 = db.session.execute(
                text("UPDATE orders SET shipping_method = 'standard' WHERE shipping_method IS NULL")
            )
            result2 = db.session.execute(
                text("UPDATE orders SET estimated_arrival_days = 3 WHERE estimated_arrival_days IS NULL")
            )
            db.session.commit()
            print(f"  ✓ 已更新默认值")
        except Exception as e:
            print(f"  - 更新默认值时跳过: {e}")
            db.session.rollback()
        
        print("\n【3/3】导入新表的 Mock 数据...")
        print("-"*40)
        
        if not Coupon.query.first():
            print("\n开始导入优惠券数据...")
            coupons_data = load_json_file('coupons.json')
            coupon_count = 0
            
            for coupon_data in coupons_data:
                coupon = Coupon(
                    id=coupon_data.get('id'),
                    name=coupon_data.get('name'),
                    description=coupon_data.get('description'),
                    type=coupon_data.get('type', 'fixed'),
                    value=coupon_data.get('value', 0),
                    discount=coupon_data.get('discount', 0),
                    min_amount=coupon_data.get('min_amount', 0),
                    max_discount=coupon_data.get('max_discount'),
                    total_quantity=coupon_data.get('total_quantity', 1000),
                    used_quantity=coupon_data.get('used_quantity', 0),
                    limit_per_user=coupon_data.get('limit_per_user', 1),
                    start_time=parse_datetime(coupon_data.get('start_time')),
                    end_time=parse_datetime(coupon_data.get('end_time')),
                    status=coupon_data.get('status', 'active')
                )
                coupon.applicable_categories = coupon_data.get('applicable_categories', [])
                coupon.applicable_products = coupon_data.get('applicable_products', [])
                db.session.add(coupon)
                coupon_count += 1
            
            db.session.commit()
            print(f"  ✓ 已导入 {coupon_count} 个优惠券")
        else:
            print(f"\n优惠券表已有数据 ({Coupon.query.count()} 条)，跳过导入")
        
        if not UserCoupon.query.first():
            print("\n开始导入用户优惠券数据...")
            user_coupons_data = load_json_file('user_coupons.json')
            user_coupon_count = 0
            
            for uc_data in user_coupons_data:
                user_coupon = UserCoupon(
                    id=uc_data.get('id'),
                    user_id=uc_data.get('user_id'),
                    coupon_id=uc_data.get('coupon_id'),
                    status=uc_data.get('status', 'unused'),
                    used_at=parse_datetime(uc_data.get('used_at')),
                    order_id=uc_data.get('order_id'),
                    received_at=parse_datetime(uc_data.get('received_at'))
                )
                db.session.add(user_coupon)
                user_coupon_count += 1
            
            db.session.commit()
            print(f"  ✓ 已导入 {user_coupon_count} 个用户优惠券")
        else:
            print(f"\n用户优惠券表已有数据 ({UserCoupon.query.count()} 条)，跳过导入")
        
        print("\n" + "="*60)
        print("数据库迁移完成！")
        print("="*60)
        print(f"用户数: {User.query.count()}")
        print(f"地址数: {Address.query.count()}")
        print(f"老师入驻数: {TeacherProfile.query.count()}")
        print(f"分类数: {Category.query.count()}")
        print(f"产品数: {Product.query.count()}")
        print(f"订单数: {Order.query.count()}")
        print(f"订单项数: {OrderItem.query.count()}")
        print(f"优惠券数: {Coupon.query.count()}")
        print(f"用户优惠券数: {UserCoupon.query.count()}")
        print(f"擅长领域数: {Specialty.query.count()}")

if __name__ == '__main__':
    migrate()
