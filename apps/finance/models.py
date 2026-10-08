from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.validators import validate_payment_proof

# 1. PROFILE (Gabungan profiles & user_permissions)
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('pic', 'PIC'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    pic_id = models.IntegerField(default=-1)
    
    # Pengganti user_permissions
    allowed_columns = models.JSONField(default=list, blank=True, help_text='List kolom yang boleh diakses. Kosongkan jika semua.')
    sheet_ids = models.JSONField(default=list, blank=True, help_text='List ID Sheet yang bisa diakses.')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal untuk otomatis membuat Profile saat User dibuat
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if hasattr(instance, '_disable_profile_signal'):
        return
    Profile.objects.get_or_create(user=instance)
    if not created and hasattr(instance, 'profile'):
        instance.profile.save()

# 2. KPI FILES
class KpiFile(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# 3. KPI SHEETS
class KpiSheet(models.Model):
    SHEET_TYPE_CHOICES = [
        ('data', 'Data'),
        ('monthly_recap', 'Monthly Recap'),
        ('yearly_recap', 'Yearly Recap'),
    ]
    
    name = models.CharField(max_length=255)
    kpi_file = models.ForeignKey(KpiFile, on_delete=models.CASCADE, related_name='sheets')
    sheet_type = models.CharField(max_length=20, choices=SHEET_TYPE_CHOICES, default='data')
    sort_order = models.IntegerField(default=0)
    
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.kpi_file.name})"

# 4. KPI FINANCE (Baris Data)
class KpiFinance(models.Model):
    sheet = models.ForeignKey(KpiSheet, on_delete=models.CASCADE, related_name='finance_data')
    
    tanggal_pickup = models.DateField(null=True, blank=True)
    nama = models.CharField(max_length=255, blank=True, default="")
    awb = models.CharField(max_length=255, blank=True, default="")
    awb_sistem = models.CharField(max_length=255, blank=True, default="")
    pengirim = models.CharField(max_length=255, blank=True, default="")
    sales = models.CharField(max_length=255, blank=True, default="")
    penerima = models.CharField(max_length=255, blank=True, default="")
    service = models.CharField(max_length=255, blank=True, default="")
    via = models.CharField(max_length=255, blank=True, default="")
    
    aktual = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    vol = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    unit = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    kubik = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    p = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    l = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    t = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    koil = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    harga = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    surcharge = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    packing = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    handling = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    penjualan = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    
    asal_pickup = models.CharField(max_length=255, blank=True, default="")
    ip_perusahaan = models.CharField(max_length=255, blank=True, default="")
    jenis_barang = models.CharField(max_length=255, blank=True, default="")
    tujuan = models.CharField(max_length=255, blank=True, default="")
    nama_vendor = models.CharField(max_length=255, blank=True, default="")
    nama_vendor_ii = models.CharField(max_length=255, blank=True, default="")
    nama_vendor_iii = models.CharField(max_length=255, blank=True, default="")
    nama_vendor_iv = models.CharField(max_length=255, blank=True, default="")
    
    vendor_i = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    vendor_ii = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    vendor_iii = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    vendor_iv = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    ops = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    asuransi = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    asuransi_jasindo = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    nilai_barang = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    total_biaya = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)
    idx_profit = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True, default=0)

    formulas = models.JSONField(default=dict, blank=True)

    # CRM Integration & Workflow Tracking
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('crm', 'CRM Import'),
        ('import', 'File Import'),
    ]
    ROW_STATUS_CHOICES = [
        ('new', 'Baru (dari CRM)'),
        ('vendor_filled', 'Vendor Diisi'),
        ('invoiced', 'Invoice Diisi'),
        ('completed', 'Selesai'),
        ('voided', 'Dibatalkan (Void)'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    row_status = models.CharField(max_length=20, choices=ROW_STATUS_CHOICES, default='completed')
    crm_lead_id = models.CharField(max_length=50, blank=True, default='', help_text='ID Lead dari CRM, contoh: LD-0042')
    
    # Inter-module connection to Operation module
    shipment = models.ForeignKey(
        'operations.Shipment', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='finance_records',
        verbose_name="Shipment Terkait"
    )

    # Referensi display-only: baris ini sudah tercatat di invoice mana.
    # TIDAK dipakai oleh proses invoicing apapun — hanya untuk tampilan
    # di worksheet supaya Finance tahu baris ini sudah ke-cover atau belum.
    linked_invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kpi_rows',
        verbose_name="Invoice Terkait (display only)"
    )

    # Status verifikasi vendor cost — independen dari status penagihan.
    # Digunakan murni untuk laporan margin/profit, TIDAK dibaca oleh proses
    # invoicing manapun. Menggantikan makna 'vendor_filled' dari row_status
    # lama secara bertahap.
    COST_VERIFICATION_CHOICES = [
        ('pending', 'Belum Diverifikasi'),
        ('verified', 'Vendor Cost Terverifikasi'),
    ]
    cost_verification_status = models.CharField(
        max_length=20,
        choices=COST_VERIFICATION_CHOICES,
        default='pending',
        verbose_name="Status Verifikasi Vendor Cost"
    )
    
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# 5. CELL STYLES
class CellStyle(models.Model):
    sheet = models.ForeignKey(KpiSheet, on_delete=models.CASCADE, related_name='cell_styles')
    row_id = models.BigIntegerField()
    field = models.CharField(max_length=255)
    styles = models.JSONField(default=dict)
    
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

# 6. AUDIT LOGS
class AuditLog(models.Model):
    row_id = models.BigIntegerField(null=True, blank=True)
    field_name = models.CharField(max_length=255, null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    user_email = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    changed_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 7. CRM INTEGRATION (PHASE 1) — DEPRECATED
# ──────────────────────────────────────────────────────────────────────
# Model di bawah ini adalah sisa arsitektur webhook lama (era sebelum
# penggabungan 3 sistem jadi 1 ERP). Sekarang data CRM diambil langsung
# dari apps.crm.Client dan apps.crm.Contract via FK native.
#
# Model TIDAK dihapus agar migration history tidak rusak, tapi:
# - ViewSet, Serializer, dan URL endpoint sudah dihapus.
# - JANGAN gunakan model ini untuk fitur baru.
# ──────────────────────────────────────────────────────────────────────
class CrmClient(models.Model):
    """DEPRECATED — Gunakan apps.crm.Client sebagai gantinya."""
    crm_id = models.CharField(max_length=50, unique=True, help_text="ID Kustomer dari CRM")
    name = models.CharField(max_length=255, help_text="Nama Kustomer / Perusahaan")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True  # Keep table for backward compat

    def __str__(self):
        return f"[DEPRECATED] {self.name} ({self.crm_id})"


class CrmContract(models.Model):
    """DEPRECATED — Gunakan apps.crm.Contract / apps.crm.Quotation sebagai gantinya."""
    crm_quotation_id = models.CharField(max_length=50, help_text="ID Quotation dari CRM")
    client = models.ForeignKey(CrmClient, on_delete=models.CASCADE, related_name='contracts')
    asal = models.CharField(max_length=100, blank=True, default="")
    tujuan = models.CharField(max_length=100, blank=True, default="")
    service = models.CharField(max_length=100, blank=True, default="")
    via = models.CharField(max_length=50, blank=True, default="")
    harga = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    penerima = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Menghindari duplikasi rute & service per klien
        unique_together = ('client', 'asal', 'tujuan', 'service', 'via')

    def __str__(self):
        return f"{self.client.name}: {self.asal}-{self.tujuan} ({self.service}) = {self.harga}"

# 8. INVOICING & PAYMENTS (PHASE 5)
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Terkirim (Sent)'),
        ('PARTIAL', 'Dibayar Sebagian (Partial)'),
        ('PAID', 'Lunas (Paid)'),
        ('VOID', 'Dibatalkan (Void)'),
    ]

    COMPANY_CHOICES = [
        ('PT AMANAH', 'PT Amanah Cargo Jaya Mandiri (Paketin Cargo)'),
        ('PT SARANA', 'Sarana Express (PT Sarana)'),
        ('PT SINERGI', 'Paketin Express (PT Sinergi)'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Invoice")
    client_name = models.CharField(max_length=255, verbose_name="Nama Klien / Perusahaan")
    date_issued = models.DateField(auto_now_add=True, verbose_name="Tanggal Terbit")
    due_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Jatuh Tempo")

    # Perusahaan penerbit (untuk header cetak -- PT AMANAH/SARANA/SINERGI
    # punya kop surat & rekening bank yang berbeda, lihat FINANCE_COMPANY_PROFILES)
    company_code = models.CharField(max_length=20, choices=COMPANY_CHOICES, default='PT AMANAH', verbose_name="Perusahaan Penerbit")

    # Snapshot data pelanggan saat invoice dibuat -- sengaja DI-COPY (bukan
    # FK live) supaya invoice yang sudah terbit tidak ikut berubah kalau
    # data Client di CRM diedit belakangan.
    kode_pelanggan = models.CharField(max_length=50, blank=True, default="", verbose_name="Kode Pelanggan")
    pic_invoice = models.CharField(max_length=255, blank=True, default="", verbose_name="PIC Invoice")
    alamat_pelanggan = models.TextField(blank=True, default="", verbose_name="Alamat Pelanggan")
    npwp = models.CharField(max_length=30, blank=True, default="", verbose_name="NPWP")
    sales_ae = models.CharField(max_length=255, blank=True, default="", verbose_name="Sales (AE)")

    # Periode penagihan (menggantikan asumsi "1 bulan kalender" yang lama)
    periode_awal = models.DateField(null=True, blank=True, verbose_name="Periode Awal")
    periode_akhir = models.DateField(null=True, blank=True, verbose_name="Periode Akhir")

    # Rincian biaya -- persis mengikuti struktur invoice cetak Paketin Cargo
    biaya_kirim = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Kirim / Freight Cost")
    diskon = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Diskon")
    biaya_tambahan = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Tambahan (Surcharge & Handling)")
    biaya_kemasan = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Kemasan / Packing Cost")
    biaya_lain = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Lain / Others Charges")
    premi_asuransi = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Premi Asuransi")
    
    subtotal = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Biaya Kirim Dan Biaya Lain")
    tax = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="PPN (1.1%)")
    materai = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Materai")
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Tagihan")
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Dibayar")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    # Rolling draft: invoice yang is_open=True masih "hidup" — shipment baru
    # yang delivered untuk klien yang sama akan otomatis nempel ke sini.
    # Setelah Finance klik "Tutup & Terbitkan", is_open=False dan invoice
    # terkunci (status SENT), shipment baru masuk ke draft baru.
    is_open = models.BooleanField(default=True, verbose_name="Draft Terbuka")
    
    # Kumpulan Shipment yang di-invoice-kan
    shipments = models.ManyToManyField('operations.Shipment', related_name='invoices', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.client_name}"

    @property
    def sub_total_biaya_kirim(self):
        """Sub Total Biaya Kirim = Biaya Kirim - Diskon + Biaya Tambahan (Surcharge & Handling)."""
        return self.biaya_kirim - self.diskon + self.biaya_tambahan

    @property
    def sub_total_biaya_lain(self):
        """Sub Total Biaya Lain = Biaya Kemasan + Biaya Lain."""
        return self.biaya_kemasan + self.biaya_lain

    @property
    def referensi(self):
        """Format: {invoice_number}/{kode_pelanggan}/{MMYYYY periode}."""
        periode = self.periode_akhir or self.date_issued
        bulan_tahun = periode.strftime('%m%Y') if periode else ''
        return f"{self.invoice_number}/{self.kode_pelanggan}/{bulan_tahun}"

    @property
    def terbilang(self):
        from .utils import terbilang_rupiah
        return terbilang_rupiah(self.total_amount)

    @property
    def total_ldp_count(self):
        return self.ldps.count()

    @property
    def total_awb_count(self):
        count = self.shipments.count()
        if count == 0 and self.ldps.exists():
            return sum([ldp.items.count() for ldp in self.ldps.all()])
        return count

    @property
    def latest_reconciliation(self):
        return self.reconciliations.order_by('-created_at').first()

    @property
    def sisa_tagihan(self):
        import decimal
        total = self.total_amount or decimal.Decimal('0')
        paid = self.amount_paid or decimal.Decimal('0')
        return max(decimal.Decimal('0'), total - paid)

    def update_totals(self, recalc_from_shipments=False):
        """
        Hitung ulang subtotal/PPN/materai/total dari rincian biaya.

        Jika recalc_from_shipments=True (dipakai oleh rolling draft), maka
        biaya_kirim di-set ulang dari SUM(shipment.price) yang terhubung
        ke invoice ini. Ini menjamin sumber angka billing langsung dari
        Shipment, BUKAN dari KpiFinance/worksheet.

        Jika False (default, backward-compatible), biaya_kirim yang sudah
        di-set manual oleh Finance tidak ditimpa — cocok untuk invoice
        yang breakdown-nya sudah diedit sebelum diterbitkan.
        """
        import decimal

        if recalc_from_shipments:
            # Sumber resmi billing: langsung dari Shipment.price, bukan sheet
            total_price = self.shipments.aggregate(
                total=models.Sum('price')
            )['total'] or decimal.Decimal('0')
            self.biaya_kirim = total_price

        self.subtotal = self.sub_total_biaya_kirim + self.sub_total_biaya_lain

        # PPN Logistik = 1.1% dari Subtotal
        tax_rate = decimal.Decimal('0.011')
        self.tax = (self.subtotal * tax_rate).quantize(decimal.Decimal('0.01'))

        # Materai 10.000 jika (Subtotal + PPN) di atas Rp 5.000.000
        if self.subtotal + self.tax > decimal.Decimal('5000000'):
            self.materai = decimal.Decimal('10000')
        else:
            self.materai = decimal.Decimal('0')

        self.total_amount = self.subtotal + self.tax + self.materai + self.premi_asuransi
        self.save()

class PaymentRecord(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Nominal Bayar")
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default="Bank Transfer")
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"


class LDP(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Siap Tagih (Confirmed)'),
        ('INVOICED', 'Sudah Di-Invoice (Invoiced)'),
        ('CANCELLED', 'Dibatalkan (Cancelled)'),
    ]

    ldp_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor LDP")
    client_name = models.CharField(max_length=255, verbose_name="Nama Klien / Perusahaan")
    client = models.ForeignKey('master.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='ldp_batches', verbose_name="Kustomer")
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='ldp_batches', verbose_name="Cabang")
    
    ldp_date = models.DateField(default=timezone.now, verbose_name="Tanggal LDP")
    periode_awal = models.DateField(null=True, blank=True, verbose_name="Periode Awal")
    periode_akhir = models.DateField(null=True, blank=True, verbose_name="Periode Akhir")
    
    total_koli = models.IntegerField(default=0, verbose_name="Total Koli")
    total_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Berat (Kg)")
    total_freight = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Biaya Kirim")
    total_surcharges = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Biaya Tambahan")
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Nilai LDP")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Status LDP")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='ldps', verbose_name="Invoice Terkait")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_ldps', verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lembar Daftar Pengiriman (LDP)"
        verbose_name_plural = "Lembar Daftar Pengiriman (LDP)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ldp_number} - {self.client_name} ({self.get_status_display()})"

    def recalculate_totals(self):
        aggregates = self.items.aggregate(
            koli=models.Sum('koli'),
            weight=models.Sum('chargeable_weight'),
            freight=models.Sum('freight_charge'),
            surcharges=models.Sum('surcharges'),
            amount=models.Sum('subtotal'),
        )
        self.total_koli = aggregates['koli'] or 0
        self.total_weight = aggregates['weight'] or 0
        self.total_freight = aggregates['freight'] or 0
        self.total_surcharges = aggregates['surcharges'] or 0
        self.total_amount = aggregates['amount'] or 0
        self.save()


class LDPItem(models.Model):
    ldp = models.ForeignKey(LDP, on_delete=models.CASCADE, related_name='items')
    shipment = models.ForeignKey('operations.Shipment', on_delete=models.SET_NULL, null=True, blank=True, related_name='ldp_items')
    
    # Snapshot fields so historical data remains immutable
    awb_number = models.CharField(max_length=50, verbose_name="Nomor Resi / AWB")
    shipment_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Kirim")
    sender_name = models.CharField(max_length=255, blank=True, default="", verbose_name="Pengirim")
    receiver_name = models.CharField(max_length=255, blank=True, default="", verbose_name="Penerima")
    origin = models.CharField(max_length=100, blank=True, default="", verbose_name="Asal")
    destination = models.CharField(max_length=100, blank=True, default="", verbose_name="Tujuan")
    service_type = models.CharField(max_length=50, blank=True, default="", verbose_name="Layanan")
    koli = models.IntegerField(default=1, verbose_name="Koli")
    
    actual_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Berat Aktual (Kg)")
    volume_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Berat Volume (Kg)")
    chargeable_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Berat Ditagih (Kg)")
    
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Tarif per Kg")
    freight_charge = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Ongkos Kirim Dasar")
    insurance_fee = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Asuransi")
    packing_fee = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Packing")
    handling_fee = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya Handling / Lainnya")
    surcharges = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Total Surcharges")
    discount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Diskon")
    subtotal = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Subtotal Tagihan")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item LDP"
        verbose_name_plural = "Item LDP"

    def __str__(self):
        return f"{self.awb_number} ({self.ldp.ldp_number})"

    @property
    def origin_display(self):
        if self.shipment:
            return self.shipment.origin_clean
        import re
        from apps.master.display import clean_city_name
        name = clean_city_name(self.origin)
        return re.sub(r"(?i)^(kota|kabupaten|kab\.)\s+", "", name).strip().title()

    @property
    def destination_display(self):
        if self.shipment:
            return self.shipment.destination_clean
        import re
        from apps.master.display import clean_city_name
        name = clean_city_name(self.destination)
        return re.sub(r"(?i)^(kota|kabupaten|kab\.)\s+", "", name).strip().title()


class InvoiceRevisionLog(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='revision_logs')
    old_total_amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Nominal Sebelum")
    new_total_amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Nominal Sesudah")
    reason = models.TextField(verbose_name="Alasan Revisi / Penyesuaian")
    revised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Direvisi Oleh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log Revisi Invoice"
        verbose_name_plural = "Log Revisi Invoice"
        ordering = ['-created_at']

    def __str__(self):
        return f"Revisi {self.invoice.invoice_number}: Rp{self.old_total_amount} -> Rp{self.new_total_amount}"


class PaymentReconciliation(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reconciliations')
    bank = models.ForeignKey('master.Bank', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bank Tujuan")
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Nominal Bayar")
    payment_datetime = models.DateTimeField(default=timezone.now, verbose_name="Waktu Transfer")
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Referensi Transfer")
    proof_file = models.FileField(upload_to='payment_proofs/', blank=True, null=True, validators=[validate_payment_proof], verbose_name="Bukti Transfer")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Diverifikasi Oleh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rekonsiliasi Pembayaran"
        verbose_name_plural = "Rekonsiliasi Pembayaran"
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment Rp{self.amount_paid} for {self.invoice.invoice_number}"

@receiver(post_save, sender=Invoice)
def update_kpi_finance_on_invoice_paid(sender, instance, **kwargs):
    """
    Ketika Invoice dibayar lunas (PAID), cari semua baris KpiFinance
    yang terhubung ke invoice ini dan tandai row_status-nya sebagai 'completed'.
    (Ini memenuhi requirement: Payment tidak update profit, tapi otomatis menyelesaikan baris KPI)
    """
    if instance.status == 'PAID':
        KpiFinance.objects.filter(linked_invoice=instance).update(row_status='completed')

class Vendor(models.Model):
    DELIVERY_TYPE_CHOICES = [
        ('Door to Door', 'Door to Door'),
        ('Port to Port', 'Port to Port'),
        ('Door to Port', 'Door to Port'),
        ('Port to Door', 'Port to Door'),
    ]
    TRANSPORT_CHOICES = [
        ('DARAT', 'DARAT'),
        ('LAUT', 'LAUT'),
        ('UDARA', 'UDARA'),
        ('KERETA', 'KERETA'),
    ]
    
    delivery_type = models.CharField(max_length=50, choices=DELIVERY_TYPE_CHOICES, blank=True, null=True, verbose_name="Tipe Pengiriman")
    primary_transport_mode = models.CharField(max_length=50, choices=TRANSPORT_CHOICES, blank=True, null=True, verbose_name="Moda Transportasi Utama")
    
    # Provided Transport Modes
    provided_darat = models.BooleanField(default=False, verbose_name="Darat")
    provided_laut = models.BooleanField(default=False, verbose_name="Laut")
    provided_udara = models.BooleanField(default=False, verbose_name="Udara")
    provided_kereta = models.BooleanField(default=False, verbose_name="Kereta")

    name = models.CharField(max_length=255, verbose_name="Nama Vendor")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nama PIC")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telepon / HP")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kota")
    address = models.TextField(blank=True, null=True, verbose_name="Alamat")
    
    service_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipe Layanan (Darat/Laut/Udara)")
    branch = models.ForeignKey('organizations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors', verbose_name="Cabang Terkait")
    
    # Account & Term Invoice
    npwp = models.CharField(max_length=50, blank=True, null=True, verbose_name="NPWP")
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nama Bank")
    bank_account_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Rekening")
    bank_account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="A/n Bank Account")
    payment_term_days = models.IntegerField(default=0, verbose_name="Invoice Payment Term (Days)")
    
    is_active = models.BooleanField(default=True, verbose_name="Status (Active)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dibuat Oleh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Waktu Diperbarui")

    def __str__(self):
        return self.name

class TransactionVendorCost(models.Model):
    transaction = models.ForeignKey(KpiFinance, on_delete=models.CASCADE, related_name='vendor_costs')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='transaction_costs')
    cost = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Biaya")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    def __str__(self):
        return f"{self.vendor.name} - Rp{self.cost} (Tx: {self.transaction.id})"

# Signal: Dua jalur paralel saat Shipment POD
#
# (A) KpiFinance row tetap dibuat — TAPI sekarang MURNI PENCATATAN/LOG.
#     Finance bebas pakai buat rekap, formula, laporan ad-hoc sendiri.
#     Baris ini TIDAK PERNAH lagi dibaca oleh proses invoicing.
#
# (B) Langsung (paralel, independen dari sheet) nempel ke Invoice DRAFT
#     yang "terbuka" untuk klien tsb (dibuat kalau belum ada). Ini JALUR
#     RESMI billing, sumbernya langsung dari Shipment.price, BUKAN dari sheet.
#
# Kedua jalur dieksekusi dalam satu signal untuk menjamin atomicity per
# save() event. Kegagalan di salah satu jalur di-log tapi tidak meng-block
# jalur lainnya.
from django.apps import apps

def _get_client_info(client):
    """Safely extract client attributes whether client is apps.master.models.Customer or apps.crm.models.Client."""
    if not client:
        return {
            'name': '',
            'sales_name': '',
            'industry': '',
            'paketin_group': '',
            'contact_person': '',
            'address': '',
            'npwp': '',
            'customer_code': '',
        }
    
    # Name
    client_name = getattr(client, 'name', None) or getattr(client, 'company_name', None) or str(client)

    # Sales / Owner
    sales_user = getattr(client, 'sales', None) or getattr(client, 'owner', None)
    sales_name = ""
    if sales_user:
        sales_name = sales_user.get_full_name() or getattr(sales_user, 'username', '')

    # Industry
    industry = ""
    if hasattr(client, 'get_type_industry_display') and callable(client.get_type_industry_display):
        industry = client.get_type_industry_display()
    elif hasattr(client, 'get_industry_display') and callable(client.get_industry_display):
        industry = client.get_industry_display()
    elif getattr(client, 'type_industry', None):
        industry = str(client.type_industry)
    elif getattr(client, 'industry', None):
        industry = str(client.industry)

    # Paketin group
    paketin_group = ""
    if hasattr(client, 'get_paketin_group_display') and callable(client.get_paketin_group_display):
        paketin_group = client.get_paketin_group_display()
    elif getattr(client, 'paketin_group', None):
        paketin_group = str(client.paketin_group)

    # Contact person
    contact_person = getattr(client, 'pic_account', None) or getattr(client, 'contact_person', None) or ''

    # Address
    address = getattr(client, 'office_address', None) or getattr(client, 'address', None) or ''

    # NPWP
    npwp = getattr(client, 'npwp', '') or ''

    # Customer code
    customer_code = getattr(client, 'customer_code', None) or (f"CST{client.id:04d}" if hasattr(client, 'id') and str(client.id).isdigit() else str(getattr(client, 'id', '')))

    return {
        'name': client_name,
        'sales_name': sales_name,
        'industry': industry,
        'paketin_group': paketin_group,
        'contact_person': contact_person,
        'address': address,
        'npwp': npwp,
        'customer_code': customer_code,
    }

@receiver(post_save, sender='operations.Shipment')
def auto_create_finance_transaction(sender, instance, **kwargs):
    """
    Signal utama saat Shipment di-save. Menjalankan dua jalur paralel:
    - Jalur A: buat/update baris KpiFinance (log/snapshot untuk worksheet)
    - Jalur B: attach shipment ke rolling draft Invoice (jalur resmi billing)

    Desain ini menjamin sheet dan invoice punya sumber angka sendiri-sendiri
    yang tidak saling bergantung — sheet boleh diedit sesuka Finance tanpa
    mengubah angka di invoice, dan sebaliknya.
    """
    Shipment = apps.get_model('operations', 'Shipment')
    client_info = _get_client_info(instance.client)
    client_name = client_info['name'] or instance.sender_name or ''

    finance_obj = KpiFinance.objects.filter(awb=instance.resi_number).first()
    if instance.status == 'POD':
        # ─── JALUR A: KpiFinance (log/snapshot) ───────────────────────
        # Baris yang sudah terkunci di sebuah Invoice (invoiced/completed)
        # tidak boleh lagi diubah otomatis oleh sync operasional.
        if finance_obj and finance_obj.row_status in ('invoiced', 'completed'):
            pass  # skip update, tapi tetap lanjut ke jalur B
        elif not finance_obj:
            from .utils import get_primary_kpi_sheet
            sheet = get_primary_kpi_sheet(instance.created_at.date())

            actual_shipment = Shipment.objects.filter(resi_number=instance.resi_number).first()

            sales_name = client_info['sales_name']
            jenis_barang = client_info['industry']

            KpiFinance.objects.create(
                sheet=sheet,
                tanggal_pickup=instance.created_at.date(),
                awb=instance.resi_number,
                pengirim=client_name,
                penerima=instance.receiver_name,
                service=instance.service_type,
                aktual=instance.weight,
                vol=instance.volume_weight,
                p=instance.length,
                l=instance.width,
                t=instance.height,
                penjualan=instance.price,
                asal_pickup=instance.origin,
                ip_perusahaan=client_info['paketin_group'],
                tujuan=instance.destination,
                jenis_barang=jenis_barang,
                sales=sales_name,
                source='import',
                row_status='new',
                shipment=actual_shipment,
            )
        else:
            # Update existing finance row
            sales_name = client_info['sales_name']
            jenis_barang = client_info['industry']

            finance_obj.pengirim = client_name
            finance_obj.sales = sales_name
            finance_obj.jenis_barang = jenis_barang
            finance_obj.ip_perusahaan = client_info['paketin_group']
            finance_obj.aktual = instance.weight
            finance_obj.vol = instance.volume_weight
            finance_obj.p = instance.length
            finance_obj.l = instance.width
            finance_obj.t = instance.height
            finance_obj.penjualan = instance.price
            finance_obj.row_status = 'new' if finance_obj.row_status == 'voided' else finance_obj.row_status
            if not finance_obj.shipment:
                finance_obj.shipment = instance
            finance_obj.save()

        # ─── JALUR B: Rolling draft Invoice (jalur resmi billing) ─────
        # Hanya untuk shipment yang punya client (kontrak), dan hanya kalau
        # shipment ini belum pernah masuk ke invoice manapun.
        if instance.client and not instance.invoices.exists():
            _attach_shipment_to_rolling_draft(instance)

    elif instance.status == 'VOID':
        # Reversal Logic — hanya berlaku untuk baris KpiFinance yang BELUM masuk invoice.
        if finance_obj and finance_obj.row_status not in ('invoiced', 'completed'):
            finance_obj.penjualan = 0
            finance_obj.row_status = 'voided'
            finance_obj.save()


def _attach_shipment_to_rolling_draft(shipment_instance):
    """
    Cari Invoice DRAFT yang masih is_open=True untuk client yang sama.
    Kalau belum ada, buat baru. Attach shipment, lalu recalc total dari
    SUM(Shipment.price) — BUKAN dari KpiFinance.

    Fungsi ini sengaja dipisah dari signal supaya bisa dipanggil ulang
    dari view lain (misal attach manual) tanpa copy-paste logic.
    """
    from django.utils import timezone

    client = shipment_instance.client
    client_info = _get_client_info(client)
    client_name = client_info['name'] or shipment_instance.sender_name or 'Unknown Client'

    # Cari draft terbuka untuk klien ini
    invoice = (
        Invoice.objects
        .filter(client_name=client_name, status='DRAFT', is_open=True)
        .first()
    )

    if not invoice:
        # Buat draft baru — snapshot data pelanggan
        sales_name = client_info['sales_name']
        invoice_code = ''.join(filter(str.isalnum, client_name))[:3].upper() or 'GEN'
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{invoice_code}"

        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            client_name=client_name,
            status='DRAFT',
            is_open=True,
            company_code=client_info['paketin_group'] or 'PT AMANAH',
            kode_pelanggan=client_info['customer_code'],
            pic_invoice=client_info['contact_person'],
            alamat_pelanggan=client_info['address'],
            npwp=client_info['npwp'],
            sales_ae=sales_name,
        )

    # Attach shipment ke invoice dan recalc total dari Shipment.price
    invoice.shipments.add(shipment_instance)
    invoice.update_totals(recalc_from_shipments=True)

    # Update linked_invoice di KpiFinance (display only) jika ada
    kpi_row = KpiFinance.objects.filter(awb=shipment_instance.resi_number).first()
    if kpi_row and not kpi_row.linked_invoice:
        kpi_row.linked_invoice = invoice
        kpi_row.save(update_fields=['linked_invoice'])

# 9. BRANCH WALLET / DEPOSIT (PHASE 3)
class BranchWallet(models.Model):
    branch = models.OneToOneField('organizations.Branch', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Saldo")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dompet {self.branch.name} - Rp{self.balance}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('TOPUP', 'Topup / Deposit'),
        ('DEDUCT', 'Potongan / Pengeluaran'),
        ('SHIPMENT', 'Potongan Resi Cash'),
    ]
    wallet = models.ForeignKey(BranchWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Nomor Resi atau Referensi Bank")
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} Rp{self.amount} - {self.wallet.branch.name}"
