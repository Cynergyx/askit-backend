from src.models.user import User, UserRole
from src.models.role import Role
from src.models.permission import Permission, DataAccessPolicy, DataMaskingPolicy
from src.services.audit_service import AuditService
from src.extensions import db
from sqlalchemy import and_, or_
from datetime import datetime

class RBACService:
    @staticmethod
    def check_permission(user_id, permission_name, resource_id=None, context=None):
        user = User.query.get(user_id)
        if not user:
            return False
        
        # This now gets permission objects, not just names
        user_permissions = user.get_permissions()
        
        # Check if any assigned permission matches the required name
        for p in user_permissions:
            if p.name == permission_name:
                # Basic permission check is successful.
                # Advanced: could add context/resource checks here
                return True
        
        return False
    
    @staticmethod
    def assign_role(user_id, role_id, granted_by_user_id, expires_at=None):
        user = User.query.get(user_id)
        role_to_assign = Role.query.get(role_id)
        granter = User.query.get(granted_by_user_id)
        
        if not all([user, role_to_assign, granter]):
            return False, "User, Role, or Granter not found."
            
        if role_to_assign.organization_id != user.organization_id:
             return False, "Cannot assign role from a different organization."

        # --- HIERARCHICAL PERMISSION CHECK ---
        # An admin cannot grant a role with permissions they do not have themselves.
        granter_permissions = {p.id for p in granter.get_permissions()}
        role_permissions = {p.id for p in role_to_assign.permissions}
        
        if not role_permissions.issubset(granter_permissions):
            return False, "Permission denied: You cannot assign a role with permissions you do not possess."
        # --- END OF CHECK ---

        existing_assignment = UserRole.query.filter_by(
            user_id=user_id, 
            role_id=role_id,
            is_active=True
        ).filter(or_(UserRole.expires_at == None, UserRole.expires_at > datetime.utcnow())).first()

        if existing_assignment:
            return False, "User already has this active role."

        new_assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
            granted_by_user_id=granted_by_user_id,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None
        )
        db.session.add(new_assignment)
        
        AuditService.log_permission_change(
            user_id=granted_by_user_id,
            organization_id=user.organization_id,
            target_user_id=user_id,
            target_role_id=role_id,
            action='GRANT',
            permission_after={'role': role_to_assign.name, 'expires_at': expires_at}
        )
        db.session.commit()
        
        return True, "Role assigned successfully."

    @staticmethod
    def revoke_role(user_id, role_id, revoked_by_user_id):
        # Find the active role assignment
        assignment = UserRole.query.filter_by(
            user_id=user_id, 
            role_id=role_id, 
            is_active=True
        ).first()
        
        if not assignment:
            return False, "User does not have this role or it is already inactive."

        # Check if revoker has permission
        if not RBACService.check_permission(revoked_by_user_id, 'role.revoke'):
            return False, "Insufficient permissions to revoke roles."
        
        assignment.is_active = False
        db.session.commit()
        
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        # Log permission change
        AuditService.log_permission_change(
            user_id=revoked_by_user_id,
            organization_id=user.organization_id,
            target_user_id=user_id,
            target_role_id=role_id,
            action='REVOKE',
            permission_before={'role': role.name}
        )
        
        return True, "Role revoked successfully."