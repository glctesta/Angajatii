from datetime import date, datetime, timezone
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.needs import ResourceNeed, ResourceNeedSnapshot, ResourceRequest
from app.models.employee import Employee, EmployeeCdcStory, EmployeeHireHistory
from app.models.organization import CostCenter, CdcSub, Function

class NeedsService:
    @staticmethod
    def get_current_headcount(sub_cdc_id, function_id=None):
        """Count active employees in a department/function."""
        query = db.session.query(func.count(EmployeeCdcStory.EmployeeCdcStoryId)).join(
            EmployeeHireHistory, EmployeeCdcStory.EmployeeHireHistoryId == EmployeeHireHistory.EmployeeHireHistoryId
        ).filter(
            EmployeeCdcStory.SubCdcId == sub_cdc_id,
            EmployeeCdcStory.DateOut.is_(None),
            EmployeeHireHistory.EndWorkDate.is_(None)
        )
        if function_id:
            query = query.filter(EmployeeCdcStory.FunctionId == function_id)
        return query.scalar() or 0

    @staticmethod
    def get_all_needs(filters=None):
        query = db.session.query(ResourceNeed).filter(ResourceNeed.EffectiveTo.is_(None))
        
        if filters:
            if filters.get('department'):
                # We join with CdcSub to filter by CostCenter (department)
                query = query.join(CdcSub).filter(CdcSub.CdcId == filters['department'])
            if filters.get('function'):
                query = query.filter(ResourceNeed.FunctionId == filters['function'])
            if filters.get('shift'):
                query = query.filter(ResourceNeed.ShiftId == filters['shift'])
                
        needs = query.all()
        result = []
        for need in needs:
            current = NeedsService.get_current_headcount(need.SubCdcId, need.FunctionId)
            result.append({
                'need': need,
                'sub_cdc': need.sub_cdc,
                'function': need.function,
                'required_count': need.RequiredHeadcount,
                'min_count': need.MinHeadcount,
                'current_count': current,
                'gap': need.RequiredHeadcount - current
            })
        return result

    @staticmethod
    def get_needs_summary_by_department():
        needs = db.session.query(ResourceNeed).filter(ResourceNeed.EffectiveTo.is_(None)).all()
        
        summary = {}
        for need in needs:
            sub_cdc = db.session.query(CdcSub).get(need.SubCdcId)
            cc = sub_cdc.cost_center if sub_cdc else None
            if not cc:
                continue
                
            cc_name = cc.CdcDescription or str(cc.CdcId)
            if cc_name not in summary:
                summary[cc_name] = {'total_required': 0, 'total_min': 0, 'total_current': 0, 'dept_id': cc.CdcId}
                
            summary[cc_name]['total_required'] += need.RequiredHeadcount
            summary[cc_name]['total_min'] += (need.MinHeadcount or 0)
            
            current = NeedsService.get_current_headcount(need.SubCdcId, need.FunctionId)
            summary[cc_name]['total_current'] += current
            
        results = []
        for dept_name, data in summary.items():
            gap = data['total_required'] - data['total_current']
            status = 'ok'
            if data['total_current'] < data['total_min']:
                status = 'critical'
            elif data['total_current'] < data['total_required']:
                status = 'warning'
                
            results.append({
                'department_name': dept_name,
                'department_id': data['dept_id'],
                'total_required': data['total_required'],
                'total_current': data['total_current'],
                'total_gap': gap,
                'status': status
            })
        return results

    @staticmethod
    def create_need(sub_cdc_id, function_id, required_headcount, min_headcount=None, 
                    shift_id=None, effective_from=None, notes=None, user_id=None):
        if not effective_from:
            effective_from = date.today()
            
        need = ResourceNeed(
            SubCdcId=sub_cdc_id,
            FunctionId=function_id,
            ShiftId=shift_id,
            RequiredHeadcount=required_headcount,
            MinHeadcount=min_headcount,
            EffectiveFrom=effective_from,
            Notes=notes,
            CreatedBy=user_id
        )
        db.session.add(need)
        db.session.commit()
        return need

    @staticmethod
    def update_need(need_id, **kwargs):
        need = db.session.query(ResourceNeed).get(need_id)
        if not need:
            return None
            
        for key, value in kwargs.items():
            if hasattr(need, key):
                setattr(need, key, value)
                
        need.UpdatedAt = datetime.now(timezone.utc)
        db.session.commit()
        return need

    @staticmethod
    def close_need(need_id):
        need = db.session.query(ResourceNeed).get(need_id)
        if need:
            need.EffectiveTo = date.today()
            db.session.commit()
        return need

    @staticmethod
    def create_snapshot():
        needs = db.session.query(ResourceNeed).filter(ResourceNeed.EffectiveTo.is_(None)).all()
        today = date.today()
        
        for need in needs:
            current = NeedsService.get_current_headcount(need.SubCdcId, need.FunctionId)
            snapshot = ResourceNeedSnapshot(
                SnapshotDate=today,
                SubCdcId=need.SubCdcId,
                FunctionId=need.FunctionId,
                ShiftId=need.ShiftId,
                RequiredHeadcount=need.RequiredHeadcount,
                CurrentHeadcount=current,
                AvailableCount=current,
                AbsentCount=0
            )
            db.session.add(snapshot)
            
        db.session.commit()

    @staticmethod
    def get_gap_analysis():
        summary = NeedsService.get_needs_summary_by_department()
        gaps = [d for d in summary if d['total_gap'] > 0]
        gaps.sort(key=lambda x: x['total_gap'], reverse=True)
        return gaps

    @staticmethod
    def create_request(sub_cdc_id, function_id, requested_count, priority, reason, user_id):
        req = ResourceRequest(
            SubCdcId=sub_cdc_id,
            FunctionId=function_id,
            RequestedCount=requested_count,
            Priority=priority,
            Reason=reason,
            RequestedBy=user_id
        )
        db.session.add(req)
        db.session.commit()
        return req

    @staticmethod
    def approve_request(request_id, user_id):
        req = db.session.query(ResourceRequest).get(request_id)
        if req:
            req.Status = 'approved'
            req.ApprovedBy = user_id
            req.ApprovedAt = datetime.now(timezone.utc)
            db.session.commit()
        return req

    @staticmethod
    def reject_request(request_id, user_id, notes=None):
        req = db.session.query(ResourceRequest).get(request_id)
        if req:
            req.Status = 'rejected'
            req.Notes = notes
            db.session.commit()
        return req
