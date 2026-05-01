from datetime import datetime
from app.database import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(500))
    before_data = db.Column(db.Text)
    after_data = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'action': self.action,
            'reason': self.reason,
            'before_data': self.before_data,
            'after_data': self.after_data,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<AuditLog {self.id} {self.target_type} {self.action}>'
