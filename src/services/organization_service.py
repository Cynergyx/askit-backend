from flask import g
from src.extensions import db
from src.models.organization import Organization
from src.models.user import User, UserRole
from src.models.role import Role
import uuid

class OrganizationService:
    @staticmethod
    def onboard_organization(payload: dict):
        if not payload.get('organization') or not payload.get('users'):
            return None, "Payload must include 'organization' and 'users' keys."
        if not isinstance(payload['users'], list) or len(payload['users']) == 0:
            return None, "'users' must be a non-empty list."
        if not any(user.get('is_admin') for user in payload['users']):
            return None, "At least one user must be designated as an admin with 'is_admin: true'."
        org_data = payload['organization']
        if not org_data.get('name') or not org_data.get('domain'):
            return None, "Organization data must include 'name' and 'domain'."

        # The Super Admin performing this action is the granter.
        granter_id = g.current_user.id

        try:
            # Using with db.session.begin() is a modern and safe way to handle transactions.
            with db.session.begin():
                if Organization.query.filter_by(domain=org_data['domain']).first():
                    raise ValueError(f"Organization with domain '{org_data['domain']}' already exists.")
                
                user_emails = [user['email'] for user in payload['users']]
                if User.query.filter(User.email.in_(user_emails)).first():
                    raise ValueError("One or more user emails already exist in the system.")

                new_org = Organization(id=str(uuid.uuid4()), name=org_data['name'], domain=org_data['domain'])
                db.session.add(new_org)
                
                admin_template = Role.query.filter_by(name='Organization Admin', is_system_role=True).first()
                member_template = Role.query.filter_by(name='Member', is_system_role=True).first()
                if not admin_template or not member_template:
                    raise Exception("System roles 'Organization Admin' or 'Member' not found. Run `flask seed`.")

                # Flush to get new_org.id before cloning roles
                db.session.flush()

                org_admin_role = admin_template.clone(new_org.id)
                member_role = member_template.clone(new_org.id)
                db.session.add_all([org_admin_role, member_role])
                
                role_lookup = {'Organization Admin': org_admin_role, 'Member': member_role}

                for role_data in payload.get('roles', []):
                    new_role = Role(id=str(uuid.uuid4()), organization_id=new_org.id, name=role_data['name'], display_name=role_data.get('display_name'), description=role_data.get('description'))
                    db.session.add(new_role)
                    role_lookup[new_role.name] = new_role

                created_users = []
                for user_data in payload['users']:
                    new_user = User(
                        id=str(uuid.uuid4()),
                        organization_id=new_org.id,
                        email=user_data['email'],
                        username=user_data.get('username', user_data['email'].split('@')[0] + str(uuid.uuid4())[:4]),
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_verified=True
                    )
                    new_user.set_password(user_data['password'])
                    
                    member_assignment = UserRole(role=member_role, granted_by_user_id=granter_id)
                    new_user.role_assignments.append(member_assignment)
                    
                    if user_data.get('is_admin'):
                        admin_assignment = UserRole(role=org_admin_role, granted_by_user_id=granter_id)
                        new_user.role_assignments.append(admin_assignment)
                    
                    for role_name in user_data.get('roles', []):
                        if role_name in role_lookup:
                            assigned_roles = [a.role for a in new_user.role_assignments]
                            if role_lookup[role_name] not in assigned_roles:
                                custom_assignment = UserRole(role=role_lookup[role_name], granted_by_user_id=granter_id)
                                new_user.role_assignments.append(custom_assignment)
                    
                    db.session.add(new_user)
                    created_users.append(new_user)

            final_users = [user.to_dict(include_details=True) for user in created_users]
            return {'organization': new_org.to_dict(), 'users': final_users}, None

        except (ValueError, Exception) as e:
            # The 'with' block handles the rollback on error
            import logging
            logging.exception("Onboarding failed")
            return None, f"An unexpected error occurred during onboarding: {str(e)}"