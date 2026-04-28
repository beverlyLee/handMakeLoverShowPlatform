from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.models import Message, Conversation, ChatMessage, User, Order
from app.database import db
from datetime import datetime
from app.services.message_service import MessageService

message_bp = Blueprint('messages', __name__)

MESSAGE_TYPES = {
    'system': '系统通知',
    'order': '订单消息',
    'activity': '活动消息'
}


def get_current_user_id():
    return g.get('user_id', 1)


@message_bp.route('/unread', methods=['GET'])
@login_required
def get_unread_count():
    user_id = get_current_user_id()
    role = request.args.get('role', None)
    
    query = Message.query.filter_by(
        user_id=user_id,
        is_read=False
    )
    
    if role and role in ['customer', 'teacher']:
        query = query.filter_by(recipient_role=role)
    
    unread_messages = query.all()
    
    unread_by_type = {
        'system': 0,
        'order': 0,
        'activity': 0
    }
    
    for msg in unread_messages:
        msg_type = msg.type
        if msg_type in unread_by_type:
            unread_by_type[msg_type] += 1
    
    unread_conversations = Conversation.query.filter(
        (Conversation.user1_id == user_id) & (Conversation.user1_unread > 0) |
        (Conversation.user2_id == user_id) & (Conversation.user2_unread > 0)
    ).all()
    
    chat_unread = 0
    for conv in unread_conversations:
        if conv.user1_id == user_id:
            chat_unread += conv.user1_unread or 0
        else:
            chat_unread += conv.user2_unread or 0
    
    total = sum(unread_by_type.values()) + chat_unread
    
    return jsonify(success(data={
        'system': unread_by_type['system'],
        'order': unread_by_type['order'],
        'activity': unread_by_type['activity'],
        'chat': chat_unread,
        'total': total
    }))


@message_bp.route('/', methods=['GET'])
@login_required
def get_messages():
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    msg_type = request.args.get('type', None)
    role = request.args.get('role', None)
    
    query = Message.query.filter_by(user_id=user_id)
    
    if msg_type and msg_type in MESSAGE_TYPES:
        query = query.filter_by(type=msg_type)
    
    if role and role in ['customer', 'teacher']:
        query = query.filter_by(recipient_role=role)
    
    total = query.count()
    
    messages = query.order_by(Message.created_at.desc()).paginate(
        page=page,
        per_page=size,
        error_out=False
    ).items
    
    message_list = [msg.to_dict() for msg in messages]
    
    return jsonify(success(data={
        'list': message_list,
        'total': total,
        'page': page,
        'size': size,
        'has_more': len(messages) >= size
    }))


@message_bp.route('/<int:message_id>', methods=['GET'])
@login_required
def get_message_detail(message_id):
    user_id = get_current_user_id()
    
    message = Message.query.filter_by(
        id=message_id,
        user_id=user_id
    ).first()
    
    if not message:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='消息不存在')), 404
    
    return jsonify(success(data=message.to_dict()))


@message_bp.route('/<int:message_id>/read', methods=['PUT'])
@login_required
def mark_as_read(message_id):
    user_id = get_current_user_id()
    
    message = Message.query.filter_by(
        id=message_id,
        user_id=user_id
    ).first()
    
    if not message:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='消息不存在')), 404
    
    if not message.is_read:
        message.is_read = True
        message.read_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify(success(msg='已标记为已读'))


@message_bp.route('/batch-read', methods=['PUT'])
@login_required
def batch_mark_as_read():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data or 'message_ids' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='message_ids 参数不能为空')), 400
    
    message_ids = data.get('message_ids', [])
    if not isinstance(message_ids, list):
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='message_ids 必须是数组')), 400
    
    if len(message_ids) == 0:
        return jsonify(success(msg='没有需要标记的消息'))
    
    messages = Message.query.filter(
        Message.id.in_(message_ids),
        Message.user_id == user_id,
        Message.is_read == False
    ).all()
    
    now = datetime.utcnow()
    for msg in messages:
        msg.is_read = True
        msg.read_at = now
    
    db.session.commit()
    
    return jsonify(success(msg=f'已标记 {len(messages)} 条消息为已读'))


@message_bp.route('/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    user_id = get_current_user_id()
    
    message = Message.query.filter_by(
        id=message_id,
        user_id=user_id
    ).first()
    
    if not message:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='消息不存在')), 404
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify(success(msg='删除成功'))


@message_bp.route('/batch-delete', methods=['DELETE'])
@login_required
def batch_delete_messages():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data or 'message_ids' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='message_ids 参数不能为空')), 400
    
    message_ids = data.get('message_ids', [])
    if not isinstance(message_ids, list):
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='message_ids 必须是数组')), 400
    
    if len(message_ids) == 0:
        return jsonify(success(msg='没有需要删除的消息'))
    
    deleted_count = Message.query.filter(
        Message.id.in_(message_ids),
        Message.user_id == user_id
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    return jsonify(success(msg=f'已删除 {deleted_count} 条消息'))


@message_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    user_id = get_current_user_id()
    
    conversation = Conversation.query.filter(
        Conversation.id == conversation_id,
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).first()
    
    if not conversation:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='会话不存在')), 404
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify(success(msg='删除成功'))


@message_bp.route('/conversations/batch-delete', methods=['DELETE'])
@login_required
def batch_delete_conversations():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data or 'conversation_ids' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='conversation_ids 参数不能为空')), 400
    
    conversation_ids = data.get('conversation_ids', [])
    if not isinstance(conversation_ids, list):
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='conversation_ids 必须是数组')), 400
    
    if len(conversation_ids) == 0:
        return jsonify(success(msg='没有需要删除的会话'))
    
    deleted_count = Conversation.query.filter(
        Conversation.id.in_(conversation_ids),
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    return jsonify(success(msg=f'已删除 {deleted_count} 个会话'))


@message_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    query = Conversation.query.filter(
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    )
    
    total = query.count()
    
    conversations = query.order_by(Conversation.updated_at.desc()).paginate(
        page=page,
        per_page=size,
        error_out=False
    ).items
    
    conv_list = [conv.to_dict(current_user_id=user_id) for conv in conversations]
    
    return jsonify(success(data={
        'list': conv_list,
        'total': total,
        'page': page,
        'size': size,
        'has_more': len(conversations) >= size
    }))


@message_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 30, type=int)
    
    conversation = Conversation.query.filter(
        Conversation.id == conversation_id,
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).first()
    
    if not conversation:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='会话不存在')), 404
    
    if conversation.user1_id == user_id and conversation.user1_unread > 0:
        conversation.user1_unread = 0
        db.session.commit()
    elif conversation.user2_id == user_id and conversation.user2_unread > 0:
        conversation.user2_unread = 0
        db.session.commit()
    
    query = ChatMessage.query.filter_by(conversation_id=conversation_id)
    total = query.count()
    
    messages = query.order_by(ChatMessage.created_at.asc()).paginate(
        page=page,
        per_page=size,
        error_out=False
    ).items
    
    message_list = [msg.to_dict(current_user_id=user_id) for msg in messages]
    
    return jsonify(success(data={
        'list': message_list,
        'total': total,
        'page': page,
        'size': size,
        'has_more': len(messages) >= size,
        'conversation': conversation.to_dict(current_user_id=user_id)
    }))


@message_bp.route('/conversations/<int:conversation_id>/send', methods=['POST'])
@login_required
def send_chat_message(conversation_id):
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='消息内容不能为空')), 400
    
    content = data.get('content', '').strip()
    if not content:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='消息内容不能为空')), 400
    
    if len(content) > 200:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='消息内容不能超过200字')), 400
    
    conversation = Conversation.query.filter(
        Conversation.id == conversation_id,
        (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
    ).first()
    
    if not conversation:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='会话不存在')), 404
    
    chat_message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=user_id,
        content=content,
        message_type='text'
    )
    db.session.add(chat_message)
    
    now = datetime.utcnow()
    conversation.last_message = content
    conversation.last_message_time = now
    conversation.last_message_sender_id = user_id
    
    if conversation.user1_id == user_id:
        conversation.user2_unread = (conversation.user2_unread or 0) + 1
    else:
        conversation.user1_unread = (conversation.user1_unread or 0) + 1
    
    db.session.commit()
    
    return jsonify(success(data=chat_message.to_dict(current_user_id=user_id), msg='发送成功'))


@message_bp.route('/conversations', methods=['POST'])
@login_required
def create_conversation():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data or 'target_user_id' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='target_user_id 参数不能为空')), 400
    
    target_user_id = data.get('target_user_id')
    
    if target_user_id == user_id:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='不能给自己发消息')), 400
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='目标用户不存在')), 404
    
    existing_conv = Conversation.query.filter(
        ((Conversation.user1_id == user_id) & (Conversation.user2_id == target_user_id)) |
        ((Conversation.user1_id == target_user_id) & (Conversation.user2_id == user_id))
    ).first()
    
    if existing_conv:
        return jsonify(success(data=existing_conv.to_dict(current_user_id=user_id), msg='会话已存在'))
    
    conversation = Conversation(
        user1_id=user_id,
        user2_id=target_user_id,
        user1_unread=0,
        user2_unread=0
    )
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify(success(data=conversation.to_dict(current_user_id=user_id), msg='创建成功'))


@message_bp.route('/send', methods=['POST'])
@login_required
def send_system_message():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    required_fields = ['title', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    message_type = data.get('type', 'system')
    if message_type not in MESSAGE_TYPES:
        message_type = 'system'
    
    message = Message(
        user_id=user_id,
        type=message_type,
        title=data.get('title'),
        content=data.get('content'),
        sender=data.get('sender', '系统'),
        sender_avatar=data.get('sender_avatar'),
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify(success(data=message.to_dict(), msg='发送成功'))


@message_bp.route('/chat/send', methods=['POST'])
@login_required
def send_direct_chat():
    user_id = get_current_user_id()
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    required_fields = ['target_user_id', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify(error(code=ResponseCode.PARAM_MISSING, msg=f'{field} 不能为空')), 400
    
    target_user_id = data.get('target_user_id')
    content = data.get('content', '').strip()
    
    if target_user_id == user_id:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='不能给自己发消息')), 400
    
    if not content:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='消息内容不能为空')), 400
    
    if len(content) > 500:
        return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='消息内容不能超过500字')), 400
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify(error(code=ResponseCode.USER_NOT_FOUND, msg='目标用户不存在')), 404
    
    message_type = data.get('message_type', 'text')
    related_id = data.get('related_id')
    related_type = data.get('related_type')
    
    chat_message, conversation = MessageService.send_chat_message(
        sender_id=user_id,
        receiver_id=target_user_id,
        content=content,
        message_type=message_type
    )
    
    return jsonify(success(data={
        'message': chat_message,
        'conversation': conversation
    }, msg='发送成功'))


@message_bp.route('/conversation/with-user/<int:target_user_id>', methods=['GET'])
@login_required
def get_conversation_with_user(target_user_id):
    user_id = get_current_user_id()
    
    conversation = Conversation.query.filter(
        ((Conversation.user1_id == user_id) & (Conversation.user2_id == target_user_id)) |
        ((Conversation.user1_id == target_user_id) & (Conversation.user2_id == user_id))
    ).first()
    
    if conversation:
        return jsonify(success(data=conversation.to_dict(current_user_id=user_id)))
    else:
        return jsonify(success(data=None, msg='会话不存在'))


@message_bp.route('/conversation/with-user/<int:target_user_id>/messages', methods=['GET'])
@login_required
def get_messages_with_user(target_user_id):
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 30, type=int)
    
    conversation = Conversation.query.filter(
        ((Conversation.user1_id == user_id) & (Conversation.user2_id == target_user_id)) |
        ((Conversation.user1_id == target_user_id) & (Conversation.user2_id == user_id))
    ).first()
    
    if not conversation:
        return jsonify(success(data={
            'list': [],
            'total': 0,
            'page': page,
            'size': size,
            'has_more': False,
            'conversation': None
        }))
    
    if conversation.user1_id == user_id and conversation.user1_unread > 0:
        conversation.user1_unread = 0
        db.session.commit()
    elif conversation.user2_id == user_id and conversation.user2_unread > 0:
        conversation.user2_unread = 0
        db.session.commit()
    
    query = ChatMessage.query.filter_by(conversation_id=conversation.id)
    total = query.count()
    
    messages = query.order_by(ChatMessage.created_at.asc()).paginate(
        page=page,
        per_page=size,
        error_out=False
    ).items
    
    message_list = [msg.to_dict(current_user_id=user_id) for msg in messages]
    
    return jsonify(success(data={
        'list': message_list,
        'total': total,
        'page': page,
        'size': size,
        'has_more': len(messages) >= size,
        'conversation': conversation.to_dict(current_user_id=user_id)
    }))


@message_bp.route('/order/<order_id>/contact', methods=['POST'])
@login_required
def contact_through_order(order_id):
    user_id = get_current_user_id()
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='订单不存在')), 404
    
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    
    if order.user_id == user_id:
        target_user_id = order.teacher_id
        if not target_user_id:
            return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='该订单没有关联的老师')), 404
    elif order.teacher_id == user_id:
        target_user_id = order.user_id
    else:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='无权操作此订单')), 403
    
    if content:
        if len(content) > 500:
            return jsonify(error(code=ResponseCode.PARAM_INVALID, msg='消息内容不能超过500字')), 400
        
        chat_message, conversation = MessageService.send_chat_message(
            sender_id=user_id,
            receiver_id=target_user_id,
            content=content,
            message_type=message_type
        )
        
        return jsonify(success(data={
            'message': chat_message,
            'conversation': conversation,
            'target_user_id': target_user_id
        }, msg='发送成功'))
    else:
        conversation = MessageService.get_or_create_conversation(user_id, target_user_id)
        return jsonify(success(data={
            'conversation': conversation.to_dict(current_user_id=user_id),
            'target_user_id': target_user_id
        }, msg='会话已创建'))
