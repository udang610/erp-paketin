import os
import sys
import django
from decimal import Decimal
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.crm.models import Client, Lead, Contract
from apps.master.models import Coverage, Service, MasterPrice
from apps.operations.models import Shipment
from apps.employees.models import Employee, Position
from apps.hr.attendance.models import AttendanceEvent

User = get_user_model()

def seed():
    print("Mulai seeding data...")

    # 1. Create User & Employee
    user, created = User.objects.get_or_create(username='admin_test', defaults={
        'email': 'admin@test.com',
        'is_staff': True,
        'is_superuser': True
    })
    if created:
        user.set_password('paketin123')
        user.save()
        print("User 'admin_test' (pass: paketin123) dibuat.")

    pos, _ = Position.objects.get_or_create(name='Staff Operasional')
    employee, _ = Employee.objects.get_or_create(user=user, defaults={
        'employee_id': 'EMP-001',
        'full_name': 'Test Admin',
        'position': pos
    })

    # 2. Master Data (Coverage & Service)
    cov_jkt, _ = Coverage.objects.get_or_create(name='Jakarta', code='CGK', type='CITY')
    cov_bdg, _ = Coverage.objects.get_or_create(name='Bandung', code='BDO', type='CITY')
    svc_udara, _ = Service.objects.get_or_create(name='Cargo Udara', code='UDR', service_type='UDARA')

    # 3. Master Price
    master_price, _ = MasterPrice.objects.get_or_create(
        origin=cov_jkt,
        destination=cov_bdg,
        service=svc_udara,
        defaults={
            'price_per_kg': Decimal('15000'),
            'min_weight': 10,
            'lead_time': '1-2 Hari'
        }
    )

    # 4. Client & Contract (CRM)
    client, _ = Client.objects.get_or_create(
        company_name='PT Tester Indo',
        defaults={
            'customer_status': 'ACTIVE',
            'owner': user
        }
    )
    contract, _ = Contract.objects.get_or_create(
        contract_number='KTR-TEST-001',
        client=client,
        owner=user,
        defaults={
            'title': 'Kontrak Pengiriman Tester',
            'start_date': datetime.date(2026, 1, 1),
            'end_date': datetime.date(2026, 12, 31),
            'status': 'ACTIVE',
            'value': Decimal('10000000')
        }
    )

    # 5. Asset Category & Item (HR)
    from apps.hr.asset_request.models import AssetCategory, AssetItem
    cat, _ = AssetCategory.objects.get_or_create(name='IT Asset')
    item, _ = AssetItem.objects.get_or_create(
        name='Laptop Lenovo Thinkpad',
        category=cat,
        defaults={
            'stock': 10,
            'unit': 'Unit',
            'purchase_price': Decimal('15000000')
        }
    )

    # 6. Payroll Settings
    from apps.hr.payroll.models import SalarySetting
    SalarySetting.objects.get_or_create(
        employee=employee,
        defaults={
            'basic_salary': Decimal('5000000'),
            'daily_rate': Decimal('200000'),
            'allowance': Decimal('500000')
        }
    )

    print("Data Dummy berhasil dibuat!")

if __name__ == '__main__':
    seed()
