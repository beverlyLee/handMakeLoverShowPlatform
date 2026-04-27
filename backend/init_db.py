#!/usr/bin/env python3
"""
数据库初始化脚本
1. 创建数据库表
2. 从 JSON 文件迁移数据到 SQLite
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models import User, Address, TeacherProfile, Order, OrderItem, Category, Product, Coupon, UserCoupon
from app.config import Config

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
            return None

def load_json_file(filename):
    filepath = os.path.join(MOCK_DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def init_database():
    app = create_app(Config)
    
    with app.app_context():
        print("创建数据库表...")
        db.create_all()
        print("数据库表创建完成！")
        
        users_data = load_json_file('users.json')
        teachers_data = load_json_file('teachers.json')
        orders_data = load_json_file('orders.json')
        categories_data = load_json_file('categories.json')
        products_data = load_json_file('products.json')
        coupons_data = load_json_file('coupons.json')
        user_coupons_data = load_json_file('user_coupons.json')
        
        if User.query.first():
            print("数据库已有数据，跳过迁移。")
            print("如果需要重新迁移，请先删除 handicraft.db 文件。")
            return
        
        print("\n开始迁移用户数据...")
        
        users_list = users_data.get('users', [])
        addresses_list = users_data.get('addresses', [])
        teachers_list = teachers_data.get('teachers', [])
        
        user_id_map = {}
        
        for user_data in users_list:
            user = User(
                id=user_data.get('id'),
                username=user_data.get('username'),
                nickname=user_data.get('nickname'),
                avatar=user_data.get('avatar'),
                phone=user_data.get('phone'),
                email=user_data.get('email'),
                gender=user_data.get('gender', 0),
                bio=user_data.get('bio'),
                created_at=parse_datetime(user_data.get('create_time'))
            )
            
            role = user_data.get('role', 'customer')
            if role == 'teacher':
                user.roles = ['customer', 'teacher']
                user.current_role = 'teacher'
            else:
                user.roles = ['customer']
                user.current_role = 'customer'
            
            db.session.add(user)
            user_id_map[user.id] = user
        
        db.session.commit()
        print(f"已迁移 {len(users_list)} 个用户")
        
        print("\n开始迁移地址数据...")
        address_count = 0
        for addr_data in addresses_list:
            user_id = addr_data.get('user_id')
            if user_id in user_id_map:
                address = Address(
                    id=addr_data.get('id'),
                    user_id=user_id,
                    name=addr_data.get('name'),
                    phone=addr_data.get('phone'),
                    province=addr_data.get('province'),
                    city=addr_data.get('city'),
                    district=addr_data.get('district'),
                    detail=addr_data.get('detail'),
                    is_default=addr_data.get('is_default', False),
                    created_at=parse_datetime(addr_data.get('create_time'))
                )
                db.session.add(address)
                address_count += 1
        
        db.session.commit()
        print(f"已迁移 {address_count} 个地址")
        
        print("\n开始迁移老师入驻数据...")
        teacher_count = 0
        for teacher_data in teachers_list:
            user_id = teacher_data.get('user_id')
            if user_id in user_id_map:
                teacher = TeacherProfile(
                    id=teacher_data.get('id'),
                    user_id=user_id,
                    teacher_id=teacher_data.get('teacher_id') or f"T{teacher_data.get('id')}",
                    real_name=teacher_data.get('real_name'),
                    phone=teacher_data.get('phone'),
                    experience_years=teacher_data.get('experience_years', 0),
                    bio=teacher_data.get('bio'),
                    intro=teacher_data.get('bio'),
                    studio_name=teacher_data.get('studio_name'),
                    studio_address=teacher_data.get('studio_address'),
                    rating=teacher_data.get('rating', 5.0),
                    student_count=teacher_data.get('student_count', 0),
                    product_count=teacher_data.get('product_count', 0),
                    order_count=teacher_data.get('order_count', 0),
                    follower_count=teacher_data.get('follower_count', 0),
                    is_verified=teacher_data.get('is_verified', True),
                    verified_at=parse_datetime(teacher_data.get('verified_at')),
                    created_at=parse_datetime(teacher_data.get('create_time')),
                    updated_at=parse_datetime(teacher_data.get('update_time'))
                )
                
                teacher.specialties = teacher_data.get('specialties', [])
                teacher.certifications = teacher_data.get('certifications', [])
                teacher.studio_images = teacher_data.get('studio_images', [])
                
                db.session.add(teacher)
                teacher_count += 1
        
        db.session.commit()
        print(f"已迁移 {teacher_count} 个老师入驻数据")
        
        print("\n开始迁移订单数据...")
        orders_list = orders_data.get('orders', [])
        order_count = 0
        order_item_count = 0
        
        for order_data in orders_list:
            order = Order(
                id=order_data.get('id'),
                user_id=order_data.get('user_id'),
                teacher_id=order_data.get('teacher_id'),
                status=order_data.get('status', 'pending'),
                total_amount=order_data.get('total_amount', 0.0),
                discount_amount=order_data.get('discount_amount', 0.0),
                pay_amount=order_data.get('pay_amount', 0.0),
                shipping_fee=order_data.get('shipping_fee', 0.0),
                pay_method=order_data.get('pay_method'),
                pay_time=parse_datetime(order_data.get('pay_time')),
                ship_time=parse_datetime(order_data.get('ship_time')),
                deliver_time=parse_datetime(order_data.get('deliver_time')),
                complete_time=parse_datetime(order_data.get('complete_time')),
                cancel_time=parse_datetime(order_data.get('cancel_time')),
                cancel_reason=order_data.get('cancel_reason'),
                remark=order_data.get('remark'),
                created_at=parse_datetime(order_data.get('create_time')),
                updated_at=parse_datetime(order_data.get('update_time'))
            )
            
            address = order_data.get('address', {})
            order.address_name = address.get('name')
            order.address_phone = address.get('phone')
            order.address_province = address.get('province')
            order.address_city = address.get('city')
            order.address_district = address.get('district')
            order.address_detail = address.get('detail')
            
            db.session.add(order)
            order_count += 1
            
            items = order_data.get('items', [])
            for item_data in items:
                order_item = OrderItem(
                    id=item_data.get('id'),
                    order_id=order.id,
                    product_id=item_data.get('product_id'),
                    product_title=item_data.get('product_title'),
                    product_image=item_data.get('product_image'),
                    price=item_data.get('price', 0.0),
                    original_price=item_data.get('original_price', 0.0),
                    quantity=item_data.get('quantity', 1),
                    total_price=item_data.get('total_price', 0.0)
                )
                db.session.add(order_item)
                order_item_count += 1
        
        db.session.commit()
        print(f"已迁移 {order_count} 个订单，{order_item_count} 个订单项")
        
        print("\n开始迁移分类数据...")
        categories_list = categories_data.get('categories', [])
        category_count = 0
        category_id_map = {}
        
        for cat_data in categories_list:
            category = Category(
                id=cat_data.get('id'),
                name=cat_data.get('name'),
                name_en=cat_data.get('name_en'),
                icon=cat_data.get('icon'),
                description=cat_data.get('description'),
                sort=cat_data.get('sort', 0),
                status=cat_data.get('status', 'active'),
                product_count=cat_data.get('product_count', 0),
                created_at=parse_datetime(cat_data.get('create_time')),
                updated_at=parse_datetime(cat_data.get('update_time'))
            )
            db.session.add(category)
            category_id_map[category.id] = category
            category_count += 1
        
        db.session.commit()
        print(f"已迁移 {category_count} 个分类")
        
        print("\n开始迁移产品数据...")
        products_list = products_data.get('products', [])
        product_count = 0
        
        for prod_data in products_list:
            product = Product(
                id=prod_data.get('id'),
                teacher_id=prod_data.get('teacher_id'),
                title=prod_data.get('title'),
                description=prod_data.get('description'),
                category_id=prod_data.get('category_id'),
                price=prod_data.get('price', 0.0),
                original_price=prod_data.get('original_price', 0.0),
                stock=prod_data.get('stock', 0),
                cover_image=prod_data.get('cover_image'),
                status=prod_data.get('status', 'active'),
                sales_count=prod_data.get('sales_count', 0),
                favorite_count=prod_data.get('favorite_count', 0),
                view_count=0,
                rating=prod_data.get('rating', 5.0),
                created_at=parse_datetime(prod_data.get('create_time')),
                updated_at=parse_datetime(prod_data.get('update_time'))
            )
            product.images = prod_data.get('images', [])
            product.tags = prod_data.get('tags', [])
            db.session.add(product)
            product_count += 1
        
        db.session.commit()
        print(f"已迁移 {product_count} 个产品")
        
        print("\n开始迁移优惠券数据...")
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
        print(f"已迁移 {coupon_count} 个优惠券")
        
        print("\n开始迁移用户优惠券数据...")
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
        print(f"已迁移 {user_coupon_count} 个用户优惠券")
        
        print("\n" + "="*50)
        print("数据库初始化完成！")
        print("="*50)
        print(f"用户数: {User.query.count()}")
        print(f"地址数: {Address.query.count()}")
        print(f"老师入驻数: {TeacherProfile.query.count()}")
        print(f"分类数: {Category.query.count()}")
        print(f"产品数: {Product.query.count()}")
        print(f"订单数: {Order.query.count()}")
        print(f"订单项数: {OrderItem.query.count()}")
        print(f"优惠券数: {Coupon.query.count()}")
        print(f"用户优惠券数: {UserCoupon.query.count()}")

if __name__ == '__main__':
    init_database()
