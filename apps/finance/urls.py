from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KpiFileViewSet, KpiSheetViewSet, KpiFinanceViewSet, 
    ProfileViewSet, CellStyleViewSet, AuditLogViewSet, 
    worksheet_view, invoice_list, invoice_detail, invoice_delete, financial_report, financial_report_export_excel, vendor_list,
    unbilled_transactions, generate_invoice, invoice_pdf,
    close_invoice, remove_shipment_from_invoice,
    ldp_list, ldp_create, ldp_detail, ldp_print, ldp_confirm, ldp_to_invoice, ldp_delete,
    api_shipment_lookup, invoice_create, api_customer_ldps, api_ldp_lookup,
    invoice_process, invoice_approve, invoice_reconcile
)

router = DefaultRouter()
router.register(r'files', KpiFileViewSet, basename='kpifile')
router.register(r'sheets', KpiSheetViewSet, basename='kpisheet')
router.register(r'finance', KpiFinanceViewSet, basename='kpifinance')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'styles', CellStyleViewSet, basename='cellstyle')
router.register(r'audit', AuditLogViewSet, basename='auditlog')

app_name = 'finance'

urlpatterns = [
    # ─── SSR Views (for ERP sidebar integration) ───
    path('', worksheet_view, name='worksheet'),
    
    # ─── LDP (Lembar Daftar Pengiriman) ───
    path('ldp/', ldp_list, name='ldp_list'),
    path('ldp/create/', ldp_create, name='ldp_create'),
    path('ldp/<int:ldp_id>/', ldp_detail, name='ldp_detail'),
    path('ldp/<int:ldp_id>/print/', ldp_print, name='ldp_print'),
    path('ldp/<int:ldp_id>/confirm/', ldp_confirm, name='ldp_confirm'),
    path('ldp/<int:ldp_id>/to-invoice/', ldp_to_invoice, name='ldp_to_invoice'),
    path('ldp/<int:ldp_id>/delete/', ldp_delete, name='ldp_delete'),
    path('ldp/api/lookup/', api_shipment_lookup, name='api_shipment_lookup'),
    
    # ─── Invoicing & Billing ───
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/create/', invoice_create, name='invoice_create'),
    path('invoices/api/ldp-lookup/', api_ldp_lookup, name='api_ldp_lookup'),
    path('invoices/api/customer-ldps/', api_customer_ldps, name='api_customer_ldps'),
    path('invoices/<int:invoice_id>/', invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/pdf/', invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:invoice_id>/pdf/<str:filename>', invoice_pdf, name='invoice_pdf_named'),
    path('invoices/<int:invoice_id>/delete/', invoice_delete, name='invoice_delete'),
    path('invoices/<int:invoice_id>/close/', close_invoice, name='close_invoice'),
    path('invoices/<int:invoice_id>/remove-shipment/<int:shipment_id>/', remove_shipment_from_invoice, name='remove_shipment_from_invoice'),
    
    # ─── Dedicated Invoice Process (Approval & Reconcile) ───
    path('invoice-process/', invoice_process, name='invoice_process'),
    path('invoice-process/approve/<int:invoice_id>/', invoice_approve, name='invoice_approve'),
    path('invoice-process/reconcile/', invoice_reconcile, name='invoice_reconcile'),
    
    # Legacy / Additional routes
    path('unbilled/', unbilled_transactions, name='unbilled_transactions'),
    path('invoices/generate/', generate_invoice, name='generate_invoice'),
    path('report/', financial_report, name='financial_report'),
    path('report/export-excel/', financial_report_export_excel, name='financial_report_export_excel'),
    path('vendors/', vendor_list, name='vendor_list'),
    
    path('api/', include(router.urls)),
]
