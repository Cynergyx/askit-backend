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
    
    # This relationship goes through the UserRole association object.
    user_assignments = db.relationship('UserRole', back_populates='role', cascade="all, delete-orphan")
    
    permissions = db.relationship(
        'Permission',
        secondary='role_permissions',
        back_populates='roles',
        lazy="joined"
    )

    def to_dict(self, include_permissions=False):
        data = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'organization_id': self.organization_id,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
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