from flask import Blueprint, request, jsonify, g
from schemas.rbac_schemas.base_schema import set_permissions_for_serialization
from schemas.rbac_schemas.user_schemas import UserPrivate
from services.rbac_services.role_service import RoleService
from utils.rbac_utils.decorators import log_activity, permission_required, tenant_scoped
from utils.rbac_utils.exceptions import APIException

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/me', methods=['GET'])
@tenant_scoped
def get_current_user_profile():
    """
    Demonstrates column-level security.
    Users can always see their own profile, but the fields they see
    are determined by their permissions.
    """
    user = g.current_user
    
    # Load user's permissions into 'g' for the schema to use
    set_permissions_for_serialization()
    
    # The UserPrivate schema will automatically mask or hide the 'email' field
    # if the user lacks the 'user:read:email' permission.
    user_data = UserPrivate.model_validate(user).model_dump()
    
    return jsonify(user_data)

@admin_bp.route('/roles', methods=['POST'])
@tenant_scoped
@permission_required('role:create')
@log_activity('role_created')
def create_role():
    data = request.json
    name = data.get('name')
    if not name:
        raise APIException("Role name is required", 400)
    
    role = RoleService.create_role(name)
    return jsonify({"id": role.id, "name": role.name}), 201

@admin_bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@tenant_scoped
@permission_required('role:edit:permissions')
@log_activity('role_permission_assigned')
def add_permission_to_role(role_id):
    data = request.json
    permission_name = data.get('permission_name')
    if not permission_name:
        raise APIException("permission_name is required", 400)
        
    RoleService.assign_permission_to_role(role_id, permission_name)
    return jsonify({"message": "Permission added successfully"}), 200

@admin_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@tenant_scoped
@permission_required('user:edit:roles')
@log_activity('user_role_assigned')
def assign_role(user_id):
    data = request.json
    role_id = data.get('role_id')
    if not role_id:
        raise APIException("role_id is required", 400)
        
    RoleService.assign_role_to_user(user_id, role_id)
    return jsonify({"message": "Role assigned successfully"}), 200