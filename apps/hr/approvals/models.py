import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.employees.models import Employee

class ApprovalFlow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255) # e.g. "Standard Leave Approval"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ApprovalStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, related_name='steps')
    step_order = models.IntegerField()
    name = models.CharField(max_length=255) # e.g. "Direct Supervisor Approval", "HRGA Approval"
    
    role_required = models.CharField(max_length=100, blank=True, null=True, help_text="If set, anyone with this role can approve")
    is_supervisor_step = models.BooleanField(default=False, help_text="If true, requires the employee's direct supervisor")

    class Meta:
        ordering = ['step_order']
        unique_together = ('flow', 'step_order')

    def __str__(self):
        return f"{self.flow.name} - Step {self.step_order}: {self.name}"


class ApprovalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(ApprovalFlow, on_delete=models.PROTECT)
    requester = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='approval_requests')
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    current_step_order = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request for {self.content_object} by {self.requester.full_name}"

class ApprovalAction(models.Model):
    class ActionType(models.TextChoices):
        APPROVE = 'APPROVE', 'Approve'
        REJECT = 'REJECT', 'Reject'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='actions')
    step = models.ForeignKey(ApprovalStep, on_delete=models.PROTECT)
    
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ActionType.choices)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor.email} {self.action} at Step {self.step.step_order}"
