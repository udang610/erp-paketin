from django.db import models

class AssetCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nama Kategori")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")

    def __str__(self):
        return self.name

class AssetItem(models.Model):
    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255, verbose_name="Nama Barang")
    stock = models.IntegerField(default=0, verbose_name="Stok Tersedia")
    unit = models.CharField(max_length=50, verbose_name="Satuan (pcs, box, dll)")
    is_active = models.BooleanField(default=True)
    
    # HRGA fields
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Harga Beli Terakhir")

    def __str__(self):
        return f"{self.name} ({self.stock} {self.unit})"

class AssetTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Persetujuan'),
        ('APPROVED', 'Disetujui'),
        ('REJECTED', 'Ditolak'),
        ('COMPLETED', 'Selesai (Sudah Diambil)'),
    ]

    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='asset_requests')
    item = models.ForeignKey(AssetItem, on_delete=models.CASCADE, related_name='transactions')
    quantity = models.IntegerField(default=1, verbose_name="Jumlah")
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Pengajuan")
    reason = models.TextField(verbose_name="Alasan / Keperluan")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Bukti Pengambilan (via mobile)
    photo_proof = models.ImageField(upload_to='asset_proofs/', blank=True, null=True, verbose_name="Foto Bukti")
    signature = models.ImageField(upload_to='asset_signatures/', blank=True, null=True, verbose_name="Tanda Tangan")
    
    # Optional HRGA Approval
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_assets')
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Req {self.quantity} {self.item.name} by {self.employee.full_name or self.employee.user.username}"
