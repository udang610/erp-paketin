from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import AuditLogViewSet

app_name = 'audit'

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='log')

urlpatterns = [
    path('', views.audit_list, name='audit_list'),
    path('api/', include(router.urls)),
]
