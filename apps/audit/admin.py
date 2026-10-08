from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'module', 'timestamp', 'ip_address')
    list_filter = ('module', 'action')
    search_fields = ('user__email', 'action', 'object_id')
    readonly_fields = [f.name for f in AuditLog._meta.fields] # Audit logs should be read-only

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
