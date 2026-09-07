import click
from flask.cli import with_appcontext

from installer.db_creator import init_db, check_database_exists
from app.extensions import db
from app.models.auth import User, Role

@click.command('install')
@click.option('--check', is_flag=True, help='Check if DB exists and tables are present')
@with_appcontext
def install_command(check):
    """Full installation: create DB, tables, and seed data."""
    if check:
        exists = check_database_exists('Employees')
        click.echo(f"Database Employees exists: {exists}")
        if exists:
            # Simple check for tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names(schema='app')
            click.echo(f"Tables in 'app' schema: {', '.join(tables) if tables else 'None'}")
        return

    click.echo("Starting installation...")
    init_db(seed=True)
    click.echo("Installation complete.")

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create or reset the admin user."""
    admin_user = db.session.query(User).filter_by(Username='admin').first()
    if not admin_user:
        admin_user = User(Username='admin', PasswordHash='', MustChangePassword=True)
        db.session.add(admin_user)
        
    admin_user.set_password('Admin@2026!')
    
    admin_role = db.session.query(Role).filter_by(RoleName='admin').first()
    if admin_role and admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)
        
    db.session.commit()
    click.echo("Admin user created/reset successfully.")

@click.command('setup')
@with_appcontext
def setup_command():
    """Run the full setup wizard."""
    from installer.setup_wizard import SetupWizard
    wizard = SetupWizard()
    wizard.run()

@click.command('create-superadmin')
@with_appcontext
def create_superadmin_command():
    """Create/reset SuperUserAdmin."""
    from installer.setup_wizard import SetupWizard
    wizard = SetupWizard()
    wizard._create_super_admin()

@click.command('import-data')
@click.option('--source', required=True, help='Source type: employee, file')
@click.option('--path', help='Path to file (if source=file)')
@with_appcontext
def import_data_command(source, path):
    """Import data from a source."""
    if source == 'employee':
        click.echo("[INFO] Importing from Employee DB...")
        # wizard._import_from_employee_db()
    elif source == 'file':
        click.echo(f"[INFO] Importing from file: {path}...")
    else:
        click.echo("[ERROR] Unknown source.")

def register_commands(app):
    app.cli.add_command(install_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(setup_command)
    app.cli.add_command(create_superadmin_command)
    app.cli.add_command(import_data_command)
