from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from schemas.rbac_schemas.user_schemas import UserCreate
from services.rbac_services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = UserCreate(**request.json)
        org_name = request.json.get('organization_name')
        if not org_name:
            return jsonify({"message": "Organization name is required"}), 400
            
        AuthService.register_user(data.username, data.email, data.password, org_name)
        return jsonify({"message": "User and organization created successfully"}), 201
    except ValidationError as e:
        return jsonify(e.errors()), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        token = AuthService.authenticate_user(email, password)
        return jsonify(access_token=token)
    except Exception as e:
        return jsonify({"message": str(e)}), 401
    
    