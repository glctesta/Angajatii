from flask import render_template, request
from flask_login import login_required
from flask_babel import _
from . import employees_bp
from app.extensions import db
from app.models import Employee, EmployeeHireHistory, Employeer, EmployeeCdcStory, CdcSub, Function
from sqlalchemy import func


@employees_bp.route('/')
@login_required
def index():
    """Employee list with search, company filter and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('q', '', type=str).strip()
    status = request.args.get('status', 'all', type=str)
    company_id = request.args.get('company', 0, type=int)

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

    # Company filter
    if company_id:
        query = query.filter(
            Employee.hire_history.any(EmployeeHireHistory.EmployeerId == company_id)
        )

    # Status filter
    if status == 'active':
        if company_id:
            query = query.filter(
                Employee.hire_history.any(
                    db.and_(
                        EmployeeHireHistory.EndWorkDate.is_(None),
                        EmployeeHireHistory.EmployeerId == company_id
                    )
                )
            )
        else:
            query = query.filter(
                Employee.hire_history.any(EmployeeHireHistory.EndWorkDate.is_(None))
            )
    elif status == 'inactive':
        if company_id:
            query = query.filter(
                ~Employee.hire_history.any(
                    db.and_(
                        EmployeeHireHistory.EndWorkDate.is_(None),
                        EmployeeHireHistory.EmployeerId == company_id
                    )
                )
            )
        else:
            query = query.filter(
                ~Employee.hire_history.any(EmployeeHireHistory.EndWorkDate.is_(None))
            )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get companies for filter dropdown
    companies = db.session.query(Employeer).order_by(Employeer.EmployeerName).all()

    return render_template(
        'employees/index.html',
        employees=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        company_id=company_id,
        companies=companies,
    )


@employees_bp.route('/<int:id>')
@login_required
def detail(id):
    """Employee detail card."""
    employee = db.session.query(Employee).get_or_404(id)
    
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
    cdc_stories = db.session.query(
        EmployeeCdcStory, CdcSub, Function
    ).join(
        CdcSub, EmployeeCdcStory.SubCdcId == CdcSub.SubCdcId
    ).outerjoin(
        Function, EmployeeCdcStory.FunctionId == Function.FunctionId
    ).filter(
        EmployeeCdcStory.EmployeeHireHistoryId.in_([c.EmployeeHireHistoryId for c in active_contracts])
    ).order_by(EmployeeCdcStory.DateIn.desc()).all() if active_contracts else []

    return render_template(
        'employees/detail.html',
        employee=employee,
        active_contracts=active_contracts,
        contracts=contracts,
        cdc_stories=cdc_stories,
    )
