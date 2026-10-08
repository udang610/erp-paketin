from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Branch, Department, Position


@admin.register(Branch)
class BranchAdmin(ModelAdmin):
    list_display = ('name', 'code', 'timezone', 'display_warehouse')
    search_fields = ('name', 'code', 'address')
    list_filter = ('has_warehouse', 'timezone')

    @display(description="Gudang Operasional", label=True)
    def display_warehouse(self, obj):
        return "Ada Gudang" if obj.has_warehouse else "Tanpa Gudang"


@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ('name', 'branch')
    list_filter = ('branch',)
    search_fields = ('name', 'branch__name', 'branch__code')


@admin.register(Position)
class PositionAdmin(ModelAdmin):
    list_display = ('name', 'department', 'get_branch')
    list_filter = ('department__branch', 'department')
    search_fields = ('name', 'department__name')

    @display(description="Cabang")
    def get_branch(self, obj):
        return obj.department.branch.name if obj.department and obj.department.branch else "-"
