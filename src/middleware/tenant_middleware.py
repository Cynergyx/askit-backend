from functools import wraps
from flask import request, jsonify, g
from src.models.organization import Organization

def tenant_isolation(f):
    """Ensure tenant isolation for multi-organization support"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get organization from subdomain or header
        org_identifier = None
        
        # Try to get from subdomain
        host = request.headers.get('Host', '')
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and subdomain != 'api':
                org_identifier = subdomain
        
        # Try to get from header
        if not org_identifier:
            org_identifier = request.headers.get('X-Organization-Domain')
        
        # Try to get from current user's organization
        if not org_identifier and hasattr(g, 'current_organization') and g.current_organization:
            org_identifier = g.current_organization.domain
        
        if not org_identifier:
            return jsonify({'message': 'Organization not specified'}), 400
        
        # Find organization
        organization = Organization.query.filter(
            (Organization.domain == org_identifier) | 
            (Organization.subdomain == org_identifier)
        ).first()
        
        if not organization or not organization.is_active:
            return jsonify({'message': 'Invalid organization'}), 400
        
        # Store tenant context
        g.tenant_organization = organization
        
        # Ensure user belongs to this organization if authenticated
        if hasattr(g, 'current_user') and g.current_user:
            if g.current_user.organization_id != organization.id:
                return jsonify({'message': 'Access denied for this organization'}), 403
        
        return f(*args, **kwargs)
    
    return decorated