from flask import Blueprint
from src.controllers.user_controller import UserController

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/', 'get_users', UserController.get_users, methods=['GET'])
user_bp.add_url_rule('/', 'create_user', UserController.create_user, methods=['POST'])
user_bp.add_url_rule('/<user_id>', 'get_user', UserController.get_user, methods=['GET'])
user_bp.add_url_rule('/<user_id>', 'update_user', UserController.update_user, methods=['PUT'])
user_bp.add_url_rule('/<user_id>', 'delete_user', UserController.delete_user, methods=['DELETE'])
user_bp.add_url_rule('/<user_id>/roles', 'assign_role', UserController.assign_role, methods=['POST'])
user_bp.add_url_rule('/<user_id>/roles', 'revoke_role', UserController.revoke_role, methods=['DELETE'])
