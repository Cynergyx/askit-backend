from src.extensions import db
from datetime import datetime, timezone
import uuid

class RoleRequest(db.Model):
    __tablename__ = 'role_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    requested_role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default='PENDING', nullable=False) # PENDING, APPROVED, DENIED
    
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    reviewer_notes = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', back_populates='role_requests', foreign_keys=[user_id])
    requested_role = db.relationship('Role', foreign_keys=[requested_role_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    organization = db.relationship('Organization')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user.email,
            'requested_role_id': self.requested_role_id,
            'requested_role_name': self.requested_role.name,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by_id': self.reviewed_by_id,
            'reviewer_notes': self.reviewer_notes
        }