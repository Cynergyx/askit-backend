from src.extensions import db
from datetime import datetime, timezone
import uuid

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    session_id = db.Column(db.String(100))
    
    # Relationships
    organization = db.relationship('Organization', backref='audit_logs')
    # user relationship is defined via backref in User model

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'created_at': self.timestamp.isoformat() if self.timestamp else None,
        }

class PermissionChangeLog(db.Model):
    __tablename__ = 'permission_change_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id')) # The admin who made the change
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    target_user_id = db.Column(db.String(36), db.ForeignKey('users.id')) # The user whose permissions were changed
    target_role_id = db.Column(db.String(36), db.ForeignKey('roles.id'))
    action = db.Column(db.Enum('GRANT', 'REVOKE', 'MODIFY', name='permission_action'), nullable=False)
    permission_before = db.Column(db.JSON)
    permission_after = db.Column(db.JSON)
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    # FIX: Explicitly define foreign keys for each relationship to User
    user = db.relationship('User', foreign_keys=[user_id])
    organization = db.relationship('Organization', backref='permission_change_logs')
    target_user = db.relationship('User', foreign_keys=[target_user_id])
    target_role = db.relationship('Role')