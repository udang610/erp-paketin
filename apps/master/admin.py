from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Bank, Coverage, Service, Price, Vehicle, Customer, Province, Regency, District, Village


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ('customer_code', 'name', 'account_type', 'city', 'display_active')
    search_fields = ('customer_code', 'name', 'city', 'pic_account')
    list_filter = ('account_type', 'is_active')

    @display(description="Status", label=True)
    def display_active(self, obj):
        return "Aktif" if obj.is_active else "Nonaktif"


@admin.register(Bank)
class BankAdmin(ModelAdmin):
    list_display = ('name', 'account_number', 'account_name', 'is_active')
    search_fields = ('name', 'account_number', 'account_name')
    list_filter = ('is_active',)


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ('code', 'name', 'divisor', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ('plate_number', 'vehicle_type', 'brand_model', 'branch', 'is_active')
    search_fields = ('plate_number', 'brand_model')
    list_filter = ('vehicle_type', 'branch', 'is_active')


@admin.register(Coverage)
class CoverageAdmin(ModelAdmin):
    list_display = ('province', 'city', 'district', 'tlc', 'is_active')
    search_fields = ('province', 'city', 'district', 'tlc')
    list_filter = ('is_active', 'province')


@admin.register(Province)
class ProvinceAdmin(ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Regency)
class RegencyAdmin(ModelAdmin):
    list_display = ('code', 'name', 'type', 'province')
    search_fields = ('code', 'name')
    list_filter = ('type', 'province')


@admin.register(District)
class DistrictAdmin(ModelAdmin):
    list_display = ('code', 'name', 'regency')
    search_fields = ('code', 'name')
    list_filter = ('regency__province',)


@admin.register(Village)
class VillageAdmin(ModelAdmin):
    list_display = ('code', 'name', 'type', 'district')
    search_fields = ('code', 'name')
    list_filter = ('type',)