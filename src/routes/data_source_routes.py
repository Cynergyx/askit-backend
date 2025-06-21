from flask import Blueprint
from src.controllers.data_source_controller import DataSourceController

datasource_bp = Blueprint('datasources', __name__)

# Route for listing all available data sources in an org
datasource_bp.add_url_rule('/', 
                           'list_data_sources', 
                           DataSourceController.list_data_sources, 
                           methods=['GET'])

# Route for bulk uploading data sources
datasource_bp.add_url_rule('/bulk-upload', 
                           'bulk_upload', 
                           DataSourceController.bulk_upload, 
                           methods=['POST'])