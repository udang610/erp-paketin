from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.accounts.models import Role, MenuVisibilitySetting
from apps.notifications.models import Notification
from apps.notifications.utils import record_activity_and_notify
from apps.audit.models import AuditLog

User = get_user_model()

class NotificationActivityTests(TestCase):
    def setUp(self):
        self.client = Client()
        MenuVisibilitySetting.seed_default_menus()

        # Create Roles
        self.finance_role, _ = Role.objects.get_or_create(name='Finance', defaults={'can_access_finance': True})
        self.cs_role, _ = Role.objects.get_or_create(name='CS', defaults={'can_access_operations': True})

        # Create Users
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            user_type='ADMIN'
        )
        self.finance_user = User.objects.create_user(
            username='finance_test',
            email='fin@test.com',
            password='password123',
            user_type='FINANCE'
        )
        self.finance_user.roles.add(self.finance_role)

        self.cs_user = User.objects.create_user(
            username='cs_test',
            email='cs@test.com',
            password='password123',
            user_type='CS'
        )
        self.cs_user.roles.add(self.cs_role)

    def test_record_activity_and_notify_creates_audit_and_notifications(self):
        record_activity_and_notify(
            title="Resi Baru Dibuat: CRD-TEST-0001",
            message="Resi baru untuk customer PT ABC telah dibuat.",
            notification_type=Notification.NotificationType.OPS,
            actor=self.cs_user,
            target_roles=['Finance', 'CS'],
            url="/operations/shipments/?resi=CRD-TEST-0001"
        )

        # Verify AuditLog created
        self.assertTrue(AuditLog.objects.filter(action__contains="CRD-TEST-0001").exists())

        # Verify Notifications created for targeted roles
        self.assertTrue(Notification.objects.filter(user=self.finance_user, title__contains="CRD-TEST-0001").exists())
        self.assertTrue(Notification.objects.filter(user=self.cs_user, title__contains="CRD-TEST-0001").exists())

    def test_notification_list_web_view(self):
        self.client.force_login(self.finance_user)
        Notification.objects.create(
            user=self.finance_user,
            title="Test Notification",
            message="Test message",
            notification_type=Notification.NotificationType.FINANCE,
            url="/finance/"
        )

        response = self.client.get(reverse('notifications:message-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/list.html')
        self.assertContains(response, "Test Notification")

    def test_mark_as_read_view(self):
        self.client.force_login(self.finance_user)
        notif = Notification.objects.create(
            user=self.finance_user,
            title="Unread Notification",
            message="Unread message",
            notification_type=Notification.NotificationType.SYSTEM,
            url="/finance/"
        )

        self.assertFalse(notif.is_read)
        response = self.client.get(reverse('notifications:mark-read', kwargs={'pk': notif.id}))
        self.assertRedirects(response, '/finance/')

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_mark_all_read_view(self):
        self.client.force_login(self.finance_user)
        Notification.objects.create(user=self.finance_user, title="N1", message="M1")
        Notification.objects.create(user=self.finance_user, title="N2", message="M2")

        self.assertEqual(Notification.objects.filter(user=self.finance_user, is_read=False).count(), 2)
        response = self.client.post(reverse('notifications:mark-all-read'))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Notification.objects.filter(user=self.finance_user, is_read=False).count(), 0)
