from flask import request, jsonify, g
from src.services.organization_service import OrganizationService
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService

class OrganizationController:
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('organization.create')
    def onboard():
        """Handles the API request to onboard a new organization."""
        payload = request.get_json()
        
        result, error = OrganizationService.onboard_organization(payload)
        
        if error:
            return jsonify({'message': error}), 400
            
        # Log this high-privilege action
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id, # The org of the admin performing the action
            action='ORGANIZATION_ONBOARD',
            resource_type='organization',
            resource_id=result['organization']['id'],
            details={'onboarded_domain': result['organization']['domain']}
        )
        
        return jsonify(result), 201