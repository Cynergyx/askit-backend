from src.extensions import db
from datetime import datetime, timezone
import uuid

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    resource = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    conditions = db.Column(db.JSON)  # For row-level security conditions
    is_system_permission = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    role_permissions = db.relationship('RolePermission', back_populates='permission', overlaps="roles,permissions")
    roles = db.relationship(
        'Role',
        secondary='role_permissions',
        back_populates='permissions',
        overlaps="role_permissions,permissions"
    )
    data_access_policies = db.relationship('DataAccessPolicy', backref='permission')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'conditions': self.conditions,
            'is_system_permission': self.is_system_permission,
            'created_at': self.created_at.isoformat()
        }

class DataAccessPolicy(db.Model):
    __tablename__ = 'data_access_policies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    column_name = db.Column(db.String(100))  # For column-level security
    access_type = db.Column(db.Enum('READ', 'WRITE', 'DELETE', name='access_type'), nullable=False)
    conditions = db.Column(db.JSON)  # Row-level security conditions
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    organization = db.relationship('Organization', backref='data_access_policies')

class DataMaskingPolicy(db.Model):
    __tablename__ = 'data_masking_policies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    column_name = db.Column(db.String(100), nullable=False)
    masking_type = db.Column(db.Enum('FULL', 'PARTIAL', 'HASH', 'ENCRYPT', name='masking_type'), nullable=False)
    masking_pattern = db.Column(db.String(255))  # e.g., "XXX-XX-XXXX" for SSN
    conditions = db.Column(db.JSON)  # When to apply masking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    organization = db.relationship('Organization', backref='data_masking_policies')
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'table_name', 'column_name', name='unique_masking_policy'),)
