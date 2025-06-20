from werkzeug.security import generate_password_hash, check_password_hash
from src.db.rbac_db.db import db
from src.models.rbac_models.association_tables import user_roles

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Foreign key to link user to their organization (tenant)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # N-level hierarchy: a user can be managed by another user
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    subordinates = db.relationship('User', backref=db.backref('manager', remote_side=[id]))

    roles = db.relationship('Role', secondary=user_roles, backref='users', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_permissions(self):
        """Returns a set of all permission strings for the user."""
        permissions = set()
        for role in self.roles.all():
            for perm in role.permissions:
                permissions.add(perm.name)
        return permissions