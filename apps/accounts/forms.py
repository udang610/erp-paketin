from django import forms
from django.contrib.auth import get_user_model
from apps.accounts.models import Role
from apps.organizations.models import Branch, Department, Position

User = get_user_model()


class UserForm(forms.ModelForm):
    """Simple User-only form (kept for backward compatibility)."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'user_type', 'phone_number', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        if 'is_active' in self.fields:
            self.fields['is_active'].widget.attrs['class'] = 'form-check-input'


class UnifiedUserForm(forms.ModelForm):
    """
    Unified form that creates/edits User + Employee profile + Role assignment in one step.
    Used from the Master > Users/Karyawan menu.
    """
    
    # ─── Account fields ───
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kosongkan jika tidak ingin mengubah',
            'autocomplete': 'new-password',
        }),
        label='Password',
        help_text='Kosongkan jika tidak ingin mengubah password. Default: Paketin123!'
    )
    
    # ─── Branch assignment ───
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cabang Penempatan',
        empty_label='--- Pilih Cabang Penempatan ---',
        help_text='Menentukan cabang penempatan user untuk pembatasan data.'
    )
    
    # ─── Role assignment (Main Role Dropdown) ───
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_preset=True).exclude(name='Superadmin').order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Role / Hak Akses Utama',
        empty_label='--- Pilih Role Utama ---',
        help_text='Pilih role utama pengguna. Hak akses modul akan otomatis disesuaikan.'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'is_active',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username untuk login'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Depan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Belakang'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@paketin.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xx-xxxx-xxxx'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Username',
            'first_name': 'Nama Depan',
            'last_name': 'Nama Belakang',
            'email': 'Email',
            'phone_number': 'Nomor HP',
            'is_active': 'Aktif',
        }

    def __init__(self, *args, **kwargs):
        self.employee_instance = kwargs.pop('employee_instance', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate branch if editing
        if self.employee_instance:
            self.fields['branch'].initial = self.employee_instance.branch
        elif self.instance and self.instance.pk and hasattr(self.instance, 'employee_profile'):
            self.fields['branch'].initial = self.instance.employee_profile.branch
        
        # Pre-populate role field if editing
        if self.instance and self.instance.pk:
            user_roles = self.instance.roles.all()
            preset_role = user_roles.filter(is_preset=True).first() or user_roles.first()
            if preset_role:
                self.fields['role'].initial = preset_role
    
    def save(self, commit=True):
        user = super().save(commit=False)
        is_new = not self.instance.pk or not User.objects.filter(pk=self.instance.pk).exists()
        
        if is_new:
            password = self.cleaned_data.get('password') or 'Paketin123!'
            user.set_password(password)
        elif self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
            
        # Automatically derive user_type from selected role
        primary_role = self.cleaned_data.get('role')
        if primary_role:
            role_to_type = {
                'CS': 'CS',
                'Driver': 'DRIVER',
                'Finance': 'FINANCE',
                'Sales': 'SALES',
                'IT': 'IT',
                'Customer': 'CUSTOMER',
                'HR': 'ADMIN',
                'VM': 'OPS',
                'Supervisor': 'MANAGER',
                'Supervisor Cabang': 'MANAGER',
            }
            user.user_type = role_to_type.get(primary_role.name, 'ADMIN')
        
        if commit:
            user.save()
            
            # Handle role assignment (Main Role)
            if primary_role:
                # Keep custom/extra non-preset roles if any, but replace preset role
                current_custom = list(user.roles.filter(is_preset=False))
                user.roles.set([primary_role] + current_custom)
            
            # Handle employee profile (branch assignment)
            self._save_employee_profile(user)
        
        return user
    
    def _save_employee_profile(self, user):
        from apps.employees.models import Employee
        
        employee = self.employee_instance
        if not employee:
            try:
                employee = user.employee_profile
            except Employee.DoesNotExist:
                employee = None
        
        branch = self.cleaned_data.get('branch')
        if branch or employee:
            if not employee:
                emp_id = f"EMP-{user.username.upper()}"
                employee = Employee(user=user, employee_id=emp_id)
            
            employee.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            employee.phone_number = self.cleaned_data.get('phone_number') or user.phone_number
            employee.branch = branch
            employee.save()
