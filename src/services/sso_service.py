from authlib.integrations.flask_client import OAuth
from flask import current_app, request
from src.models.user import User
from src.models.organization import Organization, OrganizationSSOConfig
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.extensions import db
import requests
import ldap
import uuid
from datetime import datetime

class SSOService:
    def __init__(self):
        self.oauth = OAuth()
    
    def setup_oauth_providers(self, app):
        """Setup OAuth providers based on organization configs"""
        # Google OAuth
        self.oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
        
        # Microsoft OAuth
        self.oauth.register(
            name='microsoft',
            client_id=app.config.get('MICROSOFT_CLIENT_ID'),
            client_secret=app.config.get('MICROSOFT_CLIENT_SECRET'),
            tenant=app.config.get('MICROSOFT_TENANT', 'common'),
            authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
            client_kwargs={'scope': 'openid email profile'}
        )
    
    @staticmethod
    def authenticate_oauth2(provider, code, organization_domain):
        """Authenticate user via OAuth2"""
        organization = Organization.query.filter_by(domain=organization_domain).first()
        if not organization:
            return None, "Organization not found"
        
        sso_config = OrganizationSSOConfig.query.filter_by(
            organization_id=organization.id,
            provider=provider,
            is_active=True
        ).first()
        
        if not sso_config:
            return None, "SSO not configured for this organization"
        
        try:
            # Exchange code for token
            token_data = SSOService._exchange_oauth_code(provider, code, sso_config.config)
            
            # Get user info from provider
            user_info = SSOService._get_oauth_user_info(provider, token_data['access_token'])
            
            # Find or create user
            user = SSOService._find_or_create_sso_user(
                email=user_info['email'],
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                provider=provider,
                provider_user_id=user_info['id'],
                organization_id=organization.id
            )
            
            # Create JWT tokens
            from flask_jwt_extended import create_access_token, create_refresh_token
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
                details={'method': f'sso_{provider}'}
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(include_sensitive=True)
            }, None
            
        except Exception as e:
            return None, f"SSO authentication failed: {str(e)}"
    
    @staticmethod
    def authenticate_saml(saml_response, organization_domain):
        """Authenticate user via SAML"""
        # SAML implementation would go here
        # This is a simplified placeholder
        pass
    
    @staticmethod
    def authenticate_ldap(username, password, organization_domain):
        """Authenticate user via LDAP"""
        organization = Organization.query.filter_by(domain=organization_domain).first()
        if not organization:
            return None, "Organization not found"
        
        sso_config = OrganizationSSOConfig.query.filter_by(
            organization_id=organization.id,
            provider='ldap',
            is_active=True
        ).first()
        
        if not sso_config:
            return None, "LDAP not configured for this organization"
        
        try:
            ldap_server = sso_config.config['server']
            base_dn = sso_config.config['base_dn']
            bind_dn = sso_config.config.get('bind_dn')
            bind_password = sso_config.config.get('bind_password')
            
            # Connect to LDAP
            conn = ldap.initialize(ldap_server)
            
            if bind_dn:
                conn.simple_bind_s(bind_dn, bind_password)
            
            # Search for user
            search_filter = f"(uid={username})"
            result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
            
            if not result:
                return None, "User not found in LDAP"
            
            user_dn, user_attrs = result[0]
            
            # Authenticate user
            try:
                test_conn = ldap.initialize(ldap_server)
                test_conn.simple_bind_s(user_dn, password)
                test_conn.unbind()
            except ldap.INVALID_CREDENTIALS:
                return None, "Invalid LDAP credentials"
            
            # Extract user information
            email = user_attrs.get('mail', [b''])[0].decode('utf-8')
            first_name = user_attrs.get('givenName', [b''])[0].decode('utf-8')
            last_name = user_attrs.get('sn', [b''])[0].decode('utf-8')
            
            # Find or create user
            user = SSOService._find_or_create_sso_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                provider='ldap',
                provider_user_id=username,
                organization_id=organization.id
            )
            
            # Create JWT tokens
            from flask_jwt_extended import create_access_token, create_refresh_token
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'organization_id': user.organization_id,
                    'roles': [role.name for role in user.get_roles()]
                }
            )
            refresh_token = create_refresh_token(identity=user.id)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(include_sensitive=True)
            }, None
            
        except Exception as e:
            return None, f"LDAP authentication failed: {str(e)}"
    
    @staticmethod
    def _exchange_oauth_code(provider, code, config):
        """Exchange OAuth authorization code for access token"""
        if provider == 'google':
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': config['redirect_uri']
            }
        elif provider == 'microsoft':
            token_url = f"https://login.microsoftonline.com/{config['tenant']}/oauth2/v2.0/token"
            data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': config['redirect_uri'],
                'scope': 'openid email profile'
            }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def _get_oauth_user_info(provider, access_token):
        """Get user information from OAuth provider"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        if provider == 'google':
            response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
        elif provider == 'microsoft':
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        
        response.raise_for_status()
        user_data = response.json()
        
        # Normalize user data format
        if provider == 'google':
            return {
                'id': user_data['id'],
                'email': user_data['email'],
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', '')
            }
        elif provider == 'microsoft':
            return {
                'id': user_data['id'],
                'email': user_data['mail'] or user_data['userPrincipalName'],
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', '')
            }
    
    @staticmethod
    def _find_or_create_sso_user(email, first_name, last_name, provider, provider_user_id, organization_id):
        """Find existing SSO user or create new one"""
        user = User.query.filter_by(
            email=email,
            organization_id=organization_id
        ).first()
        
        if user:
            # Update SSO info if needed
            if not user.is_sso_user:
                user.is_sso_user = True
                user.sso_provider = provider
                user.sso_user_id = provider_user_id
            user.last_login = datetime.utcnow()
            db.session.commit()
        else:
            # Create new SSO user
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=email.split('@')[0],
                first_name=first_name,
                last_name=last_name,
                organization_id=organization_id,
                is_sso_user=True,
                sso_provider=provider,
                sso_user_id=provider_user_id,
                last_login=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        return user