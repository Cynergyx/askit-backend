from flask import Blueprint
from src.controllers.role_request_controller import RoleRequestController

role_request_bp = Blueprint('role_requests', __name__)

# User-facing endpoint
role_request_bp.add_url_rule('/requests', 'request_role', RoleRequestController.request_role, methods=['POST'])

# Admin-facing endpoints
role_request_bp.add_url_rule('/requests', 'list_requests', RoleRequestController.list_requests, methods=['GET'])
role_request_bp.add_url_rule('/requests/<request_id>/approve', 'approve_request', RoleRequestController.approve_request, methods=['POST'])
role_request_bp.add_url_rule('/requests/<request_id>/deny', 'deny_request', RoleRequestController.deny_request, methods=['POST'])