from functools import wraps
from flask import g
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.utils.rbac_utils.exceptions import ForbiddenError, UnauthorizedError
from src.services.rbac_services.audit_service import AuditService

def tenant_scoped(f):
    """
    Ensures a valid JWT is present and the user belongs to an organization.
    Loads the user and their organization_id into the Flask `g` object.
    This is the primary decorator for almost all authenticated endpoints.
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # The @jwt.user_lookup_loader in app.py has already loaded the user into g.current_user
        if not g.get('current_user'):
            raise UnauthorizedError("User not found.")
        if not g.get('current_org_id'):
             raise ForbiddenError("User is not associated with an organization.")
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission: str):
    """
    Checks if the current user has the required permission.
    Must be used *after* @tenant_scoped.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = g.get('current_user')
            if not current_user:
                raise UnauthorizedError("Authentication required.")
            
            user_permissions = current_user.get_permissions()
            if permission not in user_permissions:
                raise ForbiddenError(f"Permission '{permission}' required.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_activity(action: str):
    """
    Decorator to log user activity to the audit trail.
    It captures the action and key details.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            # Then log the activity
            try:
                user_id = g.current_user.id
                org_id = g.current_org_id
                
                # Create a serializable representation of the result
                details = {"result": str(result), "args": str(args), "kwargs": str(kwargs)}

                AuditService.log(
                    user_id=user_id,
                    organization_id=org_id,
                    action=action,
                    details=details
                )
            except Exception as e:
                # Don't let logging failures break the request
                print(f"Failed to log activity: {e}")

            return result
        return decorated_function
    return decorator