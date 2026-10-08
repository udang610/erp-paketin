from apps.audit.models import AuditLog

def log_action(user, action, module, obj=None, old_val=None, new_val=None, ip=None):
    obj_type = obj.__class__.__name__ if obj else None
    obj_id = str(obj.pk) if obj else None
    
    # Avoid logging if user is missing and it's required (though it's nullable)
    # user can be None for system actions
    
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        module=module,
        object_type=obj_type,
        object_id=obj_id,
        old_value=old_val,
        new_value=new_val,
        ip_address=ip
    )
