import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Shipment, DocumentPouch, Tracking
from apps.organizations.models import Branch

@login_required
def do_balik_list(request):
    """Halaman Dashboard & Daftar Status DO Balik"""
    status_tab = request.GET.get('tab', 'all')
    search_query = request.GET.get('q', '').strip()
    branch_filter = request.GET.get('branch', '')
    status_filter = request.GET.get('status', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Filter shipments yang memerlukan DO Balik
    shipments_qs = Shipment.objects.filter(
        Q(with_do_balik=True) | Q(client__with_pod_resi=True) | Q(status='POD_BALIK') | Q(do_balik_date__isnull=False)
    ).exclude(is_hidden=True).select_related('client', 'origin_coverage', 'destination_coverage').order_by('-updated_at')

    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)

    if search_query:
        matched_qs = shipments_qs.filter(
            Q(resi_number__icontains=search_query) |
            Q(receiver_name__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(destination__icontains=search_query)
        )
        filtered_qs = matched_qs
        if branch_filter:
            filtered_qs = filtered_qs.filter(
                Q(origin__icontains=branch_filter) | Q(destination__icontains=branch_filter)
            )
        if status_filter:
            filtered_qs = filtered_qs.filter(status=status_filter)
            
        date_filtered_qs = filtered_qs
        if psd:
            date_filtered_qs = date_filtered_qs.filter(created_at__date__gte=psd)
        if ped:
            date_filtered_qs = date_filtered_qs.filter(created_at__date__lte=ped)
            
        if date_filtered_qs.exists():
            shipments_qs = date_filtered_qs
        elif filtered_qs.exists():
            shipments_qs = filtered_qs
        else:
            shipments_qs = matched_qs
    else:
        if branch_filter:
            shipments_qs = shipments_qs.filter(
                Q(origin__icontains=branch_filter) | Q(destination__icontains=branch_filter)
            )
        if status_filter:
            shipments_qs = shipments_qs.filter(status=status_filter)
        if psd:
            shipments_qs = shipments_qs.filter(created_at__date__gte=psd)
        if ped:
            shipments_qs = shipments_qs.filter(created_at__date__lte=ped)

    # Filter tab
    if status_tab == 'pending_delivery':
        shipments_qs = shipments_qs.filter(status__in=['PENDING', 'PICKUP', 'INBOUND_ORIGIN', 'OUTGOING', 'TRANSIT', 'INCOMING_DESTINATION', 'DELIVERY'])
    elif status_tab == 'signed_dest':
        # Sudah POD di tujuan tapi belum masuk pouch & belum POD_BALIK
        shipments_qs = shipments_qs.filter(status='POD', do_balik_date__isnull=True, document_pouches__isnull=True)
    elif status_tab == 'in_pouch':
        # Sedang dalam perjalanan pouch
        shipments_qs = shipments_qs.filter(document_pouches__status='DISPATCHED')
    elif status_tab == 'received_origin':
        # Sudah diverifikasi di hub asal (POD_BALIK)
        shipments_qs = shipments_qs.filter(Q(status='POD_BALIK') | Q(do_balik_date__isnull=False))

    pouches = DocumentPouch.objects.all().select_related('origin_branch', 'dest_branch', 'created_by', 'received_by').prefetch_related('shipments').order_by('-created_at')[:50]
    branches = Branch.objects.all()

    # Hitung counter stats
    total_do = Shipment.objects.filter(Q(with_do_balik=True) | Q(client__with_pod_resi=True)).count()
    count_signed = Shipment.objects.filter(status='POD', do_balik_date__isnull=True, document_pouches__isnull=True).filter(Q(with_do_balik=True) | Q(client__with_pod_resi=True)).count()
    count_pouch = DocumentPouch.objects.filter(status='DISPATCHED').count()
    count_verified = Shipment.objects.filter(Q(status='POD_BALIK') | Q(do_balik_date__isnull=False)).count()

    has_active_filter = bool(search_query or branch_filter or status_filter or start_date or end_date)

    context = {
        'shipments': shipments_qs[:100],
        'pouches': pouches,
        'branches': branches,
        'active_tab': status_tab,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'has_active_filter': has_active_filter,
        'stats': {
            'total_do': total_do,
            'count_signed': count_signed,
            'count_pouch': count_pouch,
            'count_verified': count_verified,
        }
    }
    return render(request, 'operations/do_balik/do_balik_list.html', context)


@login_required
def do_balik_create_pouch(request):
    """Hub Tujuan membuat Pouch Dokumen DO Balik untuk dikirim ke Hub Asal"""
    if request.method == 'POST':
        origin_branch_id = request.POST.get('origin_branch')
        dest_branch_id = request.POST.get('dest_branch')
        courier_service = request.POST.get('courier_service', '')
        airwaybill_no = request.POST.get('airwaybill_no', '')
        notes = request.POST.get('notes', '')
        shipment_ids = request.POST.getlist('shipment_ids')

        if not dest_branch_id or not shipment_ids:
            messages.error(request, 'Harap pilih Cabang Tujuan dan minimal 1 resi DO Balik.')
            return redirect('operations:do-balik-list')

        origin_branch = Branch.objects.filter(id=origin_branch_id).first() if origin_branch_id else None
        dest_branch = Branch.objects.filter(id=dest_branch_id).first()

        pouch = DocumentPouch.objects.create(
            origin_branch=origin_branch,
            dest_branch=dest_branch,
            courier_service=courier_service,
            airwaybill_no=airwaybill_no,
            status='DISPATCHED',
            notes=notes,
            created_by=request.user,
            dispatched_at=timezone.now()
        )
        pouch.shipments.set(shipment_ids)

        for s in pouch.shipments.all():
            Tracking.objects.create(
                shipment=s,
                status='TRANSIT',
                location=origin_branch.name if origin_branch else 'Hub Tujuan',
                notes=f'Fisik Surat Jalan (DO Balik) dimasukkan ke Pouch {pouch.pouch_number} via {courier_service or "Ekspedisi Internal"}',
                created_by=request.user
            )

        messages.success(request, f'Pouch Dokumen {pouch.pouch_number} berhasil dibuat ({len(shipment_ids)} DO Balik siap dikirim).')
        return redirect('operations:do-balik-list')

    # GET: Tampilkan form pilih AWB yang sudah POD tapi belum dibuatkan pouch
    available_shipments = Shipment.objects.filter(
        Q(with_do_balik=True) | Q(client__with_pod_resi=True) | Q(status='POD')
    ).filter(do_balik_date__isnull=True, document_pouches__isnull=True).exclude(status__in=['PENDING', 'CANCELLED', 'VOID'])

    branches = Branch.objects.all()
    return render(request, 'operations/do_balik/do_balik_pouch_edit.html', {
        'available_shipments': available_shipments[:100],
        'branches': branches
    })


@login_required
def do_balik_verify_pouch(request, pk):
    """Hub Asal menerima & memverifikasi kelengkapan fisik DO Balik dari Pouch"""
    pouch = get_object_or_404(DocumentPouch, pk=pk)

    if request.method == 'POST':
        verified_shipment_ids = request.POST.getlist('verified_shipment_ids')
        notes = request.POST.get('notes', '')

        now = timezone.now()
        pouch.status = 'RECEIVED'
        pouch.received_by = request.user
        pouch.received_at = now
        pouch.notes = (pouch.notes or '') + f"\n[Verifikasi {now.strftime('%d/%m/%Y %H:%M')} oleh {request.user.username}]: {notes}"
        pouch.save()

        # Update shipments
        for s in pouch.shipments.filter(id__in=verified_shipment_ids):
            s.status = 'POD_BALIK'
            s.do_balik_date = now.date()
            s.save(update_fields=['status', 'do_balik_date', 'updated_at'])

            Tracking.objects.create(
                shipment=s,
                status='POD_BALIK',
                location=pouch.dest_branch.name if pouch.dest_branch else 'Hub Asal',
                notes=f'Fisik Surat Jalan / DO Balik telah diterima & diverifikasi lengkap di Hub Asal dari Pouch {pouch.pouch_number}',
                created_by=request.user
            )

        messages.success(request, f'Pouch {pouch.pouch_number} berhasil diverifikasi. {len(verified_shipment_ids)} resi berstatus POD BALIK dan siap ditagihkan.')
        return redirect('operations:do-balik-list')

    return render(request, 'operations/do_balik/do_balik_verify_edit.html', {'pouch': pouch})


@login_required
def do_balik_quick_verify(request, pk):
    """Verifikasi langsung per satu resi (Direct Verification di Hub Asal)"""
    shipment = get_object_or_404(Shipment, pk=pk)
    now = timezone.now()
    shipment.status = 'POD_BALIK'
    shipment.do_balik_date = now.date()
    shipment.save(update_fields=['status', 'do_balik_date', 'updated_at'])

    Tracking.objects.create(
        shipment=shipment,
        status='POD_BALIK',
        location='Hub Asal',
        notes='Fisik Surat Jalan / DO Balik telah diverifikasi langsung oleh Finance/Ops di Hub Asal',
        created_by=request.user
    )

    messages.success(request, f'Resi {shipment.resi_number} berhasil di-update menjadi POD BALIK.')
    return redirect(request.META.get('HTTP_REFERER', 'operations:do-balik-list'))
