from flask import render_template, request
from flask_login import login_required
from flask_babel import _
from . import employees_bp
from app.extensions import db
from app.models import Employee, EmployeeHireHistory


@employees_bp.route('/')
@login_required
def index():
    """Employee list with search and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('q', '', type=str).strip()
    status = request.args.get('status', 'all', type=str)

    query = db.session.query(Employee).order_by(Employee.EmployeeSurname, Employee.EmployeeName)

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

    # Status filter: active = has at least one hire with EndWorkDate IS NULL
    if status == 'active':
        query = query.filter(
            Employee.hire_history.any(EmployeeHireHistory.EndWorkDate.is_(None))
        )
    elif status == 'inactive':
        query = query.filter(
            ~Employee.hire_history.any(EmployeeHireHistory.EndWorkDate.is_(None))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'employees/index.html',
        employees=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
    )


@employees_bp.route('/<int:id>')
@login_required
def detail(id):
    """Employee detail card."""
    employee = db.session.query(Employee).get_or_404(id)
    
    # Get active contract (EndWorkDate IS NULL)
    active_contract = db.session.query(EmployeeHireHistory).filter_by(
        EmployeeId=id
    ).filter(
        EmployeeHireHistory.EndWorkDate.is_(None)
    ).first()
    
    # Get all contracts
    contracts = db.session.query(EmployeeHireHistory).filter_by(
        EmployeeId=id
    ).order_by(EmployeeHireHistory.HireDate.desc()).all()

    return render_template(
        'employees/detail.html',
        employee=employee,
        active_contract=active_contract,
        contracts=contracts,
    )
