from flask import request, jsonify, g, current_app
from src.models.organization import Organization
from src.models.data_source import DataSource
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from src.services.schema_service import SchemaService
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
            if not all(k in item for k in ['name', 'type', 'password', 'host', 'port', 'database_name', 'username']):
                errors.append(f"Item {i}: Missing one or more required fields.")
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

    @staticmethod
    @jwt_required_with_org
    @require_permission('datasource.read')
    def get_enriched_schema(data_source_id):
        """Gets the introspected schema and user-provided metadata for a data source."""
        try:
            # Verify the data source belongs to the user's organization
            ds = DataSource.query.filter_by(id=data_source_id, organization_id=g.current_organization.id).first()
            if not ds:
                return jsonify({'message': 'Data source not found or access denied'}), 404

            enriched_schema = SchemaService.get_enriched_schema(data_source_id)
            return jsonify(enriched_schema), 200
        except FileNotFoundError as e:
            return jsonify({'message': str(e)}), 404
        except ConnectionError as e:
            return jsonify({'message': str(e)}), 502 # Bad Gateway - indicates upstream issue
        except Exception as e:
            return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500
            
    @staticmethod
    @jwt_required_with_org
    @require_permission('datasource.update') # A new permission might be better
    def update_schema_description(data_source_id):
        """Updates the description for a specific table or column."""
        data = request.get_json()
        if not data or not data.get('table_name') or 'description' not in data:
            return jsonify({'message': 'table_name and description are required'}), 400

        # Verify the data source belongs to the user's organization
        ds = DataSource.query.filter_by(id=data_source_id, organization_id=g.current_organization.id).first()
        if not ds:
            return jsonify({'message': 'Data source not found or access denied'}), 404

        try:
            metadata = SchemaService.update_schema_description(
                data_source_id=data_source_id,
                table_name=data.get('table_name'),
                column_name=data.get('column_name'), # This can be null for table descriptions
                description=data.get('description')
            )
            
            AuditService.log_action(
                user_id=g.current_user.id,
                organization_id=g.current_organization.id,
                action='SCHEMA_DESCRIPTION_UPDATED',
                resource_type='schema_metadata',
                resource_id=metadata.id,
                details={'table': data.get('table_name'), 'column': data.get('column_name')}
            )
            return jsonify(metadata.to_dict()), 200
        except Exception as e:
            return jsonify({'message': f'Failed to update description: {e}'}), 500