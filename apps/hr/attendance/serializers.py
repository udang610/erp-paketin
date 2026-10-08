from rest_framework import serializers
from .models import AttendancePolicy, AttendanceEvent

class AttendancePolicySerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = AttendancePolicy
        fields = '__all__'


class AttendanceEventSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)

    class Meta:
        model = AttendanceEvent
        fields = '__all__'
        read_only_fields = ['id', 'server_timestamp', 'status', 'created_at', 'updated_at']

class AttendanceEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceEvent
        fields = [
            'event_type', 'device_timestamp', 'latitude', 'longitude', 
            'gps_accuracy', 'is_mock_location', 'device_id', 
            'ip_address', 'notes', 'photo'
        ]
        
    # employee, policy, server_timestamp, status, face_verified will be set by the view/service layer
