from src.extensions import db
from datetime import datetime, timezone
import uuid

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    subdomain = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    settings = db.Column(db.JSON)  # Organization-specific settings
    sso_config = db.Column(db.JSON)  # SSO configuration
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'subdomain': self.subdomain,
            'is_active': self.is_active,
            'settings': self.settings,
            'created_at': self.created_at.isoformat()
        }

class OrganizationSSOConfig(db.Model):
    __tablename__ = 'organization_sso_configs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # oauth2, saml, ldap, okta
    config = db.Column(db.JSON, nullable=False)  # Provider-specific configuration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships
    organization = db.relationship('Organization', backref='sso_configs')
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'provider', name='unique_org_sso_provider'),)
