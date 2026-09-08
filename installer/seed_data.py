"""
Seed initial data: languages, roles, permissions, admin user, default license.
"""
from datetime import date
from app.extensions import db
from app.models.auth import Role, Permission, User, RolePermission
from app.models.i18n import Language
from app.models.license import License


def seed_database():
    """Populate initial data for the Employees database."""

    # 1. Seed Languages
    languages = [
        {'code': 'it', 'name': 'Italiano'},
        {'code': 'ro', 'name': 'Romana'},
        {'code': 'en', 'name': 'English'},
        {'code': 'es', 'name': 'Espanol'},
        {'code': 'fr', 'name': 'Francais'},
        {'code': 'de', 'name': 'Deutsch'},
    ]
    for lang_data in languages:
        lang = db.session.query(Language).filter_by(LanguageCode=lang_data['code']).first()
        if not lang:
            lang = Language(LanguageCode=lang_data['code'], LanguageName=lang_data['name'])
            db.session.add(lang)

    db.session.commit()
    print("[Seed] OK - Lingue inserite.")

    # 2. Seed Roles
    roles_data = [
        {'name': 'superadmin',  'desc': 'Super Administrator - Full system access', 'sys': True},
        {'name': 'admin',       'desc': 'System Administrator',  'sys': True},
        {'name': 'hr_manager',  'desc': 'HR Manager',            'sys': True},
        {'name': 'hr_operator', 'desc': 'HR Operator',           'sys': True},
        {'name': 'supervisor',  'desc': 'Supervisor',            'sys': True},
        {'name': 'employee',    'desc': 'Employee',              'sys': True},
        {'name': 'viewer',      'desc': 'Viewer',                'sys': True},
    ]
    role_objs = {}
    for rd in roles_data:
        role = db.session.query(Role).filter_by(RoleName=rd['name']).first()
        if not role:
            role = Role(RoleName=rd['name'], RoleDescription=rd['desc'], IsSystemRole=rd['sys'])
            db.session.add(role)
        role_objs[rd['name']] = role

    db.session.commit()
    print("[Seed] OK - Ruoli inseriti.")

    # 3. Seed Permissions
    permissions_data = [
        # (code, name, module, license_level)
        ('employees.view',     'View Employees',           'employees',    'basic'),
        ('employees.edit',     'Edit Employees',           'employees',    'basic'),
        ('employees.create',   'Create Employees',         'employees',    'basic'),
        ('employees.delete',   'Delete Employees',         'employees',    'basic'),
        ('contracts.view',     'View Contracts',           'contracts',    'basic'),
        ('contracts.edit',     'Edit Contracts',           'contracts',    'basic'),
        ('organization.view',  'View Organization',        'organization', 'basic'),
        ('organization.edit',  'Edit Organization',        'organization', 'basic'),
        ('needs.view',         'View Resource Needs',      'needs',        'basic'),
        ('needs.edit',         'Edit Resource Needs',      'needs',        'basic'),
        ('needs.approve',      'Approve Resource Requests','needs',        'basic'),
        ('admin.users',        'Manage Users',             'admin',        'basic'),
        ('admin.roles',        'Manage Roles',             'admin',        'basic'),
        ('admin.licenses',     'Manage Licenses',          'admin',        'basic'),
        ('admin.audit',        'View Audit Log',           'admin',        'basic'),
        ('dashboard.view',     'View Dashboard',           'dashboard',    'basic'),
    ]

    admin_role = role_objs['admin']
    perm_objs = {}

    for p_code, p_name, p_mod, p_level in permissions_data:
        perm = db.session.query(Permission).filter_by(PermissionCode=p_code).first()
        if not perm:
            perm = Permission(
                PermissionCode=p_code, PermissionName=p_name,
                ModuleName=p_mod, LicenseLevel=p_level
            )
            db.session.add(perm)
            db.session.flush()  # Get the ID
        perm_objs[p_code] = perm

        # Assign all permissions to admin role
        existing = db.session.query(RolePermission).filter_by(
            RoleId=admin_role.RoleId, PermissionId=perm.PermissionId
        ).first()
        if not existing:
            rp = RolePermission(RoleId=admin_role.RoleId, PermissionId=perm.PermissionId)
            db.session.add(rp)

    # Assign read permissions to hr_manager
    hr_manager = role_objs['hr_manager']
    hr_perms = ['employees.view', 'employees.edit', 'employees.create',
                'contracts.view', 'contracts.edit', 'organization.view',
                'needs.view', 'needs.edit', 'needs.approve', 'dashboard.view']
    for pc in hr_perms:
        perm = perm_objs.get(pc)
        if perm:
            existing = db.session.query(RolePermission).filter_by(
                RoleId=hr_manager.RoleId, PermissionId=perm.PermissionId
            ).first()
            if not existing:
                db.session.add(RolePermission(RoleId=hr_manager.RoleId, PermissionId=perm.PermissionId))

    # Assign view permissions to viewer
    viewer = role_objs['viewer']
    viewer_perms = ['employees.view', 'contracts.view', 'organization.view',
                    'needs.view', 'dashboard.view']
    for pc in viewer_perms:
        perm = perm_objs.get(pc)
        if perm:
            existing = db.session.query(RolePermission).filter_by(
                RoleId=viewer.RoleId, PermissionId=perm.PermissionId
            ).first()
            if not existing:
                db.session.add(RolePermission(RoleId=viewer.RoleId, PermissionId=perm.PermissionId))

    db.session.commit()
    print("[Seed] OK - Permessi inseriti e assegnati ai ruoli.")

    # 4. Seed Admin User
    admin_user = db.session.query(User).filter_by(Username='admin').first()
    if not admin_user:
        admin_user = User(
            Username='admin',
            PasswordHash='',
            Email='admin@company.local',
            MustChangePassword=True,
            PreferredLanguage='it',
        )
        admin_user.set_password('Admin@2026!')
        db.session.add(admin_user)
        db.session.flush()

        # Assign admin role
        from app.models.auth import UserRole
        ur = UserRole(UserId=admin_user.UserId, RoleId=admin_role.RoleId)
        db.session.add(ur)

    db.session.commit()
    print("[Seed] OK - Utente admin creato (user: admin, pwd: Admin@2026!).")

    # 5. Seed Default License
    active_license = db.session.query(License).filter_by(LicenseKey='DEFAULT-BASIC').first()
    if not active_license:
        active_license = License(
            LicenseKey='DEFAULT-BASIC',
            LicenseLevel='basic',
            CompanyName='Default Installation',
            MaxUsers=999,
            ExpiresAt=date(2030, 12, 31),
        )
        db.session.add(active_license)

    db.session.commit()
    print("[Seed] OK - Licenza default inserita (Basic, scadenza 2030-12-31).")

    # 7. Seed AppSettings
    from app.models.settings import AppSetting, DEFAULT_SETTINGS
    for s_data in DEFAULT_SETTINGS:
        existing = db.session.query(AppSetting).filter_by(SettingKey=s_data['SettingKey']).first()
        if not existing:
            setting = AppSetting(**s_data)
            db.session.add(setting)
    db.session.commit()
    print("[Seed] OK - Impostazioni di sistema inserite.")

    print("[Seed] === Seeding completato ===")

