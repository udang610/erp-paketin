from django.urls import path
from .views import sales, quotation, activity, reports

app_name = 'crm'

urlpatterns = [
    # Clients (from sales)
    path('clients/', sales.ClientListView.as_view(), name='client-list'),
    path('clients/create/', sales.ClientCreateView.as_view(), name='client-create'),
    path('clients/<int:pk>/', sales.ClientDetailView.as_view(), name='client-detail'),
    path('clients/<int:pk>/edit/', sales.ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', sales.ClientDeleteView.as_view(), name='client-delete'),
    path('clients/<int:pk>/sync-to-master/', sales.ClientSyncToMasterView.as_view(), name='client-sync-to-master'),
    path('clients/export/excel/', sales.ClientExportExcelView.as_view(), name='client-export-excel'),

    # Leads (from sales)
    path('leads/', sales.LeadListView.as_view(), name='lead-list'),
    path('leads/create/', sales.LeadCreateView.as_view(), name='lead-create'),
    path('leads/<int:pk>/', sales.LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<int:pk>/edit/', sales.LeadUpdateView.as_view(), name='lead-update'),
    path('leads/<int:pk>/delete/', sales.LeadDeleteView.as_view(), name='lead-delete'),
    path('leads/<int:pk>/status/', sales.LeadQuickStatusView.as_view(), name='lead-status'),
    path('leads/<int:pk>/whatsapp/', sales.LeadWhatsAppFollowUpView.as_view(), name='lead-whatsapp'),
    path('leads/export/', sales.LeadExportCSVView.as_view(), name='lead-export'),
    path('leads/export/excel/', sales.LeadExportExcelView.as_view(), name='lead-export-excel'),

    # Contracts (from sales)
    path('contracts/', sales.ContractListView.as_view(), name='contract-list'),
    path('contracts/create/', sales.ContractCreateView.as_view(), name='contract-create'),
    path('contracts/<int:pk>/', sales.ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:pk>/edit/', sales.ContractUpdateView.as_view(), name='contract-update'),
    path('contracts/<int:pk>/delete/', sales.ContractDeleteView.as_view(), name='contract-delete'),
    path('contracts/export/excel/', sales.ContractExportExcelView.as_view(), name='contract-export-excel'),

    # Quotations (from quotation)
    path('quotations/', quotation.QuotationListView.as_view(), name='quotation-list'),
    path('quotations/create/', quotation.QuotationCreateView.as_view(), name='quotation-create'),
    path('quotations/<int:pk>/', quotation.QuotationDetailView.as_view(), name='quotation-detail'),
    path('quotations/<int:pk>/edit/', quotation.QuotationUpdateView.as_view(), name='quotation-update'),
    path('quotations/<int:pk>/delete/', quotation.QuotationDeleteView.as_view(), name='quotation-delete'),
    path('quotations/<int:pk>/print/', quotation.QuotationPrintView.as_view(), name='quotation-print'),
    path('quotations/export/excel/', quotation.QuotationExportExcelView.as_view(), name='quotation-export-excel'),

    # Activities (from activity)
    path('activities/', activity.ActivityListView.as_view(), name='activity-list'),
    path('activities/create/', activity.ActivityCreateView.as_view(), name='activity-create'),
    path('activities/<int:pk>/edit/', activity.ActivityUpdateView.as_view(), name='activity-update'),
    path('activities/<int:pk>/delete/', activity.ActivityDeleteView.as_view(), name='activity-delete'),
    path('activities/export/excel/', activity.ActivityExportExcelView.as_view(), name='activity-export-excel'),

    # Reminders (from activity)
    path('reminders/', activity.ReminderListView.as_view(), name='reminder-list'),
    path('reminders/create/', activity.ReminderCreateView.as_view(), name='reminder-create'),
    path('reminders/<int:pk>/edit/', activity.ReminderUpdateView.as_view(), name='reminder-update'),
    path('reminders/<int:pk>/delete/', activity.ReminderDeleteView.as_view(), name='reminder-delete'),
    path('reminders/<int:pk>/toggle/', activity.ReminderToggleCompleteView.as_view(), name='reminder-toggle'),
    path('reminders/export/excel/', activity.ReminderExportExcelView.as_view(), name='reminder-export-excel'),
    path('api/due-reminders/', activity.due_reminders_api, name='due-reminders-api'),

    # Reports
    path('reports/', reports.sales_report_view, name='sales-report'),
    path('reports/export-excel/', reports.sales_report_export_excel, name='sales-report-export-excel'),
]
