import json
from flask import request
from app.extensions import db
from app.models.audit import AuditLog

def log_action(user_id, action, module, entity_type=None, entity_id=None, old_values=None, new_values=None):
    ip_address = request.remote_addr if request else None
    user_agent = request.user_agent.string if request and request.user_agent else None
    
    if isinstance(old_values, dict):
        old_values = json.dumps(old_values)
    if isinstance(new_values, dict):
        new_values = json.dumps(new_values)
        
    audit_log = AuditLog(
        UserId=user_id,
        Action=action,
        Module=module,
        EntityType=entity_type,
        EntityId=entity_id,
        OldValues=old_values,
        NewValues=new_values,
        IpAddress=ip_address,
        UserAgent=user_agent
    )
    db.session.add(audit_log)
    db.session.commit()
