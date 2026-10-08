import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(value, max_size_mb=10):
    """
    Validasi ukuran maksimum file yang diunggah (default: 10MB).
    """
    file_size = value.size
    limit = max_size_mb * 1024 * 1024
    if file_size > limit:
        raise ValidationError(
            _('Ukuran berkas melebihi batas maksimum %(max_size)s MB. Ukuran saat ini: %(current_size).2f MB.') % {
                'max_size': max_size_mb,
                'current_size': file_size / (1024 * 1024)
            }
        )

def validate_image_file(value):
    """
    Validasi berkas gambar (JPG, JPEG, PNG, WEBP). Maks 5MB.
    """
    validate_file_size(value, max_size_mb=5)
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(
            _('Format berkas tidak didukung (%(ext)s). Format yang diizinkan: %(allowed)s.') % {
                'ext': ext,
                'allowed': ', '.join(valid_extensions)
            }
        )

def validate_document_file(value):
    """
    Validasi berkas dokumen & lampiran (PDF, JPG, JPEG, PNG, WEBP, DOCX, XLSX). Maks 10MB.
    """
    validate_file_size(value, max_size_mb=10)
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp', '.docx', '.xlsx']
    if ext not in valid_extensions:
        raise ValidationError(
            _('Format berkas tidak didukung (%(ext)s). Format yang diizinkan: %(allowed)s.') % {
                'ext': ext,
                'allowed': ', '.join(valid_extensions)
            }
        )

def validate_payment_proof(value):
    """
    Validasi khusus bukti transfer / pembayaran (PDF, JPG, JPEG, PNG). Maks 5MB.
    """
    validate_file_size(value, max_size_mb=5)
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError(
            _('Format bukti transfer tidak didukung (%(ext)s). Harap unggah berkas PDF atau Gambar (JPG, PNG).') % {
                'ext': ext
            }
        )
