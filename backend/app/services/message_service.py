from app.models import Message, Conversation, ChatMessage, User, Order
from app.database import db
from datetime import datetime
from app.models.message import MESSAGE_TYPES, MESSAGE_TYPE_SYSTEM, MESSAGE_TYPE_ORDER, MESSAGE_TYPE_ACTIVITY

MESSAGE_CATEGORY_ANNOUNCEMENT = 'announcement'
MESSAGE_CATEGORY_CHAT = 'chat'

ANNOUNCEMENT_SUBTYPES = {
    'activity_publish': '活动发布',
    'system': '系统通知',
    'ship': '发货通知',
    'making_complete': '制作完成',
    'refund': '退款通知',
    'review': '评价通知',
    'order_pay': '订单支付',
    'order_accept': '订单接单',
    'order_reject': '订单拒单',
    'order_cancel': '订单取消',
    'order_complete': '订单完成'
}

CHAT_SUBTYPES = {
    'user_teacher': '用户老师交流',
    'user_merchant': '用户商家交流',
    'review_reply': '评价回复'
}

class MessageService:
    
    @staticmethod
    def send_announcement(
        user_id,
        subtype,
        title,
        content,
        related_id=None,
        related_type=None,
        sender='系统',
        sender_avatar=None
    ):
        message_type = MessageService._get_message_type_by_subtype(subtype)
        
        message = Message(
            user_id=user_id,
            type=message_type,
            title=title,
            content=content,
            sender=sender,
            sender_avatar=sender_avatar,
            is_read=False,
            related_id=related_id,
            related_type=related_type
        )
        
        db.session.add(message)
        db.session.commit()
        
        return message.to_dict()
    
    @staticmethod
    def send_chat_message(
        sender_id,
        receiver_id,
        content,
        message_type='text',
        related_id=None,
        related_type=None
    ):
        conversation = Conversation.query.filter(
            ((Conversation.user1_id == sender_id) & (Conversation.user2_id == receiver_id)) |
            ((Conversation.user1_id == receiver_id) & (Conversation.user2_id == sender_id))
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user1_id=sender_id,
                user2_id=receiver_id,
                user1_unread=0,
                user2_unread=0
            )
            db.session.add(conversation)
            db.session.flush()
        
        chat_message = ChatMessage(
            conversation_id=conversation.id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            is_read=False
        )
        db.session.add(chat_message)
        
        now = datetime.utcnow()
        conversation.last_message = content
        conversation.last_message_time = now
        conversation.last_message_sender_id = sender_id
        
        if conversation.user1_id == sender_id:
            conversation.user2_unread = (conversation.user2_unread or 0) + 1
        else:
            conversation.user1_unread = (conversation.user1_unread or 0) + 1
        
        db.session.commit()
        
        return chat_message.to_dict(current_user_id=sender_id), conversation.to_dict(current_user_id=sender_id)
    
    @staticmethod
    def send_order_pay_notification(order):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        customer_title = '订单支付成功'
        customer_content = f'您的订单 {order.id} 已支付成功，等待老师接单。\n\n'
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if order.items:
            customer_content += f'商品：{order.items[0].product_title}'
            if order.items.count() > 1:
                customer_content += f' 等{order.items.count()}件商品'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='order_pay',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_title = '新订单提醒'
            teacher_content = f'您有新的订单需要处理！\n\n'
            teacher_content += f'订单号：{order.id}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}\n'
            if order.items:
                teacher_content += f'商品：{order.items[0].product_title}'
                if order.items.count() > 1:
                    teacher_content += f' 等{order.items.count()}件商品'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='order_pay',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_order_accept_notification(order, action='start_making'):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        if action == 'ship':
            customer_title = '订单已接单'
            customer_content = f'您的订单 {order.id} 已被老师接单，即将安排发货。\n\n'
            teacher_title = '已接单确认'
            teacher_content = f'您已确认接单，订单 {order.id} 即将安排发货。\n\n'
        else:
            customer_title = '订单开始制作'
            customer_content = f'您的订单 {order.id} 已开始制作。\n\n'
            teacher_title = '已开始制作'
            teacher_content = f'您已开始制作订单 {order.id}。\n\n'
        
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if teacher:
            customer_content += f'老师：{teacher.nickname or teacher.username}\n'
        if order.items:
            customer_content += f'商品：{order.items[0].product_title}'
            if order.items.count() > 1:
                customer_content += f' 等{order.items.count()}件商品'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='order_accept',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_content += f'订单号：{order.id}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}\n'
            if order.items:
                teacher_content += f'商品：{order.items[0].product_title}'
                if order.items.count() > 1:
                    teacher_content += f' 等{order.items.count()}件商品'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='order_accept',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_order_reject_notification(order, reject_reason):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        customer_title = '订单被拒单'
        customer_content = f'很抱歉，您的订单 {order.id} 被老师拒单了。\n\n'
        customer_content += f'拒单理由：{reject_reason}\n\n'
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if teacher:
            customer_content += f'老师：{teacher.nickname or teacher.username}\n'
        customer_content += f'\n您可以重新下单或联系客服咨询。'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='order_reject',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_title = '已拒单确认'
            teacher_content = f'您已拒单，订单 {order.id} 已关闭。\n\n'
            teacher_content += f'订单号：{order.id}\n'
            teacher_content += f'拒单理由：{reject_reason}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='order_reject',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_making_complete_notification(order):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        customer_title = '订单已制作完成'
        customer_content = f'您的订单 {order.id} 制作已完成，即将发货。\n\n'
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if teacher:
            customer_content += f'老师：{teacher.nickname or teacher.username}\n'
        if order.items:
            customer_content += f'商品：{order.items[0].product_title}'
            if order.items.count() > 1:
                customer_content += f' 等{order.items.count()}件商品'
        customer_content += f'\n\n请耐心等待发货通知。'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='making_complete',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_title = '制作完成确认'
            teacher_content = f'您已完成订单 {order.id} 的制作。\n\n'
            teacher_content += f'订单号：{order.id}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}\n'
            teacher_content += f'\n请尽快安排发货。'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='making_complete',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_ship_notification(order):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        customer_title = '订单发货通知'
        customer_content = f'您的订单 {order.id} 已发货！\n\n'
        customer_content += f'快递公司：{order.shipping_company or "待填写"}\n'
        customer_content += f'物流单号：{order.tracking_number or "待填写"}\n\n'
        if order.estimated_arrival_days:
            customer_content += f'预计{order.estimated_arrival_days}天内送达\n\n'
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if teacher:
            customer_content += f'老师：{teacher.nickname or teacher.username}\n'
        if order.items:
            customer_content += f'商品：{order.items[0].product_title}'
            if order.items.count() > 1:
                customer_content += f' 等{order.items.count()}件商品'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='ship',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_title = '发货确认'
            teacher_content = f'您已确认发货，订单 {order.id} 已发出。\n\n'
            teacher_content += f'订单号：{order.id}\n'
            teacher_content += f'快递公司：{order.shipping_company or "待填写"}\n'
            teacher_content += f'物流单号：{order.tracking_number or "待填写"}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='ship',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_order_complete_notification(order):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        customer_title = '订单完成通知'
        customer_content = f'您的订单 {order.id} 已确认收货，订单已完成。\n\n'
        customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
        if order.items:
            customer_content += f'商品：{order.items[0].product_title}'
            if order.items.count() > 1:
                customer_content += f' 等{order.items.count()}件商品'
        customer_content += f'\n\n感谢您的购买，欢迎再次光临！'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='order_complete',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            teacher_title = '订单已完成通知'
            teacher_content = f'订单 {order.id} 已确认收货，订单已完成。\n\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            teacher_content += f'收入已到账，请查看账户余额。'
            
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='order_complete',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def send_order_cancel_notification(order, cancel_reason, is_teacher=False):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        if is_teacher:
            customer_title = '订单被取消'
            customer_content = f'老师已取消您的订单 {order.id}。\n\n'
            customer_content += f'取消理由：{cancel_reason}\n\n'
            customer_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if teacher:
                customer_content += f'老师：{teacher.nickname or teacher.username}'
            
            MessageService.send_announcement(
                user_id=order.user_id,
                subtype='order_cancel',
                title=customer_title,
                content=customer_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
            
            if teacher:
                teacher_title = '已取消订单确认'
                teacher_content = f'您已取消订单 {order.id}。\n\n'
                teacher_content += f'订单号：{order.id}\n'
                teacher_content += f'取消理由：{cancel_reason}\n'
                teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
                if customer:
                    teacher_content += f'客户：{customer.nickname or customer.username}'
                
                MessageService.send_announcement(
                    user_id=order.teacher_id,
                    subtype='order_cancel',
                    title=teacher_title,
                    content=teacher_content,
                    related_id=order.id,
                    related_type='order',
                    sender='订单中心'
                )
        else:
            if teacher:
                teacher_title = '订单被取消'
                teacher_content = f'客户已取消订单 {order.id}。\n\n'
                teacher_content += f'取消理由：{cancel_reason}\n\n'
                teacher_content += f'订单金额：¥{order.pay_amount:.2f}'
                
                MessageService.send_announcement(
                    user_id=order.teacher_id,
                    subtype='order_cancel',
                    title=teacher_title,
                    content=teacher_content,
                    related_id=order.id,
                    related_type='order',
                    sender='订单中心'
                )
            
            if customer:
                customer_title = '订单取消确认'
                customer_content = f'您已取消订单 {order.id}。\n\n'
                customer_content += f'订单号：{order.id}\n'
                customer_content += f'取消理由：{cancel_reason}\n'
                customer_content += f'订单金额：¥{order.pay_amount:.2f}'
                
                MessageService.send_announcement(
                    user_id=order.user_id,
                    subtype='order_cancel',
                    title=customer_title,
                    content=customer_content,
                    related_id=order.id,
                    related_type='order',
                    sender='订单中心'
                )
    
    @staticmethod
    def send_review_notification(review, is_reply=False):
        if is_reply:
            title = '评价有新回复'
            content = f'您的评价收到了新的回复。\n\n'
            content += f'回复内容：{review.reply_content or ""}'
        else:
            title = '新评价通知'
            content = f'您收到了一条新的评价。\n\n'
            content += f'评分：{review.rating or 5}星\n'
            content += f'评价内容：{review.content or ""}'
        
        MessageService.send_announcement(
            user_id=review.teacher_id,
            subtype='review',
            title=title,
            content=content,
            related_id=review.id,
            related_type='review',
            sender='评价中心'
        )
    
    @staticmethod
    def send_activity_publish_notification(activity, target_users=None):
        title = f'新活动发布：{activity.title}'
        content = f'{activity.description}\n\n'
        if activity.start_time:
            content += f'开始时间：{activity.start_time}\n'
        if activity.end_time:
            content += f'结束时间：{activity.end_time}\n'
        if activity.location:
            content += f'活动地点：{activity.location}'
        
        if target_users:
            for user_id in target_users:
                MessageService.send_announcement(
                    user_id=user_id,
                    subtype='activity_publish',
                    title=title,
                    content=content,
                    related_id=activity.id,
                    related_type='activity',
                    sender='活动中心'
                )
        else:
            pass
    
    @staticmethod
    def send_refund_notification(order, refund_status, refund_amount=0, reason=''):
        customer = User.query.get(order.user_id)
        teacher = User.query.get(order.teacher_id) if order.teacher_id else None
        
        if refund_status == 'approved':
            customer_title = '退款申请已通过'
            customer_content = f'您的订单 {order.id} 退款申请已通过。\n\n'
            customer_content += f'退款金额：¥{refund_amount:.2f}\n'
            customer_content += f'退款将在1-3个工作日内原路返回。'
            
            teacher_title = '退款已通过'
            teacher_content = f'订单 {order.id} 的退款申请已通过。\n\n'
            teacher_content += f'退款金额：¥{refund_amount:.2f}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}'
        elif refund_status == 'rejected':
            customer_title = '退款申请被拒绝'
            customer_content = f'很抱歉，您的订单 {order.id} 退款申请被拒绝。\n\n'
            customer_content += f'拒绝理由：{reason}'
            
            teacher_title = '退款已拒绝'
            teacher_content = f'您已拒绝订单 {order.id} 的退款申请。\n\n'
            teacher_content += f'拒绝理由：{reason}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}'
        else:
            customer_title = '退款申请已提交'
            customer_content = f'您的订单 {order.id} 退款申请已提交，等待审核。\n\n'
            customer_content += f'申请退款金额：¥{refund_amount:.2f}\n'
            customer_content += f'退款理由：{reason}'
            
            teacher_title = '新退款申请'
            teacher_content = f'订单 {order.id} 有新的退款申请。\n\n'
            teacher_content += f'申请退款金额：¥{refund_amount:.2f}\n'
            teacher_content += f'退款理由：{reason}\n'
            teacher_content += f'订单金额：¥{order.pay_amount:.2f}\n'
            if customer:
                teacher_content += f'客户：{customer.nickname or customer.username}'
        
        MessageService.send_announcement(
            user_id=order.user_id,
            subtype='refund',
            title=customer_title,
            content=customer_content,
            related_id=order.id,
            related_type='order',
            sender='订单中心'
        )
        
        if teacher:
            MessageService.send_announcement(
                user_id=order.teacher_id,
                subtype='refund',
                title=teacher_title,
                content=teacher_content,
                related_id=order.id,
                related_type='order',
                sender='订单中心'
            )
    
    @staticmethod
    def get_or_create_conversation(user1_id, user2_id):
        conversation = Conversation.query.filter(
            ((Conversation.user1_id == user1_id) & (Conversation.user2_id == user2_id)) |
            ((Conversation.user1_id == user2_id) & (Conversation.user2_id == user1_id))
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user1_id=user1_id,
                user2_id=user2_id,
                user1_unread=0,
                user2_unread=0
            )
            db.session.add(conversation)
            db.session.commit()
        
        return conversation
    
    @staticmethod
    def _get_message_type_by_subtype(subtype):
        if subtype in ['activity_publish', 'system']:
            return MESSAGE_TYPE_ACTIVITY if subtype == 'activity_publish' else MESSAGE_TYPE_SYSTEM
        elif subtype in ['ship', 'making_complete', 'refund', 'review', 
                         'order_pay', 'order_accept', 'order_reject', 
                         'order_cancel', 'order_complete']:
            return MESSAGE_TYPE_ORDER
        else:
            return MESSAGE_TYPE_SYSTEM
