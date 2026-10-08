from django.urls import path
from . import views

app_name = 'master'
urlpatterns = [
    # List Views
    path('banks/', views.master_list, {'model_name': 'bank', 'title': 'Banks', 'icon': 'ph-bank'}, name='banks'),
    path('branches/', views.master_list, {'model_name': 'branch', 'title': 'Branches', 'icon': 'ph-buildings'}, name='branches'),
    path('coverage/', views.master_list, {'model_name': 'coverage', 'title': 'Coverage By District', 'icon': 'ph-map-trifold'}, name='coverage'),
    path('courier/', views.master_list, {'model_name': 'courier', 'title': 'Courier / Driver', 'icon': 'ph-steering-wheel'}, name='courier'),
    path('customer/', views.master_list, {'model_name': 'customer', 'title': 'Customer', 'icon': 'ph-users'}, name='customer'),
    path('vehicle/', views.master_list, {'model_name': 'vehicle', 'title': 'Vehicle', 'icon': 'ph-truck'}, name='vehicle'),
    path('vehicle/category/', views.master_list, {'model_name': 'vehicle_category', 'title': 'Kategori Armada', 'icon': 'ph-car-profile'}, name='vehicle_category'),
    path('price/', views.master_list, {'model_name': 'price', 'title': 'Price', 'icon': 'ph-currency-circle-dollar'}, name='price'),
    path('sales/', views.master_list, {'model_name': 'sales', 'title': 'Sales', 'icon': 'ph-briefcase'}, name='sales'),
    path('services/', views.master_list, {'model_name': 'service', 'title': 'Services', 'icon': 'ph-star'}, name='services'),
    path('vendors/', views.master_list, {'model_name': 'vendor', 'title': 'Vendors', 'icon': 'ph-storefront'}, name='vendors'),

    # Price Import & Template
    path('price/import/', views.price_import, name='price_import'),
    path('price/download-template/', views.price_download_template, name='price_download_template'),

    # Create & Action Views
    path('customer/<str:pk>/sync-to-crm/', views.customer_sync_to_crm, name='customer_sync_to_crm'),
    path('<str:model_name>/create/', views.master_create, name='master_create'),
    path('<str:model_name>/update/<str:pk>/', views.master_update, name='master_update'),
    path('<str:model_name>/delete/<str:pk>/', views.master_delete, name='master_delete'),
    path('<str:model_name>/detail/<str:pk>/', views.master_detail, name='master_detail'),

    # Region API (Cascading Dropdown Wilayah Indonesia)
    path('api/provinces/', views.api_provinces, name='api-provinces'),
    path('api/cities-by-province/', views.api_cities_by_province, name='api-cities-by-province'),
    path('api/regencies/<int:province_id>/', views.api_regencies, name='api-regencies'),
    path('api/districts/<int:regency_id>/', views.api_districts, name='api-districts'),
    path('api/districts-by-city/', views.api_districts_by_city, name='api-districts-by-city'),
    path('api/villages/<int:district_id>/', views.api_villages, name='api-villages'),
]