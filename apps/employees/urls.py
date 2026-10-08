from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import EmployeeViewSet, RegisteredDeviceViewSet, FaceProfileViewSet

app_name = 'employees'

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'devices', RegisteredDeviceViewSet, basename='device')
router.register(r'face-profiles', FaceProfileViewSet, basename='face-profile')

urlpatterns = [
    # Web views (HR Module)
    path('', views.employee_list, name='employee_list'),
    path('employee/add/', views.employee_create, name='employee_create'),
    path('employee/<uuid:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/<uuid:pk>/edit/', views.employee_update, name='employee_update'),
    path('employee/<uuid:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # AJAX helper for user dropdown
    path('api/user-info/<uuid:user_id>/', views.get_user_info, name='get_user_info'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
]
