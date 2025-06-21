from src.extensions import db
from datetime import datetime, timezone
import uuid

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    parent_role_id = db.Column(db.String(36), db.ForeignKey('roles.id'))
    level = db.Column(db.Integer, default=0)
    is_system_role = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    organization = db.relationship('Organization', backref='roles')
    parent_role = db.relationship('Role', remote_side=[id], backref='child_roles')
    user_roles = db.relationship('UserRole', back_populates='role')
    role_permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('name', 'organization_id', name='unique_role_per_org'),)
    
    def get_permissions(self):
        permissions = [rp.permission for rp in self.role_permissions if rp.is_active]
        # Inherit from parent roles
        if self.parent_role:
            permissions.extend(self.parent_role.get_permissions())
        return list(set(permissions))
    
    def get_all_child_roles(self):
        children = list(self.child_roles)
        for child in self.child_roles:
            children.extend(child.get_all_child_roles())
        return children
    
    def to_dict(self, include_permissions=False):
        data = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'organization_id': self.organization_id,
            'parent_role_id': self.parent_role_id,
            'level': self.level,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
        if include_permissions:
            data['permissions'] = [perm.to_dict() for perm in self.get_permissions()]
        return data

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False)
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    role = db.relationship('Role', back_populates='role_permissions')
    permission = db.relationship('Permission', back_populates='role_permissions')
    granter = db.relationship('User')
    
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)
