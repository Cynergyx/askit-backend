from src.extensions import db
from src.models.organization import Organization
from src.models.user import User
from src.models.role import Role
import uuid

class OrganizationService:
    @staticmethod
    def onboard_organization(payload: dict):
        """
        Onboards a new organization, its roles, and its initial admin users
        in a single database transaction.
        """
        # --- 1. Validation ---
        if not payload.get('organization') or not payload.get('users'):
            return None, "Payload must include 'organization' and 'users' keys."
        
        if not isinstance(payload['users'], list) or len(payload['users']) == 0:
            return None, "'users' must be a non-empty list."
        
        if not any(user.get('is_admin') for user in payload['users']):
            return None, "At least one user must be designated as an admin with 'is_admin: true'."
            
        org_data = payload['organization']
        if not org_data.get('name') or not org_data.get('domain'):
            return None, "Organization data must include 'name' and 'domain'."

        # --- 2. Begin Transaction ---
        try:
            with db.session.begin_nested():
                # Check for existing organization or user emails
                if Organization.query.filter_by(domain=org_data['domain']).first():
                    return None, f"Organization with domain '{org_data['domain']}' already exists."
                
                user_emails = [user['email'] for user in payload['users']]
                if User.query.filter(User.email.in_(user_emails)).first():
                    return None, "One or more user emails already exist in the system."

                # --- 3. Create Organization ---
                new_org = Organization(
                    id=str(uuid.uuid4()),
                    name=org_data['name'],
                    domain=org_data['domain']
                )
                db.session.add(new_org)
                
                # --- 4. Clone System Roles for the New Organization ---
                # Find the system template roles (e.g., from the first org or marked as system)
                admin_template = Role.query.filter_by(name='Organization Admin', is_system_role=True).first()
                member_template = Role.query.filter_by(name='Member', is_system_role=True).first()
                if not admin_template or not member_template:
                    raise Exception("System roles 'Organization Admin' or 'Member' not found. Run `flask seed`.")

                # Clone them
                org_admin_role = admin_template.clone(new_org.id)
                member_role = member_template.clone(new_org.id)
                db.session.add_all([org_admin_role, member_role])
                
                role_lookup = {
                    'Organization Admin': org_admin_role,
                    'Member': member_role
                }

                # --- 5. Create Custom Roles ---
                for role_data in payload.get('roles', []):
                    new_role = Role(
                        id=str(uuid.uuid4()),
                        organization_id=new_org.id,
                        name=role_data['name'],
                        display_name=role_data.get('display_name'),
                        description=role_data.get('description')
                    )
                    db.session.add(new_role)
                    role_lookup[new_role.name] = new_role

                # --- 6. Create Users and Assign Roles ---
                created_users = []
                for user_data in payload['users']:
                    new_user = User(
                        id=str(uuid.uuid4()),
                        organization_id=new_org.id,
                        email=user_data['email'],
                        username=user_data.get('username', user_data['email'].split('@')[0]),
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_verified=True # Users created by an admin are pre-verified
                    )
                    new_user.set_password(user_data['password'])
                    
                    # Assign default Member role
                    new_user.roles.append(member_role)
                    
                    # Assign Organization Admin role if specified
                    if user_data.get('is_admin'):
                        new_user.roles.append(org_admin_role)

                    # Assign other custom roles
                    for role_name in user_data.get('roles', []):
                        if role_name in role_lookup and role_lookup[role_name] not in new_user.roles:
                            new_user.roles.append(role_lookup[role_name])
                    
                    db.session.add(new_user)
                    created_users.append(new_user.to_dict())

            # --- 7. Commit Transaction ---
            db.session.commit()
            
            return {
                'organization': new_org.to_dict(),
                'users': created_users
            }, None

        except Exception as e:
            db.session.rollback()
            return None, f"An unexpected error occurred during onboarding: {str(e)}"