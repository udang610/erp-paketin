from rest_framework import serializers
from .models import KpiFile, KpiSheet, KpiFinance, Profile, CellStyle, AuditLog

class KpiFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiFile
        fields = '__all__'

class KpiSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiSheet
        fields = '__all__'

class KpiFinanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiFinance
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'email', 'name', 'role', 'pic_id', 'allowed_columns', 'sheet_ids', 'is_superuser']

    def get_email(self, obj):
        return obj.user.email or obj.user.username

    def get_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.username

class CellStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CellStyle
        fields = "__all__"

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'

# CrmClientSerializer and CrmContractSerializer REMOVED (deprecated legacy models)
