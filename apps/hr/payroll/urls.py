from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalarySettingViewSet, PayslipViewSet

router = DefaultRouter()
router.register(r'settings', SalarySettingViewSet, basename='salarysetting')
router.register(r'payslips', PayslipViewSet, basename='payslip')

app_name = 'payroll'

urlpatterns = [
    path('api/', include(router.urls)),
]
