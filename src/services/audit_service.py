from src.models.audit import AuditLog, PermissionChangeLog
from src.app import db
from flask import request
from datetime import datetime
import uuid

class AuditService:
    @staticmethod
    def log_action(user_id, organization_id, action, resource_type=None, resource_id=None, details=None):
        """Log user action for audit trail"""
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=AuditService._get_client_ip(),
            user_agent=request.headers.get('User-Agent', '') if request else '',
            session_id=request.headers.get('X-Session-ID', '') if request else ''
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        return audit_log
    
    @staticmethod
    def log_permission_change(user_id, organization_id, target_user_id=None, target_role_id=None, 
                            action='MODIFY', permission_before=None, permission_after=None, reason=None):
        """Log permission changes for compliance"""
        change_log = PermissionChangeLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            target_user_id=target_user_id,
            target_role_id=target_role_id,
            action=action,
            permission_before=permission_before or {},
            permission_after=permission_after or {},
            reason=reason
        )
        
        db.session.add(change_log)
        db.session.commit()
        
        return change_log
    
    @staticmethod
    def get_audit_logs(organization_id, user_id=None, action=None, start_date=None, end_date=None, limit=100):
        """Retrieve audit logs with filters"""
        query = AuditLog.query.filter_by(organization_id=organization_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if action:
            query = query.filter_by(action=action)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_permission_change_logs(organization_id, target_user_id=None, limit=100):
        """Retrieve permission change logs"""
        query = PermissionChangeLog.query.filter_by(organization_id=organization_id)
        
        if target_user_id:
            query = query.filter_by(target_user_id=target_user_id)
        
        return query.order_by(PermissionChangeLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def _get_client_ip():
        """Get client IP address from request"""
        if not request:
            return None
        
        # Check for forwarded IP (behind proxy)
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr