from flask import Blueprint
from src.controllers.audit_controller import AuditController

audit_bp = Blueprint('audit', __name__)

audit_bp.add_url_rule('/logs', 'get_audit_logs', AuditController.get_audit_logs, methods=['GET'])
audit_bp.add_url_rule('/permissions', 'get_permission_changes', AuditController.get_permission_changes, methods=['GET'])
audit_bp.add_url_rule('/summary', 'get_audit_summary', AuditController.get_audit_summary, methods=['GET'])
