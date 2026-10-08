from rest_framework import permissions
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

class IsSuperAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and getattr(request.user, 'is_superuser', False)

@login_required
def api_me(request):
    return JsonResponse({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'is_superuser': request.user.is_superuser,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import UnifiedUserForm
from apps.core.mixins import has_module_access

User = get_user_model()


def _can_manage_users(user):
    """Check if user can access user management."""
    return user.is_superuser or has_module_access(user, 'can_access_admin') or has_module_access(user, 'can_access_hr')


@login_required
def user_list(request):
    if not _can_manage_users(request.user):
        messages.error(request, "Anda tidak memiliki akses ke Manajemen Pengguna.")
        return redirect('dashboard')
    
    users = User.objects.filter(is_superuser=False).exclude(roles__name='Superadmin').prefetch_related('roles').select_related()
    
    # Filters
    user_type = request.GET.get('user_type', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    search_q = request.GET.get('q', '').strip()
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    if search_q:
        from django.db.models import Q
        matched_users = users.filter(
            Q(username__icontains=search_q) |
            Q(first_name__icontains=search_q) |
            Q(last_name__icontains=search_q) |
            Q(email__icontains=search_q) |
            Q(phone_number__icontains=search_q) |
            Q(roles__name__icontains=search_q)
        )
        filtered_users = matched_users
        if user_type:
            filtered_users = filtered_users.filter(user_type=user_type)
        if role_filter:
            filtered_users = filtered_users.filter(roles__name=role_filter)
        if status_filter == 'active':
            filtered_users = filtered_users.filter(is_active=True)
        elif status_filter == 'inactive':
            filtered_users = filtered_users.filter(is_active=False)
            
        date_filtered_users = filtered_users
        if psd:
            date_filtered_users = date_filtered_users.filter(date_joined__date__gte=psd)
        if ped:
            date_filtered_users = date_filtered_users.filter(date_joined__date__lte=ped)
            
        if date_filtered_users.exists():
            users = date_filtered_users
        elif filtered_users.exists():
            users = filtered_users
        else:
            users = matched_users
    else:
        if user_type:
            users = users.filter(user_type=user_type)
        if role_filter:
            users = users.filter(roles__name=role_filter)
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        if psd:
            users = users.filter(date_joined__date__gte=psd)
        if ped:
            users = users.filter(date_joined__date__lte=ped)
    
    users = users.distinct().order_by('-date_joined')
    
    # Get preset roles for filter dropdown (exclude Superadmin)
    from apps.accounts.models import Role
    preset_roles = Role.objects.filter(is_preset=True).exclude(name='Superadmin').order_by('name')
    
    active_filters = bool(user_type or role_filter or status_filter or start_date or end_date)

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'current_type': user_type,
        'current_role': role_filter,
        'current_status': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'search_q': search_q,
        'preset_roles': preset_roles,
        'active_filters': active_filters,
        'user_count': users.count(),
    })

@login_required
def user_create(request):
    if not _can_manage_users(request.user):
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UnifiedUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Pengguna {user.username} berhasil dibuat. Password default: Paketin123!")
            return redirect('accounts:user_list')
    else:
        form = UnifiedUserForm(initial={'user_type': request.GET.get('user_type', 'ADMIN')})
        
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Tambah Pengguna Baru',
        'is_create': True,
    })

@login_required
def user_update(request, user_id):
    if not _can_manage_users(request.user):
        return redirect('dashboard')
        
    user_obj = get_object_or_404(User, id=user_id)
    
    # Get employee instance if exists
    employee_instance = None
    try:
        employee_instance = user_obj.employee_profile
    except Exception:
        pass
    
    if request.method == 'POST':
        form = UnifiedUserForm(request.POST, instance=user_obj, employee_instance=employee_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Data pengguna {user_obj.username} berhasil diperbarui.")
            return redirect('accounts:user_list')
    else:
        form = UnifiedUserForm(instance=user_obj, employee_instance=employee_instance)
        
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': f'Edit Pengguna: {user_obj.username}',
        'is_create': False,
        'user_obj': user_obj,
    })


@login_required
def user_delete(request, user_id):
    """Soft-delete: deactivate user instead of hard delete."""
    if not _can_manage_users(request.user):
        return redirect('dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        if user_obj.is_superuser:
            messages.error(request, "Superadmin tidak bisa dinonaktifkan dari sini.")
        else:
            user_obj.is_active = False
            user_obj.save()
            messages.success(request, f"Pengguna {user_obj.username} berhasil dinonaktifkan.")
    
    return redirect('accounts:user_list')


@login_required
def user_reset_password(request, user_id):
    """Reset user password to default."""
    if not _can_manage_users(request.user):
        return redirect('dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        default_password = 'Paketin123!'
        user_obj.set_password(default_password)
        user_obj.save()
        messages.success(request, f"Password {user_obj.username} berhasil direset ke default (Paketin123!).")
    
    return redirect('accounts:user_list')


@login_required
def api_roles(request):
    """API endpoint to get roles data for dynamic form interactions."""
    from apps.accounts.models import Role
    roles = Role.objects.filter(is_preset=True).values(
        'id', 'name', 'description',
        'can_access_crm', 'can_access_operations', 'can_access_finance',
        'can_access_hr', 'can_access_admin', 'can_access_vm', 'can_access_monitoring',
        'is_branch_scoped',
    )
    return JsonResponse({'roles': list(roles)})
