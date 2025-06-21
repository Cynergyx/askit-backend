from src.models.user import User, UserRole
from src.models.role import Role, RolePermission
from src.models.permission import Permission, DataAccessPolicy, DataMaskingPolicy
from src.services.audit_service import AuditService
from src.extensions import db
from sqlalchemy import and_, or_
import json

class RBACService:
    @staticmethod
    def check_permission(user_id, permission_name, resource_id=None, context=None):
        """Check if user has specific permission"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        user_permissions = user.get_permissions()
        permission = next((p for p in user_permissions if p.name == permission_name), None)
        
        if not permission:
            return False
        
        # Check row-level security conditions
        if permission.conditions and context:
            return RBACService._evaluate_conditions(permission.conditions, context)
        
        return True
    
    @staticmethod
    def _evaluate_conditions(conditions, context):
        """Evaluate row-level security conditions"""
        try:
            # Simple condition evaluation - in production, use a proper expression evaluator
            for condition in conditions:
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if field not in context:
                    return False
                
                context_value = context[field]
                
                if operator == 'eq' and context_value != value:
                    return False
                elif operator == 'ne' and context_value == value:
                    return False
                elif operator == 'in' and context_value not in value:
                    return False
                elif operator == 'contains' and value not in context_value:
                    return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def assign_role(user_id, role_id, granted_by_user_id, expires_at=None):
        """Assign role to user"""
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        granter = User.query.get(granted_by_user_id)
        
        if not all([user, role, granter]):
            return False, "User, role, or granter not found"
        
        # Check if granter has permission to assign this role
        if not RBACService.check_permission(granted_by_user_id, 'role.assign'):
            return False, "Insufficient permissions to assign role"
        
        # Check if user already has this role
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id, is_active=True).first()
        if existing:
            return False, "User already has this role"
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by_user_id,
            expires_at=expires_at
        )
        
        db.session.add(user_role)
        db.session.commit()
        
        # Log permission change
        AuditService.log_permission_change(
            user_id=granted_by_user_id,
            organization_id=user.organization_id,
            target_user_id=user_id,
            target_role_id=role_id,
            action='GRANT',
            permission_after={'role': role.name}
        )
        
        return True, "Role assigned successfully"
    
    @staticmethod
    def revoke_role(user_id, role_id, revoked_by_user_id):
        """Revoke role from user"""
        user_role = UserRole.query.filter_by(
            user_id=user_id, 
            role_id=role_id, 
            is_active=True
        ).first()
        
        if not user_role:
            return False, "User role assignment not found"
        
        # Check if revoker has permission
        if not RBACService.check_permission(revoked_by_user_id, 'role.revoke'):
            return False, "Insufficient permissions to revoke role"
        
        user_role.is_active = False
        db.session.commit()
        
        # Log permission change
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        AuditService.log_permission_change(
            user_id=revoked_by_user_id,
            organization_id=user.organization_id,
            target_user_id=user_id,
            target_role_id=role_id,
            action='REVOKE',
            permission_before={'role': role.name}
        )
        
        return True, "Role revoked successfully"
    
    @staticmethod
    def get_user_accessible_data(user_id, table_name, base_query=None):
        """Apply row-level security to data queries"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Get applicable data access policies
        policies = DataAccessPolicy.query.filter(
            and_(
                DataAccessPolicy.organization_id == user.organization_id,
                DataAccessPolicy.table_name == table_name,
                DataAccessPolicy.access_type == 'READ',
                DataAccessPolicy.is_active == True
            )
        ).all()
        
        # Apply policies to query (simplified example)
        filtered_query = base_query
        for policy in policies:
            if policy.conditions:
                # Apply conditions to query
                for condition in policy.conditions:
                    field = condition.get('field')
                    operator = condition.get('operator')
                    value = condition.get('value')
                    
                    if operator == 'eq':
                        filtered_query = filtered_query.filter(getattr(base_query.column_descriptions[0]['type'], field) == value)
                    # Add more operators as needed
        
        return filtered_query
    
    @staticmethod
    def apply_data_masking(user_id, data, table_name):
        """Apply data masking policies to query results"""
        user = User.query.get(user_id)
        if not user:
            return data
        
        # Get masking policies for this table
        policies = DataMaskingPolicy.query.filter(
            and_(
                DataMaskingPolicy.organization_id == user.organization_id,
                DataMaskingPolicy.table_name == table_name,
                DataMaskingPolicy.is_active == True
            )
        ).all()
        
        if not policies:
            return data
        
        # Apply masking to data
        from src.services.data_masking_service import DataMaskingService
        return DataMaskingService.mask_data(data, policies)