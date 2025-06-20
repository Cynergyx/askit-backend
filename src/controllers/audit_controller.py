from flask import request, jsonify, g
from src.services.audit_service import AuditService
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from datetime import datetime, timedelta

class AuditController:
    @staticmethod
    @jwt_required_with_org
    @require_permission('audit.read')
    def get_audit_logs():
        """Get audit logs with filters"""
        # Get query parameters
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'message': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'message': 'Invalid end_date format'}), 400
        
        # Get audit logs
        logs = AuditService.get_audit_logs(
            organization_id=g.current_organization.id,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            'audit_logs': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('audit.read')
    def get_permission_changes():
        """Get permission change logs"""
        target_user_id = request.args.get('target_user_id')
        limit = request.args.get('limit', 100, type=int)
        
        logs = AuditService.get_permission_change_logs(
            organization_id=g.current_organization.id,
            target_user_id=target_user_id,
            limit=limit
        )
        
        return jsonify({
            'permission_changes': [log.to_dict() for log in logs],
            'count': len(logs)
        }), 200
    
    @staticmethod
    @jwt_required_with_org
    @require_permission('audit.read')
    def get_audit_summary():
        """Get audit summary/statistics"""
        # Get summary for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        logs = AuditService.get_audit_logs(
            organization_id=g.current_organization.id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Get more for summary
        )
        
        # Generate summary statistics
        action_counts = {}
        user_activity = {}
        daily_activity = {}
        
        for log in logs:
            # Count actions
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            
            # Count user activity
            if log.user_id:
                user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1
            
            # Count daily activity
            day = log.timestamp.date().isoformat()
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        return jsonify({
            'summary': {
                'total_events': len(logs),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'action_counts': action_counts,
                'top_users': sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10],
                'daily_activity': daily_activity
            }
        }), 200