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
