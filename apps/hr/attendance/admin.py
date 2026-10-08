from django.contrib import admin
from .models import AttendancePolicy, AttendanceEvent

@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'work_mode', 'check_in_time', 'check_out_time')
    list_filter = ('work_mode', 'branch')
    search_fields = ('name',)

@admin.register(AttendanceEvent)
class AttendanceEventAdmin(admin.ModelAdmin):
    list_display = ('employee', 'event_type', 'status', 'server_timestamp', 'face_verified')
    list_filter = ('event_type', 'status', 'face_verified', 'is_mock_location')
    search_fields = ('employee__full_name', 'employee__employee_id')
    date_hierarchy = 'server_timestamp'
