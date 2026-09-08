from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_babel import _
from . import employees_bp
from app.extensions import db
from app.models import Employee, EmployeeHireHistory, Employeer, EmployeeCdcStory, CdcSub, Function
from sqlalchemy import func


@employees_bp.route('/')
@login_required
def index():
    """Employee list with search, company filter, pagination and access control."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('q', '', type=str).strip()
    status = request.args.get('status', 'active', type=str)
    company_id = request.args.get('company', 0, type=int)
    show_not_valid = request.args.get('show_nv', '0', type=str) == '1'

    # --- Company access control ---
    accessible_ids = current_user.get_accessible_company_ids()
    can_see_all = current_user.can_see_all_companies

    # If user has no linked employee and is not admin, show empty
    if not can_see_all and not accessible_ids:
        return render_template(
            'employees/index.html',
            employees=[], pagination=None, search='', status=status,
            company_id=0, companies=[], show_not_valid=False,
            can_see_all=False,
        )

    query = db.session.query(Employee).order_by(Employee.EmployeeSurname, Employee.EmployeeName)

    # Exclude NotValidForLegalDoc unless explicitly requested
    if not show_not_valid:
        query = query.filter(
            db.or_(Employee.NotValidForLegalDoc.is_(None), Employee.NotValidForLegalDoc == False)
        )

    # Search filter
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Employee.EmployeeSurname.ilike(search_term),
                Employee.EmployeeName.ilike(search_term),
                Employee.EmployeeNID.ilike(search_term),
            )
        )

    # Company filter: explicit selection or access restriction
    effective_company_ids = None
    if company_id:
        # User selected a specific company
        if not can_see_all and company_id not in accessible_ids:
            company_id = 0  # Reset if not accessible
        else:
            effective_company_ids = [company_id]
    
    if not effective_company_ids and not can_see_all and accessible_ids:
        # Restrict to user's accessible companies
        effective_company_ids = accessible_ids

    if effective_company_ids:
        query = query.filter(
            Employee.hire_history.any(
                EmployeeHireHistory.EmployeerId.in_(effective_company_ids)
            )
        )

    # Status filter
    if status == 'active':
        active_filter = EmployeeHireHistory.EndWorkDate.is_(None)
        if effective_company_ids:
            active_filter = db.and_(active_filter, EmployeeHireHistory.EmployeerId.in_(effective_company_ids))
        query = query.filter(Employee.hire_history.any(active_filter))
    elif status == 'inactive':
        active_filter = EmployeeHireHistory.EndWorkDate.is_(None)
        if effective_company_ids:
            active_filter = db.and_(active_filter, EmployeeHireHistory.EmployeerId.in_(effective_company_ids))
        query = query.filter(~Employee.hire_history.any(active_filter))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get companies for filter dropdown (only accessible ones for non-admin)
    if can_see_all:
        companies = db.session.query(Employeer).order_by(Employeer.EmployeerName).all()
    else:
        companies = db.session.query(Employeer).filter(
            Employeer.EmployeerId.in_(accessible_ids)
        ).order_by(Employeer.EmployeerName).all()

    return render_template(
        'employees/index.html',
        employees=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        company_id=company_id,
        companies=companies,
        show_not_valid=show_not_valid,
        can_see_all=can_see_all,
    )


@employees_bp.route('/<int:id>')
@login_required
def detail(id):
    """Employee detail card."""
    employee = db.session.query(Employee).get_or_404(id)

    # Access control: non-admin users can only see employees from their companies
    if not current_user.can_see_all_companies:
        accessible_ids = current_user.get_accessible_company_ids()
        if accessible_ids:
            has_access = db.session.query(EmployeeHireHistory).filter(
                EmployeeHireHistory.EmployeeId == id,
                EmployeeHireHistory.EmployeerId.in_(accessible_ids)
            ).first()
            if not has_access:
                flash(_('Non hai accesso a questo dipendente.'), 'error')
                return redirect(url_for('employees.index'))
    
    # Get all contracts with company info
    contracts = db.session.query(
        EmployeeHireHistory, Employeer
    ).join(
        Employeer, EmployeeHireHistory.EmployeerId == Employeer.EmployeerId
    ).filter(
        EmployeeHireHistory.EmployeeId == id
    ).order_by(EmployeeHireHistory.HireDate.desc()).all()
    
    # Active contracts
    active_contracts = [c for c, emp in contracts if c.EndWorkDate is None]

    # Current CdC assignments
    cdc_stories = []
    if active_contracts:
        cdc_stories = db.session.query(
            EmployeeCdcStory, CdcSub, Function
        ).join(
            CdcSub, EmployeeCdcStory.SubCdcId == CdcSub.SubCdcId
        ).outerjoin(
            Function, EmployeeCdcStory.FunctionId == Function.FunctionId
        ).filter(
            EmployeeCdcStory.EmployeeHireHistoryId.in_(
                [c.EmployeeHireHistoryId for c in active_contracts]
            ),
            EmployeeCdcStory.DateOut.is_(None)
        ).order_by(EmployeeCdcStory.DateIn.desc()).all()

    return render_template(
        'employees/detail.html',
        employee=employee,
        active_contracts=active_contracts,
        contracts=contracts,
        cdc_stories=cdc_stories,
    )


@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit employee basic fields (including NotValidForLegalDoc flag)."""
    employee = db.session.query(Employee).get_or_404(id)

    # Only admin can edit
    if not current_user.can_see_all_companies and not current_user.has_role('hr'):
        flash(_('Non hai i permessi per modificare questo dipendente.'), 'error')
        return redirect(url_for('employees.detail', id=id))

    if request.method == 'POST':
        employee.NotValidForLegalDoc = 'NotValidForLegalDoc' in request.form
        employee.EmployeeName = request.form.get('EmployeeName', employee.EmployeeName).strip()
        employee.EmployeeSurname = request.form.get('EmployeeSurname', employee.EmployeeSurname).strip()
        employee.EmployeeOldSurName = request.form.get('EmployeeOldSurName', '').strip() or None
        employee.EmployeeSex = request.form.get('EmployeeSex', employee.EmployeeSex)
        db.session.commit()
        flash(_('Dipendente aggiornato.'), 'success')
        return redirect(url_for('employees.detail', id=id))

    return render_template('employees/edit.html', employee=employee)


# ==================== HIRING ====================

@employees_bp.route('/hiring/')
@login_required
def hiring_index():
    """Hiring dashboard - list of pending/recent hirings."""
    from app.models import ResourceRequest, CdcSub, Function
    pending_requests = db.session.query(
        ResourceRequest, CdcSub, Function
    ).join(
        CdcSub, ResourceRequest.SubCdcId == CdcSub.SubCdcId
    ).join(
        Function, ResourceRequest.FunctionId == Function.FunctionId
    ).filter(
        ResourceRequest.Status.in_(['approved', 'pending'])
    ).order_by(ResourceRequest.RequestedAt.desc()).all()

    return render_template(
        'employees/hiring/index.html',
        pending_requests=pending_requests,
    )


@employees_bp.route('/hiring/new', methods=['GET', 'POST'])
@login_required
def hiring_new():
    """Multi-tab hiring form."""
    from app.models import (
        ContractType, CostCenter, CdcSub, CodeCore,
        DocumentType, RelativeType, RegistryType, Town, County
    )
    from app.models.medical import MedicalCenter
    from app.services.hiring_service import HiringService
    from datetime import date as date_cls

    if request.method == 'POST':
        # Parse all form data
        errors = []

        # Parse dates safely
        def parse_date(field_name):
            val = request.form.get(field_name, '').strip()
            if val:
                try:
                    return date_cls.fromisoformat(val)
                except ValueError:
                    errors.append(f"Data non valida: {field_name}")
            return None

        hire_date = parse_date('hire_date')
        start_work_date = parse_date('start_work_date')
        end_work_date_contract = parse_date('end_work_date_contract')

        if not hire_date or not start_work_date:
            errors.append("Data stipula e data inizio lavoro sono obbligatorie.")

        if errors:
            for e in errors:
                flash(e, 'danger')
            # Re-render form - fall through to GET

        else:
            # Collect children
            children = []
            child_names = request.form.getlist('child_name[]')
            child_dates = request.form.getlist('child_birthdate[]')
            child_cnps = request.form.getlist('child_cnp[]')
            child_relatives = request.form.getlist('child_relative_type[]')
            for i in range(len(child_names)):
                if child_names[i].strip():
                    children.append({
                        'name': child_names[i].strip(),
                        'birth_date': date_cls.fromisoformat(child_dates[i]) if child_dates[i] else date_cls.today(),
                        'cnp': child_cnps[i].strip() if i < len(child_cnps) else '',
                        'relative_type_id': int(child_relatives[i]) if i < len(child_relatives) and child_relatives[i] else None,
                    })

            data = {
                # Personal
                'cnp': request.form.get('cnp', '').strip(),
                'name': request.form.get('name', '').strip(),
                'surname': request.form.get('surname', '').strip(),
                'middle_name': request.form.get('middle_name', '').strip(),
                'sex': request.form.get('sex', 'M'),
                'birth_town_id': int(request.form.get('birth_town_id') or 0) or None,
                # Document
                'doc_type_id': int(request.form.get('doc_type_id') or 0) or None,
                'doc_serie': request.form.get('doc_serie', '').strip(),
                'doc_number': request.form.get('doc_number', '').strip(),
                'doc_issued_by': request.form.get('doc_issued_by', '').strip(),
                'doc_issue_date': parse_date('doc_issue_date'),
                'doc_expire_date': parse_date('doc_expire_date'),
                # Address official
                'addr_town_id': int(request.form.get('addr_town_id') or 0) or None,
                'addr_street': request.form.get('addr_street', '').strip(),
                'addr_street2': request.form.get('addr_street2', '').strip(),
                'addr_numero': request.form.get('addr_numero', '').strip(),
                'addr_bloc': request.form.get('addr_bloc', '').strip(),
                'addr_scala': request.form.get('addr_scala', '').strip(),
                'addr_piano': request.form.get('addr_piano', '').strip(),
                'addr_apartment': request.form.get('addr_apartment', '').strip(),
                # Contact
                'phone': request.form.get('phone', '').strip(),
                'phone2': request.form.get('phone2', '').strip(),
                'email': request.form.get('email', '').strip(),
                'work_email': request.form.get('work_email', '').strip(),
                # Children
                'children': children,
                # Contract
                'employeer_id': int(request.form.get('employeer_id') or 0),
                'contract_type_id': int(request.form.get('contract_type_id') or 0),
                'hire_date': hire_date,
                'start_work_date': start_work_date,
                'end_work_date_contract': end_work_date_contract,
                'hours_per_day': int(request.form.get('hours_per_day') or 8),
                'salary': int(request.form.get('salary') or 0),
                'test_period': int(request.form.get('test_period') or 90),
                'core_code': request.form.get('core_code', '').strip(),
                # Assignment
                'sub_cdc_id': int(request.form.get('sub_cdc_id') or 0),
                'function_id': int(request.form.get('function_id') or 0),
                # Registry
                'registry_type_id': int(request.form.get('registry_type_id') or 0),
                'created_by_username': current_user.Username,
            }

            result = HiringService.create_hiring(data)

            if result['success']:
                # Create user account
                employee = db.session.query(Employee).get(result['employee_id'])
                user, password = HiringService.create_user_account(employee, data['email'])

                flash(
                    _('Assunzione completata! Contratto: %(contract)s. Utente: %(user)s',
                      contract=result['contract_number'], user=user.Username),
                    'success'
                )
                return redirect(url_for('employees.detail', id=result['employee_id']))
            else:
                for err in result['errors']:
                    flash(err, 'danger')

    # GET: Load all dropdown data
    companies = db.session.query(Employeer).filter(
        Employeer.DateOut.is_(None)
    ).order_by(Employeer.EmployeerName).all()

    contract_types = db.session.query(ContractType).all()
    cost_centers = db.session.query(CostCenter).order_by(CostCenter.CdcDescription).all()
    doc_types = db.session.query(DocumentType).all()
    relative_types = db.session.query(RelativeType).filter(RelativeType.DateOut.is_(None)).all()
    registry_types = db.session.query(RegistryType).order_by(RegistryType.Acronim).all()
    code_cores = db.session.query(CodeCore).filter(CodeCore.DateOut.is_(None)).order_by(CodeCore.CoreCode).all()
    medical_centers = db.session.query(MedicalCenter).filter_by(IsActive=True).all()
    counties = db.session.query(County).order_by(County.CountyName).all()

    return render_template(
        'employees/hiring/new.html',
        companies=companies,
        contract_types=contract_types,
        cost_centers=cost_centers,
        doc_types=doc_types,
        relative_types=relative_types,
        registry_types=registry_types,
        code_cores=code_cores,
        medical_centers=medical_centers,
        counties=counties,
    )


# ==================== CASCADING DROPDOWN APIs ====================

@employees_bp.route('/api/subcdc/<int:cdc_id>')
@login_required
def api_get_sub_cdcs(cdc_id):
    """Get SubCdCs for a given CostCenter."""
    from flask import jsonify
    sub_cdcs = db.session.query(CdcSub).filter_by(CdcId=cdc_id).order_by(CdcSub.SubCdcDescription).all()
    return jsonify([{'id': s.SubCdcId, 'name': s.SubCdcDescription} for s in sub_cdcs])


@employees_bp.route('/api/functions')
@login_required
def api_get_functions():
    """Get all functions."""
    from flask import jsonify
    functions = db.session.query(Function).order_by(Function.FunctionDescription).all()
    return jsonify([{
        'id': f.FunctionId,
        'name': f.FunctionDescription,
        'code': f.FunctionCode
    } for f in functions])


@employees_bp.route('/api/towns/<int:county_id>')
@login_required
def api_get_towns(county_id):
    """Get towns for a given county."""
    from flask import jsonify
    from app.models import Town
    towns = db.session.query(Town).filter_by(CountyId=county_id).order_by(Town.TownName).all()
    return jsonify([{'id': t.TownId, 'name': t.TownName} for t in towns])


# ==================== CNP VALIDATION API ====================

@employees_bp.route('/api/cnp/validate')
@login_required
def api_validate_cnp():
    """Endpoint for CNP validation with existing employee check."""
    from flask import jsonify
    from app.services.cnp_validator import validate_cnp
    from app.models import EmployeeDisciplinaryHistory

    cnp = request.args.get('cnp', '').strip()
    if not cnp:
        return jsonify({'valid': False, 'error': 'CNP richiesto'})

    result = validate_cnp(cnp)

    # Serialize birth_date to string
    if result.get('birth_date'):
        result['birth_date'] = result['birth_date'].strftime('%Y-%m-%d')

    # Check if employee already exists
    if result['valid']:
        existing = db.session.query(Employee).filter_by(EmployeeNID=cnp).first()
        if existing:
            result['existing'] = True
            result['employee_id'] = existing.EmployeeId
            result['employee_name'] = existing.full_name

            contracts = db.session.query(EmployeeHireHistory, Employeer).join(
                Employeer, EmployeeHireHistory.EmployeerId == Employeer.EmployeerId
            ).filter(
                EmployeeHireHistory.EmployeeId == existing.EmployeeId
            ).order_by(EmployeeHireHistory.HireDate.desc()).all()

            result['contracts'] = [{
                'company': emp.EmployeerName,
                'hire_date': c.HireDate.strftime('%d/%m/%Y') if c.HireDate else '-',
                'end_date': c.EndWorkDate.strftime('%d/%m/%Y') if c.EndWorkDate else 'Attivo',
            } for c, emp in contracts]

            disc_count = db.session.query(EmployeeDisciplinaryHistory).join(
                EmployeeHireHistory,
                EmployeeDisciplinaryHistory.EmployeeHireHistoryId == EmployeeHireHistory.EmployeeHireHistoryId
            ).filter(
                EmployeeHireHistory.EmployeeId == existing.EmployeeId
            ).count()
            result['disciplinary_count'] = disc_count
        else:
            result['existing'] = False

    return jsonify(result)

