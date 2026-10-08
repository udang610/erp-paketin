import logging
from django.utils import timezone
from apps.master.models import Customer

logger = logging.getLogger(__name__)

def sync_client_to_master(client, user=None):
    """
    Sinkronisasi data dari CRM Client ke Master Customer ERP.
    Jika belum ada Customer di Master, akan dibuatkan record baru.
    Jika sudah ada, field utama akan diperbarui dari data Client.
    """
    created = False
    customer = client.master_customer

    if not customer:
        # Coba cari Customer di Master dengan nama yang sama persis jika belum terlink
        customer = Customer.objects.filter(name__iexact=client.company_name.strip()).first()
        if not customer:
            customer = Customer()
            created = True
    
    # Mapping Data dari Client ke Master Customer
    customer.name = client.company_name
    customer.divisi = client.divisi or ''
    customer.account_type = client.account_type or 'MASTER'
    customer.pic_account = client.contact_person or client.company_name
    customer.pic_phone = client.phone or '-'
    customer.email = client.email or ''
    customer.website = client.website or ''
    customer.office_address = client.address or ''
    customer.city = client.city or ''
    customer.district = client.district or ''
    customer.postal_code = client.postal_code or ''
    customer.npwp = client.npwp or ''
    customer.type_industry = client.industry or 'OTHER'
    
    # Pickup details
    customer.pickup_same_as_office = True
    customer.pic_pickup = client.pic_pickup or client.contact_person or client.company_name
    customer.pic_pickup_phone = client.pic_pickup_phone or client.phone or '-'
    
    # Payment & Finance details
    customer.payment_type = client.payment_type or 'Transfer'
    customer.term_of_payment = client.term_of_payment or '0'
    if not customer.ppn_percentage:
        customer.ppn_percentage = '1.2'
    if customer.insurance_percentage is None:
        customer.insurance_percentage = 0
    if customer.min_premi_insurance is None:
        customer.min_premi_insurance = 0
    if customer.with_pod_resi is None:
        customer.with_pod_resi = False
    
    if client.owner:
        customer.sales = client.owner
        
    # Status aktif jika di CRM sudah Aktif / Priority / Regular
    if client.customer_status in ['ACTIVE', 'PRIORITY', 'REGULAR']:
        customer.status = 'Aktif'
        customer.is_active = True
    elif not customer.pk:
        customer.status = 'Aktif'
        customer.is_active = True

    if not customer.effective_start_date:
        customer.effective_start_date = timezone.now().date()

    customer.save()

    # Link-kan master_customer ke client jika belum
    if client.master_customer != customer:
        client.master_customer = customer
        # Pastikan status client juga ACTIVE jika customer sudah aktif
        if client.customer_status == 'PROSPECT':
            client.customer_status = 'ACTIVE'
        client.save(update_fields=['master_customer', 'customer_status'])

    return customer, created


def sync_master_to_client(customer, user=None):
    """
    Sinkronisasi data dari Master Customer ERP kembali ke CRM Client.
    """
    client = getattr(customer, 'crm_client', None)
    if not client:
        return None, False

    client.company_name = customer.name
    client.divisi = customer.divisi or ''
    client.account_type = customer.account_type or 'MASTER'
    if customer.pic_account:
        client.contact_person = customer.pic_account
    if customer.pic_phone:
        client.phone = customer.pic_phone
    if customer.email:
        client.email = customer.email
    if customer.website:
        client.website = customer.website
    if customer.office_address:
        client.address = customer.office_address
    if customer.city:
        client.city = customer.city
    if customer.district:
        client.district = customer.district
    if customer.pic_pickup:
        client.pic_pickup = customer.pic_pickup
    if customer.pic_pickup_phone:
        client.pic_pickup_phone = customer.pic_pickup_phone
    if customer.payment_type:
        client.payment_type = customer.payment_type
    if customer.term_of_payment:
        client.term_of_payment = customer.term_of_payment
    if customer.npwp:
        client.npwp = customer.npwp
    if customer.type_industry:
        client.industry = customer.type_industry
    if customer.sales:
        client.owner = customer.sales

    if customer.status == 'Aktif':
        if client.customer_status == 'PROSPECT':
            client.customer_status = 'ACTIVE'

    client.save()
    return client, True
