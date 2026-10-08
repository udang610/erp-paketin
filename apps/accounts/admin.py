from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import display
from .models import User, Role, MenuPermission


@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = (
        'name', 'display_preset_badge',
        'can_access_crm', 'can_access_operations', 'can_access_finance',
        'can_access_hr', 'can_access_vm', 'can_access_monitoring', 'can_access_admin',
        'is_branch_scoped',
    )
    list_filter = ('is_preset', 'can_access_admin', 'is_branch_scoped')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_preset')}),
        ('Akses Modul Bawaan', {
            'fields': (
                'can_access_crm', 'can_access_operations', 'can_access_finance',
                'can_access_hr', 'can_access_vm', 'can_access_monitoring', 'can_access_admin',
            ),
            'description': 'Centang modul yang otomatis terbuka untuk role ini.',
        }),
        ('Pembatasan & Scope', {
            'fields': ('is_branch_scoped',),
            'description': 'Pengaturan pembatasan akses data per-cabang.',
        }),
        ('Informasi Sistem', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @display(description="Tipe Role", label=True)
    def display_preset_badge(self, obj):
        if obj.is_preset:
            return "Preset Bawaan"
        return "Custom"

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_preset:
            return False
        return super().has_delete_permission(request, obj)


class EmployeeInline(StackedInline):
    """Inline Employee profile in User admin."""
    model = None
    can_delete = False
    verbose_name_plural = 'Profil Karyawan'
    fk_name = 'user'
    extra = 0
    
    def get_model(self):
        if self.model is None:
            from apps.employees.models import Employee
            EmployeeInline.model = Employee
        return self.model
    
    fields = ('employee_id', 'full_name', 'branch', 'department', 'position', 'status', 'join_date')


# Dynamically set the inline model
try:
    from apps.employees.models import Employee
    EmployeeInline.model = Employee
except Exception:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ('username', 'email', 'get_full_name_display', 'user_type', 'display_roles', 'display_status', 'is_staff')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'roles')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    filter_horizontal = ('roles', 'extra_permissions', 'groups', 'user_permissions')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informasi Pribadi', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Kategori & Hak Akses', {
            'fields': ('user_type', 'is_employee', 'roles', 'extra_permissions'),
            'description': 'Pilih Role utama. Tambahkan Extra Permissions untuk custom override hak akses fitur.',
        }),
        ('Hak Akses Django Admin', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Riwayat Aktivitas', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_type', 'roles'),
        }),
    )
    
    inlines = []
    
    def get_inlines(self, request, obj=None):
        if EmployeeInline.model is not None:
            return [EmployeeInline]
        return []

    @display(description="Nama Lengkap")
    def get_full_name_display(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else "-"

    @display(description="Role Terpasang", label=True)
    def display_roles(self, obj):
        roles = [r.name for r in obj.roles.all()]
        return ", ".join(roles) if roles else "Tanpa Role"

    @display(description="Status", label=True)
    def display_status(self, obj):
        return "Aktif" if obj.is_active else "Nonaktif"


@admin.register(MenuPermission)
class MenuPermissionAdmin(ModelAdmin):
    list_display = ('codename', 'name', 'module', 'roles_count')
    list_filter = ('module',)
    search_fields = ('codename', 'name')
    filter_horizontal = ('roles',)

    @display(description="Jumlah Role Terhubung")
    def roles_count(self, obj):
        return obj.roles.count()


from .models import MenuVisibilitySetting

@admin.register(MenuVisibilitySetting)
class MenuVisibilitySettingAdmin(ModelAdmin):
    list_display = ('name', 'code', 'module_category', 'display_type', 'is_visible', 'display_hidden_roles')
    list_editable = ('is_visible',)
    list_filter = ('module_category', 'is_module_header', 'is_visible')
    search_fields = ('name', 'code')
    filter_horizontal = ('hidden_for_roles',)
    actions = ['make_visible', 'make_hidden']
    ordering = ('module_category', 'sort_order', 'code')

    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'module_category', 'is_module_header', 'sort_order')
        }),
        ('Pengaturan Visibilitas', {
            'fields': ('is_visible', 'hidden_for_roles'),
            'description': 'Centang "Status Tampil" agar menu muncul. Hapus centang untuk menyembunyikan secara global. Anda juga dapat memilih role tertentu untuk disembunyikan.',
        }),
    )

    @display(description="Tipe", label=True)
    def display_type(self, obj):
        return "Header Modul" if obj.is_module_header else "Submenu Item"

    @display(description="Role Tersembunyi")
    def display_hidden_roles(self, obj):
        roles = [r.name for r in obj.hidden_for_roles.all()]
        return ", ".join(roles) if roles else "-"

    @admin.action(description="Tampilkan Menu/Modul Terpilih")
    def make_visible(self, request, queryset):
        count = queryset.update(is_visible=True)
        self.message_user(request, f"{count} menu/modul berhasil diaktifkan (tampil).")

    @admin.action(description="Sembunyikan (Hide) Menu/Modul Terpilih")
    def make_hidden(self, request, queryset):
        count = queryset.update(is_visible=False)
        self.message_user(request, f"{count} menu/modul berhasil disembunyikan.")

