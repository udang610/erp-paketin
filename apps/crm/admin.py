from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import Client, Lead, Contract, Quotation, QuotationItem, Activity, Reminder


class QuotationItemInline(TabularInline):
    model = QuotationItem
    extra = 1


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ('company_name', 'client_id', 'branch', 'owner', 'display_status')
    list_filter = ('branch', 'customer_status', 'customer_category')
    search_fields = ('company_name', 'contact_person', 'phone')
    autocomplete_fields = ['owner', 'branch']

    @display(description="Status", label=True)
    def display_status(self, obj):
        return obj.get_customer_status_display()


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ('lead_id', 'client', 'owner', 'display_status', 'estimated_value', 'created_at')
    list_filter = ('status', 'lead_source')
    search_fields = ('client__company_name', 'lead_id')
    autocomplete_fields = ['owner', 'client']

    @display(description="Status Lead", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(Contract)
class ContractAdmin(ModelAdmin):
    list_display = ('contract_number', 'client', 'owner', 'display_status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('contract_number', 'client__company_name', 'title')
    autocomplete_fields = ['owner', 'client', 'lead']

    @display(description="Status Kontrak", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(Quotation)
class QuotationAdmin(ModelAdmin):
    list_display = ('quotation_number', 'lead', 'owner', 'display_status', 'total_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('lead__client__company_name', 'quotation_number')
    autocomplete_fields = ['owner', 'lead']
    inlines = [QuotationItemInline]

    @display(description="Status Penawaran", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ('activity_type', 'lead', 'owner', 'next_followup', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('lead__client__company_name', 'description')
    autocomplete_fields = ['owner', 'lead']


@admin.register(Reminder)
class ReminderAdmin(ModelAdmin):
    list_display = ('title', 'owner', 'due_date', 'display_completed')
    list_filter = ('completed', 'due_date')
    search_fields = ('title',)
    autocomplete_fields = ['owner']

    @display(description="Selesai", label=True)
    def display_completed(self, obj):
        return "Selesai" if obj.completed else "Pending"
