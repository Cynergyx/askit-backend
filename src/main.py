from flask import Flask, jsonify
from .extensions import db, jwt, migrate, cors, redis_client

def create_app(config_object_name='config.DevelopmentConfig'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_object_name)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Configure CORS
    
    # Initialize redis_client, ensuring it can handle missing REDIS_URL for testing
    if app.config.get('REDIS_URL'):
        redis_client.init_app(app)

    # Register blueprints
    from src.routes.auth_routes import auth_bp
    from src.routes.user_routes import user_bp
    from src.routes.role_routes import role_bp
    from src.routes.audit_routes import audit_bp
    from src.routes.database_access_routes import db_access_bp
    from src.routes.data_source_routes import datasource_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(role_bp, url_prefix='/api/roles')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(db_access_bp, url_prefix='/api/users')
    app.register_blueprint(datasource_bp, url_prefix='/api/datasources')


    # Register JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Invalid token'}), 401
    
    # Register a simple health check route
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200

    # Generic error handler
    @app.errorhandler(500)
    def internal_error(error):
        # In a real app, you would log the error
        db.session.rollback()
        return jsonify({"message": "An internal server error occurred."}), 500

    return app