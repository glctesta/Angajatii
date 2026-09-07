from datetime import date
import bcrypt
from app.extensions import db
from app.models.auth import Role, Permission, User, RolePermission
from app.models.i18n import Language
from app.models.license import License

def seed_database():
    # 1. Seed Languages
    languages = [
        {'code': 'it', 'name': 'Italiano'},
        {'code': 'ro', 'name': 'Română'},
        {'code': 'en', 'name': 'English'},
        {'code': 'es', 'name': 'Español'},
        {'code': 'fr', 'name': 'Français'},
        {'code': 'de', 'name': 'Deutsch'}
    ]
    for lang_data in languages:
        lang = Language.query.filter_by(LanguageCode=lang_data['code']).first()
        if not lang:
            lang = Language(LanguageCode=lang_data['code'], LanguageName=lang_data['name'])
            db.session.add(lang)
            
    # 2. Seed Roles
    roles = [
        {'name': 'admin', 'desc': 'System Administrator', 'sys': True},
        {'name': 'hr_manager', 'desc': 'HR Manager', 'sys': True},
        {'name': 'hr_operator', 'desc': 'HR Operator', 'sys': True},
        {'name': 'supervisor', 'desc': 'Supervisor', 'sys': True},
        {'name': 'employee', 'desc': 'Employee', 'sys': True},
        {'name': 'viewer', 'desc': 'Viewer', 'sys': True}
    ]
    role_objs = {}
    for role_data in roles:
        role = Role.query.filter_by(RoleName=role_data['name']).first()
        if not role:
            role = Role(RoleName=role_data['name'], RoleDescription=role_data['desc'], IsSystemRole=role_data['sys'])
            db.session.add(role)
        role_objs[role_data['name']] = role
        
    db.session.commit()
    
    # 3. Seed Permissions
    permissions = [
        ('employees.view', 'View Employees', 'Employees'),
        ('employees.edit', 'Edit Employees', 'Employees'),
        ('employees.create', 'Create Employees', 'Employees'),
        ('employees.delete', 'Delete Employees', 'Employees'),
        ('needs.view', 'View Needs', 'Needs'),
        ('needs.edit', 'Edit Needs', 'Needs'),
    ]
    
    admin_role = role_objs['admin']
    for p_code, p_name, p_mod in permissions:
        perm = Permission.query.filter_by(PermissionCode=p_code).first()
        if not perm:
            perm = Permission(PermissionCode=p_code, PermissionName=p_name, ModuleName=p_mod)
            db.session.add(perm)
        db.session.commit() # Need id
        
        # Assign to admin
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
            
    # 4. Seed Admin User
    admin_user = User.query.filter_by(Username='admin').first()
    if not admin_user:
        admin_user = User(
            Username='admin',
            PasswordHash='',  # will be set below
            Email='admin@company.local',
            MustChangePassword=True
        )
        admin_user.set_password('Admin@2026!')
        db.session.add(admin_user)
        admin_user.roles.append(admin_role)

    # 5. Seed License
    active_license = License.query.filter_by(LicenseKey='DEFAULT-BASIC').first()
    if not active_license:
        active_license = License(
            LicenseKey='DEFAULT-BASIC',
            LicenseLevel='basic',
            MaxUsers=999,
            ExpiresAt=date(2030, 12, 31)
        )
        db.session.add(active_license)

    db.session.commit()
