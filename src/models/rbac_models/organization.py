from src.db.rbac_db.db import db

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    users = db.relationship('User', backref='organization', lazy=True)
    roles = db.relationship('Role', backref='organization', lazy=True, cascade="all, delete-orphan")