from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AssetCategory, AssetItem, AssetTransaction
from .serializers import AssetCategorySerializer, AssetItemSerializer, AssetTransactionSerializer

class AssetCategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class AssetItemViewSet(viewsets.ModelViewSet):
    queryset = AssetItem.objects.filter(is_active=True)
    serializer_class = AssetItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class AssetTransactionViewSet(viewsets.ModelViewSet):
    queryset = AssetTransaction.objects.all().order_by('-request_date')
    serializer_class = AssetTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'admin'):
            return self.queryset
        if hasattr(user, 'employee_profile'):
            return self.queryset.filter(employee=user.employee_profile)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'employee_profile'):
            serializer.save(employee=user.employee_profile)
        else:
            # Fallback or error, for now we save without employee or raise exception
            # Real app should raise exception
            serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        transaction = self.get_object()
        if transaction.status != 'PENDING':
            return Response({'error': 'Can only approve PENDING requests'}, status=status.HTTP_400_BAD_REQUEST)
            
        # check stock
        if transaction.item.stock < transaction.quantity:
            return Response({'error': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)
            
        transaction.status = 'APPROVED'
        transaction.approved_by = request.user
        from django.utils import timezone
        transaction.approval_date = timezone.now()
        transaction.save()
        
        # decrease stock
        item = transaction.item
        item.stock -= transaction.quantity
        item.save()
        
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        transaction = self.get_object()
        if transaction.status != 'PENDING':
            return Response({'error': 'Can only reject PENDING requests'}, status=status.HTTP_400_BAD_REQUEST)
            
        transaction.status = 'REJECTED'
        transaction.save()
        
        return Response({'status': 'rejected'})
