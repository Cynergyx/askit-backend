from flask import request, jsonify, g
from src.models.user import User
from src.models.data_source import DataSource
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
        
        # This will now trigger the to_dict() method in UserDatabaseAccess, which decrypts the password
        access_records = target_user.database_accesses.all()
        return jsonify([record.to_dict() for record in access_records]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign')
    def grant_access(user_id):
        """Grant a user access to a pre-registered data source."""
        data = request.get_json()
        if not data or 'data_source_id' not in data:
            return jsonify({'message': 'data_source_id is required'}), 400

        target_user = User.query.filter_by(id=user_id, organization_id=g.current_organization.id).first()
        if not target_user:
            return jsonify({'message': 'Target user not found'}), 404

        data_source = DataSource.query.filter_by(
            id=data['data_source_id'], 
            organization_id=g.current_organization.id
        ).first()
        if not data_source:
            return jsonify({'message': 'Data source not found or does not belong to this organization'}), 404
            
        # Check if this grant already exists
        existing = UserDatabaseAccess.query.filter_by(
            user_id=user_id,
            data_source_id=data['data_source_id']
        ).first()
        if existing:
            return jsonify({'message': 'This database access has already been granted to the user'}), 409

        new_grant = UserDatabaseAccess(
            id=str(uuid.uuid4()),
            user_id=target_user.id,
            data_source_id=data_source.id,
            granted_by=g.current_user.id
        )

        db.session.add(new_grant)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='DB_ACCESS_GRANTED',
            resource_type='user_database_access',
            resource_id=new_grant.id,
            details={
                'target_user_id': target_user.id,
                'data_source_id': data_source.id,
                'data_source_name': data_source.name
            }
        )

        return jsonify(new_grant.to_dict()), 201

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign')
    def revoke_access(user_id, grant_id):
        """Revoke a specific database access grant from a user."""
        access_grant = UserDatabaseAccess.query.filter_by(
            id=grant_id,
            user_id=user_id
        ).join(DataSource).filter(DataSource.organization_id == g.current_organization.id).first()


        if not access_grant:
            return jsonify({'message': 'Database access grant not found for this user'}), 404

        details = {
            'target_user_id': user_id,
            'data_source_id': access_grant.data_source_id,
            'data_source_name': access_grant.data_source.name,
        }

        db.session.delete(access_grant)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='DB_ACCESS_REVOKED',
            resource_type='user_database_access',
            resource_id=grant_id,
            details=details
        )
        
        return jsonify({'message': 'Database access revoked successfully'}), 200