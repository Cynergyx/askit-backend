from flask import Blueprint
from src.controllers.data_source_request_controller import DataSourceRequestController

ds_request_bp = Blueprint('data_source_requests', __name__)

ds_request_bp.add_url_rule('/', 'request_access', DataSourceRequestController.request_access, methods=['POST'])
ds_request_bp.add_url_rule('/', 'list_requests', DataSourceRequestController.list_requests, methods=['GET'])
ds_request_bp.add_url_rule('/<request_id>/approve', 'approve_request', DataSourceRequestController.approve_request, methods=['POST'])