from flask import Blueprint
from src.controllers.data_source_controller import DataSourceController

datasource_bp = Blueprint('datasources', __name__)

datasource_bp.add_url_rule('/', 'list_data_sources', DataSourceController.list_data_sources, methods=['GET'])
datasource_bp.add_url_rule('/bulk-upload', 'bulk_upload', DataSourceController.bulk_upload, methods=['POST'])

datasource_bp.add_url_rule('/<data_source_id>/schema', 'get_enriched_schema', DataSourceController.get_enriched_schema, methods=['GET'])
datasource_bp.add_url_rule('/<data_source_id>/schema/description', 'update_schema_description', DataSourceController.update_schema_description, methods=['POST'])