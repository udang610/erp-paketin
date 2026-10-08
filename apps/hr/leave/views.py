from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LeaveType, LeaveBalance, LeaveRequest, LeaveRequestStatus
from .serializers import (
    LeaveTypeSerializer, LeaveBalanceSerializer, 
    LeaveRequestSerializer, LeaveRequestCreateSerializer
)
from apps.accounts.views import IsSuperAdminOrReadOnly
from apps.employees.models import Employee

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all().select_related('employee', 'leave_type')
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(name='HRGA').exists():
            return super().get_queryset()
        return super().get_queryset().filter(employee__user=user)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().select_related('employee', 'leave_type').order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(name='HRGA').exists():
            return super().get_queryset()
        return super().get_queryset().filter(employee__user=user)

    def perform_create(self, serializer):
        try:
            employee = self.request.user.employee_profile
        except Employee.DoesNotExist:
            employee = None
        serializer.save(employee=employee)

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        user = request.user
        
        # Determine if user is HRGA or Supervisor (for now, HRGA can approve anything)
        if not (user.is_superuser or user.roles.filter(name='HRGA').exists()):
            return Response({'detail': 'Not authorized to approve.'}, status=status.HTTP_403_FORBIDDEN)
            
        leave_request.status = 'APPROVED'
        leave_request.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        user = request.user
        
        if not (user.is_superuser or user.roles.filter(name='HRGA').exists()):
            return Response({'detail': 'Not authorized to reject.'}, status=status.HTTP_403_FORBIDDEN)
            
        leave_request.status = 'REJECTED'
        leave_request.save()
        return Response({'status': 'rejected'})

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect

@login_required
def leave_list(request):
    user = request.user
    is_hrga = user.is_superuser or user.roles.filter(name__in=['HRGA', 'ADMIN', 'Superadmin']).exists()

    if request.method == 'POST' and is_hrga:
        action = request.POST.get('action')
        leave_id = request.POST.get('leave_id')
        if leave_id and action in ['approve', 'reject']:
            target_leave = LeaveRequest.objects.filter(id=leave_id).first()
            if target_leave:
                if action == 'approve':
                    target_leave.status = LeaveRequestStatus.APPROVED
                    target_leave.save()
                    messages.success(request, f'Pengajuan cuti untuk {target_leave.employee.full_name} berhasil disetujui.')
                elif action == 'reject':
                    target_leave.status = LeaveRequestStatus.REJECTED
                    target_leave.save()
                    messages.warning(request, f'Pengajuan cuti untuk {target_leave.employee.full_name} telah ditolak.')
            return redirect('leave:leave_list')

    search_q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    qs = LeaveRequest.objects.all().select_related('employee__user', 'employee__branch', 'leave_type').order_by('-created_at')

    if not is_hrga:
        if hasattr(user, 'employee_profile'):
            qs = qs.filter(employee=user.employee_profile)
        else:
            qs = qs.none()

    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)

    if search_q:
        matched_qs = qs.filter(
            Q(employee__full_name__icontains=search_q) |
            Q(employee__employee_id__icontains=search_q) |
            Q(reason__icontains=search_q)
        )
        filtered_qs = matched_qs
        if status_filter:
            filtered_qs = filtered_qs.filter(status=status_filter)
        if type_filter:
            filtered_qs = filtered_qs.filter(leave_type_id=type_filter)
            
        date_filtered_qs = filtered_qs
        if psd:
            date_filtered_qs = date_filtered_qs.filter(start_date__gte=psd)
        if ped:
            date_filtered_qs = date_filtered_qs.filter(end_date__lte=ped)
            
        if date_filtered_qs.exists():
            qs = date_filtered_qs
        elif filtered_qs.exists():
            qs = filtered_qs
        else:
            qs = matched_qs
    else:
        if status_filter:
            qs = qs.filter(status=status_filter)
        if type_filter:
            qs = qs.filter(leave_type_id=type_filter)
        if psd:
            qs = qs.filter(start_date__gte=psd)
        if ped:
            qs = qs.filter(end_date__lte=ped)

    base_qs = LeaveRequest.objects.all()
    if not is_hrga and hasattr(user, 'employee_profile'):
        base_qs = base_qs.filter(employee=user.employee_profile)

    stat_total = base_qs.count()
    stat_pending = base_qs.filter(status__in=[LeaveRequestStatus.PENDING_SUPERVISOR, LeaveRequestStatus.PENDING_HRGA]).count()
    stat_approved = base_qs.filter(status=LeaveRequestStatus.APPROVED).count()
    stat_rejected = base_qs.filter(status=LeaveRequestStatus.REJECTED).count()

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    leave_types = LeaveType.objects.all().order_by('name')
    has_active_filter = bool(status_filter or type_filter or start_date or end_date)

    context = {
        'leaves': page_obj,
        'page_obj': page_obj,
        'search_q': search_q,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'start_date': start_date,
        'end_date': end_date,
        'has_active_filter': has_active_filter,
        'stat_total': stat_total,
        'stat_pending': stat_pending,
        'stat_approved': stat_approved,
        'stat_rejected': stat_rejected,
        'leave_types': leave_types,
        'is_hrga': is_hrga,
        'total_count': qs.count(),
    }
    return render(request, 'hrga/leave/leave_list.html', context)
