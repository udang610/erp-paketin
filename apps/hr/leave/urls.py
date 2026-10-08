from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import LeaveTypeViewSet, LeaveBalanceViewSet, LeaveRequestViewSet

app_name = 'leave'

router = DefaultRouter()
router.register(r'types', LeaveTypeViewSet, basename='type')
router.register(r'balances', LeaveBalanceViewSet, basename='balance')
router.register(r'requests', LeaveRequestViewSet, basename='request')

urlpatterns = [
    # Web views
    path('', views.leave_list, name='leave_list'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
