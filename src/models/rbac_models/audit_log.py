import datetime
from src.db.rbac_db.db import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for system actions
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False) # e.g., "user_created", "role_permission_changed"
    details = db.Column(db.JSON, nullable=True) # Store before/after state or other relevant info
    
    user = db.relationship('User')
    organization = db.relationship('Organization')