from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import AttendancePolicyViewSet, AttendanceEventViewSet

app_name = 'attendance'

router = DefaultRouter()
router.register(r'policies', AttendancePolicyViewSet, basename='policy')
router.register(r'events', AttendanceEventViewSet, basename='event')

urlpatterns = [
    # Web views
    path('', views.attendance_list, name='attendance_list'),
    path('policies/', views.attendance_policy_list, name='policy_list'),
    path('policies/add/', views.attendance_policy_edit, name='policy_create'),
    path('policies/<uuid:pk>/edit/', views.attendance_policy_edit, name='policy_edit'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
