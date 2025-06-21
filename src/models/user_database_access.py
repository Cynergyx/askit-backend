from src.extensions import db
from datetime import datetime
import uuid

class UserDatabaseAccess(db.Model):
    __tablename__ = 'user_database_access'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    database_name = db.Column(db.String(100), nullable=False)
    view_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # In a real-world scenario, connection details with secrets should be encrypted
    # or stored in a secure vault, not plaintext in the DB.
    connection_details = db.Column(db.JSON) 
    
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='database_accesses', foreign_keys=[user_id])
    organization = db.relationship('Organization')
    granter = db.relationship('User', foreign_keys=[granted_by])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'database_name': self.database_name,
            'view_name': self.view_name,
            'description': self.description,
            'connection_details': self.connection_details,
            'granted_at': self.granted_at.isoformat()
        }