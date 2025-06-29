from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from src.models.user import User
from src.models.organization import Organization

def jwt_required_with_org(f):
    """JWT required with organization validation"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # try:
            verify_jwt_in_request()
            
            # Get user and organization info from JWT
            claims = get_jwt()
            user_id = get_jwt_identity()
            org_id = claims.get('organization_id')
            
            # Validate user exists and is active
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'message': 'Invalid user'}), 401
            
            # Validate organization
            organization = Organization.query.get(org_id)
            if not organization or not organization.is_active:
                return jsonify({'message': 'Invalid organization'}), 401
            
            # Store in g for use in views
            g.current_user = user
            g.current_organization = organization
            g.user_roles = claims.get('roles', [])
            
            return f(*args, **kwargs)
            
        # except Exception as e:
        #     return jsonify({'message': 'Authentication failed'}), 401
    
    return decorated

def optional_jwt_with_org(f):
    """Optional JWT with organization validation"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            
            current_user_id = get_jwt_identity()
            if current_user_id:
                claims = get_jwt()
                user = User.query.get(current_user_id)
                org_id = claims.get('organization_id')
                organization = Organization.query.get(org_id)
                
                g.current_user = user
                g.current_organization = organization
                g.user_roles = claims.get('roles', [])
            else:
                g.current_user = None
                g.current_organization = None
                g.user_roles = []
            
            return f(*args, **kwargs)
            
        except Exception:
            g.current_user = None
            g.current_organization = None
            g.user_roles = []
            return f(*args, **kwargs)
    
    return decorated