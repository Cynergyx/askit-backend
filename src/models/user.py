from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_sso_user = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    sso_provider = db.Column(db.String(50))
    sso_user_id = db.Column(db.String(255))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    organization = db.relationship('Organization', backref='users')
    
    # FIX: Explicitly define the foreign key for the user_roles relationship
    user_roles = db.relationship('UserRole', back_populates='user', cascade='all, delete-orphan', foreign_keys='UserRole.user_id')
    audit_logs = db.relationship('AuditLog', backref='user', foreign_keys='AuditLog.user_id')
    database_accesses = db.relationship('UserDatabaseAccess', back_populates='user', cascade='all, delete-orphan', lazy='dynamic', foreign_keys='UserDatabaseAccess.user_id')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_roles(self):
        return [ur.role for ur in self.user_roles if ur.is_active and ur.role.is_active]
    
    def get_permissions(self):
        permissions = set()
        for role in self.get_roles():
            permissions.update(role.get_permissions())
        return list(permissions)
    
    def to_dict(self, include_details=False, include_db_access=False):
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_sso_user': self.is_sso_user,
            'sso_provider': self.sso_provider,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        if include_details:
            data['roles'] = [role.to_dict() for role in self.get_roles()]
            data['permissions'] = [perm.to_dict() for perm in self.get_permissions()]
        
        if include_db_access:
            data['database_accesses'] = [access.to_dict() for access in self.database_accesses.all()]

        return data

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', back_populates='user_roles', foreign_keys=[user_id])
    role = db.relationship('Role', back_populates='user_roles')
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)