from functools import wraps
from flask import jsonify, g
from src.services.rbac_service import RBACService

def require_permission(permission_name, resource_id_param=None):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({'message': 'Authentication required'}), 401
            
            # Get resource ID from kwargs if specified
            resource_id = kwargs.get(resource_id_param) if resource_id_param else None
            
            # Check permission
            if not RBACService.check_permission(g.current_user.id, permission_name, resource_id):
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_role(role_name):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'user_roles') or role_name not in g.user_roles:
                return jsonify({'message': 'Insufficient role privileges'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def require_any_role(*role_names):
    """Decorator to require any of the specified roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'user_roles') or not any(role in g.user_roles for role in role_names):
                return jsonify({'message': 'Insufficient role privileges'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator