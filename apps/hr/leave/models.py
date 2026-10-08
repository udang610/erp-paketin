import uuid
from django.db import models
from apps.employees.models import Employee

class LeaveType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100) # e.g. Annual Leave, Sick Leave, Maternity Leave
    description = models.TextField(blank=True, null=True)
    requires_attachment = models.BooleanField(default=False)
    default_quota_days = models.IntegerField(default=12)

    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField()
    allocated_days = models.IntegerField()
    used_days = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.year})"
    
    @property
    def remaining_days(self):
        return self.allocated_days - self.used_days

class LeaveRequestStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_SUPERVISOR = 'PENDING_SUPERVISOR', 'Pending Supervisor Approval'
    PENDING_HRGA = 'PENDING_HRGA', 'Pending HRGA Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    CANCELLED = 'CANCELLED', 'Cancelled'

class LeaveRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    
    reason = models.TextField()
    attachment_url = models.URLField(blank=True, null=True)
    
    status = models.CharField(max_length=30, choices=LeaveRequestStatus.choices, default=LeaveRequestStatus.PENDING_SUPERVISOR)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Leave {self.employee.full_name} ({self.start_date} to {self.end_date})"
