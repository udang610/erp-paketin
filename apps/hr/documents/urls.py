from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import DocumentCategoryViewSet, DocumentViewSet, DocumentVersionViewSet

app_name = 'documents'

router = DefaultRouter()
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'files', DocumentViewSet, basename='file')
router.register(r'versions', DocumentVersionViewSet, basename='version')

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('api/', include(router.urls)),
]
