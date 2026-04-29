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
    Logistics, LogisticsItem, Image,
    Message, Conversation, ChatMessage, Like
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

def migrate_order_addresses():
    print("\n【4/4】迁移订单地址数据...")
    print("-"*40)
    
    orders_data = load_json_file('orders.json')
    orders_list = orders_data.get('orders', []) if isinstance(orders_data, dict) else []
    
    address_map = {}
    for order_data in orders_list:
        order_id = order_data.get('id')
        if order_id:
            address_map[order_id] = order_data.get('address', {})
    
    all_orders = Order.query.all()
    orders_to_update = []
    
    for order in all_orders:
        if order.address_name and order.address_phone:
            continue
        
        address = address_map.get(order.id, {})
        
        if not address:
            user_addresses = Address.query.filter_by(user_id=order.user_id).all()
            if user_addresses:
                default_address = next((a for a in user_addresses if a.is_default), user_addresses[0])
                address = {
                    'name': default_address.name,
                    'phone': default_address.phone,
                    'province': default_address.province,
                    'city': default_address.city,
                    'district': default_address.district,
                    'detail': default_address.detail
                }
        
        if address and address.get('name') and address.get('phone'):
            order.address_name = address.get('name')
            order.address_phone = address.get('phone')
            order.address_province = address.get('province')
            order.address_city = address.get('city')
            order.address_district = address.get('district')
            order.address_detail = address.get('detail')
            orders_to_update.append(order)
            print(f"  ✓ 更新订单地址: {order.id} - {address.get('name')}")
    
    if orders_to_update:
        db.session.commit()
        print(f"  ✓ 已更新 {len(orders_to_update)} 个订单的地址数据")
    else:
        print("  - 所有订单已有地址数据，无需更新")

def migrate():
    with app.app_context():
        print("="*60)
        print("数据库迁移脚本")
        print("="*60)
        
        print("\n【1/5】创建新表...")
        print("-"*40)
        
        new_tables = ['coupons', 'user_coupons', 'logistics', 'logistics_items', 'images', 'messages', 'conversations', 'chat_messages', 'likes']
        for table in new_tables:
            if not check_table_exists(table):
                print(f"  创建表: {table}")
            else:
                print(f"  表已存在: {table}")
        
        db.create_all()
        db.session.commit()
        print("  ✓ 新表创建完成")
        
        if not Image.query.first():
            print("\n图片表为空，已准备好接收上传的图片")
        
        print("\n【2/4】为已有表添加新字段...")
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
        add_column_if_not_exists('orders', 'accept_time DATETIME')
        add_column_if_not_exists('orders', 'start_making_time DATETIME')
        add_column_if_not_exists('orders', 'complete_making_time DATETIME')
        
        print("\n正在检查 teacher_profiles 表:")
        add_column_if_not_exists('teacher_profiles', 'auto_accept BOOLEAN DEFAULT 0')
        
        print("\n正在检查 messages 表:")
        add_column_if_not_exists('messages', 'recipient_role VARCHAR(20) DEFAULT "customer"')
        
        print("\n正在检查 reviews 表:")
        add_column_if_not_exists('reviews', 'is_read BOOLEAN DEFAULT 0')
        add_column_if_not_exists('reviews', 'read_at DATETIME')
        add_column_if_not_exists('reviews', 'reviewer_role VARCHAR(20) DEFAULT "customer"')
        
        print("\n正在检查 append_reviews 表:")
        add_column_if_not_exists('append_reviews', 'reviewer_role VARCHAR(20) DEFAULT "customer"')
        
        print("\n正在检查 products 表:")
        add_column_if_not_exists('products', 'like_count INTEGER DEFAULT 0')
        add_column_if_not_exists('products', 'heat_score REAL DEFAULT 0.0')
        add_column_if_not_exists('products', 'popularity_score REAL DEFAULT 0.0')
        
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
        
        print("\n为已有产品计算热度值...")
        try:
            products = Product.query.all()
            for product in products:
                product.update_heat_score()
            db.session.commit()
            print(f"  ✓ 已为 {len(products)} 个产品计算热度值")
        except Exception as e:
            print(f"  - 计算热度值时跳过: {e}")
            db.session.rollback()
        
        print("\n【3/4】导入新表的 Mock 数据...")
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
        
        migrate_order_addresses()
        
        print("\n【5/5】初始化消息数据...")
        print("-"*40)
        
        if not Message.query.first():
            print("\n开始初始化消息数据...")
            
            mock_messages = [
                {
                    'id': 1,
                    'user_id': 1,
                    'type': 'system',
                    'title': '欢迎加入手工爱好者平台',
                    'content': '亲爱的手作爱好者：\n\n🎉 欢迎加入手工爱好者平台！\n\n在这里，您可以：\n• 浏览精选手工作品\n• 与手作达人交流学习\n• 购买优质手工材料\n• 分享您的创作故事\n\n我们致力于为手工爱好者打造一个温馨、专业的交流社区。\n\n✨ 新用户专享福利：\n首次下单立享9折优惠，优惠码：NEWCRAFT\n\n如有任何问题，欢迎随时联系客服。\n\n祝您创作愉快！\n\n—— 手工爱好者平台团队',
                    'sender': '系统管理员',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-27 10:00:00')
                },
                {
                    'id': 2,
                    'user_id': 1,
                    'type': 'order',
                    'title': '订单发货通知',
                    'content': '您好！您的订单 ORD202404250001 已发货。\n\n📦 订单信息：\n• 商品：手工编织羊毛围巾 x1\n• 快递公司：顺丰速运\n• 快递单号：SF1234567890\n\n预计3-5个工作日送达，请注意查收。\n\n如有问题，请联系客服。',
                    'sender': '订单中心',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-27 14:30:00')
                },
                {
                    'id': 3,
                    'user_id': 1,
                    'type': 'activity',
                    'title': '五一手工市集活动预告',
                    'content': '🎪 五一手工市集来啦！\n\n时间：2024年5月1日-5月3日\n地点：市中心文化广场\n\n活动内容：\n• 手作达人现场展示\n• 手工DIY体验区\n• 手工作品义卖\n• 手工材料特卖\n\n现场注册用户可获赠精美手工小礼品一份！\n\n更多详情请关注我们的公众号。\n\n期待与您相见！',
                    'sender': '活动运营',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-28 09:00:00')
                },
                {
                    'id': 4,
                    'user_id': 1,
                    'type': 'system',
                    'title': '账号安全提醒',
                    'content': '尊敬的用户：\n\n系统检测到您的账号在新设备上登录。\n\n📱 登录信息：\n• 设备：iPhone 14\n• 时间：2024-04-28 10:30:00\n• IP：192.168.1.100\n\n如果这是您本人的操作，请忽略此消息。\n\n如果不是您本人操作，请立即：\n1. 修改密码\n2. 检查账号绑定信息\n3. 联系客服\n\n为保障您的账号安全，请勿将密码告知他人。',
                    'sender': '安全中心',
                    'is_read': True,
                    'read_at': parse_datetime('2024-04-28 10:35:00'),
                    'created_at': parse_datetime('2024-04-28 10:30:00')
                },
                {
                    'id': 5,
                    'user_id': 1,
                    'type': 'order',
                    'title': '订单完成提醒',
                    'content': '您好！您的订单 ORD202404200002 已确认收货，订单已完成。\n\n📦 订单信息：\n• 商品：手工陶瓷茶杯套装 x1\n• 下单时间：2024-04-20\n• 完成时间：2024-04-28\n\n🌟 感谢您的购买！\n\n如果您对商品满意，欢迎在订单评价中分享您的使用体验。您的评价对其他用户很有帮助。\n\n如有任何问题，请联系客服。',
                    'sender': '订单中心',
                    'is_read': True,
                    'read_at': parse_datetime('2024-04-28 12:00:00'),
                    'created_at': parse_datetime('2024-04-28 11:00:00')
                }
            ]
            
            for msg_data in mock_messages:
                message = Message(
                    id=msg_data.get('id'),
                    user_id=msg_data.get('user_id'),
                    type=msg_data.get('type'),
                    title=msg_data.get('title'),
                    content=msg_data.get('content'),
                    sender=msg_data.get('sender'),
                    sender_avatar=msg_data.get('sender_avatar'),
                    is_read=msg_data.get('is_read', False),
                    read_at=msg_data.get('read_at'),
                    related_id=msg_data.get('related_id'),
                    related_type=msg_data.get('related_type'),
                    created_at=msg_data.get('created_at')
                )
                db.session.add(message)
            
            db.session.commit()
            print(f"  ✓ 已初始化 {len(mock_messages)} 条消息")
            
            print("\n开始初始化会话和聊天数据...")
            
            mock_conversations = [
                {
                    'id': 1,
                    'user1_id': 1,
                    'user2_id': 2,
                    'last_message': '好的，我今天下午有空，可以过来学习',
                    'last_message_time': parse_datetime('2024-04-28 15:30:00'),
                    'last_message_sender_id': 2,
                    'user1_unread': 2,
                    'user2_unread': 0
                },
                {
                    'id': 2,
                    'user1_id': 1,
                    'user2_id': 3,
                    'last_message': '感谢您的购买！如果有任何问题随时联系我',
                    'last_message_time': parse_datetime('2024-04-27 09:15:00'),
                    'last_message_sender_id': 3,
                    'user1_unread': 0,
                    'user2_unread': 0
                }
            ]
            
            for conv_data in mock_conversations:
                conversation = Conversation(
                    id=conv_data.get('id'),
                    user1_id=conv_data.get('user1_id'),
                    user2_id=conv_data.get('user2_id'),
                    last_message=conv_data.get('last_message'),
                    last_message_time=conv_data.get('last_message_time'),
                    last_message_sender_id=conv_data.get('last_message_sender_id'),
                    user1_unread=conv_data.get('user1_unread', 0),
                    user2_unread=conv_data.get('user2_unread', 0)
                )
                db.session.add(conversation)
            
            mock_chat_messages = [
                {
                    'id': 1,
                    'conversation_id': 1,
                    'sender_id': 2,
                    'content': '您好！我是手工编织的张老师，请问您有什么想学习的吗？',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 10:00:00')
                },
                {
                    'id': 2,
                    'conversation_id': 1,
                    'sender_id': 1,
                    'content': '张老师您好！我对编织很感兴趣，但是完全没有基础，请问可以学吗？',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 10:15:00')
                },
                {
                    'id': 3,
                    'conversation_id': 1,
                    'sender_id': 2,
                    'content': '当然可以！我们有专门针对零基础学员的入门课程。从最基本的起针、平针开始，一步步教您。您什么时候有空可以过来试听一下？',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 10:30:00')
                },
                {
                    'id': 4,
                    'conversation_id': 1,
                    'sender_id': 1,
                    'content': '太好了！我周末有空，请问周六上午可以吗？',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 14:00:00')
                },
                {
                    'id': 5,
                    'conversation_id': 1,
                    'sender_id': 2,
                    'content': '周六上午9点到11点我有空，您可以过来。工作室地址在创意园A栋302室。',
                    'message_type': 'text',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-25 16:00:00')
                },
                {
                    'id': 6,
                    'conversation_id': 1,
                    'sender_id': 2,
                    'content': '另外，提醒一下，第一次上课不需要带任何材料，我们会提供基础的编织工具和毛线。您只要人来就可以了😊',
                    'message_type': 'text',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-25 16:05:00')
                },
                {
                    'id': 7,
                    'conversation_id': 1,
                    'sender_id': 1,
                    'content': '好的，我今天下午有空，可以过来学习',
                    'message_type': 'text',
                    'is_read': False,
                    'created_at': parse_datetime('2024-04-28 15:30:00')
                },
                {
                    'id': 8,
                    'conversation_id': 2,
                    'sender_id': 3,
                    'content': '您好！我是手工陶瓷坊的李师傅。感谢您购买了我们的陶瓷茶杯套装！',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-20 14:00:00')
                },
                {
                    'id': 9,
                    'conversation_id': 2,
                    'sender_id': 1,
                    'content': '李师傅您好！茶杯收到了，非常精美！请问使用时有什么需要注意的吗？',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 10:00:00')
                },
                {
                    'id': 10,
                    'conversation_id': 2,
                    'sender_id': 3,
                    'content': '非常高兴您喜欢！这款陶瓷茶杯是手工拉坯烧制的，使用时请注意：\n\n1. 首次使用建议用温水清洗\n2. 避免温差过大（不要从冰箱直接倒开水）\n3. 建议手洗，避免洗碗机\n4. 不适合微波炉使用\n\n如果有任何问题，随时联系我！',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 10:30:00')
                },
                {
                    'id': 11,
                    'conversation_id': 2,
                    'sender_id': 1,
                    'content': '好的，明白了！谢谢您的提醒，我会注意的。',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-25 11:00:00')
                },
                {
                    'id': 12,
                    'conversation_id': 2,
                    'sender_id': 3,
                    'content': '感谢您的购买！如果有任何问题随时联系我',
                    'message_type': 'text',
                    'is_read': True,
                    'created_at': parse_datetime('2024-04-27 09:15:00')
                }
            ]
            
            for chat_data in mock_chat_messages:
                chat_message = ChatMessage(
                    id=chat_data.get('id'),
                    conversation_id=chat_data.get('conversation_id'),
                    sender_id=chat_data.get('sender_id'),
                    content=chat_data.get('content'),
                    message_type=chat_data.get('message_type', 'text'),
                    is_read=chat_data.get('is_read', False),
                    read_at=chat_data.get('read_at'),
                    created_at=chat_data.get('created_at')
                )
                db.session.add(chat_message)
            
            db.session.commit()
            print(f"  ✓ 已初始化 {len(mock_conversations)} 个会话，{len(mock_chat_messages)} 条聊天消息")
        else:
            print(f"\n消息表已有数据 ({Message.query.count()} 条)，跳过初始化")
        
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
        print(f"消息数: {Message.query.count()}")
        print(f"会话数: {Conversation.query.count()}")
        print(f"聊天消息数: {ChatMessage.query.count()}")
        print(f"点赞数: {Like.query.count()}")

if __name__ == '__main__':
    migrate()
