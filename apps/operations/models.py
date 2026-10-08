from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from apps.core.validators import validate_document_file, validate_image_file
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File

class PickupOrder(models.Model):
    pickup_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Pickup", blank=True, null=True)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ASSIGNED_TO_DRIVER', 'Assigned to Driver'),
        ('PICKED_UP', 'Picked Up'),
        ('CANCELLED', 'Cancelled'),
    ]

    pickup_date = models.DateField(verbose_name="Tanggal Pickup")
    pickup_time = models.TimeField(verbose_name="Waktu Pickup", null=True, blank=True)
    vehicle = models.CharField(max_length=50, blank=True, null=True, verbose_name="Req. Vehicle")
    client = models.ForeignKey('master.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Customer")
    
    reff_doc_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Reff Doc. No (PR)")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    
    req_packing = models.BooleanField(default=False, verbose_name="Req. Packing?")
    insurance = models.BooleanField(default=False, verbose_name="Insurance?")
    
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="City")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="District")
    pic_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="PIC Pickup")
    pic_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="PIC Phone")
    pickup_address = models.TextField(blank=True, null=True, verbose_name="Pickup Address")
    
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Weight", default=0)
    colly = models.IntegerField(verbose_name="Colly", default=1)
    shipment_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Shipment Type")
    description_item = models.TextField(blank=True, null=True, verbose_name="Description Item")
    
    file_upload = models.FileField(upload_to='pickup_docs/', blank=True, null=True, validators=[validate_document_file], verbose_name="File Upload")
    
    driver = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_pickups', verbose_name="Driver")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_hidden = models.BooleanField(default=False, verbose_name="Disembunyikan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pickup_number:
            import datetime
            today = datetime.date.today()
            date_str = today.strftime('%Y%m%d')
            prefix = f"PKP-{date_str}-"
            
            last_pickup = PickupOrder.objects.filter(pickup_number__startswith=prefix).order_by('-pickup_number').first()
            if last_pickup:
                try:
                    last_num = int(last_pickup.pickup_number.split('-')[-1])
                except ValueError:
                    last_num = 0
                new_num = last_num + 1
            else:
                new_num = 1
            self.pickup_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pickup_number} - {self.client.company_name if self.client else 'Unknown'}"

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PICKUP', 'Pick Up'),
        ('INBOUND_ORIGIN', 'Inbound Origin'),
        ('OUTGOING', 'Outgoing'),
        ('TRANSFER', 'Transfer Location'),
        ('TRANSIT', 'Transit'),
        ('INCOMING_DESTINATION', 'Incoming Destination'),
        ('DELIVERY', 'Delivery'),
        ('DELIVERY_FAILED', 'Gagal Antar (Undelivered)'),
        ('REDELIVER', 'Re-Delivery'),
        ('POD', 'POD'),
        ('POD_BALIK', 'POD Balik'),
        ('PARTIAL_DELIVERED', 'Partial Delivered'),
        ('RETURNED', 'Return'),
        ('VOID', 'Void'),
    ]

    SERVICE_CHOICES = [
        ('REG', 'Reguler'),
        ('ODS', 'One Day Service'),
        ('SDS', 'Same Day Service'),
        ('RD', 'Reguler Darat'),
        ('RL', 'Reguler Laut'),
        ('RUC', 'Reguler Udara Cargo'),
        ('RU', 'Reguler Udara'),
        ('TRK', 'Trucking'),
    ]

    # Divisor per service for volumetric weight calculation: PxLxT / divisor
    SERVICE_DIVISOR = {
        'REG': 5000, 'ODS': 5000, 'SDS': 5000,
        'RD': 4000, 'RL': 1000000, 'RUC': 6000,
        'RU': 5000, 'TRK': 4000,
    }
    
    COMPANY_CHOICES = [
        ('PT AMANAH', 'PAKETIN CARGO (PT AMANAH)'),
        ('PT SARANA', 'SARANA EXPRESS (PT SARANA)'),
        ('PT SINERGI', 'PAKETIN EXPRESS (PT SINERGI)'),
    ]

    INPUT_TYPE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('IMPORT', 'Import Excel'),
    ]
    
    # Identitas Resi
    resi_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Resi")
    
    # Klien (PT) yang mengirim, diambil dari CRM
    client = models.ForeignKey('master.Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Perusahaan/Klien Pengirim (Kontrak)")
    
    # Hubungan ke CRM untuk traceability
    contract = models.ForeignKey('crm.Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments', verbose_name="Kontrak Terkait")
    quotation = models.ForeignKey('crm.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments', verbose_name="Penawaran (Quotation)")
    
    # Data Pengirim (Detail Shipper) 
    sender_name = models.CharField(max_length=255, verbose_name="Nama Penanggung Jawab (PIC)", blank=True, null=True)
    sender_attention = models.CharField(max_length=255, verbose_name="Shipper Attention", blank=True, null=True)
    sender_phone = models.CharField(max_length=50, verbose_name="No. HP PIC", blank=True, null=True)
    sender_address = models.TextField(verbose_name="Alamat Pengirim", blank=True, null=True)
    sender_city = models.CharField(max_length=100, verbose_name="Kota Pengirim", blank=True, null=True)
    sender_district = models.CharField(max_length=100, verbose_name="Kecamatan Pengirim", blank=True, null=True)
    sender_postal_code = models.CharField(max_length=10, verbose_name="Kode Pos Pengirim", blank=True, null=True)
    shipper_same_as_pickup = models.BooleanField(default=False, verbose_name="Detail Shipper = Detail Pickup")
    
    # Data Penerima (Detail Receiver)
    receiver_name = models.CharField(max_length=255, verbose_name="Nama Penerima")
    receiver_attention = models.CharField(max_length=255, verbose_name="Receiver Attention", blank=True, null=True)
    receiver_phone = models.CharField(max_length=50, verbose_name="No. HP Penerima")
    receiver_address = models.TextField(verbose_name="Alamat Penerima")
    receiver_city = models.CharField(max_length=100, verbose_name="Kota Penerima", blank=True, null=True)
    receiver_district = models.CharField(max_length=100, verbose_name="Kecamatan Penerima", blank=True, null=True)
    receiver_postal_code = models.CharField(max_length=10, verbose_name="Kode Pos Penerima", blank=True, null=True)
    
    # Detail Pengiriman
    origin = models.CharField(max_length=100, verbose_name="Kota Asal")
    destination = models.CharField(max_length=100, verbose_name="Kota Tujuan")
    service_type = models.CharField(max_length=5, choices=SERVICE_CHOICES, default='REG', verbose_name="Tipe Layanan")

    @property
    def get_tlc_origin(self):
        if not self.origin:
            return "-"
        import re
        from apps.master.models import Coverage
        from apps.master.display import clean_city_name
        search_city = clean_city_name(self.origin)
        coverage = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
        if coverage and coverage.tlc:
            return coverage.tlc.upper()
        # Fallback to the first 3 letters of the stripped city name instead of "KOT"
        return search_city[:3].upper()

    @property
    def get_tlc_dest(self):
        if not self.destination:
            return "-"
        import re
        from apps.master.models import Coverage
        from apps.master.display import clean_city_name
        search_city = clean_city_name(self.destination)
        coverage = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
        if coverage and coverage.tlc:
            return coverage.tlc.upper()
        return search_city[:3].upper()

    @property
    def get_city_origin(self):
        if not self.origin:
            return "-"
        from apps.master.display import city_display_name
        return city_display_name(self.origin)

    @property
    def get_city_dest(self):
        if not self.destination:
            return "-"
        from apps.master.display import city_display_name
        return city_display_name(self.destination)

    @property
    def origin_clean(self):
        if not self.origin:
            return "-"
        import re
        from apps.master.display import clean_city_name
        name = clean_city_name(self.origin)
        name = re.sub(r"(?i)^(kota|kabupaten|kab\.)\s+", "", name).strip().title()
        tlc = self.get_tlc_origin
        if tlc and tlc != '-':
            return f"{name} - {tlc}"
        return name

    @property
    def destination_clean(self):
        if not self.destination:
            return "-"
        import re
        from apps.master.display import clean_city_name
        name = clean_city_name(self.destination)
        name = re.sub(r"(?i)^(kota|kabupaten|kab\.)\s+", "", name).strip().title()
        tlc = self.get_tlc_dest
        if tlc and tlc != '-':
            return f"{name} - {tlc}"
        return name

    @property
    def return_record(self):
        """Return latest ReturnShipment instance if any."""
        return self.returns.order_by('-created_at').first()

    @property
    def has_failed_delivery(self):
        """Check if shipment ever had a failed delivery status or record."""
        if self.status in ['DELIVERY_FAILED', 'REDELIVER', 'RETURNED']:
            return True
        if self.returns.exists():
            return True
        return self.tracking_history.filter(status__in=['DELIVERY_FAILED', 'REDELIVER', 'RETURNED']).exists()

    @property
    def is_redelivery(self):
        """Check if shipment is in redelivery status or action."""
        if self.status == 'REDELIVER':
            return True
        ret = self.return_record
        if ret and ret.action_type == 'REDELIVER':
            return True
        return self.tracking_history.filter(status='REDELIVER').exists()

    @property
    def is_returned_to_origin(self):
        """Check if shipment is returned to origin."""
        if self.status == 'RETURNED':
            return True
        ret = self.return_record
        if ret and ret.action_type == 'RETURN_TO_ORIGIN':
            return True
        return self.tracking_history.filter(status='RETURNED').exists()
    
    # Master Data Relations
    origin_coverage = models.ForeignKey('master.Coverage', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipment_origins')
    destination_coverage = models.ForeignKey('master.Coverage', on_delete=models.SET_NULL, null=True, blank=True, related_name='shipment_destinations')
    service_master = models.ForeignKey('master.Service', on_delete=models.SET_NULL, null=True, blank=True)
    is_manual_override = models.BooleanField('Input Manual (Bypass)', default=False)
    
    # Shipment Info (COD, Insurance, Surcharge, Handling)
    is_cod = models.BooleanField(default=False, verbose_name="COD?")
    cod_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="COD Value")
    insurance_type = models.CharField(max_length=5, choices=[('NO', 'No'), ('YES', 'Yes')], default='NO', verbose_name="Insurance?")
    item_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Item Value (Rp)")
    surcharge_type = models.CharField(max_length=5, choices=[('NO', 'No'), ('YES', 'Yes')], default='NO', verbose_name="Surcharge?")
    surcharge_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Surcharge Cost")
    handling_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Handling Cost")
    
    # Detail Package
    SHIPMENT_TYPE_CHOICES = [
        ('PACKAGE', 'Package'),
        ('DOCUMENT', 'Document'),
    ]
    shipment_type_detail = models.CharField(max_length=20, choices=SHIPMENT_TYPE_CHOICES, default='PACKAGE', verbose_name="Shipment Type")
    pickup_number_ref = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pickup No (Ref)")
    reference_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Reference No")
    special_instruction = models.TextField(blank=True, null=True, verbose_name="Special Instruction")
    description_item = models.TextField(blank=True, null=True, verbose_name="Description Item")
    
    PAYMENT_CHOICES = [
        ('CASH', 'Tunai (POS Cash)'),
        ('CREDIT', 'Tagihan / Invoice (POS Credit)'),
    ]
    
    # Dimensi & Harga
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Berat Aktual (Kg)", default=0)
    length = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Panjang (cm)", default=0)
    width = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Lebar (cm)", default=0)
    height = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tinggi (cm)", default=0)
    volume_weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Berat Volume (Kg)", default=0)
    chargeable_weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Berat Ditagihkan (Chargeable)", default=0)
    total_colly = models.IntegerField(verbose_name="Total Koli", default=1)
    
    packing_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Biaya Packing (Rp)")
    price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Harga (Rp)", default=0)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='CASH', verbose_name="Tipe Pembayaran")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status Pengiriman")
    
    # Metadata
    input_type = models.CharField(max_length=10, choices=INPUT_TYPE_CHOICES, default='MANUAL', verbose_name="Tipe Input")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_shipments', verbose_name="Dibuat Oleh")
    is_hidden = models.BooleanField(default=False, verbose_name="Disembunyikan")
    
    # POD (Proof Of Delivery) Fields
    pod_receiver_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nama Penerima (POD)")
    pod_date = models.DateTimeField(blank=True, null=True, verbose_name="Tanggal Terima (POD)")
    pod_image = models.ImageField(upload_to='pod_images/', blank=True, null=True, verbose_name="Bukti Foto (POD)")
    with_do_balik = models.BooleanField(default=False, verbose_name="DO Balik?")
    do_balik_date = models.DateField(blank=True, null=True, verbose_name="Tanggal DO Balik")

    # Failed Delivery (Undelivered) Fields
    delivery_attempts = models.IntegerField(default=0, verbose_name="Jumlah Percobaan Antar")
    failed_reason = models.CharField(max_length=100, blank=True, null=True, verbose_name="Alasan Gagal Antar")
    failed_note = models.TextField(blank=True, null=True, verbose_name="Catatan Gagal Antar")
    failed_date = models.DateTimeField(blank=True, null=True, verbose_name="Waktu Gagal Antar")
    failed_image = models.ImageField(upload_to='pod_failed/', blank=True, null=True, verbose_name="Bukti Foto Gagal Antar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sender = self.client.name if self.client else self.sender_name
        return f"{self.resi_number} ({sender} → {self.receiver_name})"

    @property
    def is_do_balik(self):
        if self.with_do_balik or self.status == 'POD_BALIK' or self.do_balik_date is not None:
            return True
        if self.client and getattr(self.client, 'with_pod_resi', False):
            return True
        return False

    @property
    def actual_weight(self):
        total = sum([item.actual_weight for item in self.items.all() if item.actual_weight])
        return total if total > 0 else self.weight

    @property
    def calculated_volume_weight(self):
        total = sum([item.get_volume_weight() for item in self.items.all()])
        return total if total > 0 else self.volume_weight

    @property
    def get_courier_name(self):
        delivery_manifest = self.manifests.filter(manifest_type='DELIVERY').select_related('driver').first()
        if delivery_manifest and delivery_manifest.driver:
            return delivery_manifest.driver.get_full_name() or delivery_manifest.driver.username
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.username
        return "-"

    @property
    def get_active_outgoing_manifest(self):
        return self.manifests.filter(manifest_type='OUTGOING', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).first()

    @property
    def colly(self):
        return self.total_colly or 1

    @property
    def insurance_amount(self):
        return getattr(self, 'insurance_fee', None) or 0

    @property
    def other_cost(self):
        return (self.surcharge_cost or 0) + (self.handling_cost or 0)

    @property
    def total_surcharges(self):
        return (self.packing_cost or 0) + self.other_cost + (self.insurance_amount or 0)

    @property
    def total_amount(self):
        return (self.price or 0) + self.total_surcharges

    @property
    def price_per_kg(self):
        from decimal import Decimal
        w = Decimal(str(self.chargeable_weight or self.weight or 1))
        p = Decimal(str(self.price or 0))
        if w > 0 and p > 0:
            return (p / w).quantize(Decimal('0.01'))
        return Decimal('0')

class ShipmentColly(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='collies')
    barcode = models.CharField(max_length=100, unique=True, verbose_name="Barcode Koli")
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Berat (Kg)", default=0)
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return self.barcode

class ShipmentItem(models.Model):
    class PackingChoices(models.TextChoices):
        NONE = 'NONE', 'Tidak Ada'
        FULL = 'FULL', 'Packing Full'
        KAYU = 'KAYU', 'Packing Kayu'
        BUSA_KARDUS = 'BUSA_KARDUS', 'Packing Busa/Kardus'

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='items')
    actual_weight = models.DecimalField('Weight Actual (kg)', max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField('Colly', default=1)
    panjang = models.DecimalField('Panjang (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    lebar = models.DecimalField('Lebar (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    tinggi = models.DecimalField('Tinggi (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    packing = models.CharField('Packing', max_length=20, choices=PackingChoices.choices, default=PackingChoices.NONE)
    description = models.CharField('Description Item', max_length=255, blank=True, null=True)
    
    def get_packing_cost(self):
        """Calculate packing cost based on type: (P+L+T+15)/3 * multiplier"""
        p = float(self.panjang or 0)
        l = float(self.lebar or 0)
        t = float(self.tinggi or 0)
        base = (p + l + t + 15) / 3
        multipliers = {'FULL': 4000, 'KAYU': 2500, 'BUSA_KARDUS': 2000}
        return base * multipliers.get(self.packing, 0)
        
    def get_volume_weight(self):
        """Calculate volumetric weight: (P*L*T) / 4000 (standard darat) - though usually varies by service, standard 4000 is common fallback"""
        p = float(self.panjang or 0)
        l = float(self.lebar or 0)
        t = float(self.tinggi or 0)
        return (p * l * t) / 4000
    
    def __str__(self):
        return f"Item of {self.shipment.resi_number}"

class Manifest(models.Model):
    MANIFEST_TYPE_CHOICES = [
        ('PICKUP', 'Pickup Manifest'),
        ('OUTGOING', 'Outgoing Manifest'),
        ('TRANSFER', 'Transfer Location Manifest'),
        ('DELIVERY', 'Delivery Runsheet'),
    ]
    STATUS_CHOICES = [
        ('PREPARING', 'Persiapan'),
        ('ON_THE_WAY', 'Dalam Perjalanan'),
        ('COMPLETED', 'Selesai'),
        ('CANCELLED', 'Void'),
    ]

    manifest_type = models.CharField(max_length=20, choices=MANIFEST_TYPE_CHOICES, default='OUTGOING', verbose_name="Tipe Manifest")

    manifest_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Manifest")
    driver = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user_type': 'DRIVER'}, verbose_name="Driver/Supir")
    vehicle = models.ForeignKey('master.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kendaraan")
    vendor = models.ForeignKey('finance.Vendor', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vendor Ekspedisi")
    vendor_ref_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Resi / SPK Vendor")
    flight_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Flight No / SMU (Air Freight)")
    vessel_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nama Kapal / No. BL (Sea Freight)")
    
    # Outgoing Specific Fields
    destination_city = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tlc / City Destination")
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='manifests', verbose_name="Branch")
    colly_cmo = models.IntegerField(default=0, verbose_name="Colly CMO")
    actual_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Actual Weight Manifest")
    commodity = models.CharField(max_length=255, blank=True, null=True, verbose_name="Commodity")
    description = models.TextField(blank=True, null=True, verbose_name="Description / Reason")
    is_bypass = models.BooleanField(default=False, verbose_name="Outgoing By Pass")
    pic = models.CharField(max_length=255, blank=True, null=True, verbose_name="PIC / Penanggung Jawab")
    is_hidden = models.BooleanField(default=False, verbose_name="Disembunyikan")

    @property
    def get_outgoing_manifest_number(self):
        first_shipment = self.shipments.first()
        if first_shipment:
            outgoing = first_shipment.manifests.filter(manifest_type='OUTGOING', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).first()
            if outgoing:
                return outgoing.manifest_number
        return self.vendor_ref_no or "-"

    @property
    def get_tlc_dest(self):
        if not self.destination_city:
            return "-"
        
        # If it's already in format "TLC - City"
        if " - " in self.destination_city:
            parts = self.destination_city.split(" - ", 1)
            if len(parts[0]) == 3:
                return parts[0].upper()
        
        # Try to find from Coverage
        from apps.master.models import Coverage
        import re
        # Check if destination_city is exactly the city name or contains it
        search_city = re.sub(r'(?i)^(kota|kabupaten)\s+', '', self.destination_city).strip()
        coverage = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
        if coverage and coverage.tlc:
            return coverage.tlc.upper()
            
        # Fallback to first 3 letters of the stripped city name
        return search_city[:3].upper()

    @property
    def get_city_dest(self):
        if not self.destination_city:
            return "-"
        
        city = self.destination_city
        if " - " in self.destination_city:
            parts = self.destination_city.split(" - ", 1)
            if len(parts[0]) == 3:
                city = parts[1]
                
        import re
        return re.sub(r'(?i)^(kota|kabupaten)\s+', '', city).strip()

    # Transfer Manifest Specific Fields
    departure_time = models.TimeField(null=True, blank=True, verbose_name="Departure Time")
    arrival_date = models.DateField(null=True, blank=True, verbose_name="Arrival Date")
    arrival_time = models.TimeField(null=True, blank=True, verbose_name="Arrival Time")
    transport_mode = models.CharField(max_length=50, null=True, blank=True, verbose_name="Moda Transportasi")
    vendor_middle = models.ForeignKey('finance.Vendor', on_delete=models.SET_NULL, null=True, blank=True, related_name="manifest_vendor_middle", verbose_name="Vendor Middle")

    date = models.DateField(verbose_name="Tanggal Keberangkatan")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PREPARING')

    @property
    def get_transfer_mode(self):
        if self.manifest_type != 'TRANSFER':
            return None
        if self.flight_no: return 'AIR'
        if self.vessel_name: return 'SEA'
        if self.vehicle or self.driver: return 'LAND'
        if self.vendor: return 'VENDOR'
        
        # Fallbacks for empty manifests
        if self.transport_mode in ['UDARA', 'AIR']: return 'AIR'
        if self.transport_mode in ['LAUT', 'SEA']: return 'SEA'
        if self.transport_mode in ['DARAT']: return 'VENDOR' # Vendor form has DARAT choice
        if self.transport_mode == 'LAND': return 'LAND'
        if self.transport_mode == 'VENDOR': return 'VENDOR'
        
        return 'VENDOR'
    
    # Relasi: Satu Manifest bisa bawa banyak Resi (Shipment)
    shipments = models.ManyToManyField(Shipment, related_name='manifests', verbose_name="Daftar Resi", blank=True)
    
    # Relasi: Manifest tipe PICKUP bawa banyak PickupOrder
    pickup_orders = models.ManyToManyField(PickupOrder, related_name='pickup_manifests', verbose_name="Daftar Pickup", blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='manifests_created', verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_colly(self):
        if self.manifest_type == 'PICKUP':
            orders = self.pickup_orders.all()
            return sum(p.colly for p in orders) if orders else 0
        shipments = self.shipments.all()
        return sum(s.colly for s in shipments) if shipments else (self.colly_cmo or 0)

    @property
    def total_weight(self):
        if self.manifest_type == 'PICKUP':
            orders = self.pickup_orders.all()
            return sum(p.weight for p in orders) if orders else 0
        shipments = self.shipments.all()
        return sum(s.total_weight for s in shipments) if shipments else (self.actual_weight or 0)

    def __str__(self):
        driver_name = self.driver.first_name if self.driver else "Tanpa Supir"
        return f"{self.manifest_number} - {driver_name}"

class Tracking(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=255, verbose_name="Lokasi Saat Ini")
    description = models.TextField(verbose_name="Keterangan", blank=True, null=True)
    # Waktu kejadian sebenarnya; timestamp tetap menyimpan waktu input/audit.
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Waktu Kejadian")
    step_order = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Urutan Langkah")
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def formatted_location(self):
        """Format coverage locations consistently as TLC - city."""
        if not self.location:
            return "-"

        import re
        from apps.master.models import Coverage
        from apps.master.display import coverage_city_label, clean_city_name

        raw = str(self.location).strip()

        # Check if already formatted like 'TLC - City'
        if " - " in raw:
            parts = raw.split(" - ", 1)
            if len(parts[0].strip()) == 3 and parts[0].strip().isalpha():
                tlc = parts[0].strip().upper()
                city = clean_city_name(parts[1])
                return f"{tlc} - {city}"

        # Clean prefix keywords like 'Cabang', 'Hub', 'Gudang', 'Kantor', 'Branch'
        cleaned = re.sub(r'(?i)^(cabang|hub|gudang|kantor|branch|agen|pos|gerai)\s+', '', raw).strip()

        # 1. Exact match on city name
        cov = Coverage.objects.filter(city__iexact=cleaned, is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
        if cov:
            return coverage_city_label(cov)

        # 2. Match with Kota/Kabupaten permutations
        sub_clean = re.sub(r'(?i)^(kota|kabupaten|kab\.?)\s+', '', cleaned).strip()
        if sub_clean:
            cov = Coverage.objects.filter(city__iexact=f"Kota {sub_clean}", is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            if not cov:
                cov = Coverage.objects.filter(city__iexact=f"Kabupaten {sub_clean}", is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            if not cov:
                cov = Coverage.objects.filter(city__iexact=sub_clean, is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            if cov:
                return coverage_city_label(cov)

        # 3. Whole word regex match for multi-word locations
        words = [w for w in re.split(r'\s+', cleaned) if len(w) >= 3 and w.lower() not in ['kota', 'kabupaten', 'wilayah']]
        for w in sorted(words, key=len, reverse=True):
            cov = Coverage.objects.filter(city__iregex=r'(^|\s)' + re.escape(w) + r'($|\s)', is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            if cov:
                return coverage_city_label(cov)

        # 4. Fallback to startswith
        if sub_clean:
            cov = Coverage.objects.filter(city__istartswith=sub_clean, is_active=True).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            if cov:
                return coverage_city_label(cov)

        return cleaned

    @property
    def badge_color(self):
        """Return Bootstrap color class for status badge in timeline."""
        color_map = {
            'PENDING': 'secondary',
            'PICKUP': 'info',
            'INBOUND_ORIGIN': 'primary',
            'OUTGOING': 'primary',
            'TRANSFER': 'primary',
            'TRANSIT': 'warning',
            'INCOMING_DESTINATION': 'primary',
            'DELIVERY': 'info',
            'DELIVERY_FAILED': 'danger',
            'REDELIVER': 'info',
            'POD': 'success',
            'POD_BALIK': 'success',
            'PARTIAL_DELIVERED': 'warning',
            'RETURNED': 'danger',
            'VOID': 'dark',
        }
        return color_map.get(self.status, 'secondary')

    @property
    def status_icon(self):
        """Return Phosphor icon class for tracking status."""
        icon_map = {
            'PENDING': 'ph-fill ph-note-pencil',
            'PICKUP': 'ph-fill ph-van',
            'INBOUND_ORIGIN': 'ph-fill ph-warehouse',
            'OUTGOING': 'ph-fill ph-truck',
            'TRANSFER': 'ph-fill ph-arrows-left-right',
            'TRANSIT': 'ph-fill ph-path',
            'INCOMING_DESTINATION': 'ph-fill ph-package',
            'DELIVERY': 'ph-fill ph-moped-front',
            'DELIVERY_FAILED': 'ph-fill ph-x-circle',
            'REDELIVER': 'ph-fill ph-arrows-clockwise',
            'POD': 'ph-fill ph-check-circle',
            'POD_BALIK': 'ph-fill ph-seal-check',
            'PARTIAL_DELIVERED': 'ph-fill ph-warning-circle',
            'RETURNED': 'ph-fill ph-arrow-u-up-left',
            'VOID': 'ph-fill ph-x-circle',
        }
        return icon_map.get(self.status, 'ph-fill ph-circle')

    @property
    def manifest_number(self):
        """Extract manifest number if present in raw description."""
        import re
        match = re.search(r'((?:MNF|DEL|TRF|PKP|INB)-[\w-]+)', self.description or '')
        return match.group(1) if match else None

    @property
    def professional_description(self):
        """Format tracking description into a concise, clean, and general logistics narrative."""
        import re
        raw = (self.description or '').strip()
        st = self.status

        # Strip internal raw tokens from user custom text if any
        clean_raw = re.sub(r'\(POS\s*(Credit|Cash)\)', '', raw, flags=re.IGNORECASE)
        clean_raw = re.sub(r'(?:Masuk|via)?\s*Manifest\s*(?:MNF|DEL|TRF|PKP|INB)?-?[\w-]+', '', clean_raw, flags=re.IGNORECASE).strip()
        clean_raw = re.sub(r'^[|\s,-]+|[|\s,-]+$', '', clean_raw).strip()

        if st == 'PENDING':
            if self.shipment and self.shipment.pickup_number_ref:
                if not clean_raw or any(k in raw.lower() for k in ['pos credit', 'pos cash', 'resi dibuat', 'resi pengiriman', 'siap diproses', 'order dibuat', 'menunggu penjemputan', 'pickup order dibuat', 'menunggu barang diambil']):
                    return "Pickup order dibuat, menunggu barang diambil"
            else:
                if not clean_raw or any(k in raw.lower() for k in ['pos credit', 'pos cash', 'resi dibuat', 'resi pengiriman', 'siap diproses', 'order dibuat', 'menunggu penjemputan', 'diterima di gudang', 'gudang asal']):
                    return "Paket telah diterima di gudang asal dan siap diproses"
            return clean_raw

        elif st == 'PICKUP':
            if not clean_raw or any(k in raw.lower() for k in ['permintaan', 'pickup', 'penjemputan', 'berhasil', 'menunggu proses selanjutnya']):
                return "Barang berhasil di-pickup, menunggu proses selanjutnya"
            return clean_raw

        elif st == 'INBOUND_ORIGIN':
            if not clean_raw or any(k in raw.lower() for k in ['inbound', 'tiba di gudang asal']):
                return "Paket telah diterima di gudang asal"
            return clean_raw

        elif st == 'OUTGOING':
            if not clean_raw or any(k in raw.lower() for k in ['manifest', 'diberangkatkan', 'outgoing']):
                return "Paket telah diberangkatkan ke kota tujuan"
            return clean_raw

        elif st == 'TRANSFER':
            if not clean_raw or any(k in raw.lower() for k in ['transfer', 'manifest']):
                return "Paket dalam proses transfer antar hub"
            return clean_raw

        elif st == 'TRANSIT':
            if not clean_raw or any(k in raw.lower() for k in ['transit']):
                return "Paket telah tiba di hub transit"
            return clean_raw

        elif st == 'INCOMING_DESTINATION':
            if not clean_raw or any(k in raw.lower() for k in ['incoming', 'tiba di gudang tujuan']):
                return "Paket telah tiba di gudang tujuan"
            return clean_raw

        elif st == 'DELIVERY':
            if not clean_raw or any(k in raw.lower() for k in ['delivery', 'diantar', 'dibawa', 'manifest']):
                return "Paket sedang dibawa kurir menuju alamat penerima"
            return clean_raw

        elif st == 'DELIVERY_FAILED':
            return clean_raw or "Paket gagal diantar menuju alamat penerima"

        elif st == 'REDELIVER':
            if not clean_raw or any(k in raw.lower() for k in ['redeliver', 'kirim ulang', 'diantar ulang', 're-delivery']):
                return clean_raw or "Paket dijadwalkan untuk dikirim ulang (Re-Delivery)"
            return clean_raw

        elif st in ['POD', 'POD_BALIK']:
            receiver = self.shipment.pod_receiver_name or ''
            if not receiver and 'Penerima:' in raw:
                parts = raw.split('Penerima:', 1)
                receiver = parts[1].split('|')[0].strip() if len(parts) > 1 else ''

            if st == 'POD_BALIK':
                if receiver:
                    return f"POD Balik selesai (Penerima: {receiver})"
                return "POD Balik telah selesai diproses"
            else:
                if receiver:
                    return f"Paket telah diterima oleh {receiver}"
                return "Paket telah diterima oleh penerima"

        elif st == 'PARTIAL_DELIVERED':
            return clean_raw or "Paket telah terkirim sebagian"

        elif st == 'RETURNED':
            return clean_raw or "Paket dalam proses pengembalian (Return)"

        elif st == 'VOID':
            return "Pengiriman dibatalkan"

        return clean_raw or raw

    class Meta:
        ordering = ['-step_order', '-occurred_at', '-timestamp']

    def save(self, *args, **kwargs):
        if not self.step_order and self.shipment_id:
            max_order = self.shipment.tracking_history.aggregate(models.Max('step_order'))['step_order__max'] or 0
            self.step_order = max_order + 10
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment.resi_number} - {self.status} at {self.location} (Step {self.step_order})"


class InboundSession(models.Model):
    inbound_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Inbound")
    location = models.CharField(max_length=255, verbose_name="Lokasi Gudang")
    description = models.TextField(verbose_name="Keterangan", blank=True, null=True)
    shipments = models.ManyToManyField(Shipment, related_name='inbound_sessions', verbose_name="Daftar Resi Inbound")
    is_void = models.BooleanField(default=False, verbose_name="Void")
    is_hidden = models.BooleanField(default=False, verbose_name="Disembunyikan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.inbound_number:
            today = timezone.now().date()
            date_str = today.strftime("%Y%m%d")
            prefix = f"INB-{date_str}-"
            
            last_inbound = InboundSession.objects.filter(inbound_number__startswith=prefix).order_by('-inbound_number').first()
            if last_inbound:
                last_seq = int(last_inbound.inbound_number.split('-')[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            self.inbound_number = f"{prefix}{new_seq:04d}"
        super().save(*args, **kwargs)

    @property
    def status_display(self):
        if self.is_void:
            return 'VOID'
        shipment_list = list(self.shipments.all())
        if not shipment_list:
            return 'ENTRY'
        all_finished = all(s.status in ['DELIVERY', 'ON_DELIVERY', 'POD', 'POD_BALIK', 'COMPLETED', 'DELIVERED', 'RETURNED'] for s in shipment_list)
        if all_finished:
            return 'SELESAI'
        return 'ENTRY'

    def __str__(self):
        return f"{self.inbound_number} at {self.location}"


class PODAttachment(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Foto'),
        ('VIDEO', 'Video'),
    ]
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='pod_attachments')
    file = models.FileField(upload_to='pod_media/%Y/%m/', verbose_name="File Bukti POD")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='IMAGE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    @property
    def is_image(self):
        return self.media_type == 'IMAGE'

    @property
    def is_video(self):
        return self.media_type == 'VIDEO'

    def __str__(self):
        return f"PODAttachment {self.id} - {self.shipment.resi_number} ({self.media_type})"


class DocumentPouch(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('DISPATCHED', 'Dalam Perjalanan (Dispatched)'),
        ('RECEIVED', 'Diterima di Hub Asal (Received)'),
        ('COMPLETED', 'Selesai / Diserahkan ke Klien (Completed)'),
    ]

    pouch_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Pouch DO")
    origin_branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='pouch_origins', verbose_name="Hub Pengirim (Tujuan Kirim)")
    dest_branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='pouch_destinations', verbose_name="Hub Penerima (Asal Kirim)")
    courier_service = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kurir / Ekspedisi Pengirim")
    airwaybill_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Resi Pengiriman Dokumen")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Status Pouch")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    shipments = models.ManyToManyField(Shipment, related_name='document_pouches', blank=True)

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_pouches')
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_pouches')
    received_at = models.DateTimeField(null=True, blank=True)
    handover_to_client_at = models.DateTimeField(null=True, blank=True)
    handover_notes = models.TextField(blank=True, null=True, verbose_name="Catatan Serah Terima Klien")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pouch_number:
            import datetime
            today = datetime.date.today().strftime('%Y%m%d')
            prefix = f"PCH-{today}-"
            last = DocumentPouch.objects.filter(pouch_number__startswith=prefix).order_by('-pouch_number').first()
            if last:
                try:
                    seq = int(last.pouch_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.pouch_number = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pouch_number} ({self.origin_branch} → {self.dest_branch})"


class ReturnShipment(models.Model):
    REASON_CHOICES = [
        ('BAD_ADDRESS', 'Alamat Tidak Lengkap / Tidak Ditemukan'),
        ('RECIPIENT_NOT_HOME', 'Penerima Tidak di Tempat / Rumah Tutup'),
        ('RECIPIENT_REFUSED', 'Penerima Menolak Menerima Paket'),
        ('PHONE_UNREACHABLE', 'Nomor Telepon / HP Tidak Aktif'),
        ('FAILED_3X', 'Gagal Antar 3x (Penerima Tidak Ada)'),
        ('COD_REJECTED', 'Penerima Batal Beli / Tidak Mau Bayar COD'),
        ('DAMAGED', 'Barang Rusak di Perjalanan'),
        ('FORCE_MAJEURE', 'Kendala Akses / Bencana / Force Majeure'),
        ('OTHER', 'Lainnya'),
    ]

    STATUS_CHOICES = [
        ('HOLD_DESTINATION', 'Laporan Masuk / Tertahan di Hub Tujuan (Pending Action)'),
        ('SCHEDULED_REDELIVERY', 'Dijadwalkan Kirim Ulang (Re-delivery)'),
        ('CONFIRM_SHIPPER', 'Menunggu Konfirmasi Shipper / CS'),
        ('APPROVED_RTO', 'Disetujui Retur ke Pengirim (Approved RTO)'),
        ('IN_TRANSIT_RTO', 'Dalam Perjalanan Kembali ke Asal (RTO Linehaul)'),
        ('RECEIVED_ORIGIN', 'Diterima di Hub Asal'),
        ('RETURNED_TO_SHIPPER', 'Selesai / Diserahkan ke Pengirim'),
        ('CANCELLED_REDELIVERED', 'Selesai Terkirim (Antar Ulang Berhasil)'),
    ]

    ACTION_CHOICES = [
        ('PENDING', 'Belum Ditentukan (Tab A: Laporan Masuk)'),
        ('REDELIVER', 'Kirim Ulang (Tab B: Kirim Ulang)'),
        ('RETURN_TO_ORIGIN', 'Kembali ke Pengirim (Tab C: Retur Pengirim)'),
    ]

    rto_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor RTO")
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='returns', verbose_name="Shipment / AWB")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, verbose_name="Alasan Retur / Gagal")
    reason_detail = models.TextField(blank=True, null=True, verbose_name="Keterangan Detail Gagal Antar")
    evidence_image = models.ImageField(upload_to='return_evidence/', blank=True, null=True, verbose_name="Foto Bukti Gagal Antar")

    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, default='PENDING', verbose_name="Tindakan Keputusan")
    scheduled_redelivery_date = models.DateField(null=True, blank=True, verbose_name="Jadwal Kirim Ulang")
    attempt_count = models.IntegerField(default=1, verbose_name="Percobaan ke-")

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='HOLD_DESTINATION', verbose_name="Status Retur")
    cs_notes = models.TextField(blank=True, null=True, verbose_name="Catatan CS / Keputusan Shipper")
    rto_manifest_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="No Manifest RTO")

    return_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Biaya Ongkir Retur")

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_returns')
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_returns')
    returned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_number(cls, prefix='FAIL'):
        import datetime
        today = datetime.date.today().strftime('%Y%m%d')
        pfx = f"{prefix}-{today}-"
        last = cls.objects.filter(rto_number__startswith=pfx).order_by('-rto_number').first()
        if last:
            try:
                seq = int(last.rto_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{pfx}{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.rto_number:
            prefix = 'FAIL'
            if self.action_type == 'REDELIVER':
                prefix = 'RD'
            elif self.action_type == 'RETURN_TO_ORIGIN':
                prefix = 'RTO'
            self.rto_number = self.generate_number(prefix)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rto_number} - {self.shipment.resi_number} ({self.get_status_display()})"

