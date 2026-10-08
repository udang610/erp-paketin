from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Shipment, ReturnShipment, Tracking
from apps.organizations.models import Branch

@login_required
def return_list(request):
    """
    Dashboard & Manajemen Retur (RTO) dengan arsitektur 3 Tab:
    - Tab A: Laporan / Antrean Masuk (Inbound Failed)
    - Tab B: Kirim Ulang (Re-delivery)
    - Tab C: Kembali ke Pengirim (Return to Origin / RTO)
    """
    active_tab = request.GET.get('tab', 'laporan').strip().lower()
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Query Base
    base_qs = ReturnShipment.objects.all().select_related(
        'shipment', 'shipment__client', 'created_by', 'approved_by'
    ).order_by('-updated_at', '-created_at')

    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)

    if search_query:
        matched_qs = base_qs.filter(
            Q(rto_number__icontains=search_query) |
            Q(shipment__resi_number__icontains=search_query) |
            Q(shipment__receiver_name__icontains=search_query) |
            Q(shipment__sender_name__icontains=search_query) |
            Q(shipment__client__name__icontains=search_query)
        )
        filtered_qs = matched_qs
        if status_filter:
            filtered_qs = filtered_qs.filter(status=status_filter)
            
        date_filtered_qs = filtered_qs
        if psd:
            date_filtered_qs = date_filtered_qs.filter(created_at__date__gte=psd)
        if ped:
            date_filtered_qs = date_filtered_qs.filter(created_at__date__lte=ped)
            
        if date_filtered_qs.exists():
            base_qs = date_filtered_qs
        elif filtered_qs.exists():
            base_qs = filtered_qs
        else:
            base_qs = matched_qs
    else:
        if status_filter:
            base_qs = base_qs.filter(status=status_filter)
        if psd:
            base_qs = base_qs.filter(created_at__date__gte=psd)
        if ped:
            base_qs = base_qs.filter(created_at__date__lte=ped)

    # Filter per Tab
    if active_tab == 'redeliver':
        # Tab B: Kirim Ulang (Re-delivery)
        returns_qs = base_qs.filter(
            Q(action_type='REDELIVER') | Q(status='SCHEDULED_REDELIVERY')
        ).exclude(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']).exclude(shipment__status__in=['POD', 'POD_BALIK'])
    elif active_tab == 'return':
        # Tab C: Kembali ke Pengirim (RTO)
        returns_qs = base_qs.filter(
            Q(action_type='RETURN_TO_ORIGIN') | 
            Q(status__in=['APPROVED_RTO', 'IN_TRANSIT_RTO', 'RECEIVED_ORIGIN', 'CONFIRM_SHIPPER'])
        ).exclude(status='RETURNED_TO_SHIPPER')
    elif active_tab == 'selesai':
        # Tab D: Riwayat Selesai (Completed Redelivery / Completed Return)
        returns_qs = base_qs.filter(
            Q(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']) |
            Q(shipment__status__in=['POD', 'POD_BALIK'])
        )
    else:
        # Tab A: Laporan / Antrean Masuk (Default)
        active_tab = 'laporan'
        returns_qs = base_qs.filter(
            Q(action_type='PENDING') | Q(status='HOLD_DESTINATION')
        ).exclude(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']).exclude(shipment__status__in=['POD', 'POD_BALIK'])

    # Counters
    count_laporan = ReturnShipment.objects.filter(
        Q(action_type='PENDING') | Q(status='HOLD_DESTINATION')
    ).exclude(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']).exclude(shipment__status__in=['POD', 'POD_BALIK']).count()

    count_redeliver = ReturnShipment.objects.filter(
        Q(action_type='REDELIVER') | Q(status='SCHEDULED_REDELIVERY')
    ).exclude(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']).exclude(shipment__status__in=['POD', 'POD_BALIK']).count()

    count_return = ReturnShipment.objects.filter(
        Q(action_type='RETURN_TO_ORIGIN') | 
        Q(status__in=['APPROVED_RTO', 'IN_TRANSIT_RTO', 'RECEIVED_ORIGIN', 'CONFIRM_SHIPPER'])
    ).exclude(status='RETURNED_TO_SHIPPER').count()

    count_selesai = ReturnShipment.objects.filter(
        Q(status__in=['CANCELLED_REDELIVERED', 'RETURNED_TO_SHIPPER']) |
        Q(shipment__status__in=['POD', 'POD_BALIK'])
    ).count()

    has_active_filter = bool(search_query or status_filter or start_date or end_date)

    context = {
        'returns': returns_qs[:150],
        'active_tab': active_tab,
        'search_query': search_query,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'has_active_filter': has_active_filter,
        'reason_choices': ReturnShipment.REASON_CHOICES,
        'stats': {
            'count_laporan': count_laporan,
            'count_redeliver': count_redeliver,
            'count_return': count_return,
            'count_selesai': count_selesai,
            'total_all': count_laporan + count_redeliver + count_return + count_selesai
        }
    }
    return render(request, 'operations/returns/return_list.html', context)


@login_required
def api_lookup_return_resi(request):
    """
    AJAX endpoint untuk scan barcode AWB / No. RTO di menu Retur.
    Mengembalikan data shipment dan data RTO terkait.
    """
    resi = request.GET.get('resi', '').strip()
    if not resi:
        return JsonResponse({'status': 'error', 'message': 'Nomor resi atau No. RTO tidak boleh kosong.'})

    rto = ReturnShipment.objects.filter(rto_number__iexact=resi).select_related('shipment').first()
    if rto:
        shipment = rto.shipment
    else:
        shipment = Shipment.objects.filter(resi_number__iexact=resi).first()
        if not shipment:
            rto = ReturnShipment.objects.filter(rto_number__icontains=resi).select_related('shipment').first()
            if rto:
                shipment = rto.shipment
        if not shipment:
            return JsonResponse({'status': 'error', 'message': f'Resi / No. RTO "{resi}" tidak ditemukan di sistem.'})
        rto = ReturnShipment.objects.filter(shipment=shipment).exclude(status='CANCELLED_REDELIVERED').first()

    data = {
        'status': 'success',
        'shipment_id': shipment.id,
        'resi_number': shipment.resi_number,
        'rto_id': rto.id if rto else None,
        'rto_number': rto.rto_number if rto else '-',
        'sender_name': shipment.sender_name or (shipment.client.name if shipment.client else '-'),
        'receiver_name': shipment.receiver_name or '-',
        'origin': shipment.origin_clean,
        'destination': shipment.destination_clean,
        'service_type': shipment.get_service_type_display(),
        'weight': float(shipment.weight or 1),
        'colly': shipment.total_colly or 1,
        'attempts': shipment.delivery_attempts or (rto.attempt_count if rto else 1),
        'reason': rto.reason if rto else (shipment.failed_reason or 'RECIPIENT_NOT_HOME'),
        'reason_display': rto.get_reason_display() if rto else (dict(ReturnShipment.REASON_CHOICES).get(shipment.failed_reason, shipment.failed_reason or '-')),
        'reason_detail': rto.reason_detail if rto else (shipment.failed_note or ''),
        'action_type': rto.action_type if rto else 'PENDING',
        'current_status': rto.get_status_display() if rto else shipment.get_status_display(),
    }
    return JsonResponse(data)


@login_required
def return_decision_quick(request):
    """
    Proses cepat konfirmasi keputusan di Tab A (Kirim Ulang vs Retur ke Pengirim).
    """
    if request.method != 'POST':
        return redirect('operations:return-list')

    resi_number = request.POST.get('resi_number', '').strip()
    decision = request.POST.get('decision') # 'REDELIVER' or 'RETURN_TO_ORIGIN'
    scheduled_date = request.POST.get('scheduled_date')
    cs_notes = request.POST.get('cs_notes', '').strip()
    return_fee = request.POST.get('return_fee', '0')

    shipment = get_object_or_404(Shipment, resi_number=resi_number)
    rto = ReturnShipment.objects.filter(shipment=shipment).exclude(status='CANCELLED_REDELIVERED').first()

    if not rto:
        rto = ReturnShipment.objects.create(
            shipment=shipment,
            reason=shipment.failed_reason or 'OTHER',
            reason_detail=shipment.failed_note or '',
            attempt_count=shipment.delivery_attempts or 1,
            created_by=request.user
        )

    now = timezone.now()
    rto.cs_notes = (rto.cs_notes or '') + f"\n[{now.strftime('%d/%m/%Y %H:%M')} oleh {request.user.username}]: {cs_notes}"

    if decision == 'REDELIVER':
        rto.action_type = 'REDELIVER'
        rto.status = 'SCHEDULED_REDELIVERY'
        if not rto.rto_number.startswith('RD-'):
            rto.rto_number = ReturnShipment.generate_number('RD')
        if scheduled_date:
            try:
                import datetime
                rto.scheduled_redelivery_date = datetime.datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            except Exception:
                pass
        rto.save()

        shipment.status = 'REDELIVER'
        shipment.save(update_fields=['status', 'updated_at'])

        # Update tracking
        date_str = rto.scheduled_redelivery_date.strftime('%d/%m/%Y') if rto.scheduled_redelivery_date else 'hari berikutnya'
        Tracking.objects.create(
            shipment=shipment,
            status='REDELIVER',
            location=shipment.get_city_dest or 'Hub Tujuan',
            description=f"Dijadwalkan Kirim Ulang (Re-Delivery ID: {rto.rto_number}) pada {date_str}. Catatan: {cs_notes}" if cs_notes else f"Dijadwalkan Kirim Ulang (Re-Delivery ID: {rto.rto_number}) pada {date_str}.",
            occurred_at=now
        )
        messages.success(request, f"Resi {resi_number} dialihkan ke Kirim Ulang (ID: {rto.rto_number}) untuk jadwal {date_str}.")
        return redirect('operations:return-list')

    elif decision == 'RETURN_TO_ORIGIN':
        rto.action_type = 'RETURN_TO_ORIGIN'
        rto.status = 'APPROVED_RTO'
        rto.approved_by = request.user
        if not rto.rto_number.startswith('RTO-'):
            rto.rto_number = ReturnShipment.generate_number('RTO')
        try:
            rto.return_fee = float(return_fee) if return_fee else 0
        except ValueError:
            pass
        rto.save()

        shipment.status = 'RETURNED'
        shipment.save(update_fields=['status', 'updated_at'])

        Tracking.objects.create(
            shipment=shipment,
            status='RETURNED',
            location=shipment.get_city_dest or 'Hub Tujuan',
            description=f"Pengajuan Retur Disetujui (RTO: {rto.rto_number}). Paket siap diberangkatkan kembali ke Hub Asal. {cs_notes}".strip(),
            occurred_at=now
        )
        messages.success(request, f"Resi {resi_number} dialihkan ke Tab C (Kembali ke Pengirim / RTO).")
        return redirect('operations:return-list')

    return redirect('operations:return-list')


@login_required
def return_create(request):
    """Mencatat paket gagal antar / scan retur (berbasis scanner seperti POD / Transit)"""
    if request.method == 'POST':
        scanned_items = request.POST.getlist('scanned_items')
        single_shipment_id = request.POST.get('shipment_id')
        reason = request.POST.get('reason', 'RECIPIENT_NOT_HOME')
        reason_detail = request.POST.get('reason_detail', '').strip()
        evidence_image = request.FILES.get('evidence_image')

        now = timezone.now()
        success_count = 0

        # Collect list of shipments
        shipments_to_process = []
        if scanned_items:
            for item_code in scanned_items:
                s_obj = Shipment.objects.filter(resi_number=item_code).first()
                if s_obj and s_obj not in shipments_to_process:
                    shipments_to_process.append(s_obj)
        elif single_shipment_id:
            s_obj = Shipment.objects.filter(pk=single_shipment_id).first()
            if s_obj:
                shipments_to_process.append(s_obj)

        if not shipments_to_process:
            messages.error(request, 'Pilih atau scan minimal satu nomor resi.')
            return redirect('operations:return-create')

        for shipment in shipments_to_process:
            shipment.status = 'DELIVERY_FAILED'
            shipment.delivery_attempts = (shipment.delivery_attempts or 0) + 1
            shipment.failed_reason = reason
            shipment.failed_note = reason_detail
            shipment.failed_date = now
            if evidence_image:
                shipment.failed_image = evidence_image
            shipment.save()

            active_rto = ReturnShipment.objects.filter(
                shipment=shipment,
                status__in=['HOLD_DESTINATION', 'SCHEDULED_REDELIVERY', 'CONFIRM_SHIPPER']
            ).first()

            if not active_rto:
                active_rto = ReturnShipment.objects.create(
                    shipment=shipment,
                    reason=reason,
                    reason_detail=reason_detail,
                    evidence_image=evidence_image,
                    status='HOLD_DESTINATION',
                    action_type='PENDING',
                    attempt_count=shipment.delivery_attempts,
                    created_by=request.user
                )
            else:
                active_rto.reason = reason
                active_rto.attempt_count = shipment.delivery_attempts
                active_rto.status = 'HOLD_DESTINATION'
                active_rto.action_type = 'PENDING'
                if evidence_image:
                    active_rto.evidence_image = evidence_image
                active_rto.reason_detail = (active_rto.reason_detail or '') + f"\n[Percobaan #{shipment.delivery_attempts}]: {reason_detail}"
                active_rto.save()

            reason_label = dict(ReturnShipment.REASON_CHOICES).get(reason, reason)
            Tracking.objects.create(
                shipment=shipment,
                status='DELIVERY_FAILED',
                location=shipment.destination or 'Hub Tujuan',
                description=f"Gagal Antar (Percobaan #{shipment.delivery_attempts}): {reason_label}. {reason_detail}".strip(),
                occurred_at=now
            )
            success_count += 1

        messages.warning(request, f'Berhasil mencatat {success_count} resi Gagal Antar di Laporan Masuk.')
        return redirect('operations:return-list')

    return render(request, 'operations/returns/return_edit.html', {
        'reason_choices': ReturnShipment.REASON_CHOICES,
        'event_date': timezone.localtime().strftime('%Y-%m-%d'),
        'event_time': timezone.localtime().strftime('%H:%M'),
    })


@login_required
def return_action(request, pk):
    """CS / Supervisor Ops memproses tindakan bertahap pada RTO"""
    rto = get_object_or_404(ReturnShipment.objects.select_related('shipment'), pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action') # 'APPROVE_RTO', 'REDELIVER', 'DISPATCH_RTO', 'RECEIVE_ORIGIN', 'HANDOVER_SHIPPER', 'SWITCH_TO_REDELIVER'
        cs_notes = request.POST.get('cs_notes', '')
        rto_manifest_no = request.POST.get('rto_manifest_no', '')
        return_fee = request.POST.get('return_fee', '0')

        now = timezone.now()
        rto.cs_notes = (rto.cs_notes or '') + f"\n[{now.strftime('%d/%m/%Y %H:%M')} oleh {request.user.username}]: {cs_notes}"

        if action == 'APPROVE_RTO':
            rto.action_type = 'RETURN_TO_ORIGIN'
            rto.status = 'APPROVED_RTO'
            rto.approved_by = request.user
            try:
                rto.return_fee = float(return_fee) if return_fee else 0
            except ValueError:
                pass
            rto.save()

            rto.shipment.status = 'RETURNED'
            rto.shipment.save(update_fields=['status', 'updated_at'])

            Tracking.objects.create(
                shipment=rto.shipment,
                status='RETURNED',
                location=rto.shipment.get_city_dest or 'Hub Tujuan',
                description=f'Pengajuan Retur Disetujui (RTO: {rto.rto_number}). Menunggu pengiriman kembali ke Hub Asal. {cs_notes}'.strip()
            )
            messages.success(request, f'Retur {rto.rto_number} telah disetujui (RTO).')

        elif action == 'REDELIVER':
            rto.action_type = 'REDELIVER'
            rto.status = 'SCHEDULED_REDELIVERY'
            rto.save()

            rto.shipment.status = 'REDELIVER'
            rto.shipment.save(update_fields=['status', 'updated_at'])

            Tracking.objects.create(
                shipment=rto.shipment,
                status='REDELIVER',
                location=rto.shipment.get_city_dest or 'Hub Tujuan',
                description=f'Dijadwalkan Antar Ulang (Re-Delivery) sesuai instruksi. {cs_notes}'.strip()
            )
            messages.success(request, f'Paket {rto.shipment.resi_number} dijadwalkan untuk antar ulang (Re-Delivery).')

        elif action == 'DISPATCH_RTO':
            rto.status = 'IN_TRANSIT_RTO'
            rto.rto_manifest_no = rto_manifest_no
            rto.save()

            Tracking.objects.create(
                shipment=rto.shipment,
                status='TRANSIT',
                location='Linehaul Retur',
                description=f'Paket Retur dalam perjalanan kembali ke Hub Asal (Manifest RTO: {rto_manifest_no or "-"}). {cs_notes}'.strip()
            )
            messages.success(request, f'Paket retur {rto.rto_number} telah diberangkatkan kembali ke Hub Asal.')

        elif action == 'RECEIVE_ORIGIN':
            rto.status = 'RECEIVED_ORIGIN'
            rto.save()

            Tracking.objects.create(
                shipment=rto.shipment,
                status='INBOUND_ORIGIN',
                location=rto.shipment.get_city_origin or 'Hub Asal',
                description=f'Fisik paket retur telah tiba dan diterima di Hub Asal. Siap diserahkan ke Pengirim.'
            )
            messages.success(request, f'Paket retur {rto.rto_number} telah diterima di Hub Asal.')

        elif action == 'HANDOVER_SHIPPER':
            rto.status = 'RETURNED_TO_SHIPPER'
            rto.returned_at = now
            rto.save()

            rto.shipment.status = 'RETURNED'
            rto.shipment.save(update_fields=['status', 'updated_at'])

            Tracking.objects.create(
                shipment=rto.shipment,
                status='RETURNED',
                location=rto.shipment.get_city_origin or 'Hub Asal',
                description=f'Paket retur telah diserahkan kembali kepada Pengirim/Shipper ({rto.shipment.sender_name}). Proses Retur Selesai.'
            )
            messages.success(request, f'Serah terima retur ke Pengirim {rto.shipment.sender_name} berhasil dicatat.')

        elif action == 'SWITCH_TO_REDELIVER':
            rto.action_type = 'REDELIVER'
            rto.status = 'SCHEDULED_REDELIVERY'
            rto.save()

            rto.shipment.status = 'REDELIVER'
            rto.shipment.save(update_fields=['status', 'updated_at'])

            Tracking.objects.create(
                shipment=rto.shipment,
                status='REDELIVER',
                location=rto.shipment.get_city_dest or 'Hub Tujuan',
                description=f'Status dialihkan untuk Kirim Ulang (Re-Delivery). {cs_notes}'.strip()
            )
            messages.success(request, f'Paket {rto.shipment.resi_number} dialihkan ke Kirim Ulang (Re-Delivery).')

        return redirect('operations:return-list')

    return render(request, 'operations/returns/return_detail.html', {'rto': rto})


@login_required
def redeliver_scan_view(request):
    """
    Form Scan Khusus Re-Delivery (Kirim Ulang).
    Mendukung scan No. RTO atau No. AWB, dengan pilihan hasil pengantaran (POD Sukses vs Gagal Antar lagi).
    """
    from .models import PODAttachment
    import datetime

    # Preloaded resi / rto from query params if any
    preload_rto = request.GET.get('rto', '').strip()
    preload_resi = request.GET.get('resi', '').strip()

    if request.method == 'POST':
        delivery_outcome = request.POST.get('delivery_outcome', 'DELIVERED').strip() # 'DELIVERED' or 'FAILED'
        scanned_items = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        pod_receiver_name = request.POST.get('pod_receiver_name', '').strip()
        failed_reason = request.POST.get('failed_reason', 'RECIPIENT_NOT_HOME')
        failed_detail = request.POST.get('failed_detail', '').strip()
        event_date = request.POST.get('event_date', '')
        event_time = request.POST.get('event_time', '')

        raw_files = request.FILES.getlist('pod_image') or ([request.FILES['pod_image']] if 'pod_image' in request.FILES else [])
        if not raw_files:
            raw_files = request.FILES.getlist('failed_image_upload') or ([request.FILES['failed_image_upload']] if 'failed_image_upload' in request.FILES else [])

        occurred_at = timezone.now()
        if event_date and event_time:
            try:
                dt_str = f"{event_date} {event_time}"
                occurred_at = timezone.make_aware(datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M'))
            except Exception:
                pass

        if not scanned_items:
            messages.error(request, 'Pilih atau scan minimal satu No. RTO / Resi AWB.')
            return redirect('operations:return-redeliver-scan')

        from apps.operations.views import process_pod_uploaded_file

        success_count = 0
        processed_shipment_ids = set()

        for item_code in scanned_items:
            rto_obj = ReturnShipment.objects.filter(rto_number=item_code).select_related('shipment').first()
            if rto_obj and rto_obj.shipment:
                shipment = rto_obj.shipment
            else:
                shipment = Shipment.objects.filter(resi_number=item_code).first()
                if not shipment:
                    rto_obj = ReturnShipment.objects.filter(rto_number__icontains=item_code).select_related('shipment').first()
                    if rto_obj:
                        shipment = rto_obj.shipment

            if not shipment or shipment.id in processed_shipment_ids:
                continue

            processed_shipment_ids.add(shipment.id)
            loc = location or shipment.destination or shipment.receiver_city or 'Hub Tujuan'

            if delivery_outcome == 'FAILED':
                # Gagal Antar Lagi
                shipment.status = 'DELIVERY_FAILED'
                shipment.delivery_attempts = (shipment.delivery_attempts or 0) + 1
                shipment.failed_reason = failed_reason
                shipment.failed_note = failed_detail
                shipment.failed_date = occurred_at

                if raw_files:
                    proc_f, m_type = process_pod_uploaded_file(raw_files[0])
                    if proc_f:
                        shipment.failed_image = proc_f
                shipment.save()

                # Update RTO record back to HOLD_DESTINATION
                active_rto = ReturnShipment.objects.filter(shipment=shipment).exclude(status='CANCELLED_REDELIVERED').first()
                if active_rto:
                    active_rto.status = 'HOLD_DESTINATION'
                    active_rto.action_type = 'PENDING'
                    active_rto.attempt_count = shipment.delivery_attempts
                    active_rto.reason_detail = (active_rto.reason_detail or '') + f"\n[Re-Delivery Gagal #{shipment.delivery_attempts}]: {failed_detail}"
                    active_rto.save()

                reason_label = dict(ReturnShipment.REASON_CHOICES).get(failed_reason, failed_reason)
                Tracking.objects.create(
                    shipment=shipment,
                    status='DELIVERY_FAILED',
                    location=loc,
                    description=f"Gagal Antar Re-Delivery (Percobaan #{shipment.delivery_attempts}): {reason_label}. {failed_detail}".strip(),
                    occurred_at=occurred_at
                )
                success_count += 1

            else:
                # Sukses POD (Delivered)
                shipment.status = 'POD'
                shipment.pod_receiver_name = pod_receiver_name
                shipment.pod_date = occurred_at

                primary_image_set = False
                for f in raw_files[:5]:
                    proc_f, m_type = process_pod_uploaded_file(f)
                    if proc_f and m_type:
                        att = PODAttachment.objects.create(
                            shipment=shipment,
                            file=proc_f,
                            media_type=m_type
                        )
                        if not primary_image_set and m_type == 'IMAGE':
                            shipment.pod_image = att.file
                            primary_image_set = True

                shipment.save()

                # Tandai RTO selesai (Kirim Ulang Berhasil)
                ReturnShipment.objects.filter(
                    shipment=shipment
                ).exclude(status='RETURNED_TO_SHIPPER').update(status='CANCELLED_REDELIVERED')

                Tracking.objects.create(
                    shipment=shipment,
                    status='POD',
                    location=loc,
                    description=f"Penerima: {pod_receiver_name} | {description}" if description else f"Penerima: {pod_receiver_name}",
                    occurred_at=occurred_at
                )
                success_count += 1

        if delivery_outcome == 'FAILED':
            messages.warning(request, f'Re-Delivery gagal dicatat untuk {success_count} resi. Data dialihkan kembali ke Tab Laporan Masuk.')
            return redirect('operations:return-list')
        else:
            messages.success(request, f'Berhasil menyelesaikan Re-Delivery untuk {success_count} resi dengan status POD (Terkirim). Data dipindahkan ke Riwayat Selesai.')
            return redirect('/operations/returns/?tab=selesai')

    # Preload object if provided in GET params
    preloaded_rto_item = None
    if preload_rto:
        preloaded_rto_item = ReturnShipment.objects.filter(rto_number__iexact=preload_rto).select_related('shipment').first()
    elif preload_resi:
        preloaded_rto_item = ReturnShipment.objects.filter(shipment__resi_number__iexact=preload_resi).select_related('shipment').first()

    return render(request, 'operations/returns/redeliver_scan_form.html', {
        'reason_choices': ReturnShipment.REASON_CHOICES,
        'event_date': timezone.localtime().strftime('%Y-%m-%d'),
        'event_time': timezone.localtime().strftime('%H:%M'),
        'preloaded_item': preloaded_rto_item,
    })
