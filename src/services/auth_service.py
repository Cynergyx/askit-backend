from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from werkzeug.security import check_password_hash
from src.models.user import User, UserRole
from src.models.organization import Organization
from src.services.audit_service import AuditService
from src.models.role import Role
from src.services.email_service import EmailService
from src.extensions import db
from datetime import datetime
import uuid
from flask import request

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
        
        if not user.is_verified:
            return None, "Please verify your email address before logging in."
        
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
            details={'method': 'password'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(include_details=True, include_db_access=True)
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
        """Registers a new user under an existing organization."""
        organization = Organization.query.filter_by(domain=organization_domain).first()
        if not organization:
            return None, "Organization not found. Registration is not allowed."

        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=email.split('@')[0] + str(uuid.uuid4())[:4],
            first_name=first_name,
            last_name=last_name,
            organization_id=organization.id
        )
        user.set_password(password)

        # Assign the default "Member" role for that organization
        member_role = Role.query.filter_by(name='Member', organization_id=organization.id).first()
        if member_role:
            member_assignment = UserRole(role=member_role, granted_by_user_id=None)
            user.role_assignments.append(member_assignment)
        
        db.session.add(user)
        db.session.commit()

        # Send verification email
        EmailService.send_verification_email(user.email, user.id)

        # Log registration
        AuditService.log_action(
            user_id=user.id,
            organization_id=user.organization_id,
            action='REGISTER',
            details={'method': 'email'},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return user.to_dict(), None