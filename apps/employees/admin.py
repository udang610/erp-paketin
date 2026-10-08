from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Employee, RegisteredDevice, FaceProfile


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ('full_name', 'employee_id', 'branch', 'department', 'position', 'display_status')
    list_filter = ('branch', 'department', 'status')
    search_fields = ('full_name', 'employee_id', 'user__email')

    @display(description="Status Pegawai", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(RegisteredDevice)
class RegisteredDeviceAdmin(ModelAdmin):
    list_display = ('employee', 'device_model', 'platform', 'display_active', 'last_active')
    list_filter = ('platform', 'is_active')
    search_fields = ('employee__full_name', 'device_model', 'device_id')

    @display(description="Status", label=True)
    def display_active(self, obj):
        return "Aktif" if obj.is_active else "Dicabut"


@admin.register(FaceProfile)
class FaceProfileAdmin(ModelAdmin):
    list_display = ('employee', 'display_active', 'enrolled_at')
    search_fields = ('employee__full_name',)

    @display(description="Status", label=True)
    def display_active(self, obj):
        return "Terdaftar" if obj.is_active else "Nonaktif"
