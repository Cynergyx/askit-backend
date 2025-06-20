from flask import g

from db.rbac_db import db
from models.rbac_models.permission import Permission
from models.rbac_models.role import Role
from models.rbac_models.user import User
from utils.rbac_utils.exceptions import APIException, NotFoundError

class RoleService:
    @staticmethod
    def create_role(name: str):
        """Creates a new role within the current user's organization."""
        org_id = g.current_org_id
        if Role.query.filter_by(name=name, organization_id=org_id).first():
            raise APIException(f"Role '{name}' already exists in this organization.", 409)
        
        role = Role(name=name, organization_id=org_id)
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def assign_permission_to_role(role_id: int, permission_name: str):
        """Assigns a permission to a role, ensuring both are in the same tenant."""
        org_id = g.current_org_id
        role = Role.query.filter_by(id=role_id, organization_id=org_id).first()
        if not role:
            raise NotFoundError("Role not found in this organization.")
        
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            # For simplicity, we can create permissions on the fly if they don't exist
            permission = Permission(name=permission_name)
            db.session.add(permission)
        
        role.permissions.append(permission)
        db.session.commit()
        return role

    @staticmethod
    def assign_role_to_user(user_id: int, role_id: int):
        """Assigns a role to a user, ensuring both are in the same tenant."""
        org_id = g.current_org_id
        user = User.query.filter_by(id=user_id, organization_id=org_id).first()
        role = Role.query.filter_by(id=role_id, organization_id=org_id).first()
        
        if not user or not role:
            raise NotFoundError("User or Role not found in this organization.")
        
        user.roles.append(role)
        db.session.commit()
        return user