import uuid
from django.db import models
from django.conf import settings
from apps.organizations.models import Branch, Department, Position

class EmploymentStatus(models.TextChoices):
    PERMANENT = 'PERMANENT', 'Permanent'
    CONTRACT = 'CONTRACT', 'Contract'
    PROBATION = 'PROBATION', 'Probation'
    INTERN = 'INTERN', 'Intern'

class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    
    status = models.CharField(max_length=20, choices=EmploymentStatus.choices, default=EmploymentStatus.CONTRACT)
    join_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Bergabung")
    contract_end_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Berakhir Kontrak")
    
    # Identitas & Pajak
    nik = models.CharField(max_length=50, blank=True, null=True, verbose_name="NIK / No. KTP")
    npwp = models.CharField(max_length=50, blank=True, null=True, verbose_name="NPWP")
    
    # Dokumen Pegawai
    document_ktp = models.FileField(upload_to='employee_docs/ktp/', blank=True, null=True, verbose_name="Dokumen KTP")
    document_contract = models.FileField(upload_to='employee_docs/contracts/', blank=True, null=True, verbose_name="Dokumen Kontrak / SK")
    
    # Rekening & Payroll
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nama Bank")
    bank_account_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nomor Rekening")
    bank_account_holder = models.CharField(max_length=255, blank=True, null=True, verbose_name="Atas Nama Rekening")
    
    # Kontak Darurat
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nama Kontak Darurat")
    emergency_contact_relation = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hubungan")
    emergency_contact_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="No. HP Darurat")
    
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


class RegisteredDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255)
    platform = models.CharField(max_length=50) # 'Android', 'iOS'
    os_version = models.CharField(max_length=50, blank=True, null=True)
    app_version = models.CharField(max_length=50, blank=True, null=True)
    device_model = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'device_id')

    def __str__(self):
        return f"{self.device_model} ({self.platform}) - {self.employee.full_name}"

class FaceProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='face_profile')
    face_embedding = models.JSONField(help_text="Stores the vectorized face representation securely")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Face Profile: {self.employee.full_name}"
