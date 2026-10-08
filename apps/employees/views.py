import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Employee, RegisteredDevice, FaceProfile
from .serializers import EmployeeSerializer, RegisteredDeviceSerializer, FaceProfileSerializer
from .forms import EmployeeForm
from apps.accounts.views import IsSuperAdminOrReadOnly
from django.contrib.auth import get_user_model

User = get_user_model()


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().select_related('user', 'branch', 'department', 'position', 'supervisor')
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(name='HR').exists() or user.roles.filter(name='HRGA').exists():
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        employee = Employee.objects.filter(user=request.user).first()
        if not employee:
            user = request.user
            name = f"{user.first_name} {user.last_name}".strip() or user.username
            return Response({
                'full_name': name,
                'email': user.email,
                'is_fallback': True
            })
            
        if request.method == 'PATCH':
            serializer = self.get_serializer(employee, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
            
        serializer = self.get_serializer(employee)
        return Response(serializer.data)


class RegisteredDeviceViewSet(viewsets.ModelViewSet):
    queryset = RegisteredDevice.objects.all().select_related('employee')
    serializer_class = RegisteredDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]


class FaceProfileViewSet(viewsets.ModelViewSet):
    queryset = FaceProfile.objects.all().select_related('employee')
    serializer_class = FaceProfileSerializer
    permission_classes = [IsSuperAdminOrReadOnly]


# ─── Web Views (HR Module) ───

@login_required
def employee_list(request):
    """Operational style Employee List for HR Module."""
    search_q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    employees = Employee.objects.all().select_related('user', 'branch', 'department', 'position').order_by('-created_at')
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    if search_q:
        matched_emp = employees.filter(
            Q(full_name__icontains=search_q) |
            Q(employee_id__icontains=search_q) |
            Q(user__username__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(phone_number__icontains=search_q)
        )
        filtered_emp = matched_emp
        if status_filter:
            filtered_emp = filtered_emp.filter(status=status_filter)
        if branch_filter:
            filtered_emp = filtered_emp.filter(branch_id=branch_filter)
            
        date_filtered_emp = filtered_emp
        if psd:
            date_filtered_emp = date_filtered_emp.filter(Q(join_date__gte=psd) | Q(join_date__isnull=True, created_at__date__gte=psd))
        if ped:
            date_filtered_emp = date_filtered_emp.filter(Q(join_date__lte=ped) | Q(join_date__isnull=True, created_at__date__lte=ped))
            
        if date_filtered_emp.exists():
            employees = date_filtered_emp
        elif filtered_emp.exists():
            employees = filtered_emp
        else:
            employees = matched_emp
    else:
        if status_filter:
            employees = employees.filter(status=status_filter)
        if branch_filter:
            employees = employees.filter(branch_id=branch_filter)
        if psd:
            employees = employees.filter(Q(join_date__gte=psd) | Q(join_date__isnull=True, created_at__date__gte=psd))
        if ped:
            employees = employees.filter(Q(join_date__lte=ped) | Q(join_date__isnull=True, created_at__date__lte=ped))
        
    from apps.organizations.models import Branch
    branches = Branch.objects.all().order_by('name')
    
    base_qs = Employee.objects.all()
    stat_total = base_qs.count()
    stat_permanent = base_qs.filter(status='PERMANENT').count()
    stat_contract = base_qs.filter(status='CONTRACT').count()
    stat_probation = base_qs.filter(status='PROBATION').count()

    has_active_filter = bool(status_filter or branch_filter or start_date or end_date)

    context = {
        'employees': employees,
        'search_q': search_q,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'start_date': start_date,
        'end_date': end_date,
        'has_active_filter': has_active_filter,
        'branches': branches,
        'stat_total': stat_total,
        'stat_permanent': stat_permanent,
        'stat_contract': stat_contract,
        'stat_probation': stat_probation,
    }
    return render(request, 'hrga/employees/employee_list.html', context)


@login_required
def employee_create(request):
    """HR Employee Create View with User select & auto-fill."""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            emp = form.save()
            messages.success(request, f"Data pegawai '{emp.full_name}' ({emp.employee_id}) berhasil ditambahkan.")
            return redirect('employees:employee_list')
        else:
            messages.error(request, "Terdapat kesalahan pengisian form. Silakan periksa kembali.")
    else:
        # Pre-select user if user_id passed in GET query
        initial = {}
        user_id = request.GET.get('user_id')
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                initial['user'] = user
                initial['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
                initial['phone_number'] = user.phone_number
                initial['employee_id'] = f"EMP-{user.username.upper()}"
            except User.DoesNotExist:
                pass
        form = EmployeeForm(initial=initial)
        
    # Build users JSON data for auto-fill on user dropdown change (like customer in POS)
    users = User.objects.filter(is_superuser=False).prefetch_related('roles')
    users_data = {}
    for u in users:
        branch_id = ''
        if hasattr(u, 'employee_profile') and u.employee_profile and u.employee_profile.branch_id:
            branch_id = str(u.employee_profile.branch_id)
        role_name = u.roles.first().name if u.roles.exists() else ''
        users_data[str(u.id)] = {
            'username': u.username,
            'full_name': f"{u.first_name} {u.last_name}".strip() or u.username,
            'email': u.email,
            'phone_number': u.phone_number or '',
            'branch_id': branch_id,
            'role_name': role_name,
            'suggested_nip': f"EMP-{u.username.upper()}"
        }

    return render(request, 'hrga/employees/employee_edit.html', {
        'form': form,
        'is_create': True,
        'title': 'Tambah Data Pegawai',
        'users_json': json.dumps(users_data),
    })


@login_required
def employee_update(request, pk):
    """HR Employee Update View."""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            emp = form.save()
            messages.success(request, f"Data pegawai '{emp.full_name}' berhasil diperbarui.")
            return redirect('employees:employee_list')
        else:
            messages.error(request, "Terdapat kesalahan pengisian form. Silakan periksa kembali.")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'hrga/employees/employee_edit.html', {
        'form': form,
        'employee': employee,
        'is_create': False,
        'title': f"Edit Pegawai: {employee.full_name}",
        'users_json': '{}',
    })


@login_required
def employee_detail(request, pk):
    """HR Employee Detail View."""
    employee = get_object_or_404(Employee.objects.select_related('user', 'branch', 'department', 'position', 'supervisor'), pk=pk)
    return render(request, 'hrga/employees/employee_detail.html', {
        'employee': employee,
    })


@login_required
def employee_delete(request, pk):
    """Delete employee profile."""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        name = employee.full_name
        employee.delete()
        messages.success(request, f"Data pegawai '{name}' berhasil dihapus.")
        return redirect('employees:employee_list')
    return redirect('employees:employee_list')


@login_required
def get_user_info(request, user_id):
    """AJAX endpoint to get user info for auto-filling."""
    try:
        user = User.objects.get(pk=user_id)
        role_name = user.roles.first().name if user.roles.exists() else ''
        branch_id = ''
        if hasattr(user, 'employee_profile') and user.employee_profile and user.employee_profile.branch_id:
            branch_id = str(user.employee_profile.branch_id)
            
        return JsonResponse({
            'status': 'success',
            'data': {
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
                'phone_number': user.phone_number or '',
                'branch_id': branch_id,
                'role_name': role_name,
                'suggested_nip': f"EMP-{user.username.upper()}"
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User tidak ditemukan'}, status=404)
