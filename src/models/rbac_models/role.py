from src.db.rbac_db.db import db
from src.models.rbac_models.association_tables import role_permissions

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    
    # Each role is specific to an organization
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # N-level hierarchy: roles can inherit from other roles
    parent_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    children = db.relationship('Role', backref=db.backref('parent', remote_side=[id]))

    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('name', 'organization_id', name='_org_role_uc'),)