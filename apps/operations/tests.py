from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import MenuVisibilitySetting

User = get_user_model()

class OperationsPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='ops_admin',
            email='ops@admin.com',
            password='password123',
            user_type='ADMIN'
        )
        self.client.force_login(self.user)
        MenuVisibilitySetting.seed_default_menus()

    def test_shipment_list_page_renders_successfully(self):
        response = self.client.get('/operations/shipments/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'operations/shipments/shipment_list.html')
        self.assertTemplateUsed(response, 'base.html')
