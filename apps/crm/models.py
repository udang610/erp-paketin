from decimal import Decimal
from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.organizations.models import Branch


class Client(models.Model):
    """B2B client/company managed by a Sales PIC."""
    class CustomerCategory(models.TextChoices):
        PERUSAHAAN = 'PERUSAHAAN', 'Perusahaan'
        PEMERINTAH = 'PEMERINTAH', 'Pemerintah'
        RUMAH_SAKIT = 'RUMAH_SAKIT', 'Rumah Sakit'
        INDUSTRI = 'INDUSTRI', 'Industri'
        DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor'
        UMKM = 'UMKM', 'UMKM'
        PERORANGAN = 'PERORANGAN', 'Perorangan'

    class CustomerStatus(models.TextChoices):
        PROSPECT = 'PROSPECT', 'Calon Pelanggan'
        ACTIVE = 'ACTIVE', 'Pelanggan Aktif'
        INACTIVE = 'INACTIVE', 'Pelanggan Tidak Aktif'
        PRIORITY = 'PRIORITY', 'Pelanggan Prioritas'
        REGULAR = 'REGULAR', 'Pelanggan Tetap'

    class IndustryChoices(models.TextChoices):
        FARMASI = 'FARMASI', 'Farmasi & Kesehatan'
        MANUFAKTUR = 'MANUFAKTUR', 'Manufaktur & Pabrik'
        OTOMOTIF = 'OTOMOTIF', 'Otomotif'
        FMCG = 'FMCG', 'FMCG (Fast Moving Consumer Goods)'
        MAKANAN_MINUMAN = 'MAKANAN_MINUMAN', 'Makanan & Minuman (F&B)'
        TEKSTIL = 'TEKSTIL', 'Tekstil & Garment'
        ELEKTRONIK = 'ELEKTRONIK', 'Elektronik & Teknologi'
        KONSTRUKSI = 'KONSTRUKSI', 'Konstruksi & Infrastruktur'
        PERTAMBANGAN = 'PERTAMBANGAN', 'Pertambangan & Energi'
        PERTANIAN = 'PERTANIAN', 'Pertanian & Agribisnis'
        KOSMETIK = 'KOSMETIK', 'Kosmetik & Kecantikan'
        RETAIL = 'RETAIL', 'Retail & Grosir'
        DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor Umum'
        PERCETAKAN = 'PERCETAKAN', 'Percetakan & Packaging'
        FURNITURE = 'FURNITURE', 'Furniture & Kerajinan'
        LOGISTIK = 'LOGISTIK', 'Logistik & Transportasi'
        E_COMMERCE = 'E_COMMERCE', 'E-Commerce'
        JASA = 'JASA', 'Jasa & Layanan'
        OTHER = 'OTHER', 'Lainnya (Other)'

    class PaketinGroupChoices(models.TextChoices):
        PT_AMANAH = 'PT AMANAH', 'PAKETIN CARGO (PT AMANAH)'
        PT_SARANA = 'PT SARANA', 'SARANA EXPRESS (PT SARANA)'
        PT_SINERGI = 'PT SINERGI', 'PAKETIN EXPRESS (PT SINERGI)'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients', verbose_name='Sales PIC')
    
    # New branch filter
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients', verbose_name='Cabang')

    # Relasi ke Master Data ERP Customer
    master_customer = models.OneToOneField('master.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_client', verbose_name='Master Customer ERP')

    # Identitas & Tipe Akun (Sesuai Data Master)
    account_type = models.CharField('Tipe Akun', max_length=50, choices=[('MASTER', 'Master'), ('SUB', 'Sub Account')], default='MASTER', blank=True)
    divisi = models.CharField('Divisi', max_length=100, blank=True, default='')
    
    company_name = models.CharField('Nama Perusahaan', max_length=255)
    contact_person = models.CharField('Contact Person (PIC Akun)', max_length=255)
    phone = models.CharField('Telepon PIC', max_length=30)
    email = models.EmailField('Email', blank=True, default='')
    industry = models.CharField('Industri', max_length=100, choices=IndustryChoices.choices, null=True)
    address = models.TextField('Alamat', blank=True, default='')
    city = models.CharField('Kota', max_length=100, blank=True, default='')
    district = models.CharField('Kecamatan', max_length=100, blank=True, default='')
    province = models.CharField('Provinsi', max_length=100, blank=True, default='')
    postal_code = models.CharField('Kode Pos', max_length=10, blank=True, default='')
    paketin_group = models.CharField('Paketin Group', max_length=50, choices=PaketinGroupChoices.choices, blank=True, null=True)
    npwp = models.CharField('NPWP', max_length=30, blank=True, default='')
    website = models.URLField('Website', max_length=255, blank=True, default='')
    customer_category = models.CharField('Kategori Pelanggan', max_length=20, choices=CustomerCategory.choices, default=CustomerCategory.PERUSAHAAN)
    customer_status = models.CharField('Status Pelanggan', max_length=20, choices=CustomerStatus.choices, default=CustomerStatus.PROSPECT)
    credit_limit = models.DecimalField('Plafon Piutang (Credit Limit)', max_digits=15, decimal_places=2, default=0, help_text='Set 0 jika tidak ada batas tagihan')

    # Detail Operasional & Pembayaran (Sesuai Data Master)
    pic_pickup = models.CharField('PIC Pickup', max_length=100, blank=True, default='')
    pic_pickup_phone = models.CharField('Telepon PIC Pickup', max_length=50, blank=True, default='')
    term_of_payment = models.CharField('Term Of Payment', max_length=50, choices=[('0', '0 Days (Cash)'), ('14', '14 Days'), ('30', '30 Days'), ('45', '45 Days'), ('60', '60 Days'), ('90', '90 Days')], default='0', blank=True)
    payment_type = models.CharField('Tipe Pembayaran', max_length=50, choices=[('Transfer', 'Transfer'), ('Cash', 'Cash')], default='Transfer', blank=True)

    notes = models.TextField('Catatan', blank=True, default='')
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    updated_at = models.DateTimeField('Diperbarui', auto_now=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['branch', '-created_at']),
            models.Index(fields=['company_name']),
        ]

    def __str__(self):
        return f"{self.client_id} - {self.company_name}" if self.client_id else self.company_name

    def get_absolute_url(self):
        return reverse('crm:client-detail', kwargs={'pk': self.pk})

    @property
    def group_prefix(self):
        if self.paketin_group == 'PT AMANAH': return 'AMN-'
        elif self.paketin_group == 'PT SARANA': return 'SRN-'
        elif self.paketin_group == 'PT SINERGI': return 'SNG-'
        return ''

    @property
    def client_id(self):
        """Format: [GRUP]-CLI-0001"""
        return f"{self.group_prefix}CLI-{self.pk:04d}" if self.pk else ""


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'Baru'
        CONTACTED = 'CONTACTED', 'Dihubungi'
        QUALIFIED = 'QUALIFIED', 'Lolos Kualifikasi'
        PROPOSAL = 'PROPOSAL', 'Proposal'
        NEGOTIATION = 'NEGOTIATION', 'Negosiasi'
        WON = 'WON', 'Menang / Berhasil'
        LOST = 'LOST', 'Kalah / Gagal'

    class LeadSource(models.TextChoices):
        WEBSITE = 'WEBSITE', 'Website'
        GOOGLE = 'GOOGLE', 'Google'
        INSTAGRAM = 'INSTAGRAM', 'Instagram'
        FACEBOOK = 'FACEBOOK', 'Facebook'
        TIKTOK = 'TIKTOK', 'TikTok'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        MARKETPLACE = 'MARKETPLACE', 'Marketplace'
        REFERRAL = 'REFERRAL', 'Rekomendasi / Referensi'
        TELEMARKETING = 'TELEMARKETING', 'Telemarketing'
        EVENT = 'EVENT', 'Acara / Pameran'
        DIRECT_VISIT = 'DIRECT_VISIT', 'Kunjungan Langsung'
        EXISTING = 'EXISTING', 'Pelanggan Lama'
        OTHER = 'OTHER', 'Lainnya'

    class ServiceType(models.TextChoices):
        UDARA = 'UDARA', 'Cargo Udara'
        LAUT = 'LAUT', 'Cargo Laut'
        DARAT = 'DARAT', 'Cargo Darat'
        TRUCKING = 'TRUCKING', 'Trucking'
        EXPRESS = 'EXPRESS', 'Express'

    class ResponseChoice(models.TextChoices):
        YES = 'Y', 'Ya'
        NO = 'T', 'Tidak'
        NEUTRAL = 'N', 'Netral'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads', verbose_name='Sales PIC')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='leads', verbose_name='Client')
    lead_source = models.CharField('Sumber Lead', max_length=20, choices=LeadSource.choices, default=LeadSource.REFERRAL)
    status = models.CharField('Status', max_length=20, choices=Status.choices, default=Status.NEW)
    estimated_value = models.DecimalField('Estimasi Nilai (Rp)', max_digits=15, decimal_places=2, default=0)
    notes = models.TextField('Catatan', blank=True, default='')

    shipping_service = models.JSONField('Jenis Pengiriman', default=list, blank=True)
    shipping_origin = models.CharField('Asal Pengiriman', max_length=150, blank=True, default='')
    shipping_destination = models.CharField('Tujuan Pengiriman', max_length=150, blank=True, default='')
    shipping_estimated_weight = models.DecimalField('Estimasi Berat (kg)', max_digits=10, decimal_places=2, default=0)
    shipping_frequency = models.CharField('Frekuensi Pengiriman', max_length=100, blank=True, default='')
    shipping_notes = models.TextField('Catatan Pengiriman', blank=True, default='')

    responds_fast = models.CharField('Respon Cepat', max_length=1, choices=ResponseChoice.choices, default=ResponseChoice.NEUTRAL)
    interested = models.CharField('Tertarik', max_length=1, choices=ResponseChoice.choices, default=ResponseChoice.NEUTRAL)
    decision_maker = models.CharField('Decision Maker', max_length=1, choices=ResponseChoice.choices, default=ResponseChoice.NEUTRAL)
    budget_available = models.CharField('Budget Tersedia', max_length=1, choices=ResponseChoice.choices, default=ResponseChoice.NEUTRAL)
    competitor_exists = models.CharField('Ada Kompetitor', max_length=1, choices=ResponseChoice.choices, default=ResponseChoice.NEUTRAL)

    closed_at = models.DateTimeField('Tanggal Closing', null=True, blank=True)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    updated_at = models.DateTimeField('Diperbarui', auto_now=True)

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead_id} - {self.client.company_name}" if self.lead_id else self.client.company_name

    def get_absolute_url(self):
        return reverse('crm:lead-detail', kwargs={'pk': self.pk})

    @property
    def lead_id(self):
        prefix = self.client.group_prefix if self.client else ""
        return f"{prefix}LD-{self.pk:04d}" if self.pk else ""

    def get_whatsapp_followup_url(self):
        from urllib.parse import quote
        phone = self.client.phone
        if not phone:
            return ""
        # Format phone to intl standard if starts with 0
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        
        text = f"Halo Bapak/Ibu {self.client.contact_person}, saya dari Paketin Cargo menindaklanjuti ketertarikan Anda pada layanan pengiriman kami."
        return f"https://wa.me/{phone}?text={quote(text)}"
        
    def get_shipping_service_display_list(self):
        if not self.shipping_service:
            return []
        
        choices_dict = dict(self.ServiceType.choices)
        displays = []
        for svc in self.shipping_service:
            displays.append(choices_dict.get(svc, svc))
        return displays

class Contract(models.Model):
    class ContractStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Aktif'
        EXPIRED = 'EXPIRED', 'Kedaluwarsa'
        TERMINATED = 'TERMINATED', 'Dibatalkan'
        RENEWED = 'RENEWED', 'Diperpanjang'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contracts', verbose_name='Sales PIC')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts', verbose_name='Lead')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contracts', verbose_name='Client')
    contract_number = models.CharField('Nomor Kontrak', max_length=50, unique=True)
    title = models.CharField('Judul Kontrak', max_length=255)
    description = models.TextField('Deskripsi', blank=True, default='')
    value = models.DecimalField('Nilai Kontrak (Rp)', max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField('Tanggal Mulai')
    end_date = models.DateField('Tanggal Berakhir')
    status = models.CharField('Status', max_length=20, choices=ContractStatus.choices, default=ContractStatus.DRAFT)
    terms = models.TextField('Syarat & Ketentuan', blank=True, default='')
    penerima = models.CharField('Nama Penerima (Consignee)', max_length=255, blank=True, default='')
    document = models.FileField('Dokumen Kontrak', upload_to='contracts/%Y/%m/', blank=True, null=True)
    renewal_reminder_days = models.PositiveIntegerField('Pengingat Sebelum Berakhir (hari)', default=30)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    updated_at = models.DateTimeField('Diperbarui', auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_number} - {self.client.company_name}"

    def get_absolute_url(self):
        return reverse('crm:contract-detail', kwargs={'pk': self.pk})

    def generate_contract_number(self):
        import datetime
        today = datetime.date.today()
        prefix = "KTR"
        if self.client and self.client.group_prefix:
            prefix = f"{self.client.group_prefix}KTR"
        date_str = today.strftime('%Y%m')
        # We might need to ensure this is truly unique if called concurrently, but this suffices for now
        count = Contract.objects.filter(created_at__year=today.year, created_at__month=today.month).count() + 1
        return f"{prefix}-{date_str}-{count:04d}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Contract)
def auto_activate_client_on_contract(sender, instance, created, **kwargs):
    if created and instance.client:
        if instance.client.customer_status == 'PROSPECT':
            instance.client.customer_status = 'ACTIVE'
            instance.client.save(update_fields=['customer_status'])

class Quotation(models.Model):
    class ServiceType(models.TextChoices):
        UDARA = 'UDARA', 'Cargo Udara'
        LAUT = 'LAUT', 'Cargo Laut'
        DARAT = 'DARAT', 'Cargo Darat'
        TRUCKING = 'TRUCKING', 'Trucking'
        EXPRESS = 'EXPRESS', 'Express'
        
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        WAITING_APPROVAL = 'WAITING_APPROVAL', 'Menunggu Persetujuan'
        APPROVED = 'APPROVED', 'Disetujui'
        REJECTED = 'REJECTED', 'Ditolak'
        SENT = 'SENT', 'Terkirim ke Klien'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotations', verbose_name='Sales PIC')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotations', verbose_name='Lead')

    panjang = models.DecimalField('Panjang (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    lebar = models.DecimalField('Lebar (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    tinggi = models.DecimalField('Tinggi (cm)', max_digits=10, decimal_places=2, default=0, blank=True)

    actual_weight = models.DecimalField('Berat Aktual (kg)', max_digits=10, decimal_places=2, default=0, blank=True)
    volumetric_weight = models.DecimalField('Berat Volumetrik (kg)', max_digits=10, decimal_places=2, default=0, editable=False)

    origin = models.CharField('Asal', max_length=100, blank=True, null=True)
    destination = models.CharField('Tujuan', max_length=100, blank=True, null=True)
    service = models.JSONField('Layanan', default=list, blank=True)

    # Master Data Relations
    origin_coverage = models.ForeignKey('master.Coverage', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotation_origins')
    destination_coverage = models.ForeignKey('master.Coverage', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotation_destinations')
    service_master = models.ForeignKey('master.Service', on_delete=models.SET_NULL, null=True, blank=True)
    is_manual_override = models.BooleanField('Input Manual (Bypass)', default=False)


    insurance = models.DecimalField('Asuransi (Rp)', max_digits=15, decimal_places=2, default=0, blank=True)
    packing = models.DecimalField('Packing (Rp)', max_digits=15, decimal_places=2, default=0, blank=True)
    quantity = models.PositiveIntegerField('Jumlah Koli', default=1, blank=True)
    price_per_kg = models.DecimalField('Harga per Kg (Rp)', max_digits=15, decimal_places=2, default=0, blank=True)
    discount = models.DecimalField('Diskon (Rp)', max_digits=15, decimal_places=2, default=0, blank=True)
    total_price = models.DecimalField('Total Harga (Rp)', max_digits=15, decimal_places=2, default=0, editable=False)
    manual_total_price = models.DecimalField('Total Harga (Manual)', max_digits=15, decimal_places=2, null=True, blank=True)

    notes = models.TextField('Catatan', blank=True, default='')
    attachment = models.FileField('File Lampiran', upload_to='quotations/attachments/', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)
    updated_at = models.DateTimeField('Diperbarui', auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        prefix = self.lead.client.group_prefix if self.lead and self.lead.client else ""
        return f"{prefix}QUO-{self.pk:04d} | {self.lead.client.company_name}"

    @property
    def quotation_number(self):
        """Format: [GRUP]-QUO-0001"""
        if not self.pk:
            return ""
        prefix = self.lead.client.group_prefix if self.lead and self.lead.client else ""
        return f"{prefix}QUO-{self.pk:04d}"

    def recalculate_totals(self):
        # Hitung berat volumetrik dari p, l, t (p*l*t / 5000 untuk darat/laut)
        if self.panjang and self.lebar and self.tinggi:
            vol = (self.panjang * self.lebar * self.tinggi) / 5000
            self.volumetric_weight = round(vol, 2)
        else:
            self.volumetric_weight = 0

        # Chargeable weight
        chargeable_weight = max(self.actual_weight or 0, self.volumetric_weight or 0)
        
        # Base price
        base = chargeable_weight * (self.price_per_kg or 0)
        
        # Subtotals
        total = base + (self.insurance or 0) + (self.packing or 0) - (self.discount or 0)
        self.total_price = total
        self.save(update_fields=['volumetric_weight', 'total_price'])

    @property
    def is_attachment_image(self):
        if not self.attachment:
            return False
        ext = self.attachment.name.split('.')[-1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']

    @property
    def is_attachment_pdf(self):
        if not self.attachment:
            return False
        return self.attachment.name.lower().endswith('.pdf')


class QuotationItem(models.Model):
    class PackingChoices(models.TextChoices):
        YES = 'YES', 'Yes'
        NO = 'NO', 'No'

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    actual_weight = models.DecimalField('Weight Actual (kg)', max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField('Colly', default=1)
    panjang = models.DecimalField('Panjang (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    lebar = models.DecimalField('Lebar (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    tinggi = models.DecimalField('Tinggi (cm)', max_digits=10, decimal_places=2, default=0, blank=True)
    packing = models.CharField('Packing', max_length=10, choices=PackingChoices.choices, default=PackingChoices.NO)
    description = models.CharField('Description Item', max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Item of {self.quotation.pk}"


class Activity(models.Model):
    class ActivityType(models.TextChoices):
        CALL = 'CALL', 'Call'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        EMAIL = 'EMAIL', 'Email'
        VISIT = 'VISIT', 'Visit'
        MEETING = 'MEETING', 'Meeting'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities', verbose_name='Sales PIC')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities', verbose_name='Lead')
    activity_type = models.CharField('Jenis Aktivitas', max_length=20, choices=ActivityType.choices, default=ActivityType.CALL)
    description = models.TextField('Deskripsi')
    result = models.TextField('Hasil', blank=True, default='')
    next_followup = models.DateField('Follow Up Selanjutnya', null=True, blank=True)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead}"


class Reminder(models.Model):
    class NotifyBeforeChoices(models.IntegerChoices):
        AT_TIME = 0, 'Tepat Waktu'
        MIN_5 = 5, '5 Menit Sebelumnya'
        MIN_15 = 15, '15 Menit Sebelumnya'
        MIN_30 = 30, '30 Menit Sebelumnya'
        HOUR_1 = 60, '1 Jam Sebelumnya'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders', verbose_name='Sales PIC')
    title = models.CharField('Judul', max_length=255)
    description = models.TextField('Deskripsi', blank=True, default='')
    due_date = models.DateField('Tanggal')
    reminder_time = models.TimeField('Waktu Reminder', null=True, blank=True)
    notify_before = models.IntegerField('Ingatkan Sebelumnya', choices=NotifyBeforeChoices.choices, default=NotifyBeforeChoices.AT_TIME)
    completed = models.BooleanField('Selesai', default=False)
    created_at = models.DateTimeField('Dibuat', auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'reminder_time']

    def __str__(self):
        return self.title
