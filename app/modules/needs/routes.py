from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_babel import _
from app.extensions import db

from . import needs_bp
from .services import NeedsService
from .forms import ResourceNeedForm, ResourceRequestForm, NeedFilterForm
from app.models.organization import CostCenter, CdcSub, Function
from app.models.needs import ResourceNeed, ResourceRequest
from app.models.attendance import Shift

@needs_bp.route('/')
@login_required
def index():
    summary = NeedsService.get_needs_summary_by_department()
    total_departments = len(summary)
    total_required = sum(d['total_required'] for d in summary)
    total_current = sum(d['total_current'] for d in summary)
    total_gap = sum(d['total_gap'] for d in summary)
    
    return render_template('needs/index.html', summary=summary, 
                           total_departments=total_departments,
                           total_required=total_required,
                           total_current=total_current,
                           total_gap=total_gap)

@needs_bp.route('/detail', methods=['GET', 'POST'])
@login_required
def detail():
    form = NeedFilterForm(request.form if request.method == 'POST' else request.args)
    
    # Populate choices
    form.department.choices = [(0, _('All'))] + [(d.CdcId, d.CdcDescription or str(d.CdcId)) for d in db.session.query(CostCenter).all()]
    form.function.choices = [(0, _('All'))] + [(f.FunctionId, f.FunctionDescription) for f in db.session.query(Function).all()]
    form.shift.choices = [(0, _('All'))] + [(s.ShiftId, s.ShiftName) for s in db.session.query(Shift).all()]

    filters = {}
    if form.department.data: filters['department'] = form.department.data
    if form.function.data: filters['function'] = form.function.data
    if form.shift.data: filters['shift'] = form.shift.data

    needs_data = NeedsService.get_all_needs(filters)
    return render_template('needs/detail.html', needs_data=needs_data, form=form)

@needs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ResourceNeedForm()
    # Populate choices
    form.sub_cdc.choices = [(c.SubCdcId, c.SubCdcDescription) for c in db.session.query(CdcSub).all()]
    form.function.choices = [(f.FunctionId, f.FunctionDescription) for f in db.session.query(Function).all()]
    form.shift.choices = [(0, _('None'))] + [(s.ShiftId, s.ShiftName) for s in db.session.query(Shift).all()]

    if form.validate_on_submit():
        NeedsService.create_need(
            sub_cdc_id=form.sub_cdc.data,
            function_id=form.function.data,
            required_headcount=form.required_headcount.data,
            min_headcount=form.min_headcount.data,
            shift_id=form.shift.data if form.shift.data != 0 else None,
            effective_from=form.effective_from.data,
            notes=form.notes.data,
            user_id=current_user.UserId
        )
        flash(_('Resource need created successfully.'), 'success')
        return redirect(url_for('needs.detail'))

    return render_template('needs/create.html', form=form, title=_('Create Resource Need'))

@needs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    need = db.session.query(ResourceNeed).get_or_404(id)
    form = ResourceNeedForm(obj=need)
    
    # Populate choices
    form.sub_cdc.choices = [(c.SubCdcId, c.SubCdcDescription) for c in db.session.query(CdcSub).all()]
    form.function.choices = [(f.FunctionId, f.FunctionDescription) for f in db.session.query(Function).all()]
    form.shift.choices = [(0, _('None'))] + [(s.ShiftId, s.ShiftName) for s in db.session.query(Shift).all()]

    if form.validate_on_submit():
        NeedsService.update_need(
            id,
            SubCdcId=form.sub_cdc.data,
            FunctionId=form.function.data,
            ShiftId=form.shift.data if form.shift.data != 0 else None,
            RequiredHeadcount=form.required_headcount.data,
            MinHeadcount=form.min_headcount.data,
            EffectiveFrom=form.effective_from.data,
            Notes=form.notes.data
        )
        flash(_('Resource need updated successfully.'), 'success')
        return redirect(url_for('needs.detail'))

    if request.method == 'GET':
        form.sub_cdc.data = need.SubCdcId
        form.function.data = need.FunctionId
        form.shift.data = need.ShiftId or 0

    return render_template('needs/create.html', form=form, title=_('Edit Resource Need'))

@needs_bp.route('/<int:id>/close', methods=['POST'])
@login_required
def close(id):
    NeedsService.close_need(id)
    flash(_('Resource need closed successfully.'), 'success')
    return redirect(url_for('needs.detail'))

@needs_bp.route('/gap-analysis')
@login_required
def gap_analysis():
    gaps = NeedsService.get_gap_analysis()
    return render_template('needs/gap_analysis.html', gaps=gaps)

@needs_bp.route('/requests')
@login_required
def requests():
    requests = db.session.query(ResourceRequest).order_by(ResourceRequest.RequestedAt.desc()).all()
    return render_template('needs/requests/index.html', requests=requests)

@needs_bp.route('/requests/create', methods=['GET', 'POST'])
@login_required
def create_request():
    form = ResourceRequestForm()
    # Populate choices
    form.sub_cdc.choices = [(c.SubCdcId, c.SubCdcDescription) for c in db.session.query(CdcSub).all()]
    form.function.choices = [(f.FunctionId, f.FunctionDescription) for f in db.session.query(Function).all()]

    if form.validate_on_submit():
        NeedsService.create_request(
            sub_cdc_id=form.sub_cdc.data,
            function_id=form.function.data,
            requested_count=form.requested_count.data,
            priority=form.priority.data,
            reason=form.reason.data,
            user_id=current_user.UserId
        )
        flash(_('Resource request submitted successfully.'), 'success')
        return redirect(url_for('needs.requests'))

    return render_template('needs/requests/create.html', form=form)

@needs_bp.route('/requests/<int:id>/approve', methods=['POST'])
@login_required
def approve_request(id):
    NeedsService.approve_request(id, current_user.UserId)
    flash(_('Request approved.'), 'success')
    return redirect(url_for('needs.requests'))

@needs_bp.route('/requests/<int:id>/reject', methods=['POST'])
@login_required
def reject_request(id):
    NeedsService.reject_request(id, current_user.UserId, request.form.get('notes'))
    flash(_('Request rejected.'), 'warning')
    return redirect(url_for('needs.requests'))

@needs_bp.route('/snapshot', methods=['POST'])
@login_required
def snapshot():
    NeedsService.create_snapshot()
    flash(_('Daily snapshot completed successfully.'), 'success')
    return redirect(url_for('needs.index'))
