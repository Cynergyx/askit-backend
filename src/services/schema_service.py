from sqlalchemy import create_engine, inspect
from src.models.data_source import DataSource, SchemaMetadata
from src.utils.security import DataEncryption
from flask import current_app
from src.extensions import db

class SchemaService:

    @staticmethod
    def _get_connection_url(data_source):
        """Constructs a SQLAlchemy connection URL from a DataSource object."""
        key = current_app.config['ENCRYPTION_KEY']
        try:
            password = DataEncryption.decrypt_data(data_source.encrypted_password, key)
        except Exception:
            raise ConnectionError("Could not decrypt database password.")
        
        # Add more database dialect mappings as needed
        if data_source.type == 'postgresql':
            dialect = 'postgresql+psycopg2'
        elif data_source.type == 'mysql':
            dialect = 'mysql+pymysql'
        else:
            dialect = data_source.type

        return f"{dialect}://{data_source.username}:{password}@{data_source.host}:{data_source.port}/{data_source.database_name}"

    @staticmethod
    def extract_raw_schema(data_source_id: str):
        """Connects to an external database and introspects its schema."""
        data_source = DataSource.query.get(data_source_id)
        if not data_source:
            raise FileNotFoundError("Data source not found.")

        url = SchemaService._get_connection_url(data_source)
        engine = create_engine(url)
        
        try:
            inspector = inspect(engine)
            schema = {}
            for table_name in inspector.get_table_names():
                schema[table_name] = {
                    "columns": [
                        {
                            "name": col['name'],
                            "type": str(col['type']),
                            "nullable": col['nullable'],
                        } for col in inspector.get_columns(table_name)
                    ]
                }
            return schema
        except Exception as e:
            raise ConnectionError(f"Failed to connect to or inspect the external database: {e}")
        finally:
            engine.dispose()

    @staticmethod
    def update_schema_description(data_source_id: str, table_name: str, description: str, column_name: str = None):
        """Updates or creates a description for a table or column."""
        metadata = SchemaMetadata.query.filter_by(
            data_source_id=data_source_id,
            table_name=table_name,
            column_name=column_name
        ).first()

        if metadata:
            metadata.description = description
        else:
            metadata = SchemaMetadata(
                data_source_id=data_source_id,
                table_name=table_name,
                column_name=column_name,
                description=description
            )
            db.session.add(metadata)
        
        db.session.commit()
        return metadata

    @staticmethod
    def get_enriched_schema(data_source_id: str):
        """Combines the raw schema with stored metadata descriptions."""
        raw_schema = SchemaService.extract_raw_schema(data_source_id)
        
        metadata_records = SchemaMetadata.query.filter_by(data_source_id=data_source_id).all()
        
        # Create a lookup for efficient merging
        metadata_map = {}
        for record in metadata_records:
            key = f"{record.table_name}:{record.column_name or ''}"
            metadata_map[key] = record.description
            
        # Merge descriptions into the raw schema
        for table, details in raw_schema.items():
            table_key = f"{table}:"
            details['description'] = metadata_map.get(table_key, None)
            for col in details['columns']:
                col_key = f"{table}:{col['name']}"
                col['description'] = metadata_map.get(col_key, None)
                
        return raw_schema