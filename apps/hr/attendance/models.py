import uuid
from django.db import models
from apps.employees.models import Employee
from apps.organizations.models import Branch

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    LATE = 'LATE', 'Late'
    ABSENT = 'ABSENT', 'Absent'
    EARLY_CHECKOUT = 'EARLY_CHECKOUT', 'Early Checkout'
    LEAVE = 'LEAVE', 'Leave'
    SICK = 'SICK', 'Sick'
    PERMISSION = 'PERMISSION', 'Permission'
    WFH = 'WFH', 'Work From Home'
    BUSINESS_TRIP = 'BUSINESS_TRIP', 'Business Trip'
    HOLIDAY = 'HOLIDAY', 'Holiday'
    OVERTIME = 'OVERTIME', 'Overtime'
    PENDING = 'PENDING', 'Pending'
    SUSPICIOUS = 'SUSPICIOUS', 'Suspicious'

class WorkMode(models.TextChoices):
    OFFICE = 'OFFICE', 'Office'
    WFH = 'WFH', 'Work From Home'
    FIELD = 'FIELD', 'Field Worker'
    REMOTE = 'REMOTE', 'Remote'

class AttendancePolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='attendance_policies')
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.OFFICE)
    
    # Timing
    check_in_time = models.TimeField()
    check_out_time = models.TimeField()
    late_threshold_minutes = models.IntegerField(default=15)
    
    # Location rules
    gps_required = models.BooleanField(default=True)
    allowed_radius_meters = models.IntegerField(default=200, help_text="0 means no restriction")
    
    # Additional rules
    face_verification_required = models.BooleanField(default=True)
    device_verification_required = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_work_mode_display()}"


class AttendanceEvent(models.Model):
    class EventType(models.TextChoices):
        CHECK_IN = 'CHECK_IN', 'Check In'
        CHECK_OUT = 'CHECK_OUT', 'Check Out'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_events')
    policy = models.ForeignKey(AttendancePolicy, on_delete=models.SET_NULL, null=True, blank=True)
    
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    
    # Timestamps
    server_timestamp = models.DateTimeField(auto_now_add=True)
    device_timestamp = models.DateTimeField()
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_accuracy = models.FloatField(null=True, blank=True, help_text="Accuracy in meters")
    is_mock_location = models.BooleanField(default=False)
    
    # Verification
    device_id = models.CharField(max_length=255, blank=True, null=True)
    face_verified = models.BooleanField(default=False)
    
    # Misc
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='attendance_photos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_event_type_display()} at {self.server_timestamp.strftime('%Y-%m-%d %H:%M')}"
