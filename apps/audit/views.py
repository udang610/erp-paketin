from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.accounts.views import IsSuperAdminOrReadOnly

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

@login_required
def audit_list(request):
    logs = AuditLog.objects.all().select_related('user')[:100]
    return render(request, 'audit/audit_list.html', {'logs': logs})
