from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.models import MenuVisibilitySetting, Role
from apps.core.context_processors import erp_context

User = get_user_model()

class MenuVisibilitySettingTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superadmin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            user_type='ADMIN'
        )
        self.finance_user = User.objects.create_user(
            username='finance_test',
            email='finance@test.com',
            password='password123',
            user_type='FINANCE'
        )
        # Ensure role is created/linked
        self.finance_role, _ = Role.objects.get_or_create(
            name='Finance',
            defaults={'can_access_finance': True}
        )
        self.finance_user.roles.add(self.finance_role)
        MenuVisibilitySetting.seed_default_menus()

    def test_seed_default_menus_creates_records(self):
        count = MenuVisibilitySetting.objects.count()
        self.assertGreaterEqual(count, 30)
        self.assertTrue(MenuVisibilitySetting.objects.filter(code='module_finance').exists())
        self.assertTrue(MenuVisibilitySetting.objects.filter(code='menu_fin_invoice').exists())

    def test_visibility_map_all_visible_by_default(self):
        vis_map = MenuVisibilitySetting.get_visibility_map(self.finance_user)
        self.assertTrue(vis_map.get('module_finance'))
        self.assertTrue(vis_map.get('menu_fin_invoice'))

    def test_toggle_visibility_globally(self):
        setting = MenuVisibilitySetting.objects.get(code='menu_fin_invoice')
        setting.is_visible = False
        setting.save()

        vis_map = MenuVisibilitySetting.get_visibility_map(self.finance_user)
        self.assertFalse(vis_map.get('menu_fin_invoice'))

    def test_hide_for_specific_role(self):
        setting = MenuVisibilitySetting.objects.get(code='menu_fin_invoice')
        setting.hidden_for_roles.add(self.finance_role)
        setting.save()

        # Hidden for FINANCE
        vis_map_finance = MenuVisibilitySetting.get_visibility_map(self.finance_user)
        self.assertFalse(vis_map_finance.get('menu_fin_invoice'))

        # Visible for SUPERADMIN
        vis_map_admin = MenuVisibilitySetting.get_visibility_map(self.superadmin)
        self.assertTrue(vis_map_admin.get('menu_fin_invoice'))

    def test_context_processor_integration(self):
        request = self.factory.get('/')
        request.user = self.finance_user
        context = erp_context(request)
        
        self.assertIn('menu_vis', context)
        self.assertTrue(context['can_access_finance'])

        # Turn off finance module globally
        mod_finance = MenuVisibilitySetting.objects.get(code='module_finance')
        mod_finance.is_visible = False
        mod_finance.save()

        context_after = erp_context(request)
        self.assertFalse(context_after['can_access_finance'])

