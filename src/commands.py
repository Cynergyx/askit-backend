import click
from flask.cli import with_appcontext
from src.extensions import db
from src.models.organization import Organization
from src.models.user import User, UserRole
from src.models.role import Role, RolePermission
from src.models.permission import Permission
import os
import uuid

@click.command(name='seed')
@with_appcontext
def seed():
    """Seeds the database with initial data in an idempotent way."""
    
    # --- Step 1: Ensure Super Admin Organization Exists ---
    org_domain = os.getenv('SUPER_ADMIN_ORG_DOMAIN', 'superorg')
    super_org = Organization.query.filter_by(domain=org_domain).first()
    if not super_org:
        super_org = Organization(
            name=org_domain.title(),
            domain=org_domain,
            is_active=True
        )
        db.session.add(super_org)
        db.session.commit()
        click.echo(f'Created super organization: {super_org.name}')
    else:
        click.echo(f'Super organization "{super_org.name}" already exists.')

    # --- Step 2: Ensure All Permissions Exist ---
    permissions_data = [
        # User Permissions
        {'name': 'user.create', 'resource': 'user', 'action': 'create'},
        {'name': 'user.read', 'resource': 'user', 'action': 'read'},
        {'name': 'user.update', 'resource': 'user', 'action': 'update'},
        {'name': 'user.delete', 'resource': 'user', 'action': 'delete'},
        # Role Permissions
        {'name': 'role.create', 'resource': 'role', 'action': 'create'},
        {'name': 'role.read', 'resource': 'role', 'action': 'read'},
        {'name': 'role.update', 'resource': 'role', 'action': 'update'},
        {'name': 'role.delete', 'resource': 'role', 'action': 'delete'},
        {'name': 'role.assign', 'resource': 'role', 'action': 'assign'},
        # Permission Permissions
        {'name': 'permission.read', 'resource': 'permission', 'action': 'read'},
        {'name': 'permission.assign', 'resource': 'permission', 'action': 'assign'},
        # Audit Permissions
        {'name': 'audit.read', 'resource': 'audit', 'action': 'read'},
        # Datasource Permissions
        {'name': 'datasource.create', 'resource': 'datasource', 'action': 'create'},
        {'name': 'datasource.read', 'resource': 'datasource', 'action': 'read'},
        # Database Access Permissions
        {'name': 'database.assign', 'resource': 'database', 'action': 'assign'},
        {'name': 'database.read', 'resource': 'database', 'action': 'read'},
        # Role Request Permissions
        {'name': 'rolerequest.create', 'resource': 'rolerequest', 'action': 'create'},
        {'name': 'rolerequest.read', 'resource': 'rolerequest', 'action': 'read'},
        {'name': 'rolerequest.manage', 'resource': 'rolerequest', 'action': 'manage'},
        # Organization Permissions
        {'name': 'organization.create', 'resource': 'organization', 'action': 'create'},
    ]
    all_permissions = {}
    for p_data in permissions_data:
        perm = Permission.query.filter_by(name=p_data['name']).first()
        if not perm:
            perm = Permission(**p_data)
            db.session.add(perm)
        all_permissions[perm.name] = perm
    db.session.commit()
    click.echo('Ensured all system permissions exist.')

    # --- Step 3: Ensure System Roles Exist and Have Correct Permissions ---
    roles_to_ensure = {
        'Super Admin': {
            'display_name': 'Super Administrator',
            'permissions': list(all_permissions.values()) # All permissions
        },
        'Organization Admin': {
            'display_name': 'Organization Administrator',
            'permissions': [p for p in all_permissions.values() if 'organization.create' not in p.name] # All except org creation
        },
        'Member': {
            'display_name': 'Member',
            'permissions': [all_permissions['rolerequest.create']]
        }
    }

    system_roles = {}
    for role_name, role_info in roles_to_ensure.items():
        role = Role.query.filter_by(name=role_name, organization_id=super_org.id).first()
        if not role:
            role = Role(
                name=role_name,
                display_name=role_info['display_name'],
                is_system_role=True,
                organization_id=super_org.id
            )
            db.session.add(role)
        
        # Ensure permissions are set correctly
        current_perms = set(role.permissions)
        required_perms = set(role_info['permissions'])
        
        # Add missing permissions
        for perm in required_perms - current_perms:
            role.permissions.append(perm)
        
        # Remove extra permissions (optional, but good for consistency)
        for perm in current_perms - required_perms:
            role.permissions.remove(perm)
            
        system_roles[role_name] = role
    
    db.session.commit()
    click.echo('Ensured system roles and their permissions are correct.')

    # --- Step 4: Ensure Super Admin User Exists and Has Role ---
    admin_email = os.getenv('SUPER_ADMIN_EMAIL')
    admin_password = os.getenv('SUPER_ADMIN_PASSWORD')
    if not admin_email or not admin_password:
        click.echo('ERROR: SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD must be set in .env')
        return

    super_admin_user = User.query.filter_by(email=admin_email).first()
    if not super_admin_user:
        super_admin_user = User(
            email=admin_email,
            username=admin_email.split('@')[0],
            first_name='Super',
            last_name='Admin',
            organization_id=super_org.id,
            is_verified=True
        )
        super_admin_user.set_password(admin_password)
        db.session.add(super_admin_user)
        db.session.commit()
        click.echo(f'Created super admin user: {super_admin_user.email}')
    else:
        click.echo(f'Super admin user "{super_admin_user.email}" already exists.')

    # --- Step 5: Assign Super Admin Role Correctly ---
    super_admin_role = system_roles['Super Admin']
    
    # Check if the user already has the role
    user_role_link = UserRole.query.filter_by(
        user_id=super_admin_user.id,
        role_id=super_admin_role.id
    ).first()

    if not user_role_link:
        # Create the UserRole association object to link the user and the role
        new_assignment = UserRole(
            user_id=super_admin_user.id,
            role_id=super_admin_role.id,
            granted_by=super_admin_user.id # Admin grants role to themselves
        )
        db.session.add(new_assignment)
        db.session.commit()
        click.echo(f'Assigned "Super Admin" role to {super_admin_user.email}.')
    else:
        click.echo(f'User {super_admin_user.email} already has the "Super Admin" role.')

    click.echo('Database seeding complete.')