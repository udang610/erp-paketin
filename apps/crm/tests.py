from django.test import TestCase
from decimal import Decimal
from apps.crm.models import Client, Lead, Quotation
from django.contrib.auth import get_user_model

User = get_user_model()

class QuotationUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='salesuser', password='password')
        self.client = Client.objects.create(company_name='Test PT', contact_person='Mr Test', owner=self.user)
        self.lead = Lead.objects.create(client=self.client, owner=self.user)
        
    def test_quotation_recalculate_totals(self):
        quotation = Quotation.objects.create(
            owner=self.user,
            lead=self.lead,
            panjang=Decimal('100'),
            lebar=Decimal('50'),
            tinggi=Decimal('50'),
            actual_weight=Decimal('10'), # volumetric will be 100*50*50/5000 = 50, so chargeable is 50
            price_per_kg=Decimal('10000'),
            insurance=Decimal('20000'),
            packing=Decimal('50000'),
            discount=Decimal('10000')
        )
        
        quotation.recalculate_totals()
        
        self.assertEqual(quotation.volumetric_weight, Decimal('50.00'))
        
        # Base price = 50 * 10000 = 500000
        # Total = 500000 + 20000 + 50000 - 10000 = 560000
        self.assertEqual(quotation.total_price, Decimal('560000'))
