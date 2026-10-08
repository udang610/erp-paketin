from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import BranchViewSet, DepartmentViewSet, PositionViewSet

app_name = 'organizations'

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')

urlpatterns = [
    # Web views
    path('', views.branch_list, name='branch_list'),
    path('branch/add/', views.branch_create, name='branch_create'),
    
    # API Endpoints
    path('api/', include(router.urls)),
]
