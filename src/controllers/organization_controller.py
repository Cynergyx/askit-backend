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
    

    @staticmethod
    @jwt_required_with_org
    @require_permission('organization.delete') # Assumes a new 'organization.delete' permission for Super Admins
    def delete_organization(org_id):
        """Handles the API request to deactivate an organization."""
        
        # Note: The 'require_permission' decorator will ensure only authorized users proceed.
        # It's good practice to also ensure this is a Super Admin role specifically if needed.
        if 'Super Admin' not in g.user_roles:
             return jsonify({'message': 'This action requires Super Admin privileges.'}), 403

        org, deactivated_users_count = OrganizationService.deactivate_organization(org_id)

        if not org:
            return jsonify({'message': deactivated_users_count}), 404

        # Log this critical action
        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id, # The Super Admin's org
            action='ORGANIZATION_DEACTIVATED',
            resource_type='organization',
            resource_id=org.id,
            details={'deactivated_domain': org.domain, 'users_affected': deactivated_users_count}
        )

        return jsonify({
            'message': f"Organization '{org.name}' and its {deactivated_users_count} users have been deactivated."
        }), 200