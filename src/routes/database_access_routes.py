from flask import Blueprint
from src.controllers.database_access_controller import DatabaseAccessController

db_access_bp = Blueprint('database_access', __name__)

# Note the URL structure: /api/users/<user_id>/database-access
db_access_bp.add_url_rule('/<user_id>/database-access', 
                          'get_access_list', 
                          DatabaseAccessController.get_access_list, 
                          methods=['GET'])

db_access_bp.add_url_rule('/<user_id>/database-access', 
                          'grant_access', 
                          DatabaseAccessController.grant_access, 
                          methods=['POST'])

db_access_bp.add_url_rule('/<user_id>/database-access/<access_id>', 
                          'revoke_access', 
                          DatabaseAccessController.revoke_access, 
                          methods=['DELETE'])