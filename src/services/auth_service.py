from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from werkzeug.security import check_password_hash
from src.models.user import User
from src.models.organization import Organization
from src.services.audit_service import AuditService
from src.app import db
from datetime import datetime
import uuid

class AuthService:
    @staticmethod
    def authenticate_user(email, password, organization_domain):
        """Authenticate user with email/password"""
        organization = Organization.query.filter_by(domain=organization_domain).first()
        if not organization:
            return None, "Organization not found"
        
        user = User.query.filter_by(email=email, organization_id=organization.id).first()
        if not user or not user.is_active:
            return None, "Invalid credentials"
        
        if user.is_sso_user:
            return None, "SSO user cannot login with password"
        
        if not user.check_password(password):
            return None, "Invalid credentials"
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'organization_id': user.organization_id,
                'roles': [role.name for role in user.get_roles()]
            }
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        # Log authentication
        AuditService.log_action(
            user_id=user.id,
            organization_id=user.organization_id,
            action='LOGIN',
            details={'method': 'password'}
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(include_sensitive=True)
        }, None
    
    @staticmethod
    def refresh_token():
        """Refresh access token"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return None, "User not found or inactive"
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'organization_id': user.organization_id,
                'roles': [role.name for role in user.get_roles()]
            }
        )
        
        return {'access_token': access_token}, None
    
    @staticmethod
    def register_user(email, password, first_name, last_name, organization_domain):
        """Register new user"""
        organization = Organization.query.filter_by(domain=organization_domain).first()
        if not organization:
            return None, "Organization not found"
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, "Email already registered"
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=email.split('@')[0],
            first_name=first_name,
            last_name=last_name,
            organization_id=organization.id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        AuditService.log_action(
            user_id=user.id,
            organization_id=user.organization_id,
            action='REGISTER',
            details={'method': 'email'}
        )
        
        return user.to_dict(), None