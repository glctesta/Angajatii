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


# ==================== REGISTRY TYPES CRUD ====================

@admin_bp.route('/registry-types')
def registry_types():
    from app.models import RegistryType
    types = db.session.query(RegistryType).order_by(RegistryType.Acronim).all()
    return render_template('admin/registry_types/index.html', types=types)


@admin_bp.route('/registry-types/new', methods=['GET', 'POST'])
def registry_type_create():
    from app.models import RegistryType
    if request.method == 'POST':
        rt = RegistryType(
            Acronim=request.form.get('Acronim', '').strip(),
            Description=request.form.get('Description', '').strip(),
            NoCopy=int(request.form.get('NoCopy', 1)),
            GenerateDocument='GenerateDocument' in request.form,
            PublicRequest='PublicRequest' in request.form,
            CdcMainId=int(request.form.get('CdcMainId', 0)) or None,
        )
        db.session.add(rt)
        db.session.commit()
        flash(_('Tipo registro creato.'), 'success')
        return redirect(url_for('admin.registry_types'))
    return render_template('admin/registry_types/form.html', rt=None)


@admin_bp.route('/registry-types/<int:id>/edit', methods=['GET', 'POST'])
def registry_type_edit(id):
    from app.models import RegistryType
    rt = db.session.query(RegistryType).get_or_404(id)
    if request.method == 'POST':
        rt.Acronim = request.form.get('Acronim', '').strip()
        rt.Description = request.form.get('Description', '').strip()
        rt.NoCopy = int(request.form.get('NoCopy', 1))
        rt.GenerateDocument = 'GenerateDocument' in request.form
        rt.PublicRequest = 'PublicRequest' in request.form
        rt.CdcMainId = int(request.form.get('CdcMainId', 0)) or None
        db.session.commit()
        flash(_('Tipo registro aggiornato.'), 'success')
        return redirect(url_for('admin.registry_types'))
    return render_template('admin/registry_types/form.html', rt=rt)


# ==================== APP SETTINGS ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    from app.models import AppSetting
    from app.models.settings import DEFAULT_SETTINGS
    from flask_login import current_user

    if request.method == 'POST':
        for key in request.form:
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                AppSetting.set_value(setting_key, request.form[key], current_user.UserId)
        flash(_('Impostazioni salvate.'), 'success')
        return redirect(url_for('admin.settings'))

    settings_list = db.session.query(AppSetting).order_by(AppSetting.Category, AppSetting.SettingKey).all()

    # Group by category
    categories = {}
    for s in settings_list:
        categories.setdefault(s.Category, []).append(s)

    return render_template('admin/settings.html', categories=categories)


# ==================== MEDICAL CENTERS CRUD ====================

@admin_bp.route('/medical')
def medical_centers():
    from app.models.medical import MedicalCenter
    centers = db.session.query(MedicalCenter).order_by(MedicalCenter.CenterName).all()
    return render_template('admin/medical/index.html', centers=centers)


@admin_bp.route('/medical/new', methods=['GET', 'POST'])
def medical_center_create():
    from app.models.medical import MedicalCenter
    from datetime import date as date_cls
    if request.method == 'POST':
        center = MedicalCenter(
            CenterName=request.form.get('CenterName', '').strip(),
            Address=request.form.get('Address', '').strip(),
            Phone=request.form.get('Phone', '').strip(),
            Email=request.form.get('Email', '').strip(),
            ContactPerson=request.form.get('ContactPerson', '').strip(),
            ContractStartDate=date_cls.fromisoformat(request.form['ContractStartDate']) if request.form.get('ContractStartDate') else None,
            ContractEndDate=date_cls.fromisoformat(request.form['ContractEndDate']) if request.form.get('ContractEndDate') else None,
            IsActive='IsActive' in request.form,
            Notes=request.form.get('Notes', '').strip(),
        )
        db.session.add(center)
        db.session.commit()
        flash(_('Centro medico creato.'), 'success')
        return redirect(url_for('admin.medical_centers'))
    return render_template('admin/medical/center_form.html', center=None)


@admin_bp.route('/medical/<int:id>/edit', methods=['GET', 'POST'])
def medical_center_edit(id):
    from app.models.medical import MedicalCenter
    from datetime import date as date_cls
    center = db.session.query(MedicalCenter).get_or_404(id)
    if request.method == 'POST':
        center.CenterName = request.form.get('CenterName', '').strip()
        center.Address = request.form.get('Address', '').strip()
        center.Phone = request.form.get('Phone', '').strip()
        center.Email = request.form.get('Email', '').strip()
        center.ContactPerson = request.form.get('ContactPerson', '').strip()
        center.ContractStartDate = date_cls.fromisoformat(request.form['ContractStartDate']) if request.form.get('ContractStartDate') else None
        center.ContractEndDate = date_cls.fromisoformat(request.form['ContractEndDate']) if request.form.get('ContractEndDate') else None
        center.IsActive = 'IsActive' in request.form
        center.Notes = request.form.get('Notes', '').strip()
        db.session.commit()
        flash(_('Centro medico aggiornato.'), 'success')
        return redirect(url_for('admin.medical_centers'))
    return render_template('admin/medical/center_form.html', center=center)


# ==================== MEDICAL DOCTORS CRUD ====================

@admin_bp.route('/medical/<int:center_id>/doctors')
def medical_doctors(center_id):
    from app.models.medical import MedicalCenter, MedicalDoctor
    center = db.session.query(MedicalCenter).get_or_404(center_id)
    doctors = db.session.query(MedicalDoctor).filter_by(MedicalCenterId=center_id).order_by(MedicalDoctor.DoctorSurname).all()
    return render_template('admin/medical/doctors.html', center=center, doctors=doctors)


@admin_bp.route('/medical/<int:center_id>/doctors/new', methods=['GET', 'POST'])
def medical_doctor_create(center_id):
    from app.models.medical import MedicalCenter, MedicalDoctor
    center = db.session.query(MedicalCenter).get_or_404(center_id)
    if request.method == 'POST':
        doctor = MedicalDoctor(
            MedicalCenterId=center_id,
            DoctorName=request.form.get('DoctorName', '').strip(),
            DoctorSurname=request.form.get('DoctorSurname', '').strip(),
            Specialization=request.form.get('Specialization', '').strip(),
            Phone=request.form.get('Phone', '').strip(),
            Email=request.form.get('Email', '').strip(),
            IsActive='IsActive' in request.form,
        )
        db.session.add(doctor)
        db.session.commit()
        flash(_('Medico aggiunto.'), 'success')
        return redirect(url_for('admin.medical_doctors', center_id=center_id))
    return render_template('admin/medical/doctor_form.html', center=center, doctor=None)


@admin_bp.route('/medical/doctors/<int:id>/edit', methods=['GET', 'POST'])
def medical_doctor_edit(id):
    from app.models.medical import MedicalCenter, MedicalDoctor
    doctor = db.session.query(MedicalDoctor).get_or_404(id)
    center = db.session.query(MedicalCenter).get_or_404(doctor.MedicalCenterId)
    if request.method == 'POST':
        doctor.DoctorName = request.form.get('DoctorName', '').strip()
        doctor.DoctorSurname = request.form.get('DoctorSurname', '').strip()
        doctor.Specialization = request.form.get('Specialization', '').strip()
        doctor.Phone = request.form.get('Phone', '').strip()
        doctor.Email = request.form.get('Email', '').strip()
        doctor.IsActive = 'IsActive' in request.form
        db.session.commit()
        flash(_('Medico aggiornato.'), 'success')
        return redirect(url_for('admin.medical_doctors', center_id=center.MedicalCenterId))
    return render_template('admin/medical/doctor_form.html', center=center, doctor=doctor)
