from flask import render_template, request, jsonify, flash, redirect, url_for
from . import admin_bp
from .forms import ImportForm, UserCreateForm, UserEditForm
from app.services.import_service import ImportService
from app.extensions import db
from app.models import User, Role, AuditLog
from datetime import datetime
from flask_babel import _

@admin_bp.route('/')
def index():
    # Admin dashboard
    user_count = db.session.query(User).count()
    return render_template('admin/index.html', user_count=user_count)

@admin_bp.route('/import')
def import_page():
    return render_template('admin/import/index.html')

@admin_bp.route('/import/employee-db', methods=['GET', 'POST'])
def import_employee_db():
    if request.method == 'POST':
        service = ImportService()
        stats = service.import_from_employee_db()
        return jsonify(stats)
    return render_template('admin/import/employee_db.html')

@admin_bp.route('/import/file', methods=['GET', 'POST'])
def import_file():
    form = ImportForm()
    if form.validate_on_submit():
        # Process file upload
        pass
    return render_template('admin/import/file.html', form=form)

@admin_bp.route('/import/results')
def import_results():
    return render_template('admin/import/results.html')

@admin_bp.route('/users')
def users_list():
    users = db.session.query(User).all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def user_create():
    form = UserCreateForm()
    # Populate roles
    form.role.choices = [(r.RoleId, r.RoleName) for r in db.session.query(Role).all()]
    if form.validate_on_submit():
        # Create user
        flash(_('User created successfully.'), 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/users/create.html', form=form)

@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
def user_edit(id):
    user = db.session.query(User).get_or_404(id)
    form = UserEditForm(obj=user)
    form.role.choices = [(r.RoleId, r.RoleName) for r in db.session.query(Role).all()]
    if form.validate_on_submit():
        # Update user
        flash(_('User updated successfully.'), 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/users/edit.html', form=form, user=user)

@admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
def user_toggle(id):
    user = db.session.query(User).get_or_404(id)
    user.IsActive = not user.IsActive
    db.session.commit()
    flash(_('User status updated.'), 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/roles')
def roles_list():
    roles = db.session.query(Role).all()
    return render_template('admin/roles/index.html', roles=roles)

@admin_bp.route('/audit')
def audit_log():
    logs = db.session.query(AuditLog).order_by(AuditLog.Timestamp.desc()).limit(100).all()
    return render_template('admin/audit.html', logs=logs)
