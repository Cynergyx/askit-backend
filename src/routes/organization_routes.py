from flask import Blueprint
from src.controllers.organization_controller import OrganizationController

organization_bp = Blueprint('organizations', __name__)

organization_bp.add_url_rule('/onboard', 
                             'onboard', 
                             OrganizationController.onboard, 
                             methods=['POST'])

organization_bp.add_url_rule('/<org_id>', 
                             'delete_organization', 
                             OrganizationController.delete_organization, 
                             methods=['DELETE'])