import click
from flask.cli import with_appcontext
from .extensions import db
from .models.organization import Organization
from .models.user import User
from .models.role import Role
from .models.permission import Permission
import os
import uuid

@click.command(name='seed')
@with_appcontext
def seed():
    """Seeds the database with initial data."""
    if Role.query.first():
        click.echo('Database already seeded.')
        return

    click.echo('Seeding database...')

    # --- Create Permissions ---
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
    permissions = [Permission(**p) for p in permissions_data]
    db.session.bulk_save_objects(permissions)
    db.session.commit()
    click.echo(f'Created {len(permissions)} permissions.')

    # --- Create Roles ---
    super_admin_role = Role(name='Super Admin', display_name='Super Administrator', is_system_role=True)
    org_admin_role = Role(name='Organization Admin', display_name='Organization Administrator', is_system_role=True)
    member_role = Role(name='Member', display_name='Member', is_system_role=True)
    
    db.session.add_all([super_admin_role, org_admin_role, member_role])
    db.session.commit()
    click.echo('Created base roles.')

    # --- Assign Permissions to Roles ---
    # Super Admin gets all permissions
    for perm in permissions:
        super_admin_role.permissions.append(perm)

    # Org Admin gets most permissions (except super-admin level ones)
    admin_perms = [p for p in permissions if 'super' not in p.name]
    for perm in admin_perms:
        org_admin_role.permissions.append(perm)

    # Member gets basic read and self-service permissions
    member_perms_names = ['rolerequest.create']
    member_perms = Permission.query.filter(Permission.name.in_(member_perms_names)).all()
    for perm in member_perms:
        member_role.permissions.append(perm)

    # --- Create Super Admin Organization and User ---
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

    # Set roles to belong to the super organization
    super_admin_role.organization_id = super_org.id
    org_admin_role.organization_id = super_org.id
    member_role.organization_id = super_org.id
    
    admin_email = os.getenv('SUPER_ADMIN_EMAIL')
    admin_password = os.getenv('SUPER_ADMIN_PASSWORD')
    if not admin_email or not admin_password:
        click.echo('SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD must be set in .env')
        return

    super_admin_user = User.query.filter_by(email=admin_email).first()
    if not super_admin_user:
        super_admin_user = User(
            email=admin_email,
            username=admin_email.split('@')[0],
            first_name='Super',
            last_name='Admin',
            organization_id=super_org.id,
            is_verified=True # Super admin is verified by default
        )
        super_admin_user.set_password(admin_password)
        db.session.add(super_admin_user)
        db.session.commit()
        click.echo(f'Created super admin user: {super_admin_user.email}')
    
    # Assign Super Admin role to the user
    super_admin_user.roles.append(super_admin_role)
    db.session.commit()
    click.echo('Assigned Super Admin role.')

    click.echo('Database seeding complete.')