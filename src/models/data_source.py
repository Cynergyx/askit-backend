from src.extensions import db
from datetime import datetime
import uuid

class DataSource(db.Model):
    __tablename__ = 'data_sources'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False) # A user-friendly name, e.g., "Production Sales DB"
    type = db.Column(db.String(50), nullable=False) # e.g., 'postgresql', 'mysql', 'snowflake'
    
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    database_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    
    # Store the encrypted password, not plaintext!
    encrypted_password = db.Column(db.String(512)) 
    
    # Extra connection params (e.g., for Snowflake warehouse, role, etc.)
    extra_params = db.Column(db.JSON) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', backref='data_sources')

    def to_dict(self):
        """
        Returns a dictionary representation of the data source.
        IMPORTANT: This does NOT include the encrypted password for security.
        """
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'type': self.type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'extra_params': self.extra_params,
            'created_at': self.created_at.isoformat()
        }