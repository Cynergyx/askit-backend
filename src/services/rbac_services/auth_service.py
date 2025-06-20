from flask_jwt_extended import create_access_token
from db.rbac_db import db
from models.rbac_models.organization import Organization
from models.rbac_models.user import User
from utils.rbac_utils.exceptions import APIException, UnauthorizedError

class AuthService:
    @staticmethod
    def register_user(username, email, password, org_name):
        """Registers a new user and a new organization."""
        if Organization.query.filter_by(name=org_name).first():
            raise APIException("Organization name already exists.", 409)
        if User.query.filter_by(email=email).first():
            raise APIException("Email already in use.", 409)

        # In a real app, this should be a two-step process or transactional
        new_org = Organization(name=org_name)
        db.session.add(new_org)
        db.session.flush() # Flush to get the new_org.id

        new_user = User(
            username=username,
            email=email,
            organization_id=new_org.id
        )
        new_user.set_password(password)
        db.session.add(new_user)
        
        # Here you would typically also create default roles for the new org
        # e.g., 'Admin', 'Member'
        
        db.session.commit()
        return new_user

    @staticmethod
    def authenticate_user(email, password):
        """Authenticates a user and returns a JWT."""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return access_token
        raise UnauthorizedError("Invalid email or password.")