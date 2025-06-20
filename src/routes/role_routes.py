from flask import Blueprint
from src.controllers.role_controller import RoleController

role_bp = Blueprint('roles', __name__)

role_bp.add_url_rule('/', 'get_roles', RoleController.get_roles, methods=['GET'])
role_bp.add_url_rule('/', 'create_role', RoleController.create_role, methods=['POST'])
role_bp.add_url_rule('/<role_id>', 'get_role', RoleController.get_role, methods=['GET'])
role_bp.add_url_rule('/<role_id>', 'update_role', RoleController.update_role, methods=['PUT'])
role_bp.add_url_rule('/<role_id>', 'delete_role', RoleController.delete_role, methods=['DELETE'])
role_bp.add_url_rule('/permissions', 'get_permissions', RoleController.get_permissions, methods=['GET'])
role_bp.add_url_rule('/<role_id>/permissions', 'assign_permission', RoleController.assign_permission, methods=['POST'])
role_bp.add_url_rule('/<role_id>/permissions', 'revoke_permission', RoleController.revoke_permission, methods=['DELETE'])
