from flask import request, jsonify, g
from src.models.user import User
from src.models.user_database_access import UserDatabaseAccess
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
import uuid

class DatabaseAccessController:

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.read')
    def get_access_list(user_id):
        """Get the list of database accesses for a specific user."""
        target_user = User.query.filter_by(id=user_id, organization_id=g.current_organization.id).first()
        if not target_user:
            return jsonify({'message': 'User not found'}), 404
        
        access_records = target_user.database_accesses.all()
        return jsonify([record.to_dict() for record in access_records]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign')
    def grant_access(user_id):
        """Grant a new database view access to a user."""
        data = request.get_json()
        required_fields = ['database_name', 'view_name']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'message': 'database_name and view_name are required'}), 400

        target_user = User.query.filter_by(id=user_id, organization_id=g.current_organization.id).first()
        if not target_user:
            return jsonify({'message': 'User not found'}), 404
            
        # Check for duplicates
        existing = UserDatabaseAccess.query.filter_by(
            user_id=user_id,
            database_name=data['database_name'],
            view_name=data['view_name']
        ).first()
        if existing:
            return jsonify({'message': 'This database access has already been granted to the user'}), 409

        new_access = UserDatabaseAccess(
            id=str(uuid.uuid4()),
            user_id=target_user.id,
            organization_id=g.current_organization.id,
            database_name=data['database_name'],
            view_name=data['view_name'],
            description=data.get('description'),
            connection_details=data.get('connection_details'),
            granted_by=g.current_user.id
        )

        db.session.add(new_access)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='DB_ACCESS_GRANTED',
            resource_type='user_database_access',
            resource_id=new_access.id,
            details={
                'target_user_id': target_user.id,
                'database': data['database_name'],
                'view': data['view_name']
            }
        )

        return jsonify(new_access.to_dict()), 201

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign') # Using 'assign' for revoke as well, could be 'database.revoke'
    def revoke_access(user_id, access_id):
        """Revoke a specific database access from a user."""
        access_record = UserDatabaseAccess.query.filter_by(
            id=access_id,
            user_id=user_id,
            organization_id=g.current_organization.id
        ).first()

        if not access_record:
            return jsonify({'message': 'Database access record not found for this user'}), 404

        details = {
            'target_user_id': user_id,
            'database': access_record.database_name,
            'view': access_record.view_name
        }

        db.session.delete(access_record)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='DB_ACCESS_REVOKED',
            resource_type='user_database_access',
            resource_id=access_id,
            details=details
        )
        
        return jsonify({'message': 'Database access revoked successfully'}), 200