from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetCategoryViewSet, AssetItemViewSet, AssetTransactionViewSet

router = DefaultRouter()
router.register(r'categories', AssetCategoryViewSet, basename='assetcategory')
router.register(r'items', AssetItemViewSet, basename='assetitem')
router.register(r'transactions', AssetTransactionViewSet, basename='assettransaction')

app_name = 'asset_request'

urlpatterns = [
    path('api/', include(router.urls)),
]
