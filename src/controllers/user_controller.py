from flask import request, jsonify, g
from src.models.user import User, UserRole
from src.models.role import Role
from src.services.rbac_service import RBACService
from src.services.audit_service import AuditService
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.extensions import db
from datetime import datetime, timezone
from sqlalchemy import or_
import uuid

class UserController:
    @staticmethod
    @jwt_required_with_org
    @require_permission('user.read')
    def get_users():
        """Get all users in organization"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query.filter_by(organization_id=g.current_organization.id)
        
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('user.read')
    def get_user(user_id):
        """Get specific user"""
        user = User.query.filter_by(
            id=user_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('user.create')
    def create_user():
        """Create new user"""
        data = request.get_json()
        
        required_fields = ['email', 'first_name', 'last_name']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'message': 'Email, first_name, and last_name are required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 400
        
        user = User(
            id=str(uuid.uuid4()),
            email=data['email'],
            username=data.get('username', data['email'].split('@')[0]),
            first_name=data['first_name'],
            last_name=data['last_name'],
            organization_id=g.current_organization.id,
            is_sso_user=data.get('is_sso_user', False)
        )
        
        if not data.get('is_sso_user') and 'password' in data:
            user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log user creation
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='USER_CREATED',
            resource_type='user',
            resource_id=user.id,
            details={'created_user_email': user.email}
        )
        
        return jsonify({'user': user.to_dict()}), 201
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('user.update')
    def update_user(user_id):
        """Update user"""
        user = User.query.filter_by(
            id=user_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Store original data for audit
        original_data = user.to_dict()
        
        # Update allowed fields
        updatable_fields = ['first_name', 'last_name', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log user update
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='USER_UPDATED',
            resource_type='user',
            resource_id=user.id,
            details={
                'original': original_data,
                'updated': user.to_dict()
            }
        )
        
        return jsonify({'user': user.to_dict()}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('user.delete')
    def delete_user(user_id):
        """Delete user (soft delete)"""
        user = User.query.filter_by(
            id=user_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.id == g.current_user.id:
            return jsonify({'message': 'Cannot delete yourself'}), 400
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Log user deletion
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='USER_DELETED',
            resource_type='user',
            resource_id=user.id,
            details={'deleted_user_email': user.email}
        )
        
        return jsonify({'message': 'User deleted successfully'}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.assign')
    def assign_role(user_id):
        """Assign role to user"""
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({'message': 'Role ID is required'}), 400
        
        success, message = RBACService.assign_role(
            user_id=user_id,
            role_id=data['role_id'],
            granted_by_user_id=g.current_user.id,
            expires_at=data.get('expires_at')
        )
        
        if not success:
            return jsonify({'message': message}), 400
        
        return jsonify({'message': message}), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('role.revoke')
    def revoke_role(user_id):
        """Revoke role from user"""
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({'message': 'Role ID is required'}), 400
        
        success, message = RBACService.revoke_role(
            user_id=user_id,
            role_id=data['role_id'],
            revoked_by_user_id=g.current_user.id
        )
        
        if not success:
            return jsonify({'message': message}), 400
        
        return jsonify({'message': message}), 200
    

    @staticmethod
    @jwt_required_with_org
    @require_permission('user.update')
    def verify_user(user_id):
        """Verify a user registration."""
        user = User.query.filter_by(
            id=user_id,
            organization_id=g.current_organization.id
        ).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.is_verified:
            return jsonify({'message': 'User is already verified'}), 400
            
        user.is_verified = True
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='USER_VERIFIED',
            resource_type='user',
            resource_id=user.id,
            details={'verified_user_email': user.email}
        )
        
        return jsonify({'message': 'User verified successfully'}), 200