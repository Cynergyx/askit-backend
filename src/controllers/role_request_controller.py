from flask import request, jsonify, g
from src.models.user import User
from src.models.role import Role
from src.models.role_request import RoleRequest
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from src.services.rbac_service import RBACService
from datetime import datetime, timezone
import uuid

class RoleRequestController:
    @staticmethod
    @jwt_required_with_org
    @require_permission('rolerequest.create')
    def request_role():
        data = request.get_json()
        if not data or 'role_id' not in data:
            return jsonify({'message': 'role_id is required'}), 400
        
        role_id_to_request = data['role_id']
        
        # Check if the role exists and belongs to the organization
        role = Role.query.filter_by(id=role_id_to_request, organization_id=g.current_organization.id).first()
        if not role:
            return jsonify({'message': 'Role not found within your organization'}), 404
        
        # Prevent requesting a role the user already has
        current_user_role_ids = {r.id for r in g.current_user.get_roles()}
        if role_id_to_request in current_user_role_ids:
            return jsonify({'message': f"You already have the '{role.name}' role."}), 409
        
        # Prevent duplicate pending requests
        pending_request = RoleRequest.query.filter_by(
            user_id=g.current_user.id,
            requested_role_id=role.id,
            status='PENDING'
        ).first()
        if pending_request:
            return jsonify({'message': 'You already have a pending request for this role'}), 409

        new_request = RoleRequest(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            requested_role_id=role.id,
            reason=data.get('reason')
        )
        db.session.add(new_request)
        db.session.commit()
        
        AuditService.log_action(g.current_user.id, g.current_organization.id, 'ROLE_REQUEST_CREATED', resource_id=new_request.id)
        return jsonify(new_request.to_dict()), 201

    @staticmethod
    @jwt_required_with_org
    @require_permission('rolerequest.read')
    def list_requests():
        status = request.args.get('status', 'PENDING')
        requests = RoleRequest.query.filter_by(organization_id=g.current_organization.id, status=status).all()
        return jsonify([req.to_dict() for req in requests]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('rolerequest.manage')
    def approve_request(request_id):
        req = RoleRequest.query.get(request_id)
        if not req or req.organization_id != g.current_organization.id or req.status != 'PENDING':
            return jsonify({'message': 'Request not found or not pending'}), 404

        success, message = RBACService.assign_role(
            user_id=req.user_id,
            role_id=req.requested_role_id,
            granted_by_user_id=g.current_user.id
        )
        if not success:
            return jsonify({'message': f'Failed to assign role: {message}'}), 400

        req.status = 'APPROVED'
        req.reviewed_by_id = g.current_user.id
        req.reviewed_at = datetime.now(timezone.utc)
        req.reviewer_notes = request.json.get('notes')
        db.session.commit()
        
        AuditService.log_action(g.current_user.id, g.current_organization.id, 'ROLE_REQUEST_APPROVED', resource_id=req.id)
        return jsonify({'message': 'Role request approved and role assigned.'}), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('rolerequest.manage')
    def deny_request(request_id):
        req = RoleRequest.query.get(request_id)
        if not req or req.organization_id != g.current_organization.id or req.status != 'PENDING':
            return jsonify({'message': 'Request not found or not pending'}), 404

        req.status = 'DENIED'
        req.reviewed_by_id = g.current_user.id
        req.reviewed_at = datetime.now(timezone.utc)
        req.reviewer_notes = request.json.get('notes', 'No reason provided.')
        db.session.commit()
        
        AuditService.log_action(g.current_user.id, g.current_organization.id, 'ROLE_REQUEST_DENIED', resource_id=req.id)
        return jsonify({'message': 'Role request denied.'}), 200