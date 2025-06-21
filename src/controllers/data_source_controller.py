from flask import request, jsonify, g, current_app
from src.models.organization import Organization
from src.models.data_source import DataSource
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from src.utils.security import DataEncryption
import uuid

class DataSourceController:

    @staticmethod
    @jwt_required_with_org
    @require_permission('datasource.read')
    def list_data_sources():
        """List all available data sources for the current organization."""
        data_sources = DataSource.query.filter_by(organization_id=g.current_organization.id).all()
        return jsonify([ds.to_dict() for ds in data_sources]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('datasource.create')
    def bulk_upload():
        """Bulk upload and onboard new data sources for the organization."""
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({'message': 'Request body must be a list of data source objects'}), 400

        key = current_app.config['ENCRYPTION_KEY']
        if not key:
            return jsonify({'message': 'Server encryption is not configured'}), 500

        new_sources = []
        errors = []
        for i, item in enumerate(data):
            # Basic validation
            if not item.get('name') or not item.get('type') or not item.get('password'):
                errors.append(f"Item {i}: 'name', 'type', and 'password' are required fields.")
                continue

            encrypted_pass = DataEncryption.encrypt_data(item['password'], key)
            
            source = DataSource(
                id=str(uuid.uuid4()),
                organization_id=g.current_organization.id,
                name=item['name'],
                type=item['type'],
                host=item.get('host'),
                port=item.get('port'),
                database_name=item.get('database_name'),
                username=item.get('username'),
                encrypted_password=encrypted_pass,
                extra_params=item.get('extra_params')
            )
            new_sources.append(source)

        if errors:
            return jsonify({'message': 'Validation failed', 'errors': errors}), 400

        if not new_sources:
            return jsonify({'message': 'No valid data sources to add'}), 400

        db.session.add_all(new_sources)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='DATASOURCE_BULK_UPLOAD',
            details={'count': len(new_sources)}
        )
        
        return jsonify({
            'message': f'Successfully onboarded {len(new_sources)} data sources.',
            'onboarded_ids': [s.id for s in new_sources]
        }), 201