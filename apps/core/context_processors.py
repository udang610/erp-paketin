from django.db.models import Q
from .mixins import has_module_access, get_user_branch, is_branch_scoped

def erp_context(request):
    """Adds module access flags, menu visibility settings, notifications, and branch to every template context."""
    if request.user.is_authenticated:
        from apps.accounts.models import MenuVisibilitySetting
        menu_vis = MenuVisibilitySetting.get_visibility_map(request.user)

        action_alerts = []
        pending_do_balik_count = 0

        if (request.user.is_superuser or has_module_access(request.user, 'can_access_operations')) and menu_vis.get('module_operations', True):
            from datetime import timedelta
            from django.utils import timezone
            from apps.operations.models import Shipment

            now = timezone.now()
            base_shipments = Shipment.objects.filter(is_hidden=False)
            if hasattr(request.user, 'user_type') and request.user.user_type == 'CUSTOMER':
                base_shipments = base_shipments.filter(created_by=request.user)

            action_alerts = [
                {
                    'label': 'Shipment menunggu proses',
                    'description': 'Periksa resi yang belum masuk alur operasional.',
                    'count': base_shipments.filter(status='PENDING').count(),
                    'tone': 'warning',
                    'icon': 'ph-hourglass-medium',
                    'url': '/operations/shipments/?status=PENDING',
                },
                {
                    'label': 'Transit lebih dari 48 jam',
                    'description': 'Pastikan status dan lokasi terakhir sudah diperbarui.',
                    'count': base_shipments.filter(status='TRANSIT', updated_at__lt=now - timedelta(hours=48)).count(),
                    'tone': 'danger',
                    'icon': 'ph-warning-circle',
                    'url': '/operations/shipments/?status=TRANSIT',
                },
                {
                    'label': 'Menunggu incoming destination',
                    'description': 'Resi siap diproses oleh hub tujuan.',
                    'count': base_shipments.filter(status='INCOMING_DESTINATION').count(),
                    'tone': 'info',
                    'icon': 'ph-map-pin-line',
                    'url': '/operations/shipments/?status=INCOMING_DESTINATION',
                },
                {
                    'label': 'Transfer location aktif',
                    'description': 'Pantau perpindahan antar lokasi dan hub.',
                    'count': base_shipments.filter(status='TRANSFER').count(),
                    'tone': 'neutral',
                    'icon': 'ph-arrows-left-right',
                    'url': '/operations/shipments/?status=TRANSFER',
                },
            ]
            action_alerts = [item for item in action_alerts if item['count']]

            # Count of pending DO Balik awaiting return
            pending_do_balik_count = base_shipments.filter(
                Q(with_do_balik=True) | Q(client__with_pod_resi=True),
                status='POD',
                do_balik_date__isnull=True
            ).count()

        unread_notifications = request.user.notifications.filter(is_read=False).count() if hasattr(request.user, 'notifications') else 0
        recent_notifications = request.user.notifications.select_related('actor').all().order_by('-created_at')[:6] if hasattr(request.user, 'notifications') else []

        return {
            'menu_vis': menu_vis,
            'can_access_crm': has_module_access(request.user, 'can_access_crm') and menu_vis.get('module_crm', True),
            'can_access_operations': has_module_access(request.user, 'can_access_operations') and menu_vis.get('module_operations', True),
            'can_access_finance': has_module_access(request.user, 'can_access_finance') and menu_vis.get('module_finance', True),
            'can_access_hr': has_module_access(request.user, 'can_access_hr') and menu_vis.get('module_hr', True),
            'can_access_admin': has_module_access(request.user, 'can_access_admin') and menu_vis.get('module_admin', True),
            'can_access_vm': has_module_access(request.user, 'can_access_vm') and menu_vis.get('module_vm', True),
            'can_access_master': (has_module_access(request.user, 'can_access_admin') or request.user.is_superuser) and menu_vis.get('module_master', True),
            'can_access_monitoring': has_module_access(request.user, 'can_access_monitoring'),
            'is_admin': has_module_access(request.user, 'can_access_admin') and menu_vis.get('module_admin', True),
            'is_branch_scoped': is_branch_scoped(request.user),
            'user_branch': get_user_branch(request.user),
            'unread_notifications': unread_notifications,
            'recent_notifications': recent_notifications,
            'action_alerts': action_alerts,
            'action_alert_count': len(action_alerts),
            'pending_do_balik_count': pending_do_balik_count,
        }
    return {}
