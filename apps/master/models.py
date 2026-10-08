from django.db import models

class Bank(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Kode Bank")
    name = models.CharField(max_length=100, verbose_name="Nama Bank")
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="No Rekening")
    account_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Atas Nama")
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='banks', verbose_name="Cabang Terkait")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alamat Bank")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return f"{self.name} - {self.account_number}"

class Coverage(models.Model):
    district = models.CharField(max_length=100, verbose_name="Kecamatan (District)")
    city = models.CharField(max_length=100, verbose_name="Kota/Kabupaten")
    province = models.CharField(max_length=100, verbose_name="Provinsi")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Kode Pos")
    tlc = models.CharField(max_length=10, blank=True, null=True, verbose_name="Kode TLC (Tiga Huruf)")
    is_covered = models.BooleanField(default=True, verbose_name="Terjangkau Layanan")
    is_verified = models.BooleanField(default=True, verbose_name="Terverifikasi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return f"{self.district}, {self.city}"

class Service(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Kode Layanan")
    name = models.CharField(max_length=100, verbose_name="Nama Layanan (Contoh: REG, ONS, CARGO)")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")
    divisor = models.IntegerField(default=5000, verbose_name="Pembagi Volume (Rumus Berat)")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    is_verified = models.BooleanField(default=True, verbose_name="Terverifikasi")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return self.name

class Price(models.Model):
    origin = models.ForeignKey(Coverage, on_delete=models.CASCADE, related_name='price_origins', verbose_name="Asal")
    destination = models.ForeignKey(Coverage, on_delete=models.CASCADE, related_name='price_destinations', verbose_name="Tujuan")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Layanan")
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Harga per Kg")
    min_weight = models.DecimalField(max_digits=10, decimal_places=2, default=1.0, verbose_name="Min Berat (Kg)")
    estimated_days = models.CharField(max_length=50, blank=True, null=True, verbose_name="Estimasi Tiba (Hari)")

    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return f"{self.origin.city} -> {self.destination.city} ({self.service.name})"

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktif'),
        ('MAINTENANCE', 'Perawatan'),
        ('INACTIVE', 'Tidak Aktif'),
    ]
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cabang Operasional")
    plate_number = models.CharField(max_length=20, unique=True, verbose_name="Plat Kendaraan")
    vehicle_type = models.CharField(max_length=50, verbose_name="Tipe Kendaraan")
    brand_model = models.CharField(max_length=100, verbose_name="Merek & Model", blank=True)
    capacity_kg = models.IntegerField(default=0, verbose_name="Kapasitas (Kg)")
    capacity_cbm = models.IntegerField(default=0, verbose_name="Kapasitas (CBM)")
    registration_expiry = models.DateField(null=True, blank=True, verbose_name="Masa Berlaku STNK")
    kir_expiry = models.DateField(null=True, blank=True, verbose_name="Masa Berlaku KIR")
    status = models.CharField(max_length=20, default='ACTIVE', choices=STATUS_CHOICES, verbose_name="Status")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return f"{self.plate_number} - {self.vehicle_type}"

class Customer(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('MASTER', 'Master'),
        ('SUB', 'Sub Account')
    ]
    PPN_CHOICES = [
        ('1.2', '1.2 %'),
        ('12', '12 %'),
        ('1', '1 %'),
        ('1.1', '1.1 %'),
    ]
    TERM_CHOICES = [
        ('0', '0 Days'),
        ('14', '14 Days'),
        ('30', '30 Days'),
        ('45', '45 Days'),
        ('60', '60 Days'),
        ('90', '90 Days')
    ]
    STATUS_CUSTOMER_CHOICES = [
        ('Draft', 'Draft'),
        ('Aktif', 'Aktif')
    ]
    PAYMENT_TYPE_CHOICES = [
        ('Transfer', 'Transfer'),
        ('Cash', 'Cash')
    ]
    INDUSTRY_CHOICES = [
        ('FARMASI', 'Farmasi & Kesehatan'),
        ('MANUFAKTUR', 'Manufaktur & Pabrik'),
        ('OTOMOTIF', 'Otomotif'),
        ('FMCG', 'FMCG (Fast Moving Consumer Goods)'),
        ('MAKANAN_MINUMAN', 'Makanan & Minuman (F&B)'),
        ('TEKSTIL', 'Tekstil & Garment'),
        ('ELEKTRONIK', 'Elektronik & Teknologi'),
        ('KONSTRUKSI', 'Konstruksi & Infrastruktur'),
        ('PERTAMBANGAN', 'Pertambangan & Energi'),
        ('PERTANIAN', 'Pertanian & Agribisnis'),
        ('KOSMETIK', 'Kosmetik & Kecantikan'),
        ('RETAIL', 'Retail & Grosir'),
        ('DISTRIBUTOR', 'Distributor Umum'),
        ('PERCETAKAN', 'Percetakan & Packaging'),
        ('FURNITURE', 'Furniture & Kerajinan'),
        ('LOGISTIK', 'Logistik & Transportasi'),
        ('E_COMMERCE', 'E-Commerce'),
        ('JASA', 'Jasa & Layanan'),
        ('OTHER', 'Lainnya (Other)')
    ]

    # Customer Details
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES, default='MASTER', verbose_name="Tipe Akun")
    customer_code = models.CharField(max_length=50, unique=True, verbose_name="Kode Master Customer")
    name = models.CharField(max_length=255, verbose_name="Nama Customer")
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='customers', verbose_name="Cabang Terkait")
    divisi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Divisi")
    type_industry = models.CharField(max_length=100, choices=INDUSTRY_CHOICES, default='OTHER', verbose_name="Tipe Industri")
    effective_start_date = models.DateField(blank=True, null=True, verbose_name="Mulai Berlaku")
    effective_end_date = models.DateField(blank=True, null=True, verbose_name="Akhir Berlaku")
    pic_account = models.CharField(max_length=100, verbose_name="PIC Akun")
    pic_phone = models.CharField(max_length=50, verbose_name="Telepon PIC")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    sales = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user_type': 'SALES'}, related_name='sales_customers', verbose_name="Sales")
    api_integration = models.BooleanField(default=False, verbose_name="Integrasi API")

    # Office Details
    city = models.CharField(max_length=100, verbose_name="Kota")
    office_address = models.TextField(verbose_name="Alamat Kantor")
    district = models.CharField(max_length=100, verbose_name="Kecamatan")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Kode POS")

    # Pickup Details
    pickup_same_as_office = models.BooleanField(default=True, verbose_name="Detail Pickup Sama Dengan Kantor")
    pic_pickup = models.CharField(max_length=100, blank=True, default='', verbose_name="PIC Pickup")
    pic_pickup_phone = models.CharField(max_length=50, blank=True, default='', verbose_name="Telepon PIC Pickup")

    # Payment & Finance Detail
    term_of_payment = models.CharField(max_length=50, choices=TERM_CHOICES, default='0', verbose_name="Term Of Payment")
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default='Transfer', verbose_name="Tipe Pembayaran")
    bank_transfer = models.ForeignKey('Bank', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Transfer Bank")
    virtual_account = models.CharField(max_length=100, blank=True, null=True, verbose_name="Virtual Account")
    ppn_percentage = models.CharField(max_length=10, choices=PPN_CHOICES, default='1.2', verbose_name="PPN %")
    npwp = models.CharField(max_length=50, verbose_name="NPWP")
    
    # Invoice & Operational Detail
    pic_invoice = models.CharField(max_length=100, blank=True, null=True, verbose_name="PIC Invoice")
    phone_invoice = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telepon PIC Invoice")
    email_invoice = models.EmailField(blank=True, null=True, verbose_name="Email Invoice")
    with_pod_resi = models.BooleanField(default=False, verbose_name="Dengan POD / Resi")
    insurance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Persentase Asuransi %")
    min_premi_insurance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Minimal Premi Asuransi")
    handling_type_shipment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipe Penanganan (Handling)")
    take_photo_pod = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ambil Foto POD")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    status = models.CharField(max_length=50, choices=STATUS_CUSTOMER_CHOICES, default='Draft', verbose_name="Status")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers', verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def save(self, *args, **kwargs):
        if not self.customer_code:
            last_cust = Customer.objects.order_by('id').last()
            next_id = last_cust.id + 1 if last_cust else 1
            self.customer_code = f"CUST-{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_code} - {self.name}"


class Province(models.Model):
    """Provinsi - 38 provinsi Indonesia (Kepmendagri 2025)"""
    code = models.CharField(max_length=10, unique=True, verbose_name="Kode Provinsi")
    name = models.CharField(max_length=255, verbose_name="Nama Provinsi")

    class Meta:
        ordering = ['name']
        verbose_name = 'Provinsi'
        verbose_name_plural = 'Provinsi'

    def __str__(self):
        return self.name


class Regency(models.Model):
    """Kabupaten/Kota - 514 kab/kota Indonesia"""
    TYPE_CHOICES = [
        ('KABUPATEN', 'Kabupaten'),
        ('KOTA', 'Kota'),
    ]
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='regencies', verbose_name="Provinsi")
    code = models.CharField(max_length=10, unique=True, verbose_name="Kode Kab/Kota")
    name = models.CharField(max_length=255, verbose_name="Nama Kab/Kota")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='KABUPATEN', verbose_name="Tipe")

    class Meta:
        ordering = ['name']
        verbose_name = 'Kabupaten/Kota'
        verbose_name_plural = 'Kabupaten/Kota'

    def __str__(self):
        return f"{self.type.title()} {self.name}" if self.type else self.name


class District(models.Model):
    """Kecamatan - 7.285 kecamatan Indonesia"""
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, related_name='districts', verbose_name="Kab/Kota")
    code = models.CharField(max_length=15, unique=True, verbose_name="Kode Kecamatan")
    name = models.CharField(max_length=255, verbose_name="Nama Kecamatan")

    class Meta:
        ordering = ['name']
        verbose_name = 'Kecamatan'
        verbose_name_plural = 'Kecamatan'

    def __str__(self):
        return self.name


class Village(models.Model):
    """Kelurahan/Desa"""
    TYPE_CHOICES = [
        ('KELURAHAN', 'Kelurahan'),
        ('DESA', 'Desa'),
    ]
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='villages', verbose_name="Kecamatan")
    code = models.CharField(max_length=20, unique=True, verbose_name="Kode Kel/Desa")
    name = models.CharField(max_length=255, verbose_name="Nama Kel/Desa")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='DESA', verbose_name="Tipe")

    class Meta:
        ordering = ['name']
        verbose_name = 'Kelurahan/Desa'
        verbose_name_plural = 'Kelurahan/Desa'

    def __str__(self):
        return self.name