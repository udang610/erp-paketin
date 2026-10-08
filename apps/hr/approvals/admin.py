from django.contrib import admin
from .models import ApprovalFlow, ApprovalStep, ApprovalRequest, ApprovalAction

class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 1

@admin.register(ApprovalFlow)
class ApprovalFlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    inlines = [ApprovalStepInline]

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'flow', 'content_type', 'current_step_order', 'status')
    list_filter = ('status', 'flow')
    search_fields = ('requester__full_name',)

@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ('request', 'step', 'actor', 'action', 'created_at')
    list_filter = ('action',)
