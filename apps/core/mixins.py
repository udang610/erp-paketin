from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def has_module_access(user, module_flag):
    """Check if user has access to a specific module via their roles."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    
    # User might have multiple roles
    if hasattr(user, 'roles'):
        for role in user.roles.all():
            if getattr(role, module_flag, False):
                return True
    return False


def is_admin(user):
    """Check if user is superuser or has admin module access."""
    return has_module_access(user, 'can_access_admin')


def is_branch_scoped(user):
    """Check if user's access is scoped to their own branch only."""
    if not user.is_authenticated or user.is_superuser:
        return False
    if hasattr(user, 'roles'):
        return user.roles.filter(is_branch_scoped=True).exists()
    return False


def get_user_branch(user):
    """Get the branch for a user from their employee profile, or None."""
    try:
        if hasattr(user, 'employee_profile') and user.employee_profile.branch:
            return user.employee_profile.branch
    except Exception:
        pass
    return None


def apply_branch_filter(queryset, user, branch_field='branch'):
    """
    Apply branch scoping to a queryset if the user is branch-scoped.
    Returns the original queryset for superusers and non-branch-scoped users.
    """
    if not user.is_authenticated or user.is_superuser:
        return queryset
    if is_branch_scoped(user):
        branch = get_user_branch(user)
        if branch:
            return queryset.filter(**{branch_field: branch})
        # If branch-scoped but no branch set, show nothing
        return queryset.none()
    return queryset


class ModuleAccessRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Base mixin to require access to a specific module.
    Override `required_module_flag` in subclasses.
    """
    required_module_flag = None

    def test_func(self):
        if not self.required_module_flag:
            return True
        return has_module_access(self.request.user, self.required_module_flag)

    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        msg = f"Anda tidak memiliki izin untuk mengakses modul ini."
        storage = messages.get_messages(self.request)
        if not any(m.message == msg for m in storage):
            messages.error(self.request, msg)
        storage.used = False
        return redirect('/')


class CRMRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_crm'

class OperationsRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_operations'

class FinanceRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_finance'

class HRRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_hr'

class AdminRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_admin'

class VMRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_vm'

class MonitoringRequiredMixin(ModuleAccessRequiredMixin):
    required_module_flag = 'can_access_monitoring'


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Mixin that filters querysets by the logged-in user (owner field).
    - Admins see all data.
    - Others see their own data, or depending on future branch logic.
    """
    owner_field = 'owner'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if is_admin(user):
            return qs

        # Add more logic here for supervisors or branch heads as needed

        # Default: only see own data
        return qs.filter(**{self.owner_field: user})


class OwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to verify the current user is the owner of the object,
    in the same branch (if Kepala Cabang), or an admin.
    """
    owner_field = 'owner'

    def test_func(self):
        user = self.request.user
        if is_admin(user):
            return True
            
        obj = self.get_object()
        owner = getattr(obj, self.owner_field)

        # Same user
        if owner == user:
            return True

        return False

    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        msg = "Anda tidak memiliki hak akses untuk mengedit atau melihat data ini."
        storage = messages.get_messages(self.request)
        if not any(m.message == msg for m in storage):
            messages.error(self.request, msg)
        storage.used = False
        return redirect('/')


class AdminOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)

    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        msg = "Hanya Admin yang dapat mengakses fitur ini."
        storage = messages.get_messages(self.request)
        if not any(m.message == msg for m in storage):
            messages.error(self.request, msg)
        storage.used = False
        return redirect('/')


class SetOwnerMixin:
    """
    Automatically set the owner field to the current user on form save.
    """
    owner_field = 'owner'

    def form_valid(self, form):
        if not getattr(form.instance, self.owner_field + '_id', None):
            setattr(form.instance, self.owner_field, self.request.user)
        return super().form_valid(form)


class BranchScopedMixin(LoginRequiredMixin):
    """
    Mixin that automatically scopes querysets to the user's branch
    if the user has a branch-scoped role.
    Admins and non-branch-scoped users see all data.
    """
    branch_field = 'branch'

    def get_queryset(self):
        qs = super().get_queryset()
        return apply_branch_filter(qs, self.request.user, self.branch_field)
