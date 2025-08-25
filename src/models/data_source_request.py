from src.extensions import db
from datetime import datetime
import uuid

class DataSourceRequest(db.Model):
    __tablename__ = 'data_source_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    requested_data_source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False)
    
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default='PENDING', nullable=False) # PENDING, APPROVED, DENIED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    reviewer_notes = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    requested_data_source = db.relationship('DataSource', foreign_keys=[requested_data_source_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    organization = db.relationship('Organization')