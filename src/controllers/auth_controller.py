from flask import request, jsonify, g
from src.services.auth_service import AuthService
from src.services.sso_service import SSOService
from src.services.audit_service import AuditService
from src.middleware.auth_middleware import jwt_required_with_org
from flask_jwt_extended import jwt_required
from src.utils.decorators import audit_action

class AuthController:
    @staticmethod
    @audit_action('LOGIN')
    def login():
        # ... (no changes to method logic)
        # Omitted for brevity, logic remains the same
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'password', 'organization')):
            return jsonify({'message': 'Email, password, and organization are required'}), 400
        
        result, error = AuthService.authenticate_user(
            email=data['email'],
            password=data['password'],
            organization_domain=data['organization']
        )
        
        if error:
            return jsonify({'message': error}), 401
        
        return jsonify(result), 200

    @staticmethod
    @audit_action('REGISTER')
    def register():
        # ... (no changes to method logic)
        # Omitted for brevity, logic remains the same
        data = request.get_json()
        
        required_fields = ['email', 'password', 'first_name', 'last_name', 'organization']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'message': 'All fields are required'}), 400
        
        result, error = AuthService.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            organization_domain=data['organization']
        )
        
        if error:
            return jsonify({'message': error}), 400
        
        return jsonify({'user': result}), 201

    @staticmethod
    @jwt_required()
    def refresh():
        # ... (no changes to method logic)
        # Omitted for brevity, logic remains the same
        result, error = AuthService.refresh_token()
        
        if error:
            return jsonify({'message': error}), 401
        
        return jsonify(result), 200

    @staticmethod
    def sso_login():
        # ... (no changes to method logic)
        # Omitted for brevity, logic remains the same
        data = request.get_json()
        
        if not data or 'provider' not in data or 'organization' not in data:
            return jsonify({'message': 'Provider and organization are required'}), 400
        
        provider = data['provider']
        organization = data['organization']
        
        if provider in ['google', 'microsoft', 'oauth2']:
            if 'code' not in data:
                return jsonify({'message': 'Authorization code is required'}), 400
            
            result, error = SSOService.authenticate_oauth2(
                provider=provider,
                code=data['code'],
                organization_domain=organization
            )
        
        elif provider == 'ldap':
            if not all(k in data for k in ('username', 'password')):
                return jsonify({'message': 'Username and password are required for LDAP'}), 400
            
            result, error = SSOService.authenticate_ldap(
                username=data['username'],
                password=data['password'],
                organization_domain=organization
            )
        
        elif provider == 'saml':
            if 'saml_response' not in data:
                return jsonify({'message': 'SAML response is required'}), 400
            
            result, error = SSOService.authenticate_saml(
                saml_response=data['saml_response'],
                organization_domain=organization
            )
        
        else:
            return jsonify({'message': 'Unsupported SSO provider'}), 400
        
        if error:
            return jsonify({'message': error}), 401
        
        return jsonify(result), 200

    @staticmethod
    @jwt_required_with_org
    def logout():
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='LOGOUT',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify({'message': 'Logged out successfully'}), 200