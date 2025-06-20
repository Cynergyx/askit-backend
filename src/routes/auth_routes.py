from flask import Blueprint
from src.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)

auth_bp.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
auth_bp.add_url_rule('/register', 'register', AuthController.register, methods=['POST'])
auth_bp.add_url_rule('/refresh', 'refresh', AuthController.refresh, methods=['POST'])
auth_bp.add_url_rule('/sso', 'sso_login', AuthController.sso_login, methods=['POST'])
auth_bp.add_url_rule('/logout', 'logout', AuthController.logout, methods=['POST'])
