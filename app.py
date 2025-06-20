from flask import Flask, jsonify, g
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from src.config import config
from src.db.rbac_db import db
from src.utils.rbac_utils.exceptions import APIException

# Import blueprints
from src.routes.rbac_routes.auth_routes import auth_bp
from src.routes.rbac_routes.admin_routes import admin_bp

# Import models to ensure they are registered with SQLAlchemy
from src.models import user, organization, role, permission, audit_log

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)

    # This function is called whenever a protected endpoint is accessed,
    # and will load the user object into Flask's `g` object
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        g.current_user = user.User.query.get(identity)
        if g.current_user:
            g.current_org_id = g.current_user.organization_id
        return g.current_user

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Register error handler
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app