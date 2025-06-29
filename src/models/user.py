from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False, index=True)
    granted_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='role_assignments')
    role = db.relationship('Role', foreign_keys=[role_id], back_populates='user_assignments')
    granted_by = db.relationship('User', foreign_keys=[granted_by_user_id])


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_sso_user = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    organization = db.relationship('Organization', backref='users')
    
    # Corrected relationship to the association object. lazy="joined" is a performance optimization.
    role_assignments = db.relationship('UserRole', foreign_keys=[UserRole.user_id], back_populates='user', cascade="all, delete-orphan", lazy="joined")
    
    audit_logs = db.relationship('AuditLog', backref='user', foreign_keys='AuditLog.user_id')
    database_accesses = db.relationship('UserDatabaseAccess', back_populates='user', cascade='all, delete-orphan', lazy='dynamic', foreign_keys='UserDatabaseAccess.user_id')
    role_requests = db.relationship('RoleRequest', back_populates='user', foreign_keys='RoleRequest.user_id', lazy=True)
    chat_sessions = db.relationship('ChatSession', back_populates='user', cascade='all, delete-orphan')

    @property
    def roles(self):
        """Returns a list of active Role objects."""
        active_roles = []
        for assignment in self.role_assignments:
            if assignment.is_active and (assignment.expires_at is None or assignment.expires_at > datetime.utcnow()):
                if assignment.role:
                    active_roles.append(assignment.role)
        return active_roles

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_roles(self):
        """Get active role objects."""
        return self.roles
    
    def get_permissions(self):
        """Get active permission objects."""
        permissions = set()
        for role in self.get_roles():
            if role and role.is_active:
                for perm in role.permissions:
                    permissions.add(perm)
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
            'is_verified': self.is_verified,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        if include_details:
            data['roles'] = [role.to_dict() for role in self.get_roles()]
            data['permissions'] = list(set([perm.name for perm in self.get_permissions()]))
        if include_db_access:
            data['database_accesses'] = [access.to_dict() for access in self.database_accesses.all()]
        return data