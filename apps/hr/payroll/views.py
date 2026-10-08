import calendar
from datetime import datetime
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SalarySetting, Payslip
from .serializers import SalarySettingSerializer, PayslipSerializer
from apps.hr.attendance.models import AttendanceEvent

class SalarySettingViewSet(viewsets.ModelViewSet):
    queryset = SalarySetting.objects.all()
    serializer_class = SalarySettingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or hasattr(user, 'profile') and user.profile.role == 'admin':
            return self.queryset
        
        # User only sees their own payslips
        if hasattr(user, 'employee_profile'):
            return self.queryset.filter(employee=user.employee_profile)
        return self.queryset.none()
        
    @action(detail=False, methods=['post'])
    def generate(self, request):
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        month = request.data.get('month')
        year = request.data.get('year')
        
        if not month or not year:
            return Response({'error': 'month and year required'}, status=status.HTTP_400_BAD_REQUEST)
            
        month = int(month)
        year = int(year)
        
        # Find all employees with salary settings
        settings = SalarySetting.objects.select_related('employee').all()
        generated = 0
        
        for setting in settings:
            employee = setting.employee
            
            # Count attendance (present)
            # Find unique days the employee checked in
            events = AttendanceEvent.objects.filter(
                employee=employee,
                server_timestamp__year=year,
                server_timestamp__month=month,
                event_type='CHECK_IN',
                status='PRESENT'
            ).values('server_timestamp__date').distinct()
            
            total_days = events.count()
            
            payslip, created = Payslip.objects.get_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'daily_rate': setting.daily_rate,
                    'allowance': setting.allowance,
                }
            )
            
            if created or payslip.status == 'DRAFT':
                payslip.total_attendance = total_days
                payslip.daily_rate = setting.daily_rate
                payslip.allowance = setting.allowance
                payslip.calculate_salary()
                generated += 1
                
        return Response({'status': 'success', 'generated': generated})
