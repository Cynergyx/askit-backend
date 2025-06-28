from src.extensions import db
from datetime import datetime
import uuid

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'))
    is_system_role = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='roles')
    users = db.relationship(
        'User',
        secondary='user_roles',
        primaryjoin="Role.id==UserRole.role_id",
        secondaryjoin="User.id==UserRole.user_id",
        back_populates='roles',
        foreign_keys="[UserRole.role_id, UserRole.user_id]",
        overlaps="role_assignments,user"
    )
    permissions = db.relationship(
        'Permission',
        secondary='role_permissions',
        back_populates='roles',
        overlaps="role_permissions,roles"
    )
    role_permissions = db.relationship(
        'RolePermission',
        back_populates='role',
        overlaps="permissions,roles"
    )

    def to_dict(self, include_permissions=False):
        data = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'organization_id': self.organization_id,
            'is_system_role': self.is_system_role,
            'created_at': self.created_at.isoformat()
        }
        if include_permissions:
            data['permissions'] = [perm.to_dict() for perm in self.permissions]
        return data

    def clone(self, new_organization_id: str):
        new_role = Role(
            id=str(uuid.uuid4()),
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            is_system_role=False,
            organization_id=new_organization_id
        )
        new_role.permissions = self.permissions
        return new_role

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), primary_key=True)

    role = db.relationship('Role', back_populates='role_permissions', overlaps="permissions,roles")
    permission = db.relationship('Permission', back_populates='role_permissions', overlaps="roles,permissions")