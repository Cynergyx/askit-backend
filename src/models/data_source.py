from src.extensions import db
from datetime import datetime, timezone
import uuid

class DataSource(db.Model):
    __tablename__ = 'data_sources'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    database_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    
    # Store the encrypted password, not plaintext!
    encrypted_password = db.Column(db.String(512)) 
    
    # Extra connection params (e.g., for Snowflake warehouse, role, etc.)
    extra_params = db.Column(db.JSON) 
    
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    organization = db.relationship('Organization', backref='data_sources')
    schema_metadata = db.relationship('SchemaMetadata', back_populates='data_source', cascade='all, delete-orphan')

    def to_dict(self):
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

class SchemaMetadata(db.Model):
    __tablename__ = 'schema_metadata'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False)
    table_name = db.Column(db.String(255), nullable=False)
    column_name = db.Column(db.String(255), nullable=True) # Null if it's a table-level description
    description = db.Column(db.Text, nullable=True)
    
    data_source = db.relationship('DataSource', back_populates='schema_metadata')
    
    __table_args__ = (db.UniqueConstraint('data_source_id', 'table_name', 'column_name', name='uq_schema_metadata_target'),)

    def to_dict(self):
        return {
            'id': self.id,
            'data_source_id': self.data_source_id,
            'table_name': self.table_name,
            'column_name': self.column_name,
            'description': self.description
        }