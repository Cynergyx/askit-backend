from models.rbac_models.audit_log import AuditLog
from src.db import db

class AuditService:
    @staticmethod
    def log(user_id: int, organization_id: int, action: str, details: dict = None):
        """Creates an audit log entry."""
        log_entry = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()