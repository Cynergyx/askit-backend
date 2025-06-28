import click
from flask.cli import with_appcontext
from src.extensions import db
from src.models.organization import Organization
from src.models.user import User, UserRole
from src.models.role import Role
from src.models.permission import Permission
import os
import uuid

@click.command(name='seed')
@with_appcontext
def seed():
    """Seeds the database with initial data."""
    if Role.query.filter_by(is_system_role=True).first():
        click.echo('Database already seeded.')
        return

    click.echo('Seeding database...')

    permissions_data = [
        # User Management
        {'name': 'user.create', 'resource': 'user', 'action': 'create'},
        {'name': 'user.read', 'resource': 'user', 'action': 'read'},
        {'name': 'user.update', 'resource': 'user', 'action': 'update'},
        {'name': 'user.delete', 'resource': 'user', 'action': 'delete'},
        # Role Management
        {'name': 'role.create', 'resource': 'role', 'action': 'create'},
        {'name': 'role.read', 'resource': 'role', 'action': 'read'},
        {'name': 'role.update', 'resource': 'role', 'action': 'update'},
        {'name': 'role.delete', 'resource': 'role', 'action': 'delete'},
        {'name': 'role.assign', 'resource': 'role', 'action': 'assign'},
        {'name': 'role.revoke', 'resource': 'role', 'action': 'revoke'},
        # Permission Management
        {'name': 'permission.read', 'resource': 'permission', 'action': 'read'},
        {'name': 'permission.assign', 'resource': 'permission', 'action': 'assign'},
        {'name': 'permission.revoke', 'resource': 'permission', 'action': 'revoke'},
        # Audit
        {'name': 'audit.read', 'resource': 'audit', 'action': 'read'},
        # Data Source Management
        {'name': 'datasource.create', 'resource': 'datasource', 'action': 'create'},
        {'name': 'datasource.read', 'resource': 'datasource', 'action': 'read'},
        # Database Access Management
        {'name': 'database.assign', 'resource': 'database', 'action': 'assign'},
        {'name': 'database.read', 'resource': 'database', 'action': 'read'},
        # Organization Management
        {'name': 'organization.create', 'resource': 'organization', 'action': 'create'},
        # Role Request Management
        {'name': 'rolerequest.create', 'resource': 'rolerequest', 'action': 'create'},
        {'name': 'rolerequest.read', 'resource': 'rolerequest', 'action': 'read'},
        {'name': 'rolerequest.manage', 'resource': 'rolerequest', 'action': 'manage'},
        # Chat
        {'name': 'chat.create', 'resource': 'chat', 'action': 'create'},
        {'name': 'chat.read', 'resource': 'chat', 'action': 'read'},
    ]
    permissions = [Permission(id=str(uuid.uuid4()), **p) for p in permissions_data]
    db.session.bulk_save_objects(permissions)
    db.session.commit()
    click.echo(f'Created {len(permissions)} permissions.')

    all_perms = Permission.query.all()
    perm_map = {p.name: p for p in all_perms}

    # Super Admin Role (System-level, no organization)
    super_admin_role = Role(id=str(uuid.uuid4()), name='Super Admin', display_name='Super Administrator', is_system_role=True, organization_id=None)
    super_admin_role.permissions.extend(all_perms)
    
    # Organization Admin and Member roles are templates. They will be cloned for each new org.
    org_admin_role_template = Role(id=str(uuid.uuid4()), name='Organization Admin', display_name='Organization Administrator', is_system_role=True)
    member_role_template = Role(id=str(uuid.uuid4()), name='Member', display_name='Member', is_system_role=True)
    db.session.add_all([super_admin_role, org_admin_role_template, member_role_template])

    # Assign permissions to templates
    admin_perms_names = [p['name'] for p in permissions_data if p['name'] != 'organization.create']
    for perm_name in admin_perms_names:
        org_admin_role_template.permissions.append(perm_map[perm_name])
    
    member_perms_names = ['user.read', 'role.read', 'rolerequest.create', 'chat.create', 'chat.read', 'database.read']
    for perm_name in member_perms_names:
        member_role_template.permissions.append(perm_map[perm_name])

    db.session.commit()
    click.echo('Created base role templates.')

    # Create the Super Admin's special organization
    super_org_domain = os.getenv('SUPER_ADMIN_ORG_DOMAIN', 'superorg')
    super_org = Organization.query.filter_by(domain=super_org_domain).first()
    if not super_org:
        super_org = Organization(id=str(uuid.uuid4()), name=super_org_domain.title(), domain=super_org_domain, is_active=True)
        db.session.add(super_org)
        db.session.commit()
        click.echo(f'Created super organization: {super_org.name}')

    super_admin_role.organization_id = super_org.id
    
    admin_email = os.getenv('SUPER_ADMIN_EMAIL')
    admin_password = os.getenv('SUPER_ADMIN_PASSWORD')
    if not admin_email or not admin_password:
        click.echo('SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD must be set in .env')
        return

    super_admin_user = User.query.filter_by(email=admin_email).first()
    if not super_admin_user:
        super_admin_user = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            username=admin_email.split('@')[0],
            first_name='Super',
            last_name='Admin',
            organization_id=super_org.id,
            is_verified=True
        )
        super_admin_user.set_password(admin_password)
        db.session.add(super_admin_user)
        # Manually create the UserRole assignment
        user_role_assignment = UserRole(
            user_id=super_admin_user.id,
            role_id=super_admin_role.id,
            granted_by_user_id=super_admin_user.id # Self-granted
        )
        db.session.add(user_role_assignment)
        db.session.commit()
        click.echo(f'Created super admin user: {super_admin_user.email}')

    click.echo('Database seeding complete.')