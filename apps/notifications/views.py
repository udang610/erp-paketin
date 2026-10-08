from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework import viewsets, permissions, mixins
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from apps.audit.models import AuditLog


# ─────────────────────────────────────────────────────────────
# WEB VIEWS (ERP UI)
# ─────────────────────────────────────────────────────────────

@login_required
def notification_list_view(request):
    """Halaman Pusat Notifikasi & Log Aktivitas Sistem untuk Pengguna & Role."""
    notif_type = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')  # unread / all
    q = request.GET.get('q', '')

    notifications_qs = Notification.objects.filter(user=request.user).select_related('actor')

    if notif_type:
        notifications_qs = notifications_qs.filter(notification_type=notif_type)

    if status_filter == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)

    if q:
        notifications_qs = notifications_qs.filter(title__icontains=q) | notifications_qs.filter(message__icontains=q)

    paginator = Paginator(notifications_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Activity Audit Logs for Superadmin/Admins
    recent_audit_logs = []
    if request.user.is_superuser or (hasattr(request.user, 'user_type') and request.user.user_type in ['ADMIN', 'MANAGER']):
        recent_audit_logs = AuditLog.objects.select_related('user').all()[:15]

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'page_obj': page_obj,
        'notifications': page_obj,
        'unread_count': unread_count,
        'selected_type': notif_type,
        'status_filter': status_filter,
        'search_query': q,
        'type_choices': Notification.NotificationType.choices,
        'recent_audit_logs': recent_audit_logs,
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_as_read_view(request, pk):
    """Tandai 1 notifikasi sebagai sudah dibaca, lalu arahkan ke link tujuannya jika ada."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.read_at = timezone.now()
    notif.save(update_fields=['is_read', 'read_at'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'ok', 'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()})

    if notif.url:
        return redirect(notif.url)
    return redirect('notifications:message-list')


@login_required
def mark_all_read_view(request):
    """Tandai seluruh notifikasi user sebagai sudah dibaca."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'unread_count': 0})

    return redirect(request.META.get('HTTP_REFERER', 'notifications:message-list'))


# ─────────────────────────────────────────────────────────────
# REST API (Mobile / Frontend)
# ─────────────────────────────────────────────────────────────

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationPreferenceViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj
