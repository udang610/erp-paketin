import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        ATTENDANCE = 'ATTENDANCE', 'Kehadiran / HR'
        LEAVE = 'LEAVE', 'Cuti / Izin'
        DOCUMENT = 'DOCUMENT', 'Dokumen & Surat Jalan'
        SYSTEM = 'SYSTEM', 'Sistem & Keamanan'
        CRM = 'CRM', 'CRM & Sales'
        OPS = 'OPS', 'Operasional'
        FINANCE = 'FINANCE', 'Finance & Keuangan'
        MASTER = 'MASTER', 'Data Master'
        VM = 'VM', 'Vendor Management'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='caused_notifications',
        verbose_name="Pelaku Aksi"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    url = models.CharField(max_length=500, blank=True, null=True, help_text="Tautan tujuan ketika notifikasi diklik")
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"

    def __str__(self):
        return f"To {self.user.username}: {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences', primary_key=True)
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Prefs for {self.user.email}"
