from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import AttendancePolicy, AttendanceEvent
from .serializers import AttendancePolicySerializer, AttendanceEventSerializer, AttendanceEventCreateSerializer
from apps.accounts.views import IsSuperAdminOrReadOnly
from apps.employees.models import Employee

class AttendancePolicyViewSet(viewsets.ModelViewSet):
    queryset = AttendancePolicy.objects.all().select_related('branch')
    serializer_class = AttendancePolicySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta

class AttendanceEventViewSet(viewsets.ModelViewSet):
    queryset = AttendanceEvent.objects.all().select_related('employee', 'policy').order_by('-server_timestamp')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceEventCreateSerializer
        return AttendanceEventSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(name='HRGA').exists():
            return super().get_queryset()
        return super().get_queryset().filter(employee__user=user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        try:
            employee = user.employee_profile
        except Employee.DoesNotExist:
            return Response({'hadir': 0, 'terlambat': 0, 'izin': 0, 'chart_data': []})

        now = timezone.now()
        start_of_week = now - timedelta(days=now.weekday())
        
        events = AttendanceEvent.objects.filter(
            employee=employee,
            date__gte=start_of_week.date()
        )
        
        hadir = events.filter(status='PRESENT').count()
        terlambat = events.filter(status='LATE').count()
        izin = events.filter(status='LEAVE').count()

        chart_data = []
        for i in range(7):
            day_date = (start_of_week + timedelta(days=i)).date()
            day_event = events.filter(date=day_date, event_type='CHECK_IN').first()
            if day_event:
                mins = day_event.device_timestamp.hour * 60 + day_event.device_timestamp.minute
                chart_data.append({'day': i, 'minutes': mins})

        return Response({
            'hadir': hadir,
            'terlambat': terlambat,
            'izin': izin,
            'chart_data': chart_data
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Radius check
        lat = serializer.validated_data.get('latitude')
        lng = serializer.validated_data.get('longitude')
        
        notes = serializer.validated_data.get('notes', '').strip()
        is_out_of_radius = False
        is_late = False
        final_status = 'PRESENT'
        
        try:
            employee = self.request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Akun Anda tidak memiliki profil karyawan. Silakan hubungi HR."},
                status=status.HTTP_400_BAD_REQUEST
            )

        policy = AttendancePolicy.objects.filter(branch=employee.branch).first() if employee.branch else None

        if lat and lng and policy:
            if policy.gps_required and policy.allowed_radius_meters > 0:
                import math
                # Use branch coordinates if they exist, otherwise default to Paketin Cargo Jatiwarna
                office_lat = float(employee.branch.latitude) if employee.branch.latitude is not None else -6.3109844
                office_lng = float(employee.branch.longitude) if employee.branch.longitude is not None else 106.9269886
                max_radius = policy.allowed_radius_meters
                
                # Haversine formula
                R = 6371000 # Earth radius in meters
                phi1 = math.radians(office_lat)
                phi2 = math.radians(float(lat))
                delta_phi = math.radians(float(lat) - office_lat)
                delta_lambda = math.radians(float(lng) - office_lng)
                
                a = math.sin(delta_phi / 2.0) ** 2 + \
                    math.cos(phi1) * math.cos(phi2) * \
                    math.sin(delta_lambda / 2.0) ** 2
                
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance = R * c
                
                if distance > max_radius:
                    is_out_of_radius = True
                    final_status = 'PENDING' # Requires approval if outside radius

        if policy and serializer.validated_data.get('event_type') == 'CHECK_IN':
            from datetime import datetime, timedelta
            now = datetime.now()
            check_in_dt = datetime.combine(now.date(), policy.check_in_time)
            threshold_dt = check_in_dt + timedelta(minutes=policy.late_threshold_minutes)
            
            if now > threshold_dt:
                is_late = True
                if final_status != 'PENDING':
                    final_status = 'LATE'

        if (is_out_of_radius or is_late) and not notes:
            reason_msg = "Anda berada di luar radius kantor." if is_out_of_radius else "Anda melewati batas waktu kelonggaran absen."
            return Response(
                {
                    "error_code": "REQUIRES_REASON", 
                    "detail": f"{reason_msg} Silakan berikan alasan Anda."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer.save(employee=employee, status=final_status)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        pass # Logic moved to create

from django.core.paginator import Paginator
from django.db.models import Q
from apps.organizations.models import Branch

@login_required
def attendance_list(request):
    search_q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    event_type_filter = request.GET.get('event_type', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    date_filter = request.GET.get('date', '').strip()

    qs = AttendanceEvent.objects.all().select_related('employee__user', 'employee__branch', 'policy').order_by('-device_timestamp')

    user = request.user
    is_hrga = user.is_superuser or user.roles.filter(name__in=['HRGA', 'ADMIN', 'Superadmin']).exists()
    if not is_hrga:
        if hasattr(user, 'employee_profile'):
            qs = qs.filter(employee=user.employee_profile)
        else:
            qs = qs.none()

    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    pdf = parse_date_safe(date_filter)

    if search_q:
        matched_qs = qs.filter(
            Q(employee__full_name__icontains=search_q) |
            Q(employee__employee_id__icontains=search_q) |
            Q(employee__user__username__icontains=search_q)
        )
        filtered_qs = matched_qs
        if status_filter:
            filtered_qs = filtered_qs.filter(status=status_filter)
        if event_type_filter:
            filtered_qs = filtered_qs.filter(event_type=event_type_filter)
        if branch_filter:
            filtered_qs = filtered_qs.filter(employee__branch_id=branch_filter)
            
        date_filtered_qs = filtered_qs
        if psd:
            date_filtered_qs = date_filtered_qs.filter(device_timestamp__date__gte=psd)
        if ped:
            date_filtered_qs = date_filtered_qs.filter(device_timestamp__date__lte=ped)
        if pdf and not (psd or ped):
            date_filtered_qs = date_filtered_qs.filter(device_timestamp__date=pdf)
            
        if date_filtered_qs.exists():
            qs = date_filtered_qs
        elif filtered_qs.exists():
            qs = filtered_qs
        else:
            qs = matched_qs
    else:
        if status_filter:
            qs = qs.filter(status=status_filter)
        if event_type_filter:
            qs = qs.filter(event_type=event_type_filter)
        if branch_filter:
            qs = qs.filter(employee__branch_id=branch_filter)
        if psd:
            qs = qs.filter(device_timestamp__date__gte=psd)
        if ped:
            qs = qs.filter(device_timestamp__date__lte=ped)
        if pdf and not (psd or ped):
            qs = qs.filter(device_timestamp__date=pdf)

    today = timezone.now().date()
    today_qs = AttendanceEvent.objects.filter(device_timestamp__date=today)
    if not is_hrga and hasattr(user, 'employee_profile'):
        today_qs = today_qs.filter(employee=user.employee_profile)

    stat_total_today = today_qs.count()
    stat_present_today = today_qs.filter(status='PRESENT').count()
    stat_late_today = today_qs.filter(status='LATE').count()
    stat_pending_today = today_qs.filter(status='PENDING').count()

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    branches = Branch.objects.all().order_by('name')
    has_active_filter = bool(status_filter or event_type_filter or branch_filter or date_filter or start_date or end_date)

    context = {
        'events': page_obj,
        'page_obj': page_obj,
        'search_q': search_q,
        'status_filter': status_filter,
        'event_type_filter': event_type_filter,
        'branch_filter': branch_filter,
        'start_date': start_date,
        'end_date': end_date,
        'date_filter': date_filter,
        'has_active_filter': has_active_filter,
        'stat_total_today': stat_total_today,
        'stat_present_today': stat_present_today,
        'stat_late_today': stat_late_today,
        'stat_pending_today': stat_pending_today,
        'branches': branches,
        'total_count': qs.count(),
        'is_hrga': is_hrga,
    }
    return render(request, 'hrga/attendance/attendance_list.html', context)

@login_required
def attendance_policy_list(request):
    if not (request.user.is_superuser or request.user.roles.filter(name='HRGA').exists()):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('core:dashboard')
        
    search_q = request.GET.get('q', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    work_mode_filter = request.GET.get('work_mode', '').strip()
    
    policies = AttendancePolicy.objects.all().select_related('branch').order_by('name')
    if search_q:
        policies = policies.filter(Q(name__icontains=search_q) | Q(branch__name__icontains=search_q))
    if branch_filter:
        policies = policies.filter(branch_id=branch_filter)
    if work_mode_filter:
        policies = policies.filter(work_mode=work_mode_filter)

    branches = Branch.objects.all().order_by('name')
    has_active_filter = bool(branch_filter or work_mode_filter)

    context = {
        'policies': policies,
        'search_q': search_q,
        'branch_filter': branch_filter,
        'work_mode_filter': work_mode_filter,
        'branches': branches,
        'has_active_filter': has_active_filter,
    }
    return render(request, 'hrga/attendance_policy/attendance_policy_list.html', context)

@login_required
def attendance_policy_edit(request, pk=None):
    if not (request.user.is_superuser or request.user.roles.filter(name='HRGA').exists()):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('core:dashboard')
        
    from .forms import AttendancePolicyForm
    
    if pk:
        policy = get_object_or_404(AttendancePolicy, pk=pk)
    else:
        policy = None
        
    if request.method == 'POST':
        form = AttendancePolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kebijakan absensi berhasil disimpan.')
            return redirect('attendance:policy_list')
    else:
        form = AttendancePolicyForm(instance=policy)
        
    context = {
        'form': form,
        'title': 'Edit Kebijakan' if pk else 'Tambah Kebijakan'
    }
    return render(request, 'hrga/attendance_policy/attendance_policy_edit.html', context)
