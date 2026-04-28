from datetime import datetime
from app.database import db

MESSAGE_TYPE_SYSTEM = 'system'
MESSAGE_TYPE_ORDER = 'order'
MESSAGE_TYPE_ACTIVITY = 'activity'

MESSAGE_TYPES = {
    MESSAGE_TYPE_SYSTEM: '系统通知',
    MESSAGE_TYPE_ORDER: '订单消息',
    MESSAGE_TYPE_ACTIVITY: '活动消息'
}


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    type = db.Column(db.String(50), default=MESSAGE_TYPE_SYSTEM, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    sender = db.Column(db.String(100), default='系统')
    sender_avatar = db.Column(db.String(500))
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    related_id = db.Column(db.Integer)
    related_type = db.Column(db.String(50))
    
    recipient_role = db.Column(db.String(20), default='customer')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='messages', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'type_name': MESSAGE_TYPES.get(self.type, '其他消息'),
            'title': self.title,
            'content': self.content,
            'sender': self.sender,
            'sender_avatar': self.sender_avatar,
            'is_read': self.is_read,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'recipient_role': self.recipient_role,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Message {self.id}: {self.title[:30]}>'


class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    last_message = db.Column(db.String(500))
    last_message_time = db.Column(db.DateTime)
    last_message_sender_id = db.Column(db.Integer)
    
    user1_unread = db.Column(db.Integer, default=0)
    user2_unread = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user1 = db.relationship('User', foreign_keys=[user1_id], backref='conversations_as_user1', lazy=True)
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='conversations_as_user2', lazy=True)
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, current_user_id=None):
        other_user_id = self.user2_id if current_user_id == self.user1_id else self.user1_id
        other_user = None
        if other_user_id:
            from app.models import User
            other_user = User.query.get(other_user_id)
        
        unread_count = 0
        if current_user_id == self.user1_id:
            unread_count = self.user1_unread or 0
        elif current_user_id == self.user2_id:
            unread_count = self.user2_unread or 0
        
        return {
            'id': self.id,
            'conversation_id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'other_user_id': other_user_id,
            'other_user_name': other_user.nickname if other_user else '用户',
            'name': other_user.nickname if other_user else '用户',
            'other_user_avatar': other_user.avatar if other_user else None,
            'avatar': other_user.avatar if other_user else None,
            'last_message': self.last_message,
            'last_message_time': self.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_message_time else None,
            'last_message_sender_id': self.last_message_sender_id,
            'unread_count': unread_count,
            'unread': unread_count,
            'is_read': unread_count == 0,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Conversation {self.id}: {self.user1_id} <-> {self.user2_id}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    
    message_type = db.Column(db.String(50), default='text')
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='chat_messages', lazy=True)

    def to_dict(self, current_user_id=None):
        is_self = False
        if current_user_id:
            is_self = self.sender_id == current_user_id
        
        sender_name = ''
        sender_avatar = ''
        if self.sender:
            sender_name = self.sender.nickname or self.sender.username
            sender_avatar = self.sender.avatar
        
        return {
            'id': self.id,
            'message_id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': sender_name,
            'sender_avatar': sender_avatar,
            'content': self.content,
            'message_type': self.message_type,
            'is_self': is_self,
            'is_read': self.is_read,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.content[:30]}>'
