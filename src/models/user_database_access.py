from src.extensions import db
from src.utils.security import DataEncryption
from flask import current_app
from datetime import datetime, timezone
import uuid

class UserDatabaseAccess(db.Model):
    __tablename__ = 'user_database_access'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    data_source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False, index=True)
    
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='database_accesses', foreign_keys=[user_id])
    data_source = db.relationship('DataSource')
    granter = db.relationship('User', foreign_keys=[granted_by])

    def to_dict(self):
        """
        Returns the full connection details for the user.
        This method decrypts the password for the user to use.
        """
        key = current_app.config['ENCRYPTION_KEY']
        if not key:
            raise ValueError("ENCRYPTION_KEY is not configured.")

        decrypted_password = None
        if self.data_source.encrypted_password:
            try:
                decrypted_password = DataEncryption.decrypt_data(self.data_source.encrypted_password, key)
            except Exception:
                # Handle decryption failure gracefully
                decrypted_password = "Error: Could not decrypt password."

        return {
            'grant_id': self.id,
            'data_source_id': self.data_source.id,
            'name': self.data_source.name,
            'type': self.data_source.type,
            'host': self.data_source.host,
            'port': self.data_source.port,
            'database_name': self.data_source.database_name,
            'username': self.data_source.username,
            'password': decrypted_password, # The decrypted password
            'extra_params': self.data_source.extra_params,
            'granted_at': self.granted_at.isoformat()
        }