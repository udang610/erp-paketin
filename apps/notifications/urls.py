from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    NotificationPreferenceViewSet,
    notification_list_view,
    mark_as_read_view,
    mark_all_read_view,
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'messages', NotificationViewSet, basename='api-message')

urlpatterns = [
    # Web UI views
    path('', notification_list_view, name='message-list'),
    path('mark-read/<uuid:pk>/', mark_as_read_view, name='mark-read'),
    path('mark-all-read/', mark_all_read_view, name='mark-all-read'),

    # REST API views
    path('api/', include(router.urls)),
    path('api/preferences/', NotificationPreferenceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='preferences'),
]
