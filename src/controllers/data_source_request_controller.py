from flask import request, jsonify, g
from src.models.data_source_request import DataSourceRequest
from src.models.user_database_access import UserDatabaseAccess
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from datetime import datetime

class DataSourceRequestController:
    @staticmethod
    @jwt_required_with_org
    @require_permission('datasource.read') 
    def request_access():
        data = request.get_json()
        data_source_id = data.get('data_source_id')
        if not data_source_id:
            return jsonify({'message': 'data_source_id is required'}), 400

        new_req = DataSourceRequest(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            requested_data_source_id=data_source_id,
            reason=data.get('reason')
        )
        db.session.add(new_req)
        db.session.commit()
        return jsonify({'message': 'Request submitted successfully.'}), 201

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign') # Admins can manage these
    def list_requests():
        status = request.args.get('status', 'PENDING')
        requests = DataSourceRequest.query.filter_by(
            organization_id=g.current_organization.id, 
            status=status
        ).all()
        return jsonify([req.to_dict() for req in requests]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('database.assign')
    def approve_request(request_id):
        req = DataSourceRequest.query.get(request_id)
        if not req or req.status != 'PENDING':
            return jsonify({'message': 'Request not found or not pending'}), 404
        
        # Grant the access
        new_grant = UserDatabaseAccess(
            user_id=req.user_id,
            data_source_id=req.requested_data_source_id,
            granted_by=g.current_user.id
        )
        db.session.add(new_grant)

        # Update the request
        req.status = 'APPROVED'
        req.reviewed_by_id = g.current_user.id
        req.reviewed_at = datetime.utcnow()
        db.session.commit()
        
        AuditService.log_action(g.current_user.id, g.current_organization.id, 'DATASOURCE_REQUEST_APPROVED', resource_id=req.id)
        return jsonify({'message': 'Access approved.'}), 200