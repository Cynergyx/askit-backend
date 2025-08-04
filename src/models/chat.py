from src.extensions import db
from datetime import datetime, timezone
import uuid

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='chat_sessions')
    organization = db.relationship('Organization')
    messages = db.relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title or f"Chat from {self.created_at.strftime('%Y-%m-%d %H:%M')}",
            'created_at': self.created_at.isoformat(),
            'message_count': len(self.messages)
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    sender = db.Column(db.Enum('user', 'ai', name='chat_sender_type'), nullable=False)
    content = db.Column(db.JSON, nullable=False)
    metadata = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    session = db.relationship('ChatSession', back_populates='messages')

    def to_dict(self):
        """
        Returns a dictionary representation of the chat message
        in the specified format.
        """
        role = 'assistant' if self.sender == 'ai' else 'user'
        
        message = {
            'role': role,
            'content': self.content
        }
            
        return message