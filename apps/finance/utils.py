"""
Utilities untuk pencetakan Invoice:
- terbilang_rupiah(): konversi angka -> teks Bahasa Indonesia
- FINANCE_COMPANY_PROFILES: kop surat & rekening bank per brand Paketin Group,
  dipakai oleh invoice_pdf.html berdasarkan Invoice.company_code
"""

_SATUAN = [
    "", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan",
    "sembilan", "sepuluh", "sebelas",
]


def _terbilang(n: int) -> str:
    n = int(n)
    if n < 12:
        return _SATUAN[n]
    if n < 20:
        return (_terbilang(n - 10) + " belas").strip()
    if n < 100:
        sisa = n % 10
        return (_terbilang(n // 10) + " puluh" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 200:
        sisa = n - 100
        return ("seratus" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 1000:
        sisa = n % 100
        return (_terbilang(n // 100) + " ratus" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 2000:
        sisa = n - 1000
        return ("seribu" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 1_000_000:
        sisa = n % 1000
        return (_terbilang(n // 1000) + " ribu" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 1_000_000_000:
        sisa = n % 1_000_000
        return (_terbilang(n // 1_000_000) + " juta" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    if n < 1_000_000_000_000:
        sisa = n % 1_000_000_000
        return (_terbilang(n // 1_000_000_000) + " miliar" + (f" {_terbilang(sisa)}" if sisa else "")).strip()
    sisa = n % 1_000_000_000_000
    return (_terbilang(n // 1_000_000_000_000) + " triliun" + (f" {_terbilang(sisa)}" if sisa else "")).strip()


def terbilang_rupiah(amount) -> str:
    """
    515610 -> "Lima Ratus Lima Belas Ribu Enam Ratus Sepuluh Rupiah"
    Rupiah dibulatkan ke bawah (sen tidak dieja).
    """
    n = int(amount)
    if n == 0:
        return "Nol Rupiah"
    negatif = n < 0
    words = _terbilang(abs(n))
    words = " ".join(words.split())  # rapikan spasi ganda
    hasil = f"{words} Rupiah".title()
    return f"Minus {hasil}" if negatif else hasil


def parse_currency_decimal(val, default=None):
    """
    Parses currency strings safely handling Indonesian formats (e.g. '500.000', '50.000,50')
    and standard HTML input[type=number] decimal notation (e.g. '50000.00', '50000').
    """
    from decimal import Decimal
    if default is None:
        default = Decimal('0')

    if val is None:
        return default
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))

    s = str(val).strip()
    if not s:
        return default

    # Remove currency prefixes like "Rp", "RP", spaces
    import re
    s = re.sub(r'^rp\.?\s*', '', s, flags=re.IGNORECASE).strip()

    if ',' in s:
        # Indonesian format: 1.000.000,50 -> 1000000.50
        s_clean = s.replace('.', '').replace(',', '.')
        try:
            return Decimal(s_clean)
        except Exception:
            return default

    if '.' in s:
        parts = s.split('.')
        # Multiple dots -> thousand separators e.g. 1.000.000
        if len(parts) > 2:
            try:
                return Decimal(s.replace('.', ''))
            except Exception:
                return default
        elif len(parts) == 2:
            # Single dot: if 3 digits after dot and integer (e.g. "500.000" but not "50000.00"),
            # check if it could be a thousand separator
            if len(parts[1]) == 3 and len(parts[0]) <= 3 and parts[1].isdigit():
                # E.g. "500.000" -> 500000
                try:
                    return Decimal(s.replace('.', ''))
                except Exception:
                    pass
            # Standard decimal (e.g. "51100.00" or "500.50")
            try:
                return Decimal(s)
            except Exception:
                try:
                    return Decimal(s.replace('.', ''))
                except Exception:
                    return default

    try:
        return Decimal(s)
    except Exception:
        return default


# Kop surat & rekening bank per brand -- sesuaikan/isi manual untuk
# PT SARANA & PT SINERGI kalau brand itu sudah aktif menerbitkan invoice.
FINANCE_COMPANY_PROFILES = {
    'PT AMANAH': {
        'legal_name': 'PT. Amanah Cargo Jaya Mandiri',
        'brand_name': 'Paketin Cargo',
        'address': (
            'Kantor Pusat : Jl. Arteri Jorr Jatiwarna No.55, RT.001/RW.002, '
            'Jatimelati, Kec. Pd. Melati, Kota Bks, Jawa Barat 17415'
        ),
        'phone': '0811 151 7716',
        'website': 'www.paketincargo.com',
        'bank_accounts': [
            {'bank': 'BANK BCA PT AMANAH CARGO JAYA MANDIRI', 'no_rek': '5510766999'},
            {'bank': 'BANK BNI PT AMANAH CARGO JAYA MANDIRI', 'no_rek': '1147244331'},
        ],
    },
    'PT SARANA': {
        'legal_name': 'PT. Sarana Express',
        'brand_name': 'Sarana Express',
        'address': '',
        'phone': '',
        'website': 'www.paketincargo.com',
        'bank_accounts': [],
    },
    'PT SINERGI': {
        'legal_name': 'PT. Sinergi',
        'brand_name': 'Paketin Express',
        'address': '',
        'phone': '',
        'website': 'www.paketincargo.com',
        'bank_accounts': [],
    },
}


def get_primary_kpi_sheet(target_date=None):
    """
    Mengambil KpiSheet pada 1 File Utama Tunggal 'KPI Finance [Year]'.
    Menjamin seluruh modul (Operasional, CRM, Invoicing) menulis ke 1 file tahunan yang sama.
    """
    from django.utils import timezone
    from apps.finance.models import KpiFile, KpiSheet

    dt = target_date or timezone.now().date()
    year = dt.year if hasattr(dt, 'year') else timezone.now().year
    month_name = dt.strftime('%B') if hasattr(dt, 'strftime') else 'Januari'

    file_obj, _ = KpiFile.objects.get_or_create(name=f"KPI Finance {year}")
    
    # Cari sheet bulan yang cocok, atau sheet pertama file, atau buat baru
    sheet_obj = file_obj.sheets.filter(name__iexact=month_name).first()
    if not sheet_obj:
        sheet_obj = file_obj.sheets.first()
    if not sheet_obj:
        sheet_obj = KpiSheet.objects.create(
            kpi_file=file_obj,
            name=month_name,
            sheet_type='data',
            sort_order=0
        )
    return sheet_obj


def sync_invoice_shipments_to_worksheet(invoice):
    """
    Opsi A: Mencatatkan seluruh resi/AWB yang ada di dalam Invoice ke baris Worksheet (KpiFinance).
    Data harga, berat, nomor invoice, kustomer, sales terisi lengkap dan terkunci (row_status='invoiced').
    """
    from django.utils import timezone
    from apps.finance.models import KpiFinance
    from apps.operations.models import Shipment

    shipments = invoice.shipments.all()
    if not shipments.exists():
        ldp_rel = getattr(invoice, 'ldps', None) or getattr(invoice, 'ldp_batches', None)
        if ldp_rel and ldp_rel.exists():
            ship_ids = []
            for ldp in ldp_rel.all():
                ship_ids.extend(ldp.items.exclude(shipment__isnull=True).values_list('shipment_id', flat=True))
            if ship_ids:
                shipments = Shipment.objects.filter(id__in=ship_ids)

    target_date = getattr(invoice, 'date_issued', None) or (invoice.created_at.date() if invoice.created_at else timezone.now().date())
    target_sheet = get_primary_kpi_sheet(target_date)

    synced_rows = 0
    for ship in shipments:
        kpi_row = KpiFinance.objects.filter(awb=ship.resi_number).first()
        if not kpi_row:
            kpi_row = KpiFinance.objects.filter(shipment=ship).first()

        sender_name = invoice.client_name or ship.sender_name or (ship.client.name if ship.client else "")
        sales_name = invoice.sales_ae or (ship.client.sales.get_full_name() if ship.client and ship.client.sales else "")

        defaults = {
            'sheet': target_sheet,
            'tanggal_pickup': ship.created_at.date() if ship.created_at else target_date,
            'nama': invoice.company_code or (ship.client.paketin_group if ship.client else 'PT AMANAH'),
            'awb': ship.resi_number,
            'awb_sistem': invoice.invoice_number,
            'pengirim': sender_name,
            'sales': sales_name,
            'penerima': ship.receiver_name or "",
            'service': ship.service_type or "REGULER",
            'via': getattr(ship, 'transport_mode', '') or "DARAT",
            'aktual': ship.weight or 0,
            'vol': ship.volume_weight or 0,
            'p': getattr(ship, 'panjang', getattr(ship, 'length', 0)) or 0,
            'l': getattr(ship, 'lebar', getattr(ship, 'width', 0)) or 0,
            't': getattr(ship, 'tinggi', getattr(ship, 'height', 0)) or 0,
            'koil': getattr(ship, 'colly_count', 1) or 1,
            'harga': getattr(ship, 'price_per_kg', getattr(ship, 'rate', 0)) or 0,
            'surcharge': getattr(ship, 'surcharge_cost', 0) or 0,
            'packing': getattr(ship, 'packing_cost', 0) or 0,
            'handling': getattr(ship, 'handling_cost', 0) or 0,
            'penjualan': ship.price or ship.total_cost or 0,
            'asal_pickup': ship.origin or "",
            'ip_perusahaan': invoice.company_code or "PT AMANAH",
            'jenis_barang': getattr(ship, 'item_description', getattr(ship, 'goods_name', '')) or "",
            'tujuan': ship.destination or "",
            'asuransi': getattr(ship, 'insurance_cost', 0) or 0,
            'nilai_barang': getattr(ship, 'goods_value', 0) or 0,
            'linked_invoice': invoice,
            'shipment': ship,
            'source': 'import',
            'row_status': 'invoiced',
        }

        if kpi_row:
            for k, v in defaults.items():
                setattr(kpi_row, k, v)
            kpi_row.save()
        else:
            KpiFinance.objects.create(**defaults)

        synced_rows += 1

    return synced_rows

