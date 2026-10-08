import logging
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

def get_role_users(roles):
    """
    Mengambil daftar User yang memiliki role tertentu atau user_type yang sesuai.
    roles: list of string, e.g. ['Finance', 'CS', 'Sales', 'Superadmin', 'HR', 'IT', 'VM', 'Supervisor', 'Driver']
    """
    User = get_user_model()
    if not roles:
        return User.objects.none()
    
    from django.db.models import Q
    role_q = Q(roles__name__in=roles) | Q(is_superuser=True)
    
    # Check user_type matches
    user_type_map = {
        'CS': 'CS',
        'Sales': 'SALES',
        'Finance': 'FINANCE',
        'HR': 'ADMIN',
        'IT': 'IT',
        'Driver': 'DRIVER',
        'Supervisor': 'MANAGER',
    }
    types = [user_type_map[r] for r in roles if r in user_type_map]
    if types:
        role_q |= Q(user_type__in=types)
        
    return User.objects.filter(role_q, is_active=True).distinct()


def record_activity_and_notify(
    title,
    message,
    notification_type,
    actor=None,
    target_roles=None,
    target_users=None,
    url=None,
    obj=None,
    old_value=None,
    new_value=None,
    ip_address=None
):
    """
    Fungsi terpusat untuk mencatat log aktivitas sistem (AuditLog) dan
    mengirimkan notifikasi ke pengguna / role yang relevan.
    """
    # 1. Catat ke AuditLog
    try:
        obj_type = obj.__class__.__name__ if obj else None
        obj_id = str(obj.pk) if obj else None
        AuditLog.objects.create(
            user=actor if actor and actor.is_authenticated else None,
            action=title,
            module=notification_type,
            object_type=obj_type,
            object_id=obj_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
    except Exception as e:
        logger.warning(f"Failed to record AuditLog: {e}")

    # 2. Kumpulkan penerima notifikasi
    recipients = set()
    if target_users:
        for u in target_users:
            if u and u.is_authenticated:
                recipients.add(u)

    if target_roles:
        role_users = get_role_users(target_roles)
        for u in role_users:
            recipients.add(u)

    # Selalu sertakan superadmin jika target roles kosong dan target_users kosong
    if not recipients and not target_users and not target_roles:
        User = get_user_model()
        for u in User.objects.filter(is_superuser=True, is_active=True):
            recipients.add(u)

    # Jangan kirim notifikasi ke actor sendiri jika actor satu-satunya, kecuali diniatkan
    notifications_to_create = []
    for user in recipients:
        notifications_to_create.append(
            Notification(
                user=user,
                actor=actor if actor and actor.is_authenticated else None,
                title=title,
                message=message,
                notification_type=notification_type,
                url=url
            )
        )

    if notifications_to_create:
        try:
            Notification.objects.bulk_create(notifications_to_create)
        except Exception as e:
            logger.warning(f"Failed to bulk_create notifications: {e}")
