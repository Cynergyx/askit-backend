from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from src.app import db
from flask import current_app
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database utility class for common operations"""
    
    @staticmethod
    def init_db():
        """Initialize database with tables"""
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    @staticmethod
    def drop_db():
        """Drop all database tables"""
        try:
            db.drop_all()
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise
    
    @staticmethod
    @contextmanager
    def transaction():
        """Database transaction context manager"""
        try:
            db.session.begin()
            yield db.session
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise
        finally:
            db.session.close()
    
    @staticmethod
    def safe_execute(query, params=None):
        """Safely execute raw SQL query"""
        try:
            if params:
                result = db.session.execute(text(query), params)
            else:
                result = db.session.execute(text(query))
            db.session.commit()
            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    @staticmethod
    def get_table_info(table_name):
        """Get table information including columns and constraints"""
        try:
            query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            result = db.session.execute(text(query), {'table_name': table_name})
            return result.fetchall()
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            return []
    
    @staticmethod
    def backup_table(table_name, backup_suffix='_backup'):
        """Create a backup of a table"""
        backup_table_name = f"{table_name}{backup_suffix}"
        try:
            query = f"CREATE TABLE {backup_table_name} AS SELECT * FROM {table_name}"
            db.session.execute(text(query))
            db.session.commit()
            logger.info(f"Table {table_name} backed up to {backup_table_name}")
            return backup_table_name
        except Exception as e:
            logger.error(f"Failed to backup table {table_name}: {str(e)}")
            raise
    
    @staticmethod
    def get_db_stats():
        """Get database statistics"""
        try:
            stats = {}
            
            # Get table sizes
            query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                avg_width
            FROM pg_stats 
            WHERE schemaname = 'public'
            """
            result = db.session.execute(text(query))
            stats['table_stats'] = result.fetchall()
            
            # Get connection info
            query = "SELECT count(*) as active_connections FROM pg_stat_activity"
            result = db.session.execute(text(query))
            stats['connections'] = result.fetchone()[0]
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            return {}

class QueryBuilder:
    """Dynamic query builder for complex queries"""
    
    def __init__(self, model):
        self.model = model
        self.query = model.query
        self.filters = []
        self.joins = []
        self.order_by_clauses = []
    
    def filter_by(self, **kwargs):
        """Add filter conditions"""
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                self.filters.append(getattr(self.model, field) == value)
        return self
    
    def filter_in(self, field, values):
        """Add IN filter"""
        if hasattr(self.model, field):
            self.filters.append(getattr(self.model, field).in_(values))
        return self
    
    def filter_like(self, field, pattern):
        """Add LIKE filter"""
        if hasattr(self.model, field):
            self.filters.append(getattr(self.model, field).like(f"%{pattern}%"))
        return self
    
    def filter_date_range(self, field, start_date, end_date):
        """Add date range filter"""
        if hasattr(self.model, field):
            field_attr = getattr(self.model, field)
            if start_date:
                self.filters.append(field_attr >= start_date)
            if end_date:
                self.filters.append(field_attr <= end_date)
        return self
    
    def join_with(self, relationship):
        """Add join"""
        self.joins.append(relationship)
        return self
    
    def order_by(self, field, desc=False):
        """Add order by clause"""
        if hasattr(self.model, field):
            field_attr = getattr(self.model, field)
            if desc:
                self.order_by_clauses.append(field_attr.desc())
            else:
                self.order_by_clauses.append(field_attr.asc())
        return self
    
    def build(self):
        """Build and return the query"""
        query = self.query
        
        # Apply joins
        for join in self.joins:
            query = query.join(join)
        
        # Apply filters
        for filter_condition in self.filters:
            query = query.filter(filter_condition)
        
        # Apply ordering
        for order_clause in self.order_by_clauses:
            query = query.order_by(order_clause)
        
        return query
    
    def paginate(self, page=1, per_page=20):
        """Add pagination to query"""
        query = self.build()
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def count(self):
        """Get count of results"""
        query = self.build()
        return query.count()
    
    def first(self):
        """Get first result"""
        query = self.build()
        return query.first()
    
    def all(self):
        """Get all results"""
        query = self.build()
        return query.all()

class DatabaseHealth:
    """Database health monitoring utilities"""
    
    @staticmethod
    def check_connection():
        """Check if database connection is healthy"""
        try:
            db.session.execute(text('SELECT 1'))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    @staticmethod
    def check_tables():
        """Check if all required tables exist"""
        required_tables = [
            'users', 'roles', 'permissions', 'organizations',
            'user_roles', 'role_permissions', 'audit_logs'
        ]
        
        try:
            existing_tables = db.engine.table_names()
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            return {
                'status': len(missing_tables) == 0,
                'missing_tables': missing_tables,
                'existing_tables': existing_tables
            }
        except Exception as e:
            logger.error(f"Table check failed: {str(e)}")
            return {'status': False, 'error': str(e)}
    
    @staticmethod
    def get_performance_metrics():
        """Get database performance metrics"""
        try:
            metrics = {}
            
            # Query performance
            query = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements 
            ORDER BY total_time DESC 
            LIMIT 10
            """
            result = db.session.execute(text(query))
            metrics['slow_queries'] = result.fetchall()
            
            # Lock information
            query = """
            SELECT 
                count(*) as lock_count,
                mode
            FROM pg_locks 
            GROUP BY mode
            """
            result = db.session.execute(text(query))
            metrics['locks'] = result.fetchall()
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}

def init_database_utils():
    """Initialize database utility functions"""
    logger.info("Database utilities initialized")
