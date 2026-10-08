from rest_framework import serializers
from .models import Employee, RegisteredDevice, FaceProfile


class EmployeeSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.full_name', read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'


class RegisteredDeviceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = RegisteredDevice
        fields = '__all__'


class FaceProfileSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = FaceProfile
        fields = ['id', 'employee', 'employee_name', 'enrolled_at', 'is_active']
        # EXCLUDE face_embedding for security reasons unless strictly necessary for a specific endpoint
