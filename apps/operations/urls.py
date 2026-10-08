from django.urls import path
from . import views, views_do_balik, views_returns

app_name = 'operations'

urlpatterns = [
    path('pos/cash/', views.pos_cash, name='pos-cash'),
    path('pos/credit/', views.pos_credit, name='pos-credit'),
    path('pos/import/', views.shipment_import, name='shipment-import'),
    path('pos/import/template/', views.shipment_import_template, name='shipment-import-template'),
    path('cek-tarif/', views.cek_tarif, name='cek-tarif'),
    
    # Pickup Order Management
    path('pickup/', views.pickup_list, name='pickup-list'),
    path('pickup/create/', views.pickup_create, name='pickup-create'),
    path('pickup/<int:pk>/update/', views.pickup_update, name='pickup-update'),
    path('pickup/<int:pk>/delete/', views.pickup_delete, name='pickup-delete'),
    path('pickup/<int:pk>/hide/', views.pickup_hide, name='pickup-hide'),
    path('pickup/assign/', views.pickup_assign, name='pickup-assign'),
    path('pickup/manifest-status/', views.pickup_manifest_status, name='pickup-manifest-status'),
    path('pickup/manifest-edit/', views.pickup_manifest_edit, name='pickup-manifest-edit'),
    path('pickup/print-sppb/<int:pk>/', views.pickup_print_sppb, name='pickup-print-sppb'),
    
    # Shipment Management (Data Resi)
    path('shipments/', views.shipment_list, name='shipment-list'),
    path('shipments/create/', views.shipment_create, name='shipment-create'),
    path('shipments/<int:pk>/', views.shipment_detail, name='shipment-detail'),
    path('shipments/<int:pk>/print/', views.shipment_print, name='shipment-print'),
    path('shipments/<int:pk>/print-awb-reguler/', views.print_awb_reguler, name='print-awb-reguler'),
    path('shipments/<int:pk>/update/', views.shipment_update, name='shipment-update'),
    path('shipments/<int:pk>/delete/', views.shipment_delete, name='shipment-delete'),
    path('shipments/<int:pk>/void/', views.shipment_void, name='shipment-void'),
    path('shipments/<int:pk>/hide/', views.shipment_hide, name='shipment-hide'),
    # Manifest Management (Surat Jalan / Outgoing / Transfer / Delivery)
    path('manifests/', views.manifest_list, name='manifest-list'),
    path('manifests/create/', views.manifest_create, name='manifest-create'),
    path('manifests/<int:pk>/', views.manifest_detail, name='manifest-detail'),
    path('manifests/<int:pk>/print/', views.manifest_print, name='manifest-print'),
    path('manifests/<int:pk>/print-linehaul/', views.print_manifest_linehaul, name='print_manifest_linehaul'),
    path('manifests/<int:pk>/print-bagtag/', views.manifest_print_bagtag, name='manifest-print-bagtag'),
    path('manifests/<int:pk>/update/', views.manifest_update, name='manifest-update'),
    path('manifests/<int:pk>/delete/', views.manifest_delete, name='manifest-delete'),
    path('manifests/<int:pk>/hide/', views.manifest_hide, name='manifest-hide'),
    path('manifests/bulk-status/', views.manifest_bulk_update_status, name='manifest-bulk-status'),
    path('manifests/bulk-incoming/', views.manifest_bulk_incoming, name='manifest-bulk-incoming'),
    path('pod/bulk-update/', views.bulk_pod_update, name='pod-bulk-update'),
    
    # Tracking
    path('tracking/', views.tracking_view, name='tracking'),
    path('scan/', views.scan_barcode, name='scan-barcode'),
    path('scan/transit/', views.scan_transit, name='scan-transit'),
    
    # Incoming Destination
    path('incoming/', views.incoming_list, name='incoming-list'),
    path('incoming/<int:pk>/', views.incoming_detail, name='incoming-detail'),
    path('incoming/<int:pk>/update/', views.incoming_update, name='incoming-update'),
    path('incoming/<int:pk>/delete/', views.incoming_delete, name='incoming-delete'),
    path('incoming/<int:pk>/hide/', views.incoming_hide, name='incoming-hide'),
    # Legacy entry points now use the universal scan form.
    path('incoming/resi/', views.incoming_create, name='incoming-by-resi'),
    path('incoming/manifest/', views.incoming_create, name='incoming-by-manifest'),
    path('incoming/create/', views.incoming_create, name='incoming-create'),
    
    # API Endpoints
    path('api/get-contract-price/', views.api_get_contract_price, name='api-get-contract-price'),
    path('api/get-client-detail/', views.api_get_client_detail, name='api-get-client-detail'),
    path('api/verify-manifest/', views.api_verify_manifest, name='api-verify-manifest'),
    path('api/verify-resi/', views.api_verify_resi, name='api-verify-resi'),
    path('api/verify-incoming/', views.api_verify_incoming, name='api-verify-incoming'),
    path('api/driver/manifests/', views.api_driver_manifests, name='api-driver-manifests'),
    path('api/driver/update-status/', views.api_driver_update_status, name='api-driver-update-status'),
    path('api/get-districts/', views.api_get_districts, name='api-get-districts'),
    
    # Tracking Manager & Timeline APIs (Solutions 1, 2, 3)
    path('shipments/<int:shipment_pk>/tracking/list/', views.api_tracking_list, name='api-tracking-list'),
    path('shipments/<int:shipment_pk>/tracking/create/', views.api_tracking_create, name='api-tracking-create'),
    path('shipments/<int:shipment_pk>/tracking/reorder/', views.api_tracking_reorder, name='api-tracking-reorder'),
    path('shipments/<int:shipment_pk>/tracking/auto-align/', views.api_tracking_auto_align, name='api-tracking-auto-align'),
    path('tracking/<int:pk>/update/', views.api_tracking_update, name='api-tracking-update'),
    path('tracking/<int:pk>/delete/', views.api_tracking_delete, name='api-tracking-delete'),
    
    # Print & Utility
    path('print-bulky/', views.print_bulky, name='print_bulky'),
    path('pod/', views.pod_list, name='pod_list'),
    path('pod/entry/', views.entry_pod, name='entry_pod'),
    path('pod/return/', views.entry_pod_return, name='entry_pod_return'),
    path('pod/<int:pk>/', views.pod_detail, name='pod-detail'),
    path('pod/<int:pk>/edit/', views.pod_edit, name='pod-edit'),
    path('pod/<int:pk>/print-e-pod/', views.print_e_pod, name='print-e-pod'),
    path('void/cash/', views.void_cash, name='void_cash'),
    path('void/credit/', views.void_credit, name='void_credit'),

    # Reports
    path('reports/sla/', views.shipment_sla_report, name='report-sla'),
    path('reports/sla/export-excel/', views.shipment_sla_export_excel, name='report-sla-export-excel'),

    # DO Balik (Surat Jalan Balik) Management
    path('do-balik/', views_do_balik.do_balik_list, name='do-balik-list'),
    path('do-balik/create-pouch/', views_do_balik.do_balik_create_pouch, name='do-balik-create-pouch'),
    path('do-balik/verify-pouch/<int:pk>/', views_do_balik.do_balik_verify_pouch, name='do-balik-verify-pouch'),
    path('do-balik/quick-verify/<int:pk>/', views_do_balik.do_balik_quick_verify, name='do-balik-quick-verify'),

    # Returns (RTO / Return to Origin) Management
    path('returns/', views_returns.return_list, name='return-list'),
    path('returns/create/', views_returns.return_create, name='return-create'),
    path('returns/scan-redelivery/', views_returns.redeliver_scan_view, name='return-redeliver-scan'),
    path('returns/api/lookup/', views_returns.api_lookup_return_resi, name='api-return-lookup'),
    path('returns/decision/', views_returns.return_decision_quick, name='return-decision-quick'),
    path('returns/<int:pk>/', views_returns.return_action, name='return-detail'),
]
