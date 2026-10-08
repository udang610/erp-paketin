from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import (
    Profile, KpiFile, KpiSheet, KpiFinance, CellStyle, AuditLog, 
    CrmClient, CrmContract, Invoice, PaymentRecord, Vendor, 
    TransactionVendorCost, BranchWallet, WalletTransaction,
    LDP, LDPItem, InvoiceRevisionLog, PaymentReconciliation
)

from django import forms
from django.utils.safestring import mark_safe

COLUMNS_CHOICES = [
    ('📝 Info Pengiriman', (
        ('tanggal_pickup', 'Tanggal Pickup'),
        ('nama', 'IP Perusahaan'),
        ('awb', 'AWB'),
        ('awb_sistem', 'AWB Sistem'),
        ('pengirim', 'Customer'),
        ('sales', 'Sales'),
        ('penerima', 'Penerima'),
    )),
    ('📦 Detail Barang', (
        ('service', 'Service'),
        ('via', 'Via'),
        ('aktual', 'Aktual'),
        ('vol', 'Vol'),
        ('unit', 'Unit'),
        ('kubik', 'Kubik'),
        ('p', 'P (Panjang)'),
        ('l', 'L (Lebar)'),
        ('t', 'T (Tinggi)'),
        ('koil', 'Koil'),
        ('asal_pickup', 'Asal Pick Up'),
        ('jenis_barang', 'Jenis Barang'),
        ('tujuan', 'Tujuan'),
    )),
    ('💰 Keuangan (Nominal)', (
        ('harga', 'Harga'),
        ('surcharge', 'Surcharge'),
        ('packing', 'Packing'),
        ('handling', 'Handling'),
        ('penjualan', 'Penjualan'),
        ('nilai_barang', 'Nilai Barang'),
        ('nama_vendor', 'Nama Vendor I'),
        ('nama_vendor_ii', 'Nama Vendor II'),
        ('nama_vendor_iii', 'Nama Vendor III'),
        ('nama_vendor_iv', 'Nama Vendor IV'),
        ('vendor_i', 'Harga Vendor I'),
        ('vendor_ii', 'Harga Vendor II'),
        ('vendor_iii', 'Harga Vendor III'),
        ('vendor_iv', 'Harga Vendor IV'),
        ('ops', 'OPS'),
        ('total_biaya', 'Total Biaya'),
        ('profit', 'Profit'),
        ('idx_profit', 'IDX Profit'),
        ('asuransi', 'Asuransi'),
        ('asuransi_jasindo', 'Asuransi Jasindo'),
    ))
]

class ProfileAdminForm(forms.ModelForm):
    allowed_columns = forms.MultipleChoiceField(
        choices=COLUMNS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Profile
        fields = '__all__'
        
    def clean_allowed_columns(self):
        return list(self.cleaned_data.get('allowed_columns', []))


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    form = ProfileAdminForm
    list_display = ('user', 'role', 'pic_id')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'user__first_name')


@admin.register(CrmClient)
class CrmClientAdmin(ModelAdmin):
    list_display = ('name', 'crm_id', 'is_active', 'updated_at')
    search_fields = ('name', 'crm_id')
    list_filter = ('is_active',)


@admin.register(CrmContract)
class CrmContractAdmin(ModelAdmin):
    list_display = ('client', 'asal', 'tujuan', 'service', 'via', 'harga', 'is_active')
    search_fields = ('client__name', 'asal', 'tujuan', 'service')
    list_filter = ('is_active', 'service', 'via')


@admin.register(KpiFile)
class KpiFileAdmin(ModelAdmin):
    list_display = ('name', 'created_at', 'created_by')
    search_fields = ('name',)


@admin.register(KpiSheet)
class KpiSheetAdmin(ModelAdmin):
    list_display = ('name', 'kpi_file', 'sheet_type', 'sort_order')
    list_filter = ('kpi_file', 'sheet_type')
    search_fields = ('name',)


@admin.register(KpiFinance)
class KpiFinanceAdmin(ModelAdmin):
    list_display = ('id', 'sheet', 'tanggal_pickup', 'awb', 'nama', 'total_biaya')
    search_fields = ('awb', 'nama', 'pengirim', 'penerima')
    list_filter = ('sheet',)


@admin.register(Vendor)
class VendorAdmin(ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'service_type', 'display_active')
    search_fields = ('name', 'contact_person', 'phone')
    list_filter = ('is_active', 'service_type')

    @display(description="Status", label=True)
    def display_active(self, obj):
        return "Aktif" if obj.is_active else "Nonaktif"


@admin.register(TransactionVendorCost)
class TransactionVendorCostAdmin(ModelAdmin):
    list_display = ('transaction', 'vendor', 'cost')
    search_fields = ('vendor__name',)


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('invoice_number', 'client_name', 'total_amount', 'display_status', 'created_at')
    search_fields = ('invoice_number', 'client_name')
    list_filter = ('status',)

    @display(description="Status Invoice", label=True)
    def display_status(self, obj):
        return obj.get_status_display()


@admin.register(BranchWallet)
class BranchWalletAdmin(ModelAdmin):
    list_display = ('branch', 'balance', 'display_active', 'updated_at')
    search_fields = ('branch__name',)
    list_filter = ('is_active',)

    @display(description="Status", label=True)
    def display_active(self, obj):
        return "Aktif" if obj.is_active else "Nonaktif"


@admin.register(WalletTransaction)
class WalletTransactionAdmin(ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'created_at')
    search_fields = ('wallet__branch__name', 'reference')
    list_filter = ('transaction_type',)


class LDPItemInline(admin.TabularInline):
    from .models import LDPItem
    model = LDPItem
    extra = 0
    fields = ('awb_number', 'shipment_date', 'origin', 'destination', 'service_type', 'koli', 'chargeable_weight', 'price_per_kg', 'freight_charge', 'subtotal')


@admin.register(LDP)
class LDPAdmin(ModelAdmin):
    list_display = ('ldp_number', 'client_name', 'branch', 'ldp_date', 'total_koli', 'total_weight', 'total_amount', 'status')
    search_fields = ('ldp_number', 'client_name')
    list_filter = ('status', 'branch', 'ldp_date')
    inlines = [LDPItemInline]


@admin.register(InvoiceRevisionLog)
class InvoiceRevisionLogAdmin(ModelAdmin):
    list_display = ('invoice', 'old_total_amount', 'new_total_amount', 'revised_by', 'created_at')
    search_fields = ('invoice__invoice_number', 'reason')


@admin.register(PaymentReconciliation)
class PaymentReconciliationAdmin(ModelAdmin):
    list_display = ('invoice', 'bank', 'amount_paid', 'payment_datetime', 'reconciled_by', 'created_at')
    search_fields = ('invoice__invoice_number', 'reference_number')

