from rest_framework import serializers
from .models import AssetCategory, AssetItem, AssetTransaction

class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = '__all__'

class AssetItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = AssetItem
        fields = '__all__'

class AssetTransactionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = AssetTransaction
        fields = '__all__'
        read_only_fields = ('employee', 'status', 'approved_by', 'approval_date')
