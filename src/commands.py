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
    """Seeds or updates the database with system roles and permissions."""
    
    # Check if the command has already run. We will still proceed to ensure roles are up-to-date.
    if Role.query.filter_by(name='Super Admin').first():
        click.echo('System roles found. Verifying and updating permissions...')
    else:
        click.echo('Seeding database with initial data...')

    # --- Permissions Data ---
    # This list defines all possible permissions in the system.
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
        {'name': 'datasource.update', 'resource': 'datasource', 'action': 'update'},
        # Database Access Management
        {'name': 'database.assign', 'resource': 'database', 'action': 'assign'},
        {'name': 'database.read', 'resource': 'database', 'action': 'read'},
        # Organization Management
        {'name': 'organization.create', 'resource': 'organization', 'action': 'create'},
        {'name': 'organization.delete', 'resource': 'organization', 'action': 'delete'},
        # Role Request Management
        {'name': 'rolerequest.create', 'resource': 'rolerequest', 'action': 'create'},
        {'name': 'rolerequest.read', 'resource': 'rolerequest', 'action': 'read'},
        {'name': 'rolerequest.manage', 'resource': 'rolerequest', 'action': 'manage'},
        # Chat
        {'name': 'chat.create', 'resource': 'chat', 'action': 'create'},
        {'name': 'chat.read', 'resource': 'chat', 'action': 'read'},
    ]
    
    # Create any permissions that don't already exist
    existing_perms = {p.name for p in Permission.query.all()}
    new_perms_data = [p for p in permissions_data if p['name'] not in existing_perms]
    if new_perms_data:
        new_permissions = [Permission(id=str(uuid.uuid4()), **p) for p in new_perms_data]
        db.session.bulk_save_objects(new_permissions)
        db.session.commit()
        click.echo(f'Created {len(new_permissions)} new permissions.')

    all_perms = Permission.query.all()
    perm_map = {p.name: p for p in all_perms}

    # --- System Role Templates ---
    # This section creates or updates the role templates that are cloned for new organizations.
    click.echo('Creating/updating system role templates...')

    # Use merge to either create or update existing system roles
    super_admin_role = Role.query.filter_by(name='Super Admin').first() or Role(id=str(uuid.uuid4()), name='Super Admin', is_system_role=True)
    super_admin_role.display_name = 'Super Administrator'
    
    org_admin_role_template = Role.query.filter_by(name='Organization Admin', is_system_role=True).first() or Role(id=str(uuid.uuid4()), name='Organization Admin', is_system_role=True)
    org_admin_role_template.display_name = 'Organization Administrator'
    
    member_role_template = Role.query.filter_by(name='Member', is_system_role=True).first() or Role(id=str(uuid.uuid4()), name='Member', is_system_role=True)
    member_role_template.display_name = 'Member'
    
    # NEW: Define Viewer and Editor role templates
    viewer_role_template = Role.query.filter_by(name='Viewer', is_system_role=True).first() or Role(id=str(uuid.uuid4()), name='Viewer', is_system_role=True)
    viewer_role_template.display_name = 'Viewer'
    viewer_role_template.description = 'Read-only access to most resources.'
    
    editor_role_template = Role.query.filter_by(name='Editor', is_system_role=True).first() or Role(id=str(uuid.uuid4()), name='Editor', is_system_role=True)
    editor_role_template.display_name = 'Editor'
    editor_role_template.description = 'Can create and edit certain resources.'
    
    # Use merge to handle both creation and updates seamlessly
    db.session.merge(super_admin_role)
    db.session.merge(org_admin_role_template)
    db.session.merge(member_role_template)
    db.session.merge(viewer_role_template)
    db.session.merge(editor_role_template)
    db.session.commit()

    # --- Assign Permissions to Roles ---
    # Clear existing permissions to ensure a clean slate on every run
    super_admin_role.permissions.clear()
    org_admin_role_template.permissions.clear()
    member_role_template.permissions.clear()
    viewer_role_template.permissions.clear()
    editor_role_template.permissions.clear()

    # Define permission sets for each role
    super_admin_role.permissions.extend(all_perms)
    
    admin_perms_names = [p['name'] for p in permissions_data if p['name'] not in ['organization.create', 'organization.delete']]
    
    # UPDATED: Member role gets permission to see available data sources
    member_perms_names = [
        'user.read', 'role.read', 'rolerequest.create', 'chat.create', 
        'chat.read', 'database.read', 'datasource.read'
    ]
    
    # NEW: Viewer permissions (read-only)
    viewer_perms_names = [
        'user.read', 'role.read', 'audit.read', 'datasource.read', 
        'chat.read', 'database.read'
    ]
    
    # NEW: Editor permissions (Viewer + create/edit capabilities)
    editor_perms_names = viewer_perms_names + [
        'chat.create', 'datasource.update'
    ]
    
    # Assign permissions from the defined lists
    for perm_name in admin_perms_names:
        if perm_map.get(perm_name): org_admin_role_template.permissions.append(perm_map[perm_name])
    
    for perm_name in member_perms_names:
        if perm_map.get(perm_name): member_role_template.permissions.append(perm_map[perm_name])
        
    for perm_name in viewer_perms_names:
        if perm_map.get(perm_name): viewer_role_template.permissions.append(perm_map[perm_name])

    for perm_name in editor_perms_names:
        if perm_map.get(perm_name): editor_role_template.permissions.append(perm_map[perm_name])

    db.session.commit()
    click.echo('System role templates and permissions have been configured.')

    # --- Super Admin User and Organization ---
    # This logic only runs once on the very first seed
    super_org_domain = os.getenv('SUPER_ADMIN_ORG_DOMAIN', 'superorg')
    super_org = Organization.query.filter_by(domain=super_org_domain).first()
    if not super_org:
        super_org = Organization(id=str(uuid.uuid4()), name=super_org_domain.title(), domain=super_org_domain, is_active=True)
        db.session.add(super_org)
        db.session.commit()
        click.echo(f'Created super organization: {super_org.name}')

    if super_admin_role:
        super_admin_role.organization_id = super_org.id
        db.session.commit()
    
    admin_email = os.getenv('SUPER_ADMIN_EMAIL')
    admin_password = os.getenv('SUPER_ADMIN_PASSWORD')
    if not admin_email or not admin_password:
        click.echo('WARNING: SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD must be set in .env to create the super admin.')
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
        db.session.commit()
        
        # Manually create the UserRole assignment
        user_role_assignment = UserRole(
            user_id=super_admin_user.id,
            role_id=super_admin_role.id,
            granted_by_user_id=super_admin_user.id # Self-granted
        )
        db.session.add(user_role_assignment)
        db.session.commit()
        click.echo(f'Created super admin user: {super_admin_user.email}')

    click.echo('Database seeding process complete.')