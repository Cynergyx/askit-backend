from flask import request, jsonify, g
from src.models.role import Role, RolePermission
from src.models.permission import Permission
from src.services.audit_service import AuditService
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.extensions import db
from datetime import datetime, timezone
import uuid

class RoleController:
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.read')
    def get_roles():
        """Get all roles in organization, with optional search by name."""
        search_name = request.args.get('name')
        
        query = Role.query.filter_by(
            organization_id=g.current_organization.id,
            is_active=True
        )
        
        if search_name:
            query = query.filter(Role.name.ilike(f'%{search_name}%'))

        roles = query.all()
        
        return jsonify({
            'roles': [role.to_dict(include_permissions=True) for role in roles]
        }), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.read')
    def get_role(role_id):
        """Get specific role"""
        role = Role.query.filter_by(
            id=role_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not role:
            return jsonify({'message': 'Role not found'}), 404
        
        return jsonify({'role': role.to_dict(include_permissions=True)}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.create')
    def create_role():
        """Create new role"""
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'message': 'Role name is required'}), 400
        
        # Check if role already exists
        existing_role = Role.query.filter_by(
            name=data['name'],
            organization_id=g.current_organization.id
        ).first()
        
        if existing_role:
            return jsonify({'message': 'Role already exists'}), 400
        
        role = Role(
            id=str(uuid.uuid4()),
            name=data['name'],
            display_name=data.get('display_name'),
            description=data.get('description'),
            organization_id=g.current_organization.id,
            parent_role_id=data.get('parent_role_id'),
            level=data.get('level', 0)
        )
        
        db.session.add(role)
        db.session.commit()
        
        # Assign permissions if provided
        if 'permissions' in data:
            for permission_id in data['permissions']:
                role_permission = RolePermission(
                    id=str(uuid.uuid4()),
                    role_id=role.id,
                    permission_id=permission_id,
                    granted_by=g.current_user.id
                )
                db.session.add(role_permission)
            
            db.session.commit()
        
        # Log role creation
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='ROLE_CREATED',
            resource_type='role',
            resource_id=role.id,
            details={'role_name': role.name}
        )
        
        return jsonify({'role': role.to_dict(include_permissions=True)}), 201
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.update')
    def update_role(role_id):
        """Update role"""
        role = Role.query.filter_by(
            id=role_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not role:
            return jsonify({'message': 'Role not found'}), 404
        
        if role.is_system_role:
            return jsonify({'message': 'Cannot modify system role'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Update role fields
        updatable_fields = ['display_name', 'description', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(role, field, data[field])
        
        role.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log role update
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='ROLE_UPDATED',
            resource_type='role',
            resource_id=role.id,
            details={'role_name': role.name}
        )
        
        return jsonify({'role': role.to_dict(include_permissions=True)}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.delete')
    def delete_role(role_id):
        """Delete role"""
        role = Role.query.filter_by(
            id=role_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not role:
            return jsonify({'message': 'Role not found'}), 404
        
        if role.is_system_role:
            return jsonify({'message': 'Cannot delete system role'}), 400
        
        # Check if role is assigned to users
        from src.models.user import UserRole
        active_assignments = UserRole.query.filter_by(
            role_id=role_id,
            is_active=True
        ).count()
        
        if active_assignments > 0:
            return jsonify({'message': 'Cannot delete role with active user assignments'}), 400
        
        role.is_active = False
        role.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log role deletion
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='ROLE_DELETED',
            resource_type='role',
            resource_id=role.id,
            details={'role_name': role.name}
        )
        
        return jsonify({'message': 'Role deleted successfully'}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('permission.read')
    def get_permissions():
        """Get all available permissions"""
        permissions = Permission.query.all()
        
        return jsonify({
            'permissions': [perm.to_dict() for perm in permissions]
        }), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('permission.assign')
    def assign_permission(role_id):
        """Assign permission to role"""
        data = request.get_json()
        
        if not data or 'permission_id' not in data:
            return jsonify({'message': 'Permission ID is required'}), 400
        
        role = Role.query.filter_by(
            id=role_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not role:
            return jsonify({'message': 'Role not found'}), 404
        
        permission = Permission.query.get(data['permission_id'])
        if not permission:
            return jsonify({'message': 'Permission not found'}), 404
        
        # Check if already assigned
        existing = RolePermission.query.filter_by(
            role_id=role_id,
            permission_id=data['permission_id'],
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'message': 'Permission already assigned to role'}), 400
        
        role_permission = RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_id,
            permission_id=data['permission_id'],
            granted_by=g.current_user.id
        )
        
        db.session.add(role_permission)
        db.session.commit()
        
        # Log permission assignment
        AuditService.log_permission_change(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            target_role_id=role_id,
            action='GRANT',
            permission_after={'permission': permission.name, 'role': role.name}
        )
        
        return jsonify({'message': 'Permission assigned successfully'}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('permission.revoke')
    def revoke_permission(role_id):
        """Revoke permission from role"""
        data = request.get_json()
        
        if not data or 'permission_id' not in data:
            return jsonify({'message': 'Permission ID is required'}), 400
        
        role_permission = RolePermission.query.filter_by(
            role_id=role_id,
            permission_id=data['permission_id'],
            is_active=True
        ).first()
        
        if not role_permission:
            return jsonify({'message': 'Permission assignment not found'}), 404
        
        role_permission.is_active = False
        db.session.commit()
        
        # Log permission revocation
        role = Role.query.get(role_id)
        permission = Permission.query.get(data['permission_id'])
        
        AuditService.log_permission_change(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            target_role_id=role_id,
            action='REVOKE',
            permission_before={'permission': permission.name, 'role': role.name}
        )
        
        return jsonify({'message': 'Permission revoked successfully'}), 200