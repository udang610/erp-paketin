from django.test import TestCase, Client as HttpClient
from decimal import Decimal
from django.utils import timezone
from apps.master.models import Customer, Bank
from apps.finance.models import Invoice, KpiFinance, KpiFile, KpiSheet, LDP, LDPItem, PaymentRecord, PaymentReconciliation
from apps.operations.models import Shipment
from apps.organizations.models import Branch
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class FinanceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='adminuser', email='admin@example.com', password='password')
        self.http_client = HttpClient()
        self.http_client.login(username='adminuser', password='password')
        
        self.branch = Branch.objects.create(name='Bekasi Central', code='BKS')
        self.customer = Customer.objects.create(
            name='Test PT',
            customer_code='CST0001',
            branch=self.branch,
            pic_account='Mr Test',
            pic_phone='08123456789',
            office_address='Jl. Test Raya No. 1',
            npwp='01.234.567.8-901.000',
            sales=self.user
        )
        
    def test_auto_create_kpi_finance_on_pod(self):
        # Create a Shipment
        shipment = Shipment.objects.create(
            resi_number='RESI-123',
            client=self.customer,
            origin='Jakarta',
            destination='Bandung',
            price=Decimal('50000'),
            weight=Decimal('5'),
            volume_weight=Decimal('3'),
            length=Decimal('10'),
            width=Decimal('10'),
            height=Decimal('10')
        )
        # Update status to POD
        shipment.status = 'POD'
        shipment.save()
        
        # Signal should create a KpiFinance record
        kpi = KpiFinance.objects.filter(awb='RESI-123').first()
        self.assertIsNotNone(kpi)
        self.assertEqual(kpi.penjualan, Decimal('50000'))
        
        # Signal should also attach to rolling draft invoice
        invoice = Invoice.objects.filter(client_name=self.customer.name, status='DRAFT', is_open=True).first()
        self.assertIsNotNone(invoice)
        self.assertIn(shipment, invoice.shipments.all())
        
    def test_invoice_calculation_update_totals(self):
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-001',
            client_name=self.customer.name,
            biaya_kirim=Decimal('100000'),
            diskon=Decimal('10000'),
            biaya_tambahan=Decimal('5000'),
            biaya_kemasan=Decimal('2000'),
            biaya_lain=Decimal('1000')
        )
        invoice.update_totals()
        
        # subtotal = (100000 - 10000 + 5000) + (2000 + 1000) = 95000 + 3000 = 98000
        self.assertEqual(invoice.subtotal, Decimal('98000'))
        # tax = 98000 * 0.011 = 1078.00
        self.assertEqual(invoice.tax, Decimal('1078.00'))
        # no materai since < 5jt
        self.assertEqual(invoice.materai, Decimal('0'))
        # total_amount = 98000 + 1078 = 99078
        self.assertEqual(invoice.total_amount, Decimal('99078.00'))

    def test_invoice_materai_calculation_over_5_million(self):
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-BIG',
            client_name=self.customer.name,
            biaya_kirim=Decimal('6000000')
        )
        invoice.update_totals()
        self.assertEqual(invoice.materai, Decimal('10000'))
        self.assertEqual(invoice.subtotal, Decimal('6000000'))
        self.assertEqual(invoice.tax, Decimal('66000.00'))
        self.assertEqual(invoice.total_amount, Decimal('6076000.00'))

    def test_invoice_paid_signal_updates_kpi(self):
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-002',
            client_name=self.customer.name,
            status='DRAFT'
        )
        
        kpi_file = KpiFile.objects.create(name='Test File')
        sheet = KpiSheet.objects.create(name='Test Sheet', kpi_file=kpi_file)
        
        kpi = KpiFinance.objects.create(sheet=sheet, awb='RESI-456', linked_invoice=invoice, row_status='invoiced')
        
        # Mark invoice as PAID
        invoice.status = 'PAID'
        invoice.save()
        
        kpi.refresh_from_db()
        self.assertEqual(kpi.row_status, 'completed')

    def test_invoice_payment_submission_view(self):
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-003',
            client_name=self.customer.name,
            biaya_kirim=Decimal('100000'),
            subtotal=Decimal('100000'),
            total_amount=Decimal('101100.00'),
            amount_paid=Decimal('0'),
            status='SENT'
        )
        
        # Test partial payment via POST
        url = reverse('finance:invoice_detail', kwargs={'invoice_id': invoice.id})
        response = self.http_client.post(url, {
            'add_payment': '1',
            'amount': '50000',
            'payment_method': 'Transfer Bank',
            'reference_number': 'TRX-12345'
        })
        self.assertEqual(response.status_code, 302)
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal('50000'))
        self.assertEqual(invoice.status, 'PARTIAL')
        
        # Complete payment
        response2 = self.http_client.post(url, {
            'add_payment': '1',
            'amount': '51100.00',
            'payment_method': 'Transfer Bank',
            'reference_number': 'TRX-12346'
        })
        self.assertEqual(response2.status_code, 302)
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal('101100.00'))
        self.assertEqual(invoice.status, 'PAID')

    def test_ldp_creation_and_recalculation(self):
        ldp = LDP.objects.create(
            ldp_number='LDPBKS2609290001',
            client_name=self.customer.name,
            client=self.customer,
            branch=self.branch,
            status='DRAFT'
        )
        
        LDPItem.objects.create(
            ldp=ldp,
            awb_number='AWB001',
            koli=2,
            chargeable_weight=Decimal('10'),
            freight_charge=Decimal('100000'),
            insurance_fee=Decimal('5000'),
            packing_fee=Decimal('10000'),
            handling_fee=Decimal('5000'),
            surcharges=Decimal('20000'),
            subtotal=Decimal('120000')
        )
        
        LDPItem.objects.create(
            ldp=ldp,
            awb_number='AWB002',
            koli=1,
            chargeable_weight=Decimal('5'),
            freight_charge=Decimal('50000'),
            insurance_fee=Decimal('0'),
            packing_fee=Decimal('0'),
            handling_fee=Decimal('0'),
            surcharges=Decimal('0'),
            subtotal=Decimal('50000')
        )
        
        ldp.recalculate_totals()
        self.assertEqual(ldp.total_koli, 3)
        self.assertEqual(ldp.total_weight, Decimal('15'))
        self.assertEqual(ldp.total_freight, Decimal('150000'))
        self.assertEqual(ldp.total_surcharges, Decimal('20000'))
        self.assertEqual(ldp.total_amount, Decimal('170000'))

    def test_payment_reconciliation_flow(self):
        bank = Bank.objects.create(code='BCA', name='Bank Central Asia', account_number='1234567890')
        invoice = Invoice.objects.create(
            invoice_number='INV-RECON-001',
            client_name=self.customer.name,
            total_amount=Decimal('500000'),
            amount_paid=Decimal('0'),
            status='SENT'
        )
        
        url = reverse('finance:invoice_reconcile')
        response = self.http_client.post(url, {
            'invoice_id': str(invoice.id),
            'bank_id': str(bank.id),
            'amount_paid': '500.000',
            'transfer_date': timezone.now().strftime('%Y-%m-%d'),
            'reference_number': 'REF-BCA-999',
            'notes': 'Pembayaran transfer BCA lunas'
        })
        self.assertEqual(response.status_code, 302)
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal('500000'))
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(invoice.reconciliations.count(), 1)

