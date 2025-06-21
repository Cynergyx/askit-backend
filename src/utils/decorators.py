from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.services.audit_service import AuditService
from src.services.rbac_service import RBACService
from src.utils.security import RateLimiting
from src.extensions import redis_client
import time
import logging

logger = logging.getLogger(__name__)

def audit_action(action, resource_type=None):
    """Decorator to automatically log actions for audit trail"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            start_time = time.time()
            
            # Get user info
            user_id = None
            organization_id = None
            if hasattr(g, 'current_user') and g.current_user:
                user_id = g.current_user.id
                organization_id = g.current_user.organization_id
            
            # Get resource ID from kwargs
            resource_id = kwargs.get('id') or kwargs.get('user_id') or kwargs.get('role_id')
            
            try:
                # Execute the function
                result = f(*args, **kwargs)
                
                # Log successful action
                if user_id and organization_id:
                    execution_time = time.time() - start_time
                    AuditService.log_action(
                        user_id=user_id,
                        organization_id=organization_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        details={
                            'execution_time': execution_time,
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'status': 'success'
                        }
                    )
                
                return result
                
            except Exception as e:
                # Log failed action
                if user_id and organization_id:
                    execution_time = time.time() - start_time
                    AuditService.log_action(
                        user_id=user_id,
                        organization_id=organization_id,
                        action=f"{action}_FAILED",
                        resource_type=resource_type,
                        resource_id=resource_id,
                        details={
                            'execution_time': execution_time,
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'status': 'error',
                            'error': str(e)
                        }
                    )
                raise
        
        return decorated
    return decorator

def rate_limit(max_requests=100, window_seconds=3600, per_user=True):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Create rate limit key
            if per_user and hasattr(g, 'current_user') and g.current_user:
                key = f"rate_limit:{g.current_user.id}:{request.endpoint}"
            else:
                key = f"rate_limit:{request.remote_addr}:{request.endpoint}"
            
            # Check current count
            current_count = redis_client.get(key)
            if current_count and int(current_count) >= max_requests:
                return jsonify({
                    'message': 'Rate limit exceeded',
                    'retry_after': redis_client.ttl(key)
                }), 429
            
            # Increment counter
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            pipe.execute()
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def validate_json_schema(schema):
    """Validate request JSON against schema"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({'message': 'Request must be JSON'}), 400
            
            try:
                data = request.get_json()
                # Simple validation - in production use jsonschema library
                for field, requirements in schema.items():
                    if requirements.get('required', False) and field not in data:
                        return jsonify({'message': f'Missing required field: {field}'}), 400
                    
                    if field in data:
                        field_type = requirements.get('type')
                        if field_type and not isinstance(data[field], field_type):
                            return jsonify({'message': f'Invalid type for field: {field}'}), 400
                
                g.validated_data = data
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'message': 'Invalid JSON data'}), 400
        
        return decorated
    return decorator

def cache_response(timeout=300, key_prefix='cache'):
    """Cache response decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}:{request.endpoint}:{hash(str(sorted(request.args.items())))}"
            
            # Add user context to cache key if available
            if hasattr(g, 'current_user') and g.current_user:
                cache_key += f":{g.current_user.id}"
            
            # Try to get from cache
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return jsonify(eval(cached_response))
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                response_data, status_code = result
                if status_code == 200:
                    redis_client.setex(cache_key, timeout, str(response_data))
            
            return result
        
        return decorated
    return decorator

def require_organization_admin(f):
    """Require organization admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'message': 'Authentication required'}), 401
        
        user_roles = [role.name for role in g.current_user.get_roles()]
        if 'organization_admin' not in user_roles and 'super_admin' not in user_roles:
            return jsonify({'message': 'Organization admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated