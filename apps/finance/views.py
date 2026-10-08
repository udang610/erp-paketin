from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import KpiFile, KpiSheet, KpiFinance, Profile, CellStyle, AuditLog
from .serializers import KpiFileSerializer, KpiSheetSerializer, KpiFinanceSerializer, ProfileSerializer, CellStyleSerializer, AuditLogSerializer

# ==================== SSR VIEWS (for ERP sidebar integration) ====================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from datetime import datetime
import django


@login_required
def worksheet_view(request):
    """
    SSR view: Worksheet SPA embedded within ERP shell.
    """
    context = {
        'is_finance_spreadsheet': True,  # Flag for base.html to adjust layout
    }
    return render(request, 'finance/worksheet/worksheet.html', context)

@login_required
def invoice_list(request):
    from .models import Invoice, Vendor, TransactionVendorCost, KpiFinance
    from django.core.paginator import Paginator
    from django.db.models import Q, Sum

    main_tab = request.GET.get('main_tab', 'client')
    tab = request.GET.get('tab', 'all')
    search = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    # Client Invoices (AR) - Exclude status PAID karena sudah diarsip di Riwayat Selesai
    client_qs = Invoice.objects.exclude(status='PAID').order_by('-created_at')

    if tab == 'draft':
        client_qs = client_qs.filter(status='DRAFT')
    elif tab == 'sent':
        client_qs = client_qs.filter(status='SENT')
    elif tab == 'partial':
        client_qs = client_qs.filter(status='PARTIAL')
    elif tab == 'paid':
        client_qs = Invoice.objects.filter(status='PAID').order_by('-created_at')
    elif tab == 'void':
        client_qs = Invoice.objects.filter(status='VOID').order_by('-created_at')

    from apps.core.date_utils import parse_date_safe
    pdf = parse_date_safe(date_from)
    pdt = parse_date_safe(date_to)

    if search:
        matched_client_qs = client_qs.filter(
            Q(invoice_number__icontains=search) | 
            Q(client_name__icontains=search) | 
            Q(kode_pelanggan__icontains=search) |
            Q(notes__icontains=search)
        )
        date_filtered_qs = matched_client_qs
        if pdf:
            date_filtered_qs = date_filtered_qs.filter(date_issued__gte=pdf)
        if pdt:
            date_filtered_qs = date_filtered_qs.filter(date_issued__lte=pdt)
            
        if date_filtered_qs.exists():
            client_qs = date_filtered_qs
        else:
            client_qs = matched_client_qs
    else:
        if pdf:
            client_qs = client_qs.filter(date_issued__gte=pdf)
        if pdt:
            client_qs = client_qs.filter(date_issued__lte=pdt)

    # Counters for Client Invoice tabs (total_client_all hanya menghitung invoice aktif / belum lunas)
    total_client_all = Invoice.objects.exclude(status='PAID').count()
    total_draft = Invoice.objects.filter(status='DRAFT').count()
    total_sent = Invoice.objects.filter(status='SENT').count()
    total_partial = Invoice.objects.filter(status='PARTIAL').count()
    total_paid = Invoice.objects.filter(status='PAID').count()
    total_void = Invoice.objects.filter(status='VOID').count()

    # Summary metrics for Client Invoices
    metrics = client_qs.aggregate(
        total_invoices=Count('id'),
        total_amount=Sum('total_amount'),
        total_paid=Sum('amount_paid'),
    )
    total_tagihan = metrics['total_amount'] or 0
    total_terbayar = metrics['total_paid'] or 0
    sisa_piutang = total_tagihan - total_terbayar

    # Vendor Bills / Costs (AP)
    vendor_qs = TransactionVendorCost.objects.select_related('vendor', 'transaction', 'transaction__shipment').order_by('-id')
    if search:
        vendor_qs = vendor_qs.filter(
            Q(vendor__name__icontains=search) |
            Q(transaction__awb__icontains=search) |
            Q(notes__icontains=search)
        )
    total_vendor_all = vendor_qs.count()
    total_vendor_cost = vendor_qs.aggregate(total=Sum('cost'))['total'] or 0
    total_active_vendors = Vendor.objects.filter(is_active=True).count()

    # Pagination
    if main_tab == 'vendor':
        paginator = Paginator(vendor_qs, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        paginator = Paginator(client_qs, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
    context = {
        'main_tab': main_tab,
        'invoices': page_obj,
        'vendor_costs': page_obj if main_tab == 'vendor' else vendor_qs[:25],
        'page_obj': page_obj,
        'tab': tab,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'total_client_all': total_client_all,
        'total_all': total_client_all,
        'total_vendor_all': total_vendor_all,
        'total_active_vendors': total_active_vendors,
        'total_vendor_cost': total_vendor_cost,
        'total_draft': total_draft,
        'total_sent': total_sent,
        'total_partial': total_partial,
        'total_paid': total_paid,
        'total_void': total_void,
        'total_tagihan': total_tagihan,
        'total_terbayar': total_terbayar,
        'sisa_piutang': sisa_piutang,
    }
    return render(request, 'finance/invoices/invoice_list.html', context)

@login_required
def invoice_detail(request, invoice_id):
    from .models import Invoice, PaymentRecord, LDP, LDPItem
    invoice = get_object_or_404(Invoice, id=invoice_id)
    payments = PaymentRecord.objects.filter(invoice=invoice).order_by('-payment_date')
    
    # Handle payment submission
    if request.method == 'POST' and 'add_payment' in request.POST:
        from decimal import Decimal
        from .utils import parse_currency_decimal
        amount = parse_currency_decimal(request.POST.get('amount'))

        method = request.POST.get('payment_method', 'Transfer Bank')
        ref = request.POST.get('reference_number', '')
        
        if amount > Decimal('0'):
            PaymentRecord.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=method,
                reference_number=ref
            )
            # Update invoice paid amount
            invoice.amount_paid += amount
            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = 'PAID'
            elif invoice.amount_paid > Decimal('0'):
                invoice.status = 'PARTIAL'
            invoice.save()
            return redirect('finance:invoice_detail', invoice_id=invoice.id)

    ldps = invoice.ldps.all().order_by('-created_at')
    awb_items = LDPItem.objects.filter(ldp__in=ldps).select_related('ldp', 'shipment').order_by('id')
    
    context = {
        'invoice': invoice,
        'payments': payments,
        'ldps': ldps,
        'awb_items': awb_items,
        'sisa_tagihan': invoice.total_amount - invoice.amount_paid
    }
    return render(request, 'finance/invoices/invoice_detail.html', context)
@login_required
def invoice_delete(request, invoice_id):
    if not request.user.is_superuser:
        from django.contrib import messages
        messages.error(request, "Anda tidak memiliki izin untuk menghapus invoice. Hanya Superadmin yang diizinkan.")
        return redirect('finance:invoice_list')
        
    if request.method == 'POST':
        from .models import Invoice
        invoice = get_object_or_404(Invoice, id=invoice_id)
        invoice_number = invoice.invoice_number
        invoice.delete()
        
        from django.contrib import messages
        messages.success(request, f"Invoice {invoice_number} berhasil dihapus permanen.")
        
    return redirect('finance:invoice_list')


@login_required
def close_invoice(request, invoice_id):
    """
    Tutup & Terbitkan: set is_open=False, status='SENT'.

    Setelah ini, signal rolling draft TIDAK BOLEH lagi menambahkan shipment
    baru ke invoice ini. Shipment baru untuk klien yang sama akan masuk ke
    draft baru yang is_open=True.
    """
    from .models import Invoice
    from django.contrib import messages

    if request.method != 'POST':
        return redirect('finance:invoice_detail', invoice_id=invoice_id)

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if invoice.status != 'DRAFT':
        messages.error(request, "Hanya invoice DRAFT yang bisa ditutup & diterbitkan.")
        return redirect('finance:invoice_detail', invoice_id=invoice.id)

    invoice.is_open = False
    invoice.status = 'SENT'
    invoice.save(update_fields=['is_open', 'status'])

    messages.success(request, f"Invoice {invoice.invoice_number} berhasil diterbitkan. Status: SENT.")
    return redirect('finance:invoice_detail', invoice_id=invoice.id)


@login_required
def remove_shipment_from_invoice(request, invoice_id, shipment_id):
    """
    Hapus satu shipment dari invoice DRAFT yang masih terbuka.
    Setelah dihapus, recalc total dari sisa shipment yang masih terhubung.
    Shipment yang dihapus jadi 'unbilled' lagi dan bisa masuk ke draft berikutnya.
    """
    from .models import Invoice, KpiFinance
    from django.contrib import messages
    from django.apps import apps

    if request.method != 'POST':
        return redirect('finance:invoice_detail', invoice_id=invoice_id)

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if invoice.status != 'DRAFT':
        messages.error(request, "Hanya bisa menghapus shipment dari invoice DRAFT.")
        return redirect('finance:invoice_detail', invoice_id=invoice.id)

    Shipment = apps.get_model('operations', 'Shipment')
    shipment = get_object_or_404(Shipment, id=shipment_id)

    invoice.shipments.remove(shipment)
    invoice.update_totals(recalc_from_shipments=True)

    # Hapus linked_invoice di KpiFinance jika ada
    kpi_row = KpiFinance.objects.filter(awb=shipment.resi_number, linked_invoice=invoice).first()
    if kpi_row:
        kpi_row.linked_invoice = None
        kpi_row.save(update_fields=['linked_invoice'])

    messages.success(request, f"Shipment {shipment.resi_number} dihapus dari invoice.")
    return redirect('finance:invoice_detail', invoice_id=invoice.id)


@login_required
def unbilled_transactions(request):
    """
    [FALLBACK / JALUR DARURAT]

    Antrian transaksi yang statusnya sudah masuk ke Finance (row_status
    'new' atau 'vendor_filled') tapi BELUM masuk ke Invoice manapun.

    Jalur utama invoicing sekarang adalah rolling draft otomatis (signal
    di models.py), BUKAN lagi dari halaman ini. Halaman ini tetap ada
    sebagai jalur alternatif untuk:
    - Shipment lama yang belum sempat ke-attach ke draft (data historis)
    - Kasus darurat yang perlu manual override
    """
    from .models import KpiFinance
    from apps.master.models import Customer

    client_id = request.GET.get('client_id') or request.GET.get('client') or ''
    periode_awal = request.GET.get('periode_awal') or ''
    periode_akhir = request.GET.get('periode_akhir') or ''

    rows = (
        KpiFinance.objects
        .filter(row_status__in=['new', 'vendor_filled'])
        .exclude(shipment__isnull=True)
        .select_related('shipment', 'shipment__client')
        .order_by('tanggal_pickup')
    )

    if client_id:
        rows = rows.filter(shipment__client_id=client_id)
    if periode_awal:
        rows = rows.filter(tanggal_pickup__gte=periode_awal)
    if periode_akhir:
        rows = rows.filter(tanggal_pickup__lte=periode_akhir)

    total_penjualan = rows.aggregate(total=Sum('penjualan'))['total'] or 0

    context = {
        'rows': rows,
        'clients': Customer.objects.filter(is_active=True).order_by('name'),
        'selected_client': client_id,
        'periode_awal': periode_awal,
        'periode_akhir': periode_akhir,
        'total_penjualan': total_penjualan,
    }
    return render(request, 'finance/invoices/unbilled_transactions.html', context)


@login_required
def generate_invoice(request):
    """
    [FALLBACK / JALUR DARURAT]

    Aksi manual Finance untuk membentuk Invoice DRAFT dari sekumpulan
    baris KpiFinance yang sudah diverifikasi. Jalur utama invoicing
    sekarang adalah rolling draft otomatis (signal di models.py).

    View ini tetap dipertahankan untuk kasus darurat / shipment historis
    yang belum ke-cover oleh rolling draft.
    """
    from .models import KpiFinance, Invoice, _get_client_info
    from apps.master.models import Customer
    from django.contrib import messages
    from django.utils import timezone
    from datetime import datetime
    import decimal

    if request.method != 'POST':
        return redirect('finance:unbilled_transactions')

    row_ids = request.POST.getlist('row_ids')
    client_id = request.POST.get('client_id') or request.POST.get('client')
    periode_awal_raw = request.POST.get('periode_awal') or ''
    periode_akhir_raw = request.POST.get('periode_akhir') or ''

    if not row_ids or not client_id:
        messages.error(request, "Pilih klien dan minimal satu transaksi sebelum generate invoice.")
        return redirect('finance:unbilled_transactions')

    customer = Customer.objects.filter(id=client_id).first()
    client_info = _get_client_info(customer)

    rows = (
        KpiFinance.objects
        .filter(id__in=row_ids, row_status__in=['new', 'vendor_filled'], shipment__client_id=client_id)
        .select_related('shipment')
    )

    if not rows.exists():
        messages.error(request, "Transaksi yang dipilih sudah tidak valid (mungkin sudah ditagih di invoice lain).")
        return redirect('finance:unbilled_transactions')

    client_display_name = client_info['name'] or 'Klien Umum'
    invoice_code = ''.join(filter(str.isalnum, client_display_name))[:3].upper() or 'GEN'
    invoice_number = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{invoice_code}"

    def _parse_date(raw):
        try:
            return datetime.strptime(raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    periode_awal = _parse_date(periode_awal_raw)
    periode_akhir = _parse_date(periode_akhir_raw)

    # Snapshot data pelanggan & rekap dari baris terpilih
    total_biaya_kirim = decimal.Decimal('0')
    total_premi_asuransi = decimal.Decimal('0')
    sales_names = set()
    for row in rows:
        total_biaya_kirim += row.penjualan or 0
        total_premi_asuransi += row.asuransi or 0
        if row.sales:
            sales_names.add(row.sales)

    if client_info['sales_name']:
        sales_names.add(client_info['sales_name'])

    invoice = Invoice.objects.create(
        invoice_number=invoice_number,
        client_name=client_display_name,
        status='DRAFT',
        notes=f"Periode: {periode_awal_raw or '-'} s/d {periode_akhir_raw or '-'}",
        company_code=client_info['paketin_group'] or 'PT AMANAH',
        kode_pelanggan=client_info['customer_code'],
        pic_invoice=client_info['contact_person'],
        alamat_pelanggan=client_info['address'],
        npwp=client_info['npwp'],
        sales_ae=", ".join(sorted(sales_names)) if sales_names else "",
        periode_awal=periode_awal,
        periode_akhir=periode_akhir,
        biaya_kirim=total_biaya_kirim,
        premi_asuransi=total_premi_asuransi,
    )

    locked_count = 0
    for row in rows:
        if row.shipment:
            invoice.shipments.add(row.shipment)
        row.row_status = 'invoiced'
        row.save(update_fields=['row_status'])
        locked_count += 1

    invoice.update_totals()

    messages.success(request, f"Invoice {invoice.invoice_number} berhasil dibuat dari {locked_count} transaksi.")
    return redirect('finance:invoice_detail', invoice_id=invoice.id)


@login_required
def invoice_pdf(request, invoice_id, filename=None):
    """
    Render Invoice ke PDF pakai xhtml2pdf (pisa), mengikuti layout
    invoice cetak Paketin Cargo (lihat finance/invoice_pdf.html).
    Jika status PAID, overlay cap stempel LUNAS di atas tabel rincian.
    """
    from .models import Invoice
    from .utils import FINANCE_COMPANY_PROFILES
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    import io

    invoice = get_object_or_404(Invoice, id=invoice_id)
    company = FINANCE_COMPANY_PROFILES.get(invoice.company_code, FINANCE_COMPANY_PROFILES['PT AMANAH'])

    import os
    from django.conf import settings
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-surat.png').replace('\\', '/')
    stamp_lunas_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'stamp_lunas.png').replace('\\', '/')

    html_string = render_to_string('finance/invoices/invoice_print_pdf.html', {
        'invoice': invoice,
        'company': company,
        'logo_path': logo_path if os.path.exists(logo_path) else None,
    }, request=request)

    # Render HTML to PDF bytes
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
    if pisa_status.err:
        return HttpResponse(f'Error generating PDF: <pre>{html_string}</pre>')

    # If PAID, overlay the stamp on top of the items table
    if invoice.status == 'PAID' and os.path.exists(stamp_lunas_path):
        try:
            import pymupdf
            pdf_buffer.seek(0)
            doc = pymupdf.open(stream=pdf_buffer.read(), filetype='pdf')
            page = doc[0]
            pw = page.rect.width   # ~595 for A4
            ph = page.rect.height  # ~842 for A4

            # Position stamp over the center of the items table area
            # Table starts roughly at 33% from top, stamp centered on table
            stamp_w = 240
            stamp_h = 100
            cx = pw * 0.55           # center-right of page
            cy = ph * 0.42           # vertically centered on items table
            stamp_rect = pymupdf.Rect(
                cx - stamp_w / 2,
                cy - stamp_h / 2,
                cx + stamp_w / 2,
                cy + stamp_h / 2,
            )
            page.insert_image(stamp_rect, filename=stamp_lunas_path, overlay=True)

            # Write modified PDF to new buffer
            final_buffer = io.BytesIO()
            doc.save(final_buffer)
            doc.close()
            pdf_bytes = final_buffer.getvalue()
        except Exception:
            # Fallback: use original PDF without overlay
            pdf_buffer.seek(0)
            pdf_bytes = pdf_buffer.read()
    else:
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    disposition = 'attachment' if request.GET.get('download') else 'inline'
    safe_number = str(invoice.invoice_number or invoice.id).replace('/', '-').replace('\\', '-').strip()
    response['Content-Disposition'] = f'{disposition}; filename="Invoice_{safe_number}.pdf"'
    return response


@login_required
def financial_report(request):
    """
    Laporan Keuangan & Billing yang selaras dengan standar Report di Operasional & CRM.
    Mendukung filter tanggal, tahun, status, klien, sales, pagination, dan metrik P&L.
    """
    import json
    from datetime import datetime, date
    from django.db.models import Sum, Q
    import django.db.models.functions
    from django.core.paginator import Paginator
    from .models import Invoice, KpiFinance, TransactionVendorCost

    # Filter parameters
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()
    current_year = datetime.now().year
    year_filter = request.GET.get('year', '').strip()
    if not year_filter and not start_date_str and not end_date_str:
        year_filter = str(current_year)

    status_filter = request.GET.get('status', '').strip()
    client_filter = request.GET.get('client', '').strip()
    sales_filter = request.GET.get('sales_ae', '').strip()
    search_query = request.GET.get('q', '').strip()

    def parse_dt(d_str):
        if not d_str:
            return None
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(d_str, fmt).date()
            except ValueError:
                continue
        return None

    parsed_start = parse_dt(start_date_str)
    parsed_end = parse_dt(end_date_str)

    # Base Queryset
    inv_qs = Invoice.objects.all().order_by('-date_issued', '-created_at')

    if parsed_start:
        inv_qs = inv_qs.filter(date_issued__gte=parsed_start)
    if parsed_end:
        inv_qs = inv_qs.filter(date_issued__lte=parsed_end)
    if year_filter and year_filter.isdigit():
        inv_qs = inv_qs.filter(date_issued__year=int(year_filter))

    if status_filter:
        inv_qs = inv_qs.filter(status=status_filter)
    if client_filter:
        inv_qs = inv_qs.filter(client_name__icontains=client_filter)
    if sales_filter:
        inv_qs = inv_qs.filter(sales_ae__icontains=sales_filter)
    if search_query:
        inv_qs = inv_qs.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client_name__icontains=search_query) |
            Q(sales_ae__icontains=search_query) |
            Q(pic_invoice__icontains=search_query) |
            Q(referensi__icontains=search_query)
        )

    # Dropdown Filter choices
    client_choices = Invoice.objects.exclude(client_name='').values_list('client_name', flat=True).distinct().order_by('client_name')
    sales_choices = Invoice.objects.exclude(sales_ae__isnull=True).exclude(sales_ae='').values_list('sales_ae', flat=True).distinct().order_by('sales_ae')

    # Executive Summaries (Calculated from filtered dataset)
    total_invoiced = inv_qs.aggregate(t=Sum('total_amount'))['t'] or 0
    total_paid_revenue = inv_qs.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_receivables = sum(max(0, float(inv.sisa_tagihan)) for inv in inv_qs)

    # Operational Cost (HPP)
    target_year = int(year_filter) if year_filter and year_filter.isdigit() else current_year
    kpi_qs = KpiFinance.objects.filter(tanggal_pickup__year=target_year)
    if parsed_start:
        kpi_qs = kpi_qs.filter(tanggal_pickup__gte=parsed_start)
    if parsed_end:
        kpi_qs = kpi_qs.filter(tanggal_pickup__lte=parsed_end)

    total_cost = kpi_qs.aggregate(t=Sum('total_biaya'))['t'] or 0
    if not total_cost:
        vc_qs = TransactionVendorCost.objects.all()
        if parsed_start:
            vc_qs = vc_qs.filter(transaction__tanggal_pickup__gte=parsed_start)
        if parsed_end:
            vc_qs = vc_qs.filter(transaction__tanggal_pickup__lte=parsed_end)
        elif year_filter and year_filter.isdigit():
            vc_qs = vc_qs.filter(transaction__tanggal_pickup__year=target_year)
        total_cost = vc_qs.aggregate(t=Sum('cost'))['t'] or 0

    total_profit = float(total_paid_revenue) - float(total_cost)

    # Monthly P&L Chart Calculation (12 Months)
    chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    monthly_rev = [0] * 12
    monthly_costs = [0] * 12
    monthly_profits = [0] * 12

    year_invoices = Invoice.objects.filter(date_issued__year=target_year)
    for inv in year_invoices:
        if inv.date_issued:
            m_idx = inv.date_issued.month - 1
            if 0 <= m_idx < 12:
                monthly_rev[m_idx] += float(inv.amount_paid or 0)

    kpi_monthly = list(KpiFinance.objects.filter(tanggal_pickup__year=target_year)
        .annotate(m=django.db.models.functions.ExtractMonth('tanggal_pickup'))
        .values('m')
        .annotate(c=Sum('total_biaya')).order_by('m'))

    for it in kpi_monthly:
        if it['m']:
            m_idx = int(it['m']) - 1
            if 0 <= m_idx < 12:
                monthly_costs[m_idx] = float(it['c'] or 0)

    for i in range(12):
        monthly_profits[i] = monthly_rev[i] - monthly_costs[i]

    # Aging Piutang (AR) Buckets
    today = date.today()
    outstanding_invoices = Invoice.objects.filter(
        status__in=['SENT', 'PARTIAL', 'DRAFT']
    ).exclude(status='PAID').order_by('due_date')

    buckets = {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0}
    for inv in outstanding_invoices:
        sisa = float(inv.sisa_tagihan)
        if sisa <= 0:
            continue
        days = (today - inv.due_date).days if inv.due_date else 0
        if days <= 30:
            buckets['0-30'] += sisa
        elif days <= 60:
            buckets['31-60'] += sisa
        elif days <= 90:
            buckets['61-90'] += sisa
        else:
            buckets['90+'] += sisa

    # Pagination
    paginator = Paginator(inv_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    status_choices = [
        ('PAID', 'Lunas (Paid)'),
        ('SENT', 'Terkirim (Sent)'),
        ('PARTIAL', 'Sebagian (Partial)'),
        ('DRAFT', 'Draft'),
        ('VOID', 'Dibatalkan (Void)')
    ]

    context = {
        'page_obj': page_obj,
        'invoices': page_obj.object_list,
        'filtered_count': inv_qs.count(),
        'start_date': start_date_str,
        'end_date': end_date_str,
        'year': str(target_year),
        'status_filter': status_filter,
        'client_filter': client_filter,
        'sales_filter': sales_filter,
        'search_query': search_query,
        'client_choices': client_choices,
        'sales_choices': sales_choices,
        'status_choices': status_choices,
        'total_invoiced': total_invoiced,
        'total_revenue': total_paid_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'total_receivables': total_receivables,
        'chart_labels': json.dumps(chart_labels),
        'revenues': json.dumps(monthly_rev),
        'costs': json.dumps(monthly_costs),
        'profits': json.dumps(monthly_profits),
        'aging_data': {
            'bucket_0_30': buckets['0-30'],
            'bucket_31_60': buckets['31-60'],
            'bucket_61_90': buckets['61-90'],
            'bucket_90_plus': buckets['90+'],
            'total': sum(buckets.values())
        }
    }
    return render(request, 'finance/reports/financial_report.html', context)


@login_required
def financial_report_export_excel(request):
    """
    Export laporan keuangan & transaksi invoice ke format Excel (.xlsx)
    mengikuti format standar export Excel di modul Operational & CRM.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from django.db.models import Q
    from datetime import datetime, date
    from .models import Invoice

    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()
    year_filter = request.GET.get('year', '').strip()
    status_filter = request.GET.get('status', '').strip()
    client_filter = request.GET.get('client', '').strip()
    sales_filter = request.GET.get('sales_ae', '').strip()
    search_query = request.GET.get('q', '').strip()

    def parse_dt(d_str):
        if not d_str:
            return None
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(d_str, fmt).date()
            except ValueError:
                continue
        return None

    parsed_start = parse_dt(start_date_str)
    parsed_end = parse_dt(end_date_str)

    inv_qs = Invoice.objects.all().order_by('-date_issued', '-created_at')
    if parsed_start:
        inv_qs = inv_qs.filter(date_issued__gte=parsed_start)
    if parsed_end:
        inv_qs = inv_qs.filter(date_issued__lte=parsed_end)
    if year_filter and year_filter.isdigit():
        inv_qs = inv_qs.filter(date_issued__year=int(year_filter))
    if status_filter:
        inv_qs = inv_qs.filter(status=status_filter)
    if client_filter:
        inv_qs = inv_qs.filter(client_name__icontains=client_filter)
    if sales_filter:
        inv_qs = inv_qs.filter(sales_ae__icontains=sales_filter)
    if search_query:
        inv_qs = inv_qs.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client_name__icontains=search_query) |
            Q(sales_ae__icontains=search_query)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Laporan Keuangan & Invoice"

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    border_thin = Border(
        left=Side(style='thin', color='D0D5DD'),
        right=Side(style='thin', color='D0D5DD'),
        top=Side(style='thin', color='D0D5DD'),
        bottom=Side(style='thin', color='D0D5DD'),
    )

    # Title
    ws.merge_cells('A1:K1')
    ws['A1'] = "LAPORAN KEUANGAN & INVOICE PENAGIHAN - ERP PAKETIN"
    ws['A1'].font = Font(name="Calibri", size=14, bold=True, color="1E293B")
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')

    ws['A2'] = f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total Data: {inv_qs.count()} Transaksi"
    ws['A2'].font = Font(name="Calibri", size=9, italic=True, color="64748B")

    headers = [
        "No", "No. Invoice", "Kustomer / Perusahaan", "PIC Invoice", "Sales (AE)",
        "Tgl. Terbit", "Jatuh Tempo", "Total Tagihan (Rp)", "Terbayar (Rp)",
        "Sisa Piutang (Rp)", "Status"
    ]

    row_num = 4
    for col_num, h_text in enumerate(headers, 1):
        cell = ws.cell(row=row_num, column=col_num, value=h_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border_thin

    tot_tagihan = 0
    tot_terbayar = 0
    tot_sisa = 0

    for idx, inv in enumerate(inv_qs, 1):
        row_num += 1
        tagihan = float(inv.total_amount or 0)
        terbayar = float(inv.amount_paid or 0)
        sisa = float(inv.sisa_tagihan or 0)
        tot_tagihan += tagihan
        tot_terbayar += terbayar
        tot_sisa += sisa

        status_disp = dict(Invoice.STATUS_CHOICES).get(inv.status, inv.status)

        row_values = [
            idx,
            inv.invoice_number or f"INV-{inv.id}",
            inv.client_name or "-",
            inv.pic_invoice or "-",
            inv.sales_ae or "-",
            inv.date_issued.strftime('%d/%m/%Y') if inv.date_issued else "-",
            inv.due_date.strftime('%d/%m/%Y') if inv.due_date else "-",
            tagihan,
            terbayar,
            sisa,
            status_disp
        ]

        for col_num, val in enumerate(row_values, 1):
            cell = ws.cell(row=row_num, column=col_num, value=val)
            cell.font = data_font
            cell.border = border_thin
            if col_num == 1:
                cell.alignment = Alignment(horizontal='center')
            elif col_num in [8, 9, 10]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal='right')
            elif col_num in [6, 7, 11]:
                cell.alignment = Alignment(horizontal='center')

    # Total Footer Row
    row_num += 1
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
    tot_label = ws.cell(row=row_num, column=1, value="TOTAL REKAPITULASI")
    tot_label.font = bold_font
    tot_label.alignment = Alignment(horizontal='right', vertical='center')

    for c in range(1, 8):
        ws.cell(row=row_num, column=c).border = border_thin
        ws.cell(row=row_num, column=c).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    for col_num, val in [(8, tot_tagihan), (9, tot_terbayar), (10, tot_sisa)]:
        cell = ws.cell(row=row_num, column=col_num, value=val)
        cell.font = bold_font
        cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        cell.border = border_thin
        cell.number_format = '#,##0'
        cell.alignment = Alignment(horizontal='right')

    ws.cell(row=row_num, column=11).border = border_thin
    ws.cell(row=row_num, column=11).fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    # Column Widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    today_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="Laporan_Keuangan_ERP_Paketin_{today_str}.xlsx"'
    wb.save(response)
    return response

@login_required
def vendor_list(request):
    """Vendor management view for finance module"""
    from .models import Vendor
    from django.contrib.auth.decorators import user_passes_test
    
    vendors = Vendor.objects.all().order_by('name')
    
    # Filter by service type
    service_filter = request.GET.get('service_type')
    if service_filter:
        vendors = vendors.filter(service_type__icontains=service_filter)
    
    # Filter by active status
    active_filter = request.GET.get('is_active')
    if active_filter == 'true':
        vendors = vendors.filter(is_active=True)
    elif active_filter == 'false':
        vendors = vendors.filter(is_active=False)
    
    context = {
        'vendors': vendors,
        'service_filter': service_filter,
        'active_filter': active_filter,
    }
    return render(request, 'finance/vendors/vendor_list.html', context)



# ==================== API ViewSets (unchanged) ====================

class KpiFileViewSet(viewsets.ModelViewSet):
    queryset = KpiFile.objects.all().order_by('-created_at')
    serializer_class = KpiFileSerializer
    permission_classes = [IsAuthenticated]

class KpiSheetViewSet(viewsets.ModelViewSet):
    queryset = KpiSheet.objects.all().order_by('sort_order')
    serializer_class = KpiSheetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        file_id = self.request.query_params.get('file_id')
        if file_id:
            queryset = queryset.filter(kpi_file_id=file_id)
        return queryset

class KpiFinanceViewSet(viewsets.ModelViewSet):
    queryset = KpiFinance.objects.all()
    serializer_class = KpiFinanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        sheet_id = self.request.query_params.get('sheet_id')
        if sheet_id:
            queryset = queryset.filter(sheet_id=sheet_id)
            
        id_gt = self.request.query_params.get('id__gt')
        if id_gt:
            queryset = queryset.filter(id__gt=id_gt)
            
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
            
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            print("UPDATE VALIDATION FAILED:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        print("BULK_CREATE RECEIVED DATA:", request.data[:3] if isinstance(request.data, list) else request.data)
        if not isinstance(request.data, list):
            return Response({"detail": "Data must be a list of objects"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data, many=True)
        if not serializer.is_valid():
            import json
            with open("validation_error.log", "w") as f:
                f.write(json.dumps(serializer.errors, default=str))
        serializer.is_valid(raise_exception=True)
        
        # True bulk insert using bulk_create for maximum database performance
        models_to_create = [KpiFinance(**item) for item in serializer.validated_data]
        created_objects = KpiFinance.objects.bulk_create(models_to_create)
        
        # Re-serialize to return IDs and populated fields
        response_serializer = self.get_serializer(created_objects, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

from .models import CellStyle, AuditLog
from .serializers import CellStyleSerializer, AuditLogSerializer

class CellStyleViewSet(viewsets.ModelViewSet):
    queryset = CellStyle.objects.all()
    serializer_class = CellStyleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        sheet_id = self.request.query_params.get("sheet_id")
        if sheet_id:
            queryset = queryset.filter(sheet_id=sheet_id)
        return queryset

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all().order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

from rest_framework.permissions import IsAuthenticated, AllowAny

# ==================== CRM WEBHOOK ====================

from rest_framework.views import APIView
from django.conf import settings as django_settings

MONTH_NAMES = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

class CrmWebhookView(APIView):
    """
    Endpoint webhook untuk menerima data lead "Win" dari CRM.
    Auth via header X-API-Key.

    POST /finance/api/crm-webhook/
    """
    permission_classes = [AllowAny]  # Auth handled manually via API Key
    authentication_classes = []      # Skip session/basic auth

    def post(self, request):
        # 1. Validate API Key
        api_key = request.headers.get('X-API-Key', '')
        if not api_key or api_key != django_settings.CRM_API_KEY:
            return Response(
                {'detail': 'Invalid or missing API Key.'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        if not data:
            return Response(
                {'detail': 'Request body is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Parse tanggal_pickup to determine year & month
        tanggal_raw = data.get('tanggal_pickup')
        if not tanggal_raw:
            return Response(
                {'detail': 'Field "tanggal_pickup" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tanggal_date = datetime.strptime(str(tanggal_raw), '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Field "tanggal_pickup" must be in YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        year = tanggal_date.year
        month_index = tanggal_date.month  # 1-12
        month_name = MONTH_NAMES[month_index - 1]

        # 3. Resolve KpiFile for this year (find or create)
        kpi_file = KpiFile.objects.filter(name__icontains=str(year)).first()
        if not kpi_file:
            kpi_file = KpiFile.objects.create(
                name=f'KPI Finance {year}',
                created_by='CRM System',
                updated_by='CRM System'
            )

        # 4. Resolve KpiSheet for this month (find or create)
        kpi_sheet = KpiSheet.objects.filter(
            kpi_file=kpi_file,
            name__iexact=month_name
        ).first()
        if not kpi_sheet:
            # Determine sort_order based on month index
            kpi_sheet = KpiSheet.objects.create(
                name=month_name,
                kpi_file=kpi_file,
                sheet_type='data',
                sort_order=month_index,
                created_by='CRM System',
                updated_by='CRM System'
            )

        # 5. Build KpiFinance row from CRM payload
        def safe_decimal(val, default=0):
            """Safely parse a decimal value from CRM payload."""
            if val is None or val == '' or val == '-':
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        crm_lead_id = data.get('crm_lead_id', '')
        finance_row = KpiFinance.objects.filter(crm_lead_id=crm_lead_id).first() if crm_lead_id else None

        if finance_row:
            # Update existing row
            finance_row.tanggal_pickup = tanggal_date
            finance_row.nama = data.get('nama', finance_row.nama)
            finance_row.ip_perusahaan = data.get('ip_perusahaan', finance_row.ip_perusahaan)
            finance_row.pengirim = data.get('pengirim', finance_row.pengirim)
            finance_row.sales = data.get('sales', finance_row.sales)
            if data.get('penerima'):
                finance_row.penerima = data.get('penerima')
            finance_row.asal_pickup = data.get('asal_pickup', finance_row.asal_pickup)
            finance_row.tujuan = data.get('tujuan', finance_row.tujuan)
            finance_row.service = data.get('service', finance_row.service)
            finance_row.via = data.get('via', finance_row.via)
            finance_row.jenis_barang = data.get('jenis_barang', finance_row.jenis_barang)
            finance_row.aktual = safe_decimal(data.get('aktual'), finance_row.aktual)
            finance_row.vol = safe_decimal(data.get('vol'), finance_row.vol)
            finance_row.penjualan = safe_decimal(data.get('penjualan'), finance_row.penjualan)
            
            # New fields for update
            if 'jenis_barang' in data: finance_row.jenis_barang = data['jenis_barang']
            if 'awb' in data: finance_row.awb = data['awb']
            if 'awb_sistem' in data: finance_row.awb_sistem = data['awb_sistem']
            if 'via' in data: finance_row.via = data['via']
            
            finance_row.unit = safe_decimal(data.get('unit'), finance_row.unit)
            finance_row.kubik = safe_decimal(data.get('kubik'), finance_row.kubik)
            finance_row.p = safe_decimal(data.get('p'), finance_row.p)
            finance_row.l = safe_decimal(data.get('l'), finance_row.l)
            finance_row.t = safe_decimal(data.get('t'), finance_row.t)
            finance_row.koil = safe_decimal(data.get('koil'), finance_row.koil)
            finance_row.harga = safe_decimal(data.get('harga'), finance_row.harga)
            finance_row.updated_by = 'CRM System'
            finance_row.save()
        else:
            finance_row = KpiFinance.objects.create(
                sheet=kpi_sheet,
                tanggal_pickup=tanggal_date,
                nama=data.get('nama', ''),
                ip_perusahaan=data.get('ip_perusahaan', ''),
                pengirim=data.get('pengirim', ''),
                sales=data.get('sales', ''),
                penerima=data.get('penerima', ''),
                asal_pickup=data.get('asal_pickup', ''),
                tujuan=data.get('tujuan', ''),
                service=data.get('service', ''),
                via=data.get('via', ''),
                jenis_barang=data.get('jenis_barang', ''),
                awb=data.get('awb', ''),
                awb_sistem=data.get('awb_sistem', ''),
                aktual=safe_decimal(data.get('aktual')),
                vol=safe_decimal(data.get('vol')),
                unit=safe_decimal(data.get('unit')),
                kubik=safe_decimal(data.get('kubik')),
                p=safe_decimal(data.get('p')),
                l=safe_decimal(data.get('l')),
                t=safe_decimal(data.get('t')),
                koil=safe_decimal(data.get('koil')),
                harga=safe_decimal(data.get('harga')),
                surcharge=safe_decimal(data.get('surcharge')),
                packing=safe_decimal(data.get('packing')),
                handling=safe_decimal(data.get('handling')),
                penjualan=safe_decimal(data.get('penjualan')),
                # CRM tracking fields
                source='crm',
                row_status='new',
                crm_lead_id=crm_lead_id,
                created_by='CRM System',
                updated_by='CRM System',
            )

        # 6. Write audit log
        crm_lead_id = data.get('crm_lead_id', 'N/A')
        try:
            AuditLog.objects.create(
                row_id=finance_row.id,
                field_name='crm_import',
                old_value='',
                new_value=f'Lead {crm_lead_id} → {finance_row.nama}',
                user_email='crm-system',
                user_name='CRM System',
                changed_by='CRM System'
            )
        except Exception:
            pass  # Non-critical, don't fail the webhook

        # 7. Return success
        return Response({
            'status': 'success',
            'row_id': finance_row.id,
            'file': {'id': kpi_file.id, 'name': kpi_file.name},
            'sheet': {'id': kpi_sheet.id, 'name': kpi_sheet.name},
            'crm_lead_id': crm_lead_id,
        }, status=status.HTTP_201_CREATED)


# ==================== LDP (LEMBAR DAFTAR PENGIRIMAN) VIEWS ====================
# ==================== LDP (LEMBAR DAFTAR PENGIRIMAN) VIEWS ====================
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import LDP, LDPItem, Invoice

def generate_ldp_number(branch=None, user=None):
    from apps.organizations.models import Branch
    branch_obj = branch
    if not branch_obj and user:
        if hasattr(user, 'employee') and getattr(user.employee, 'branch', None):
            branch_obj = user.employee.branch
        elif hasattr(user, 'branch') and getattr(user, 'branch', None):
            branch_obj = user.branch
    if not branch_obj:
        branch_obj = Branch.objects.filter(code='BKS').first() or Branch.objects.filter(code='JKT').first() or Branch.objects.filter(name__icontains='bekasi').first() or Branch.objects.filter(name__icontains='jakarta').first() or Branch.objects.first()
    
    branch_code = branch_obj.code.upper().strip() if branch_obj and branch_obj.code else 'BKS'
    # Format: LDP{BRANCH}{YYMMDD}{SEQ} -> misal LDPBKS2609210001
    today_str = timezone.now().strftime('%y%m%d')
    prefix = f"LDP{branch_code}{today_str}"
    
    last_ldp = LDP.objects.filter(ldp_number__startswith=prefix).order_by('-ldp_number').first()
    if last_ldp:
        try:
            seq_part = last_ldp.ldp_number[len(prefix):]
            last_seq = int(seq_part)
        except (ValueError, IndexError):
            last_seq = 0
        new_seq = last_seq + 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}", branch_obj


@login_required
def ldp_list(request):
    """
    List of LDP (Lembar Daftar Pengiriman) - Single tab layout matching Photo 1 & Photo 3.
    """
    from apps.master.models import Customer
    from apps.organizations.models import Branch
    from apps.master.display import clean_branch_label

    search = request.GET.get('search') or request.GET.get('q', '').strip()
    customer_id = request.GET.get('customer', '').strip()
    date_filter = request.GET.get('date', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = LDP.objects.all().select_related('client', 'branch', 'created_by', 'invoice').prefetch_related('items')

    if search:
        qs = qs.filter(
            Q(ldp_number__icontains=search) | 
            Q(client_name__icontains=search) | 
            Q(notes__icontains=search) |
            Q(invoice__invoice_number__icontains=search)
        )

    if customer_id:
        qs = qs.filter(client_id=customer_id)
    if date_filter:
        qs = qs.filter(ldp_date=date_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)

    customers = Customer.objects.filter(is_active=True).order_by('name')

    context = {
        'ldp_list': qs.order_by('-created_at'),
        'search': search,
        'customer_id': customer_id,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'customers': customers,
    }
    return render(request, 'finance/ldp/ldp_list.html', context)


@login_required
def ldp_create(request):
    """
    Form Entry LDP (matching Photo 2).
    """
    from apps.operations.models import Shipment
    from apps.master.models import Customer
    from apps.organizations.models import Branch
    from django.contrib import messages

    customer_id = request.GET.get('customer', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    status_filter = request.GET.get('status', 'ALL')

    # Query shipments based on filters
    shipments = []
    if customer_id or date_from or date_to:
        active_ldp_shipment_ids = LDPItem.objects.filter(
            ldp__status__in=['DRAFT', 'CONFIRMED', 'INVOICED']
        ).values_list('shipment_id', flat=True)

        shipments_qs = Shipment.objects.exclude(id__in=active_ldp_shipment_ids).exclude(status='VOID')
        if customer_id:
            shipments_qs = shipments_qs.filter(client_id=customer_id)
        if date_from:
            shipments_qs = shipments_qs.filter(created_at__date__gte=date_from)
        if date_to:
            shipments_qs = shipments_qs.filter(created_at__date__lte=date_to)
        if status_filter != 'ALL':
            shipments_qs = shipments_qs.filter(status=status_filter)

        shipments = list(shipments_qs.order_by('-created_at')[:300])

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_shipments')
        if not selected_ids:
            messages.error(request, "Pilih minimal satu resi / shipment untuk membuat LDP.")
            return redirect(request.get_full_path())

        cust_obj = Customer.objects.filter(pk=customer_id).first() if customer_id else None
        client_name = cust_obj.name if cust_obj else (request.POST.get('custom_client_name') or 'Klien Umum')
        branch_obj = cust_obj.branch if (cust_obj and cust_obj.branch) else None

        ldp_number, branch_assigned = generate_ldp_number(branch=branch_obj, user=request.user)

        p_awal = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        p_akhir = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None

        selected_shipments = Shipment.objects.filter(id__in=selected_ids)
        
        # Ensure no selected shipments are already in another active LDP
        existing_conflict = LDPItem.objects.filter(
            shipment_id__in=selected_ids,
            ldp__status__in=['DRAFT', 'CONFIRMED', 'INVOICED']
        ).select_related('ldp')
        if existing_conflict.exists():
            conflict_names = ", ".join([f"{item.awb_number} ({item.ldp.ldp_number})" for item in existing_conflict[:5]])
            messages.error(request, f"AWB berikut sudah terdaftar di LDP lain: {conflict_names}. Mohon hapus dari antrean.")
            return redirect(request.get_full_path())

        if not p_awal and selected_shipments.exists():
            first_s = selected_shipments.order_by('created_at').first()
            if first_s and first_s.created_at:
                p_awal = first_s.created_at.date()
        if not p_akhir and selected_shipments.exists():
            last_s = selected_shipments.order_by('-created_at').first()
            if last_s and last_s.created_at:
                p_akhir = last_s.created_at.date()

        ldp = LDP.objects.create(
            ldp_number=ldp_number,
            client_name=client_name,
            client=cust_obj,
            branch=branch_assigned,
            ldp_date=timezone.now().date(),
            periode_awal=p_awal,
            periode_akhir=p_akhir,
            status='DRAFT',
            created_by=request.user,
        )
        items_to_create = []
        for s in selected_shipments:
            sid = str(s.id)
            weight_val = Decimal(str(s.weight or 0))
            vol_val = Decimal(str(s.volume_weight or 0))
            chargeable_val = Decimal(str(s.chargeable_weight or max(weight_val, vol_val) or 1))
            
            default_freight = Decimal(str(s.price or 0))
            default_pkg = (default_freight / chargeable_val).quantize(Decimal('0.01')) if chargeable_val > 0 else Decimal('0')
            default_ins = Decimal(str(s.insurance_amount or 0))
            default_packing = Decimal(str(s.packing_cost or 0))
            default_other = Decimal(str(s.other_cost or 0))

            def parse_dec(field_name, default_val):
                raw = request.POST.get(f"{field_name}_{sid}", "").strip().replace('.', '').replace(',', '.')
                if not raw:
                    raw = request.POST.get(f"{field_name}_{sid}", "").strip()
                try:
                    return Decimal(str(raw)) if raw != '' else default_val
                except:
                    return default_val

            price_per_kg_val = parse_dec('price_per_kg', default_pkg)
            freight = parse_dec('freight_charge', (price_per_kg_val * chargeable_val).quantize(Decimal('0.01')))
            ins = parse_dec('insurance_fee', default_ins)
            packing = parse_dec('packing_fee', default_packing)
            other = parse_dec('handling_fee', default_other)
            discount_val = parse_dec('discount', Decimal('0'))

            surcharges_total = ins + packing + other
            subtotal_val = max(Decimal('0'), freight + surcharges_total - discount_val)

            items_to_create.append(LDPItem(
                ldp=ldp,
                shipment=s,
                awb_number=s.resi_number,
                shipment_date=s.created_at.date() if s.created_at else None,
                sender_name=s.sender_name or '',
                receiver_name=s.receiver_name or '',
                origin=s.origin or '',
                destination=s.destination or '',
                service_type=s.service_type or 'REG',
                koli=int(s.colly or 1),
                actual_weight=weight_val,
                volume_weight=vol_val,
                chargeable_weight=chargeable_val,
                price_per_kg=price_per_kg_val,
                freight_charge=freight,
                insurance_fee=ins,
                packing_fee=packing,
                handling_fee=other,
                surcharges=surcharges_total,
                discount=discount_val,
                subtotal=subtotal_val,
            ))

        LDPItem.objects.bulk_create(items_to_create)
        ldp.recalculate_totals()

        messages.success(request, f"Dokumen {ldp.ldp_number} berhasil diterbitkan dengan {len(items_to_create)} resi.")
        return redirect('finance:ldp_list')

    customers = Customer.objects.filter(is_active=True).order_by('name')

    context = {
        'is_edit': False,
        'ldp': None,
        'shipments': shipments,
        'customer_id': customer_id,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'customers': customers,
    }
    return render(request, 'finance/ldp/ldp_edit.html', context)


@login_required
def ldp_detail(request, ldp_id):
    """
    Detail / Edit view of LDP - Uses the same Form Entry LDP layout (Photo 2).
    """
    from apps.operations.models import Shipment
    from apps.master.models import Customer
    from django.contrib import messages

    ldp = get_object_or_404(LDP.objects.select_related('client', 'branch', 'created_by', 'invoice'), id=ldp_id)
    items = ldp.items.all().order_by('id')

    if request.method == 'POST':
        action = request.POST.get('form_action')
        if action == 'update_ldp':
            selected_ids = request.POST.getlist('selected_shipments')
            if selected_ids:
                # Remove unselected
                LDPItem.objects.filter(ldp=ldp).exclude(shipment_id__in=selected_ids).delete()

                # Process all selected shipments (update existing & create new)
                existing_items_map = {item.shipment_id: item for item in LDPItem.objects.filter(ldp=ldp)}
                selected_shipments = Shipment.objects.filter(id__in=selected_ids)
                
                items_to_create = []
                for s in selected_shipments:
                    sid = str(s.id)
                    weight_val = Decimal(str(s.weight or 0))
                    vol_val = Decimal(str(s.volume_weight or 0))
                    chargeable_val = Decimal(str(s.chargeable_weight or max(weight_val, vol_val) or 1))
                    
                    default_freight = Decimal(str(s.price or 0))
                    default_pkg = (default_freight / chargeable_val).quantize(Decimal('0.01')) if chargeable_val > 0 else Decimal('0')
                    default_ins = Decimal(str(s.insurance_amount or 0))
                    default_packing = Decimal(str(s.packing_cost or 0))
                    default_other = Decimal(str(s.other_cost or 0))

                    def parse_dec(field_name, default_val):
                        raw = request.POST.get(f"{field_name}_{sid}", "").strip().replace('.', '').replace(',', '.')
                        if not raw:
                            raw = request.POST.get(f"{field_name}_{sid}", "").strip()
                        try:
                            return Decimal(str(raw)) if raw != '' else default_val
                        except:
                            return default_val

                    price_per_kg_val = parse_dec('price_per_kg', default_pkg)
                    freight = parse_dec('freight_charge', (price_per_kg_val * chargeable_val).quantize(Decimal('0.01')))
                    ins = parse_dec('insurance_fee', default_ins)
                    packing = parse_dec('packing_fee', default_packing)
                    other = parse_dec('handling_fee', default_other)
                    discount_val = parse_dec('discount', Decimal('0'))

                    surcharges_total = ins + packing + other
                    subtotal_val = max(Decimal('0'), freight + surcharges_total - discount_val)

                    if s.id in existing_items_map:
                        item_obj = existing_items_map[s.id]
                        item_obj.price_per_kg = price_per_kg_val
                        item_obj.freight_charge = freight
                        item_obj.insurance_fee = ins
                        item_obj.packing_fee = packing
                        item_obj.handling_fee = other
                        item_obj.surcharges = surcharges_total
                        item_obj.discount = discount_val
                        item_obj.subtotal = subtotal_val
                        item_obj.save()
                    else:
                        items_to_create.append(LDPItem(
                            ldp=ldp,
                            shipment=s,
                            awb_number=s.resi_number,
                            shipment_date=s.created_at.date() if s.created_at else None,
                            sender_name=s.sender_name or '',
                            receiver_name=s.receiver_name or '',
                            origin=s.origin or '',
                            destination=s.destination or '',
                            service_type=s.service_type or 'REG',
                            koli=int(s.colly or 1),
                            actual_weight=weight_val,
                            volume_weight=vol_val,
                            chargeable_weight=chargeable_val,
                            price_per_kg=price_per_kg_val,
                            freight_charge=freight,
                            insurance_fee=ins,
                            packing_fee=packing,
                            handling_fee=other,
                            surcharges=surcharges_total,
                            discount=discount_val,
                            subtotal=subtotal_val,
                        ))

                if items_to_create:
                    LDPItem.objects.bulk_create(items_to_create)

                ldp.recalculate_totals()
                messages.success(request, f"Dokumen {ldp.ldp_number} berhasil diperbarui.")
            else:
                messages.warning(request, "LDP harus memiliki minimal 1 resi.")

            return redirect('finance:ldp_detail', ldp_id=ldp.id)

    customers = Customer.objects.filter(is_active=True).order_by('name')

    context = {
        'is_edit': True,
        'ldp': ldp,
        'items': items,
        'customer_id': str(ldp.client_id) if ldp.client_id else '',
        'date_from': ldp.periode_awal.strftime('%Y-%m-%d') if ldp.periode_awal else '',
        'date_to': ldp.periode_akhir.strftime('%Y-%m-%d') if ldp.periode_akhir else '',
        'status_filter': 'ALL',
        'customers': customers,
    }
    return render(request, 'finance/ldp/ldp_edit.html', context)


@login_required
def api_shipment_lookup(request):
    """
    AJAX endpoint for scanning / searching AWB barcode.
    """
    from apps.operations.models import Shipment
    resi = request.GET.get('resi', '').strip()
    current_ldp_id = request.GET.get('ldp_id', '').strip()

    if not resi:
        return JsonResponse({'status': 'error', 'message': 'Nomor resi kosong.'})

    shipment = Shipment.objects.filter(resi_number__iexact=resi).first()
    if not shipment:
        return JsonResponse({'status': 'error', 'message': f'Resi "{resi}" tidak ditemukan di sistem.'})

    if shipment.status == 'VOID':
        return JsonResponse({'status': 'error', 'message': f'Resi "{resi}" berstatus VOID dan tidak dapat dimasukkan ke LDP.'})

    # Check if already in another active LDP
    ldp_items_qs = LDPItem.objects.filter(
        awb_number__iexact=resi,
        ldp__status__in=['DRAFT', 'CONFIRMED', 'INVOICED']
    ).select_related('ldp')

    if current_ldp_id and current_ldp_id.isdigit():
        ldp_items_qs = ldp_items_qs.exclude(ldp_id=int(current_ldp_id))

    existing_ldp = ldp_items_qs.first()
    if existing_ldp:
        return JsonResponse({
            'status': 'error',
            'is_in_ldp': True,
            'message': f'AWB {resi} sudah terbuat pada dokumen LDP {existing_ldp.ldp.ldp_number} (Status: {existing_ldp.ldp.get_status_display()}) dan tidak bisa discan lagi.'
        })

    weight = float(shipment.weight or 0)
    vol = float(shipment.volume_weight or 0)
    chargeable = float(shipment.chargeable_weight or max(weight, vol) or 1)
    freight = float(shipment.price or 0)
    ins = float(shipment.insurance_amount or 0)
    packing = float(shipment.packing_cost or 0)
    other = float(shipment.other_cost or 0)
    surcharges = ins + packing + other
    subtotal = freight + surcharges

    price_per_kg = (freight / chargeable) if chargeable > 0 else 0

    data = {
        'status': 'success',
        'id': shipment.id,
        'resi_number': shipment.resi_number,
        'created_at': shipment.created_at.strftime('%d/%m/%Y') if shipment.created_at else '-',
        'sender_name': shipment.sender_name or '-',
        'receiver_name': shipment.receiver_name or '-',
        'origin': f"{shipment.origin} ({shipment.get_tlc_origin})" if shipment.get_tlc_origin and shipment.get_tlc_origin != '-' else (shipment.origin or '-'),
        'destination': f"{shipment.destination} ({shipment.get_tlc_dest})" if shipment.get_tlc_dest and shipment.get_tlc_dest != '-' else (shipment.destination or '-'),
        'service_type': shipment.service_type or 'REG',
        'colly': shipment.colly or 1,
        'weight': weight,
        'chargeable_weight': chargeable,
        'freight': freight,
        'price_per_kg': price_per_kg,
        'discount': 0,
        'packing': packing,
        'insurance': ins,
        'other_cost': other,
        'surcharges': surcharges,
        'subtotal': subtotal,
        'operational_status': shipment.get_status_display(),
        'user_input': (shipment.created_by.get_full_name() or shipment.created_by.username) if shipment.created_by else '-',
        'is_in_ldp': False,
        'ldp_number': None,
    }
    return JsonResponse(data)


@login_required
def ldp_print(request, ldp_id):
    """Printable official LDP sheet."""
    ldp = get_object_or_404(LDP.objects.select_related('client', 'branch', 'created_by'), id=ldp_id)
    items = ldp.items.all().order_by('id')
    return render(request, 'finance/ldp/ldp_print.html', {
        'ldp': ldp,
        'items': items,
    })


@login_required
def ldp_confirm(request, ldp_id):
    """Mark LDP as CONFIRMED (Siap Tagih)."""
    from django.contrib import messages
    if request.method == 'POST':
        ldp = get_object_or_404(LDP, id=ldp_id)
        if ldp.status == 'DRAFT':
            ldp.status = 'CONFIRMED'
            ldp.save(update_fields=['status'])
            messages.success(request, f"LDP {ldp.ldp_number} dikonfirmasi dan status berubah menjadi SIAP TAGIH.")
        return redirect('finance:ldp_detail', ldp_id=ldp.id)
    return redirect('finance:ldp_list')


@login_required
def ldp_to_invoice(request, ldp_id):
    """Convert a single LDP directly into a Draft Invoice."""
    from django.contrib import messages
    if request.method == 'POST':
        ldp = get_object_or_404(LDP.objects.select_related('client'), id=ldp_id)
        if ldp.status == 'INVOICED' and ldp.invoice:
            messages.warning(request, f"LDP ini sudah terhubung ke Invoice {ldp.invoice.invoice_number}.")
            return redirect('finance:invoice_detail', invoice_id=ldp.invoice.id)

        branch_code = ldp.branch.code.upper() if ldp.branch and ldp.branch.code else 'BKS'
        today_str = timezone.now().strftime('%y%m%d')
        prefix = f"{branch_code}INV{today_str}"
        last_inv = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last_inv:
            try:
                seq = int(last_inv.invoice_number[len(prefix):]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        inv_number = f"{prefix}{seq:04d}"

        cust = ldp.client
        invoice = Invoice.objects.create(
            invoice_number=inv_number,
            client_name=ldp.client_name,
            status='DRAFT',
            is_open=True,
            company_code='PT AMANAH',
            kode_pelanggan=cust.customer_code if cust else '',
            pic_invoice=(getattr(cust, 'pic_invoice', '') or getattr(cust, 'pic_account', '')) if cust else '',
            alamat_pelanggan=(getattr(cust, 'office_address', '') or getattr(cust, 'address', '')) if cust else '',
            npwp=getattr(cust, 'npwp', '') if cust else '',
            sales_ae=cust.sales.get_full_name() or cust.sales.username if (cust and cust.sales) else '',
            periode_awal=ldp.periode_awal,
            periode_akhir=ldp.periode_akhir,
            biaya_kirim=ldp.total_freight,
            biaya_tambahan=ldp.total_surcharges,
            notes=f"Dibuat dari LDP: {ldp.ldp_number}",
        )

        shipment_ids = ldp.items.exclude(shipment__isnull=True).values_list('shipment_id', flat=True)
        if shipment_ids:
            invoice.shipments.set(shipment_ids)
        
        invoice.update_totals()

        ldp.status = 'INVOICED'
        ldp.invoice = invoice
        ldp.save(update_fields=['status', 'invoice'])

        messages.success(request, f"Berhasil membuat Draft Invoice {invoice.invoice_number} dari LDP {ldp.ldp_number}.")
        return redirect('finance:invoice_detail', invoice_id=invoice.id)
    return redirect('finance:ldp_detail', ldp_id=ldp_id)


@login_required
def ldp_delete(request, ldp_id):
    """Delete LDP record and release items."""
    from django.contrib import messages
    if request.method == 'POST':
        ldp = get_object_or_404(LDP, id=ldp_id)
        if ldp.status == 'INVOICED':
            messages.error(request, "LDP yang sudah memiliki Invoice tidak dapat dihapus. Batalkan invoice terlebih dahulu.")
            return redirect('finance:ldp_detail', ldp_id=ldp.id)
        num = ldp.ldp_number
        ldp.delete()
        messages.success(request, f"LDP {num} berhasil dihapus.")
        return redirect('finance:ldp_list')
    return redirect('finance:ldp_list')


# ==================== INVOICE CREATION FROM LDPs (Foto 4) ====================

def generate_invoice_number(branch=None, user=None):
    from apps.organizations.models import Branch
    branch_obj = branch
    if not branch_obj and user:
        if hasattr(user, 'employee') and getattr(user.employee, 'branch', None):
            branch_obj = user.employee.branch
        elif hasattr(user, 'branch') and getattr(user, 'branch', None):
            branch_obj = user.branch
    if not branch_obj:
        branch_obj = Branch.objects.first()
    
    branch_code = branch_obj.code.upper() if branch_obj and branch_obj.code else 'BKS'
    today_str = timezone.now().strftime('%y%m%d')
    prefix = f"{branch_code}INV{today_str}"
    
    last_inv = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
    if last_inv:
        try:
            seq = int(last_inv.invoice_number[len(prefix):]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}", branch_obj


@login_required
def invoice_create(request):
    """
    Form Buat Invoice dari pilihan LDP Customer atau Scan Barcode Batch LDP.
    """
    from apps.master.models import Customer
    from django.contrib import messages

    customer_id = request.GET.get('customer', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    status_filter = request.GET.get('status', 'ALL').strip()
    customers = Customer.objects.filter(is_active=True).order_by('name')

    available_ldps = []
    selected_customer = None
    ldps_qs = LDP.objects.filter(invoice__isnull=True)

    if customer_id:
        selected_customer = Customer.objects.filter(pk=customer_id).first()
        if selected_customer:
            ldps_qs = ldps_qs.filter(
                Q(client=selected_customer) | Q(client_name__iexact=selected_customer.name)
            )

    if date_from:
        try:
            from datetime import datetime
            d_from = datetime.strptime(date_from, '%d/%m/%Y').date()
            ldps_qs = ldps_qs.filter(ldp_date__gte=d_from)
        except Exception:
            pass

    if date_to:
        try:
            from datetime import datetime
            d_to = datetime.strptime(date_to, '%d/%m/%Y').date()
            ldps_qs = ldps_qs.filter(ldp_date__lte=d_to)
        except Exception:
            pass

    if status_filter and status_filter != 'ALL':
        ldps_qs = ldps_qs.filter(status=status_filter)
    else:
        ldps_qs = ldps_qs.filter(status__in=['DRAFT', 'CONFIRMED'])

    if customer_id or date_from or date_to:
        available_ldps = ldps_qs.prefetch_related('items').order_by('-created_at')

    if request.method == 'POST':
        cust_id = request.POST.get('customer')
        selected_ldp_ids = request.POST.getlist('selected_ldps')

        if not selected_ldp_ids:
            messages.error(request, "Pilih atau scan minimal 1 batch LDP untuk membuat Invoice.")
            return redirect(f"{request.path}?customer={cust_id}" if cust_id else request.path)

        ldps = LDP.objects.filter(id__in=selected_ldp_ids)
        if not ldps.exists():
            messages.error(request, "Batch LDP yang dipilih tidak ditemukan.")
            return redirect(request.path)

        # Resolve customer if not explicitly selected from dropdown
        cust_obj = Customer.objects.filter(pk=cust_id).first() if cust_id else None
        if not cust_obj:
            first_with_client = ldps.filter(client__isnull=False).first()
            if first_with_client and first_with_client.client:
                cust_obj = first_with_client.client

        client_name = cust_obj.name if cust_obj else (request.POST.get('client_name') or ldps.first().client_name or 'Klien Umum')
        branch_obj = cust_obj.branch if (cust_obj and cust_obj.branch) else (ldps.first().branch if ldps.first().branch else None)

        inv_number, branch_assigned = generate_invoice_number(branch=branch_obj, user=request.user)

        total_freight = sum([ldp.total_freight for ldp in ldps])
        total_surcharges = sum([ldp.total_surcharges for ldp in ldps])
        
        # Calculate item-level aggregates
        total_packing = sum([sum([it.packing_fee for it in ldp.items.all()]) for ldp in ldps])
        total_insurance = sum([sum([it.insurance_fee for it in ldp.items.all()]) for ldp in ldps])
        total_discount = sum([sum([it.discount for it in ldp.items.all()]) for ldp in ldps])
        total_handling = sum([sum([it.handling_fee for it in ldp.items.all()]) for ldp in ldps])

        # Calculate start and end period from LDPs
        p_awals = [ldp.periode_awal for ldp in ldps if ldp.periode_awal]
        p_akhirs = [ldp.periode_akhir for ldp in ldps if ldp.periode_akhir]
        min_p = min(p_awals) if p_awals else None
        max_p = max(p_akhirs) if p_akhirs else None

        sales_name = ""
        if cust_obj and cust_obj.sales:
            sales_name = cust_obj.sales.get_full_name() or cust_obj.sales.username

        invoice = Invoice.objects.create(
            invoice_number=inv_number,
            client_name=client_name,
            status='DRAFT',
            is_open=True,
            company_code='PT AMANAH',
            kode_pelanggan=getattr(cust_obj, 'customer_code', '') if cust_obj else '',
            pic_invoice=(getattr(cust_obj, 'pic_invoice', '') or getattr(cust_obj, 'pic_account', '')) if cust_obj else '',
            alamat_pelanggan=(getattr(cust_obj, 'office_address', '') or getattr(cust_obj, 'address', '')) if cust_obj else '',
            npwp=getattr(cust_obj, 'npwp', '') if cust_obj else '',
            sales_ae=sales_name,
            periode_awal=min_p,
            periode_akhir=max_p,
            biaya_kirim=total_freight,
            biaya_tambahan=total_surcharges or total_handling,
            biaya_kemasan=total_packing,
            premi_asuransi=total_insurance,
            diskon=total_discount,
            notes=f"Dibuat dari {ldps.count()} batch LDP.",
        )

        all_shipment_ids = []
        for ldp in ldps:
            ldp.status = 'INVOICED'
            ldp.invoice = invoice
            ldp.save(update_fields=['status', 'invoice'])
            ship_ids = ldp.items.exclude(shipment__isnull=True).values_list('shipment_id', flat=True)
            all_shipment_ids.extend(ship_ids)

        if all_shipment_ids:
            invoice.shipments.set(all_shipment_ids)
            from .utils import sync_invoice_shipments_to_worksheet
            sync_invoice_shipments_to_worksheet(invoice)

        invoice.update_totals(recalc_from_shipments=False)

        messages.success(request, f"Draft Invoice {invoice.invoice_number} berhasil dibuat dari {ldps.count()} batch LDP.")
        return redirect('finance:invoice_detail', invoice_id=invoice.id)

    # Preview invoice number for header
    preview_inv_num, _ = generate_invoice_number(user=request.user)

    context = {
        'customers': customers,
        'selected_customer': selected_customer,
        'customer_id': customer_id,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'available_ldps': available_ldps,
        'preview_inv_num': preview_inv_num,
    }
    return render(request, 'finance/invoices/invoice_edit.html', context)


@login_required
def api_ldp_lookup(request):
    """
    JSON API for scanning / looking up an LDP batch by ldp_number to add to Invoice creation form.
    """
    query = (request.GET.get('ldp_number') or request.GET.get('q') or request.GET.get('resi') or '').strip()
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Nomor LDP tidak boleh kosong.'})

    query_clean = query.split('/')[-1].strip()

    ldp = LDP.objects.filter(
        Q(ldp_number__iexact=query) | Q(ldp_number__iexact=query_clean)
    ).prefetch_related('items', 'client').first()

    if not ldp:
        ldp = LDP.objects.filter(ldp_number__icontains=query).prefetch_related('items', 'client').first()

    if not ldp:
        return JsonResponse({'status': 'error', 'message': f'Batch LDP "{query}" tidak ditemukan di sistem.'})

    if ldp.status == 'INVOICED' or ldp.invoice_id:
        inv_num = ldp.invoice.invoice_number if ldp.invoice else 'Invoice Terkait'
        return JsonResponse({
            'status': 'error',
            'message': f'LDP {ldp.ldp_number} sudah pernah dibuatkan invoice ({inv_num}). Tidak dapat dimasukkan lagi.'
        })

    if ldp.status == 'CANCELLED':
        return JsonResponse({
            'status': 'error',
            'message': f'LDP {ldp.ldp_number} berstatus Dibatalkan (CANCELLED).'
        })

    client_id = ldp.client_id or ''
    client_name = ldp.client.name if ldp.client else (ldp.client_name or 'Klien Umum')
    client_code = ldp.client.customer_code if ldp.client else ''

    items_data = []
    for it in ldp.items.all():
        items_data.append({
            'awb_number': it.awb_number,
            'shipment_date': it.shipment_date.strftime('%d/%m/%Y') if it.shipment_date else '-',
            'sender_name': it.sender_name or '-',
            'receiver_name': it.receiver_name or '-',
            'origin': it.origin or '-',
            'destination': it.destination or '-',
            'service_type': it.service_type or 'REG',
            'koli': it.koli or 1,
            'weight': float(it.chargeable_weight or 0),
            'price_per_kg': float(it.price_per_kg or 0),
            'freight_charge': float(it.freight_charge or 0),
            'discount': float(it.discount or 0),
            'packing_fee': float(it.packing_fee or 0),
            'insurance_fee': float(it.insurance_fee or 0),
            'handling_fee': float(it.handling_fee or 0),
            'surcharges': float(it.surcharges or 0),
            'subtotal': float(it.subtotal or 0),
        })

    data = {
        'id': ldp.id,
        'ldp_number': ldp.ldp_number,
        'ldp_date': ldp.ldp_date.strftime('%d/%m/%Y') if ldp.ldp_date else '-',
        'client_id': client_id,
        'client_name': client_name,
        'client_code': client_code,
        'total_koli': ldp.total_koli,
        'total_weight': float(ldp.total_weight),
        'total_freight': float(ldp.total_freight),
        'total_surcharges': float(ldp.total_surcharges),
        'total_amount': float(ldp.total_amount),
        'total_awb': ldp.items.count(),
        'items': items_data,
    }

    return JsonResponse({'status': 'success', 'data': data})


@login_required
def api_customer_ldps(request):
    """
    JSON API to get un-invoiced LDPs and their item breakdown for a customer.
    """
    customer_id = request.GET.get('customer_id', '').strip()
    if not customer_id:
        return JsonResponse({'status': 'error', 'message': 'Customer ID is required.'})

    ldps = LDP.objects.filter(
        client_id=customer_id,
        status__in=['DRAFT', 'CONFIRMED'],
        invoice__isnull=True
    ).prefetch_related('items').order_by('-created_at')

    data = []
    for ldp in ldps:
        items_data = []
        for it in ldp.items.all():
            items_data.append({
                'awb_number': it.awb_number,
                'created_at': it.shipment_date.strftime('%d/%m/%Y') if it.shipment_date else '-',
                'origin': it.origin,
                'destination': it.destination,
                'service_type': it.service_type,
                'weight': float(it.chargeable_weight),
                'freight_charge': float(it.freight_charge),
                'price_per_kg': float(it.price_per_kg),
                'discount': float(it.discount),
                'packing_fee': float(it.packing_fee),
                'insurance_fee': float(it.insurance_fee),
                'handling_fee': float(it.handling_fee),
                'surcharges': float(it.surcharges),
                'subtotal': float(it.subtotal),
            })

        data.append({
            'id': ldp.id,
            'ldp_number': ldp.ldp_number,
            'ldp_date': ldp.ldp_date.strftime('%d/%m/%Y') if ldp.ldp_date else '-',
            'total_koli': ldp.total_koli,
            'total_weight': float(ldp.total_weight),
            'total_freight': float(ldp.total_freight),
            'total_surcharges': float(ldp.total_surcharges),
            'total_amount': float(ldp.total_amount),
            'total_awb': ldp.items.count(),
            'items': items_data,
        })

    return JsonResponse({'status': 'success', 'data': data})


# ==================== INVOICE PROCESS (APPROVAL & RECONCILE) ====================

@login_required
def invoice_process(request):
    """
    Dedicated Menu: Invoice Process
    Tab 1: Approval Invoice (Draft validation & approval)
    Tab 2: Reconcile Invoice (Payment reconciliation for unpaid/partial invoices)
    Tab 3: Riwayat Selesai (Completed / Paid invoices archive)
    """
    from apps.master.models import Bank
    from django.core.paginator import Paginator

    tab = request.GET.get('tab', 'approval')
    search = request.GET.get('q', '').strip()
    customer_query = request.GET.get('customer', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    def apply_filters(qs):
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) |
                Q(client_name__icontains=search) |
                Q(kode_pelanggan__icontains=search) |
                Q(npwp__icontains=search)
            )
        if customer_query:
            qs = qs.filter(Q(client_name__icontains=customer_query) | Q(kode_pelanggan__icontains=customer_query))
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        return qs

    # 1. Approval Tab: Draft Invoices
    draft_qs = Invoice.objects.filter(status='DRAFT').prefetch_related('ldps', 'shipments').order_by('-created_at')
    if tab == 'approval':
        draft_qs = apply_filters(draft_qs)
    total_draft = Invoice.objects.filter(status='DRAFT').count()

    # 2. Reconcile Tab: Unpaid / Partial Official Invoices (Need Reconcile)
    reconcile_qs = Invoice.objects.filter(status__in=['SENT', 'PARTIAL']).prefetch_related('ldps', 'reconciliations').order_by('-created_at')
    if tab == 'reconcile':
        reconcile_qs = apply_filters(reconcile_qs)

    # 3. Completed Tab: Paid Invoices (Riwayat Selesai)
    completed_qs = Invoice.objects.filter(status='PAID').prefetch_related('ldps', 'reconciliations').order_by('-updated_at')
    if tab == 'completed':
        completed_qs = apply_filters(completed_qs)
    
    unpaid_invoices = Invoice.objects.filter(status__in=['SENT', 'PARTIAL']).order_by('-date_issued')
    total_unpaid = unpaid_invoices.count()
    total_completed = Invoice.objects.filter(status='PAID').count()

    banks = Bank.objects.filter(is_active=True).order_by('name')
    active_filters = bool(customer_query or start_date or end_date)

    # Pagination
    if tab == 'reconcile':
        paginator = Paginator(reconcile_qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
    elif tab == 'completed':
        paginator = Paginator(completed_qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
    else:
        paginator = Paginator(draft_qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'tab': tab,
        'page_obj': page_obj,
        'draft_invoices': page_obj if tab == 'approval' else draft_qs[:20],
        'reconcile_invoices': page_obj if tab == 'reconcile' else reconcile_qs[:20],
        'completed_invoices': page_obj if tab == 'completed' else completed_qs[:20],
        'unpaid_invoices_dropdown': unpaid_invoices,
        'total_draft': total_draft,
        'total_unpaid': total_unpaid,
        'total_completed': total_completed,
        'banks': banks,
        'search': search,
        'customer_query': customer_query,
        'start_date': start_date,
        'end_date': end_date,
        'active_filters': active_filters,
    }
    return render(request, 'finance/invoice_process/invoice_process.html', context)


@login_required
def invoice_approve(request, invoice_id):
    """
    Approve Draft Invoice -> Make it Official (Status: SENT).
    """
    from django.contrib import messages
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        company_code = request.POST.get('company_code', invoice.company_code)
        due_date_str = request.POST.get('due_date', '')
        notes = request.POST.get('notes', '')

        invoice.company_code = company_code
        if due_date_str:
            try:
                invoice.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if notes:
            invoice.notes = f"{invoice.notes}\n{notes}".strip() if invoice.notes else notes

        invoice.status = 'SENT'
        invoice.is_open = False
        invoice.save()

        from .utils import sync_invoice_shipments_to_worksheet
        sync_invoice_shipments_to_worksheet(invoice)

        messages.success(request, f"Invoice {invoice.invoice_number} berhasil di-approve dan diterbitkan sebagai Invoice Resmi.")
        return redirect(f"/finance/invoice-process/?tab=approval")
    return redirect('finance:invoice_process')


@login_required
def invoice_reconcile(request):
    """
    Process payment reconciliation for an invoice (Input No Inv, Transfer Date, Bank, Upload Foto/Bukti).
    """
    from django.contrib import messages
    from apps.master.models import Bank
    from .models import PaymentReconciliation, Invoice, KpiFinance

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        invoice = get_object_or_404(Invoice, id=invoice_id)

        bank_id = request.POST.get('bank_id')
        from .utils import parse_currency_decimal
        amount_paid = parse_currency_decimal(request.POST.get('amount_paid'))
        transfer_date_str = request.POST.get('transfer_date', '')
        reference_number = request.POST.get('reference_number', '').strip()
        notes = request.POST.get('notes', '').strip()
        proof_file = request.FILES.get('proof_file')

        if amount_paid <= 0:
            messages.error(request, "Nominal pembayaran harus lebih dari 0.")
            return redirect('/finance/invoice-process/?tab=reconcile')

        bank_obj = Bank.objects.filter(id=bank_id).first() if bank_id else None

        transfer_dt = timezone.now()
        if transfer_date_str:
            try:
                naive_dt = datetime.strptime(transfer_date_str, '%Y-%m-%d')
                transfer_dt = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
            except (ValueError, TypeError):
                pass

        # Create Reconciliation Record
        recon = PaymentReconciliation.objects.create(
            invoice=invoice,
            bank=bank_obj,
            amount_paid=amount_paid,
            payment_datetime=transfer_dt,
            reference_number=reference_number,
            proof_file=proof_file,
            notes=notes,
            reconciled_by=request.user,
        )

        # Update Invoice Paid Amount
        invoice.amount_paid += amount_paid
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = 'PAID'
        else:
            invoice.status = 'PARTIAL'
        invoice.save()

        # Update linked KPI row status if PAID
        if invoice.status == 'PAID':
            KpiFinance.objects.filter(linked_invoice=invoice).update(row_status='completed')

        messages.success(request, f"Rekonsiliasi pembayaran Rp {amount_paid:,.0f} untuk Invoice {invoice.invoice_number} berhasil dicatat.")
        return redirect('/finance/invoice-process/?tab=reconcile')

    return redirect('/finance/invoice-process/?tab=reconcile')
