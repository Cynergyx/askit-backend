from src.db.rbac_db.db import db

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) # e.g., 'user:create', 'document:read_all'