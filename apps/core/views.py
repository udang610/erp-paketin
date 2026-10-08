from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.core.mixins import has_module_access, is_branch_scoped, get_user_branch
from django.db.models import Q

@login_required
def dashboard(request):
    filter_param = request.GET.get('filter', 'semua')
    from django.utils import timezone
    now = timezone.now()

    branch_scoped = is_branch_scoped(request.user)
    user_branch = get_user_branch(request.user) if branch_scoped else None

    def apply_filter(qs, date_field):
        # Apply custom date range if provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            return qs.filter(**{f"{date_field}__range": [start_date, end_date]})
            
        # Otherwise fallback to the pill filter
        if filter_param == 'bulan_ini':
            return qs.filter(**{f"{date_field}__month": now.month, f"{date_field}__year": now.year})
        elif filter_param == 'tahun_ini':
            return qs.filter(**{f"{date_field}__year": now.year})
        return qs

    crm_clients = crm_leads = crm_quotations = 0
    if request.user.is_superuser or has_module_access(request.user, 'can_access_crm') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.crm.models import Client, Lead, Quotation
        client_qs = Client.objects.all()
        lead_qs = Lead.objects.all()
        quot_qs = Quotation.objects.all()
        if user_branch:
            client_qs = client_qs.filter(owner__employee_profile__branch=user_branch)
            lead_qs = lead_qs.filter(owner__employee_profile__branch=user_branch)
            quot_qs = quot_qs.filter(lead__owner__employee_profile__branch=user_branch)
        crm_clients = apply_filter(client_qs, 'created_at').count()
        crm_leads = apply_filter(lead_qs, 'created_at').count()
        crm_quotations = apply_filter(quot_qs, 'created_at').count()

    # Finance Data (Diambil dari Invoicing yang sudah Lunas / PAID)
    finance_records = total_revenue = 0
    chart_revenue = [0] * 12
    chart_profit = [0] * 12
    filtered_paid_inv = None
    if request.user.is_superuser or has_module_access(request.user, 'can_access_finance') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.finance.models import Invoice, KpiFinance
        from django.db.models import Sum, Q
        from django.db.models.functions import ExtractMonth
        from datetime import datetime

        current_year = datetime.now().year
        paid_inv_qs = Invoice.objects.filter(status='PAID')
        if user_branch:
            paid_inv_qs = paid_inv_qs.filter(
                Q(shipments__created_by__employee_profile__branch=user_branch) |
                Q(ldps__branch=user_branch)
            ).distinct()

        filtered_paid_inv = apply_filter(paid_inv_qs, 'date_issued')
        finance_records = filtered_paid_inv.count()
        total_revenue = filtered_paid_inv.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        monthly_data = list(paid_inv_qs.filter(date_issued__year=current_year)
            .annotate(month=ExtractMonth('date_issued'))
            .values('month')
            .annotate(total_revenue=Sum('total_amount'))
            .order_by('month'))

        for item in monthly_data:
            if item['month']:
                idx = int(item['month']) - 1
                chart_revenue[idx] = float(item['total_revenue'] or 0)

        paid_inv_ids = list(paid_inv_qs.values_list('id', flat=True))
        if paid_inv_ids:
            monthly_profit_data = list(KpiFinance.objects.filter(
                Q(linked_invoice_id__in=paid_inv_ids) | Q(shipment__invoices__id__in=paid_inv_ids),
                tanggal_pickup__year=current_year
            ).annotate(month=ExtractMonth('tanggal_pickup'))
            .values('month')
            .annotate(total_profit=Sum('profit'))
            .order_by('month'))

            for item in monthly_profit_data:
                if item['month']:
                    idx = int(item['month']) - 1
                    chart_profit[idx] = float(item['total_profit'] or 0)

    hr_employees = hr_attendances = hr_present = hr_absent = 0
    if request.user.is_superuser or has_module_access(request.user, 'can_access_hr') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.employees.models import Employee
        from apps.hr.attendance.models import AttendanceEvent
        emp_qs = Employee.objects.filter(user__is_active=True)
        att_qs = AttendanceEvent.objects.all()
        if user_branch:
            emp_qs = emp_qs.filter(branch=user_branch)
            att_qs = att_qs.filter(employee__branch=user_branch)
        hr_employees = emp_qs.count()
        today = now.date()
        hr_attendances = apply_filter(att_qs, 'created_at').count()
        hr_present = att_qs.filter(event_type='CHECK_IN', created_at__date=today).values('employee').distinct().count()
        hr_absent = max(0, hr_employees - hr_present)

    # Operations Data
    ops_total = ops_pending = ops_in_transit = ops_delivered = 0
    ops_transfer = ops_transit = 0
    active_routes = []
    map_status_choices = []
    map_origin_choices = []
    map_destination_choices = []
    map_service_choices = []
    action_alerts = []
    if request.user.is_superuser or has_module_access(request.user, 'can_access_operations') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.operations.models import Shipment
        from datetime import timedelta
        map_status_choices = Shipment.STATUS_CHOICES
        ops_shipments = Shipment.objects.filter(is_hidden=False)
        if user_branch:
            branch_term = user_branch.name or ''
            ops_shipments = ops_shipments.filter(
                Q(created_by__employee_profile__branch=user_branch) |
                Q(origin__icontains=branch_term) |
                Q(sender_city__icontains=branch_term)
            )
        from apps.master.display import clean_city_name, city_display_name
        from apps.master.models import Coverage

        distinct_origins = list(ops_shipments.values_list('origin', flat=True).exclude(origin__isnull=True).exclude(origin='').distinct())
        distinct_destinations = list(ops_shipments.values_list('destination', flat=True).exclude(destination__isnull=True).exclude(destination='').distinct())

        map_origin_choices = []
        for orig in distinct_origins:
            search_city = clean_city_name(orig)
            cov = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            tlc = cov.tlc.upper() if (cov and cov.tlc) else search_city[:3].upper()
            disp_city = city_display_name(orig)
            map_origin_choices.append((orig, f"{tlc} - {disp_city}"))
        map_origin_choices.sort(key=lambda x: x[1])

        map_destination_choices = []
        for dest in distinct_destinations:
            search_city = clean_city_name(dest)
            cov = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            tlc = cov.tlc.upper() if (cov and cov.tlc) else search_city[:3].upper()
            disp_city = city_display_name(dest)
            map_destination_choices.append((dest, f"{tlc} - {disp_city}"))
        map_destination_choices.sort(key=lambda x: x[1])
        map_service_choices = Shipment.SERVICE_CHOICES
        base_ops = apply_filter(ops_shipments, 'created_at')
        ops_total = base_ops.count()
        ops_pending = base_ops.filter(status='PENDING').count()
        ops_transfer = base_ops.filter(status='TRANSFER').count()
        ops_transit = base_ops.filter(status='TRANSIT').count()
        transit_statuses = ['OUTGOING', 'TRANSFER', 'TRANSIT', 'INCOMING_DESTINATION', 'DELIVERY']
        ops_in_transit = base_ops.filter(status__in=transit_statuses).count()
        ops_delivered = base_ops.filter(status__in=['POD', 'POD_BALIK']).count()

        pending_count = base_ops.filter(status='PENDING').count()
        transit_aging_count = base_ops.filter(
            status='TRANSIT', updated_at__lt=now - timedelta(hours=48)
        ).count()
        incoming_count = base_ops.filter(status='INCOMING_DESTINATION').count()
        transfer_count = base_ops.filter(status='TRANSFER').count()
        action_alerts = [
            {'key': 'pending', 'label': 'Shipment menunggu proses', 'description': 'Periksa resi yang belum masuk alur operasional.', 'count': pending_count, 'tone': 'warning', 'icon': 'ph-hourglass-medium', 'url': '/operations/shipments/?status=PENDING'},
            {'key': 'transit-aging', 'label': 'Transit lebih dari 48 jam', 'description': 'Pastikan status dan lokasi terakhir sudah diperbarui.', 'count': transit_aging_count, 'tone': 'danger', 'icon': 'ph-warning-circle', 'url': '/operations/shipments/?status=TRANSIT'},
            {'key': 'incoming', 'label': 'Menunggu incoming destination', 'description': 'Resi siap diproses oleh hub tujuan.', 'count': incoming_count, 'tone': 'info', 'icon': 'ph-map-pin-line', 'url': '/operations/shipments/?status=INCOMING_DESTINATION'},
            {'key': 'transfer', 'label': 'Transfer location aktif', 'description': 'Pantau perpindahan antar lokasi dan hub.', 'count': transfer_count, 'tone': 'neutral', 'icon': 'ph-arrows-left-right', 'url': '/operations/shipments/?status=TRANSFER'},
        ]
        action_alerts = [item for item in action_alerts if item['count']]
        
        # Aggregate active routes for the map (Filtered by base_ops)
        map_status = request.GET.get('map_status', '').strip()
        map_origin = request.GET.get('map_origin', '').strip()
        map_destination = request.GET.get('map_destination', '').strip()
        map_service = request.GET.get('map_service', '').strip()
        map_start_date = request.GET.get('map_start_date', '').strip()
        map_end_date = request.GET.get('map_end_date', '').strip()

        if map_status:
            active_shipments = base_ops.exclude(status='VOID').filter(status=map_status)
        else:
            active_shipments = base_ops.exclude(status__in=['POD', 'POD_BALIK', 'RETURNED', 'VOID'])

        if map_origin:
            active_shipments = active_shipments.filter(Q(origin__iexact=map_origin) | Q(sender_city__iexact=map_origin))
        if map_destination:
            active_shipments = active_shipments.filter(Q(destination__iexact=map_destination) | Q(receiver_city__iexact=map_destination))
        if map_service:
            active_shipments = active_shipments.filter(service_type=map_service)
        if map_start_date and map_end_date:
            active_shipments = active_shipments.filter(created_at__date__range=[map_start_date, map_end_date])
        elif map_start_date:
            active_shipments = active_shipments.filter(created_at__date__gte=map_start_date)
        elif map_end_date:
            active_shipments = active_shipments.filter(created_at__date__lte=map_end_date)

        # Formatted labels for filter badge display (with TLC and Area Name)
        map_origin_label = dict(map_origin_choices).get(map_origin, '')
        if not map_origin_label and map_origin:
            search_city = clean_city_name(map_origin)
            cov = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            tlc = cov.tlc.upper() if (cov and cov.tlc) else search_city[:3].upper()
            map_origin_label = f"{tlc} - {city_display_name(map_origin)}"

        map_destination_label = dict(map_destination_choices).get(map_destination, '')
        if not map_destination_label and map_destination:
            search_city = clean_city_name(map_destination)
            cov = Coverage.objects.filter(city__icontains=search_city).exclude(tlc__isnull=True).exclude(tlc__exact='').first()
            tlc = cov.tlc.upper() if (cov and cov.tlc) else search_city[:3].upper()
            map_destination_label = f"{tlc} - {city_display_name(map_destination)}"

        map_start_date_display = ''
        if map_start_date:
            try:
                from datetime import datetime as dt
                map_start_date_display = dt.strptime(map_start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                map_start_date_display = map_start_date

        map_end_date_display = ''
        if map_end_date:
            try:
                from datetime import datetime as dt
                map_end_date_display = dt.strptime(map_end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                map_end_date_display = map_end_date
        
        from apps.core.geo_utils import get_coordinates_for_location
        routes_dict = {}
        for s in active_shipments.select_related('client'):
            origin_name = s.get_city_origin
            destination_name = s.get_city_dest
            key = f"{origin_name}-{destination_name}-{s.status}"
            if key not in routes_dict:
                routes_dict[key] = {
                    'origin': origin_name,
                    'destination': destination_name,
                    'origin_label': f"{s.get_tlc_origin} - {origin_name}",
                    'destination_label': f"{s.get_tlc_dest} - {destination_name}",
                    'origin_coords': get_coordinates_for_location(origin_name, s.get_tlc_origin),
                    'dest_coords': get_coordinates_for_location(destination_name, s.get_tlc_dest),
                    'status': s.status,
                    'status_display': s.get_status_display() if hasattr(s, 'get_status_display') else s.status,
                    'count': 0,
                    'resis': [],
                }
            routes_dict[key]['count'] += 1
            if len(routes_dict[key]['resis']) < 25:
                routes_dict[key]['resis'].append({
                    'resi_number': s.resi_number,
                    'pk': s.pk,
                    'service': s.get_service_type_display() if hasattr(s, 'get_service_type_display') else (s.service_type or 'REG'),
                    'sender': s.sender_name or (s.client.name if s.client else '-'),
                    'receiver': s.receiver_name or '-',
                    'colly': s.total_colly or 1,
                    'weight': float(s.weight or s.chargeable_weight or 0),
                })
            
        active_routes = list(routes_dict.values())
        
        # Additional Operations Analytics
        ops_returned = base_ops.filter(status='RETURNED').count()
        import json
        
        # Deliveries by region (top destination) - All valid shipments
        dest_counts = {}
        for s in base_ops.exclude(status='VOID'):
            city = (s.get_city_dest or s.destination or '').strip()
            if city:
                dest_counts[city] = dest_counts.get(city, 0) + 1

        sorted_dest = sorted(dest_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        deliveries_region_labels = json.dumps([x[0] for x in sorted_dest])
        deliveries_region_data = json.dumps([x[1] for x in sorted_dest])
        
        # Total shipment by customer (top clients - registered master customers only)
        client_counts = {}
        for s in base_ops.exclude(status='VOID').filter(client__isnull=False).select_related('client'):
            if s.client:
                c_name = (getattr(s.client, 'name', None) or str(s.client)).strip()
                if c_name:
                    client_counts[c_name] = client_counts.get(c_name, 0) + 1

        sorted_clients = sorted(client_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        top_clients_labels = json.dumps([x[0] for x in sorted_clients])
        top_clients_data = json.dumps([x[1] for x in sorted_clients])

        # Complete Status Breakdown for Operations Module
        ops_status_map = {
            'PENDING': 'Menunggu',
            'PICKUP': 'Pick Up',
            'INBOUND': 'Inbound Hub',
            'OUTGOING': 'Outgoing',
            'TRANSFER': 'Transfer Loc.',
            'TRANSIT': 'Transit',
            'INCOMING_DESTINATION': 'Incoming Dest.',
            'DELIVERY': 'Delivery',
            'POD': 'POD Terkirim',
            'RETURNED': 'Retur',
        }
        ops_detailed_status_labels = []
        ops_detailed_status_data = []
        for code, label in ops_status_map.items():
            cnt = base_ops.filter(status=code).count()
            ops_detailed_status_labels.append(label)
            ops_detailed_status_data.append(cnt)

        # Service Types Breakdown
        service_counts = {}
        for s in base_ops.exclude(status='VOID'):
            stype = s.service_type or 'REGULER'
            service_counts[stype] = service_counts.get(stype, 0) + 1
        ops_service_labels = list(service_counts.keys())
        ops_service_data = list(service_counts.values())

        # Manifest breakdown
        from apps.operations.models import Manifest
        m_qs = apply_filter(Manifest.objects.all(), 'created_at')
        if user_branch:
            m_qs = m_qs.filter(origin_branch=user_branch)
        ops_manifest_outgoing = m_qs.filter(manifest_type='OUTGOING').count()
        ops_manifest_transfer = m_qs.filter(manifest_type='TRANSFER').count()
        ops_manifest_delivery = m_qs.filter(manifest_type='DELIVERY').count()
        ops_manifest_labels = ['Outgoing', 'Transfer Location', 'Delivery']
        ops_manifest_data = [ops_manifest_outgoing, ops_manifest_transfer, ops_manifest_delivery]

        ops_pod_rate = round((ops_delivered / ops_total * 100), 1) if ops_total > 0 else 0

    # CRM breakdown
    crm_leads_new = crm_leads_won = crm_leads_lost = 0
    crm_leads_contacted = crm_leads_qualified = crm_leads_proposal = crm_leads_negotiation = 0
    crm_activity_labels = []
    crm_activity_data = []
    crm_act_type_labels = []
    crm_act_type_data = []
    crm_quotation_status_labels = ['Draft', 'Terkirim', 'Disetujui', 'Ditolak']
    crm_quotation_status_data = [0, 0, 0, 0]
    crm_lead_pipeline_labels = ['Baru', 'Dihubungi', 'Kualifikasi', 'Proposal', 'Negosiasi', 'Won', 'Lost']
    crm_lead_pipeline_data = [0] * 7
    crm_total_pipeline_val = 0
    crm_total_won_val = 0

    if request.user.is_superuser or has_module_access(request.user, 'can_access_crm') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.crm.models import Lead, Activity, Quotation
        from django.db.models import Count, Sum
        base_leads = apply_filter(Lead.objects.all(), 'created_at')
        base_activities = apply_filter(Activity.objects.all(), 'created_at')
        base_quotations = apply_filter(Quotation.objects.all(), 'created_at')
        
        crm_leads_new = base_leads.filter(status__iexact='NEW').count()
        crm_leads_contacted = base_leads.filter(status__iexact='CONTACTED').count()
        crm_leads_qualified = base_leads.filter(status__iexact='QUALIFIED').count()
        crm_leads_proposal = base_leads.filter(status__iexact='PROPOSAL').count()
        crm_leads_negotiation = base_leads.filter(status__iexact='NEGOTIATION').count()
        crm_leads_won = base_leads.filter(status__iexact='WON').count()
        crm_leads_lost = base_leads.filter(status__iexact='LOST').count()

        crm_lead_pipeline_data = [
            crm_leads_new, crm_leads_contacted, crm_leads_qualified,
            crm_leads_proposal, crm_leads_negotiation, crm_leads_won, crm_leads_lost
        ]

        # Activity by Sales PIC
        activity_qs = base_activities.values(
            'owner__first_name', 'owner__last_name', 'owner__username', 'owner__email'
        ).annotate(total=Count('id')).order_by('-total')[:6]
        
        for r in activity_qs:
            name = f"{r.get('owner__first_name', '')} {r.get('owner__last_name', '')}".strip()
            if not name:
                name = r.get('owner__username') or (r.get('owner__email', '').split('@')[0] if r.get('owner__email') else 'Sales')
            crm_activity_labels.append(name)
            crm_activity_data.append(r['total'])

        # Activity by Type (Telepon, WhatsApp, Visit, Meeting, Email)
        activity_type_dict = {
            'CALL': 'Telepon',
            'WHATSAPP': 'WhatsApp',
            'VISIT': 'Kunjungan (Visit)',
            'MEETING': 'Meeting',
            'EMAIL': 'Email',
        }
        act_type_qs = base_activities.values('activity_type').annotate(total=Count('id')).order_by('-total')
        for r in act_type_qs:
            crm_act_type_labels.append(activity_type_dict.get(r['activity_type'], r['activity_type']))
            crm_act_type_data.append(r['total'])

        # Quotations breakdown
        q_draft = base_quotations.filter(status__iexact='DRAFT').count()
        q_sent = base_quotations.filter(status__iexact='SENT').count()
        q_appr = base_quotations.filter(status__iexact='APPROVED').count()
        q_rej = base_quotations.filter(status__iexact='REJECTED').count()
        crm_quotation_status_data = [q_draft, q_sent, q_appr, q_rej]

        crm_total_pipeline_val = base_leads.exclude(status__in=['WON', 'LOST']).aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0
        crm_total_won_val = base_leads.filter(status='WON').aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0

    # Finance Deep Dive Data
    fin_invoices_paid = fin_invoices_sent = fin_invoices_draft = fin_invoices_partial = 0
    fin_margin_monthly = [0] * 12
    fin_top_clients_labels = []
    fin_top_clients_data = []
    if request.user.is_superuser or has_module_access(request.user, 'can_access_finance') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.finance.models import Invoice, KpiFinance
        inv_qs = apply_filter(Invoice.objects.all(), 'date_issued')
        fin_invoices_paid = inv_qs.filter(status='PAID').count()
        fin_invoices_sent = inv_qs.filter(status='SENT').count()
        fin_invoices_draft = inv_qs.filter(status='DRAFT').count()
        fin_invoices_partial = inv_qs.filter(status='PARTIAL').count()

        for m in range(12):
            rev = chart_revenue[m]
            prof = chart_profit[m]
            fin_margin_monthly[m] = round((prof / rev * 100), 1) if rev > 0 else 0

        # Top clients by revenue (from paid invoices)
        if filtered_paid_inv is not None:
            fin_top_qs = filtered_paid_inv.values('client_name').annotate(
                total_rev=Sum('total_amount')
            ).exclude(client_name__isnull=True).exclude(client_name='').order_by('-total_rev')[:5]
            for item in fin_top_qs:
                fin_top_clients_labels.append(item['client_name'])
                fin_top_clients_data.append(float(item['total_rev'] or 0))

    # HR & GA Deep Dive Data
    hr_dept_labels = []
    hr_dept_data = []
    hr_attendance_rate = 0
    hr_status_labels = ['Hadir', 'Terlambat', 'Izin / Cuti', 'Alpa']
    hr_status_data = [0, 0, 0, 0]
    if request.user.is_superuser or has_module_access(request.user, 'can_access_hr') or has_module_access(request.user, 'can_access_monitoring'):
        from apps.employees.models import Employee
        from apps.hr.attendance.models import AttendanceEvent, AttendanceStatus
        from django.db.models import Count
        dept_qs = Employee.objects.filter(user__is_active=True).values('branch__name').annotate(total=Count('id')).order_by('-total')[:6]
        for d in dept_qs:
            bname = d['branch__name'] or 'Pusat'
            hr_dept_labels.append(bname)
            hr_dept_data.append(d['total'])
        hr_attendance_rate = round((hr_present / hr_employees * 100), 1) if hr_employees > 0 else 0

        # Today Attendance Status breakdown
        att_today_qs = AttendanceEvent.objects.filter(server_timestamp__date=now.date())
        att_hadir = att_today_qs.filter(status=AttendanceStatus.PRESENT).count()
        att_late = att_today_qs.filter(status=AttendanceStatus.LATE).count()
        att_leave = att_today_qs.filter(status__in=[AttendanceStatus.PERMISSION, AttendanceStatus.LEAVE, AttendanceStatus.SICK]).count()
        att_alpa = att_today_qs.filter(status=AttendanceStatus.ABSENT).count()
        if (att_hadir + att_late + att_leave + att_alpa) == 0:
            att_hadir = hr_present
            att_alpa = max(0, hr_employees - hr_present)
        hr_status_data = [att_hadir, att_late, att_leave, att_alpa]

    # Vendor Management (VM) Data
    vm_total_vendors = 0
    vm_active_vendors = 0
    vm_inactive_vendors = 0
    vm_avg_top = 0
    vm_total_vendor_cost = 0
    vm_transport_labels = ['Darat', 'Laut', 'Udara', 'Kereta']
    vm_transport_data = [0, 0, 0, 0]
    vm_delivery_labels = []
    vm_delivery_data = []
    vm_top_cost_labels = []
    vm_top_cost_data = []
    vm_city_labels = []
    vm_city_data = []

    has_vm = request.user.is_superuser or has_module_access(request.user, 'can_access_vm') or has_module_access(request.user, 'can_access_monitoring')
    if has_vm:
        from apps.finance.models import Vendor, TransactionVendorCost
        from django.db.models import Avg, Sum, Count
        vendor_qs = Vendor.objects.all()
        if user_branch:
            vendor_qs = vendor_qs.filter(branch=user_branch)
        
        vm_total_vendors = vendor_qs.count()
        vm_active_vendors = vendor_qs.filter(is_active=True).count()
        vm_inactive_vendors = vendor_qs.filter(is_active=False).count()
        avg_top_val = vendor_qs.filter(payment_term_days__gt=0).aggregate(Avg('payment_term_days'))['payment_term_days__avg']
        vm_avg_top = round(avg_top_val or 0, 1)

        # Transport Modes
        darat_cnt = vendor_qs.filter(provided_darat=True).count()
        laut_cnt = vendor_qs.filter(provided_laut=True).count()
        udara_cnt = vendor_qs.filter(provided_udara=True).count()
        kereta_cnt = vendor_qs.filter(provided_kereta=True).count()
        if (darat_cnt + laut_cnt + udara_cnt + kereta_cnt) == 0 and vm_total_vendors > 0:
            # Fallback by primary_transport_mode
            darat_cnt = vendor_qs.filter(primary_transport_mode='DARAT').count()
            laut_cnt = vendor_qs.filter(primary_transport_mode='LAUT').count()
            udara_cnt = vendor_qs.filter(primary_transport_mode='UDARA').count()
            kereta_cnt = vendor_qs.filter(primary_transport_mode='KERETA').count()
        vm_transport_data = [darat_cnt, laut_cnt, udara_cnt, kereta_cnt]

        # Delivery Type Breakdown
        deliv_qs = vendor_qs.values('delivery_type').annotate(total=Count('id')).exclude(delivery_type__isnull=True).exclude(delivery_type='').order_by('-total')
        for d in deliv_qs:
            vm_delivery_labels.append(d['delivery_type'])
            vm_delivery_data.append(d['total'])

        # Top 5 Vendors by Total Cost
        top_v_qs = TransactionVendorCost.objects.values('vendor__name').annotate(
            total_cost=Sum('cost')
        ).exclude(vendor__name__isnull=True).order_by('-total_cost')[:5]
        for v in top_v_qs:
            vm_top_cost_labels.append(v['vendor__name'])
            vm_top_cost_data.append(float(v['total_cost'] or 0))
        
        cost_sum = TransactionVendorCost.objects.aggregate(Sum('cost'))['cost__sum']
        vm_total_vendor_cost = cost_sum or 0

        # Top Cities
        city_qs = vendor_qs.values('city').annotate(total=Count('id')).exclude(city__isnull=True).exclude(city='').order_by('-total')[:5]
        for c in city_qs:
            vm_city_labels.append(c['city'])
            vm_city_data.append(c['total'])

    # Check if user has single or multiple roles (for UI layout)
    is_superuser = request.user.is_superuser
    has_monitoring = has_module_access(request.user, 'can_access_monitoring')
    has_crm = has_module_access(request.user, 'can_access_crm') or has_monitoring
    has_ops = has_module_access(request.user, 'can_access_operations') or has_monitoring
    has_fin = has_module_access(request.user, 'can_access_finance') or has_monitoring
    has_hr = has_module_access(request.user, 'can_access_hr') or has_monitoring
    has_vm = has_module_access(request.user, 'can_access_vm') or has_monitoring
    
    roles_count = sum([has_crm, has_ops, has_fin, has_hr, has_vm])
    is_single_role = not is_superuser and not has_monitoring and roles_count == 1
    
    total_profit_current = 0
    fin_margin_pct = 0
    if finance_records > 0 and filtered_paid_inv is not None:
        filtered_inv_ids = list(filtered_paid_inv.values_list('id', flat=True))
        if filtered_inv_ids:
            from apps.finance.models import KpiFinance
            total_profit_current = KpiFinance.objects.filter(
                Q(linked_invoice_id__in=filtered_inv_ids) | Q(shipment__invoices__id__in=filtered_inv_ids)
            ).distinct().aggregate(Sum('profit'))['profit__sum'] or 0
        if total_revenue > 0:
            fin_margin_pct = round((float(total_profit_current) / float(total_revenue) * 100), 1)

    import json
    context = {
        'crm_clients': crm_clients,
        'crm_leads': crm_leads,
        'crm_quotations': crm_quotations,
        'crm_leads_new': crm_leads_new,
        'crm_leads_contacted': crm_leads_contacted,
        'crm_leads_qualified': crm_leads_qualified,
        'crm_leads_proposal': crm_leads_proposal,
        'crm_leads_negotiation': crm_leads_negotiation,
        'crm_leads_won': crm_leads_won,
        'crm_leads_lost': crm_leads_lost,
        'crm_lead_pipeline_labels': json.dumps(crm_lead_pipeline_labels),
        'crm_lead_pipeline_data': json.dumps(crm_lead_pipeline_data),
        'crm_activity_labels': json.dumps(crm_activity_labels),
        'crm_activity_data': json.dumps(crm_activity_data),
        'crm_act_type_labels': json.dumps(crm_act_type_labels),
        'crm_act_type_data': json.dumps(crm_act_type_data),
        'crm_quotation_status_labels': json.dumps(crm_quotation_status_labels),
        'crm_quotation_status_data': json.dumps(crm_quotation_status_data),
        'crm_total_pipeline_val': crm_total_pipeline_val,
        'crm_total_won_val': crm_total_won_val,
        'finance_records': finance_records,
        'total_revenue': total_revenue,
        'total_profit': total_profit_current,
        'fin_margin_pct': fin_margin_pct,
        'chart_revenue': chart_revenue,
        'chart_profit': chart_profit,
        'fin_margin_monthly': json.dumps(fin_margin_monthly),
        'fin_invoices_paid': fin_invoices_paid,
        'fin_invoices_sent': fin_invoices_sent,
        'fin_invoices_draft': fin_invoices_draft,
        'fin_invoices_partial': fin_invoices_partial,
        'fin_top_clients_labels': json.dumps(fin_top_clients_labels),
        'fin_top_clients_data': json.dumps(fin_top_clients_data),
        'hr_employees': hr_employees,
        'hr_attendances': hr_attendances,
        'hr_present': hr_present,
        'hr_absent': hr_absent,
        'hr_attendance_rate': hr_attendance_rate,
        'hr_status_labels': json.dumps(hr_status_labels),
        'hr_status_data': json.dumps(hr_status_data),
        'hr_dept_labels': json.dumps(hr_dept_labels),
        'hr_dept_data': json.dumps(hr_dept_data),
        'vm_total_vendors': vm_total_vendors,
        'vm_active_vendors': vm_active_vendors,
        'vm_inactive_vendors': vm_inactive_vendors,
        'vm_avg_top': vm_avg_top,
        'vm_total_vendor_cost': vm_total_vendor_cost,
        'vm_transport_labels': json.dumps(vm_transport_labels),
        'vm_transport_data': json.dumps(vm_transport_data),
        'vm_delivery_labels': json.dumps(vm_delivery_labels),
        'vm_delivery_data': json.dumps(vm_delivery_data),
        'vm_top_cost_labels': json.dumps(vm_top_cost_labels),
        'vm_top_cost_data': json.dumps(vm_top_cost_data),
        'vm_city_labels': json.dumps(vm_city_labels),
        'vm_city_data': json.dumps(vm_city_data),
        'ops_total': ops_total,
        'ops_pending': ops_pending,
        'ops_in_transit': ops_in_transit,
        'ops_delivered': ops_delivered,
        'ops_transfer': ops_transfer,
        'ops_transit': ops_transit,
        'ops_pod_rate': ops_pod_rate,
        'ops_detailed_status_labels': json.dumps(locals().get('ops_detailed_status_labels', [])),
        'ops_detailed_status_data': json.dumps(locals().get('ops_detailed_status_data', [])),
        'ops_service_labels': json.dumps(locals().get('ops_service_labels', [])),
        'ops_service_data': json.dumps(locals().get('ops_service_data', [])),
        'ops_manifest_labels': json.dumps(locals().get('ops_manifest_labels', [])),
        'ops_manifest_data': json.dumps(locals().get('ops_manifest_data', [])),
        'ops_returned': locals().get('ops_returned', 0),
        'deliveries_region_labels': locals().get('deliveries_region_labels', '[]'),
        'deliveries_region_data': locals().get('deliveries_region_data', '[]'),
        'top_clients_labels': locals().get('top_clients_labels', '[]'),
        'top_clients_data': locals().get('top_clients_data', '[]'),
        'is_single_role': is_single_role,
        'is_superuser': is_superuser,
        'has_monitoring': has_monitoring,
        'has_crm': has_crm,
        'has_ops': has_ops,
        'has_fin': has_fin,
        'has_hr': has_hr,
        'has_vm': has_vm,
        'active_routes_json': json.dumps(active_routes),
        'active_route_count': len(active_routes),
        'map_status': request.GET.get('map_status', ''),
        'map_origin': request.GET.get('map_origin', ''),
        'map_origin_label': map_origin_label,
        'map_destination': request.GET.get('map_destination', ''),
        'map_destination_label': map_destination_label,
        'map_service': request.GET.get('map_service', ''),
        'map_start_date': map_start_date,
        'map_start_date_display': map_start_date_display,
        'map_end_date': map_end_date,
        'map_end_date_display': map_end_date_display,
        'map_status_choices': map_status_choices,
        'map_origin_choices': map_origin_choices,
        'map_destination_choices': map_destination_choices,
        'map_service_choices': map_service_choices,
        'action_alerts': action_alerts,
        'action_alert_count': sum(item['count'] for item in action_alerts),
    }
    return render(request, 'dashboard.html', context)
@login_required
def universal_search(request):
    q = request.GET.get('q', '').strip()
    from django.shortcuts import redirect, render
    from django.contrib import messages
    from django.db.models import Q
    from django.urls import reverse

    if not q:
        messages.warning(request, "Silakan masukkan kata kunci pencarian.")
        return redirect('dashboard')

    can_ops = request.user.is_superuser or has_module_access(request.user, 'can_access_operations') or has_module_access(request.user, 'can_access_monitoring')
    can_crm = request.user.is_superuser or has_module_access(request.user, 'can_access_crm') or has_module_access(request.user, 'can_access_monitoring')
    can_fin = request.user.is_superuser or has_module_access(request.user, 'can_access_finance') or has_module_access(request.user, 'can_access_monitoring')
    can_hr = request.user.is_superuser or has_module_access(request.user, 'can_access_hr') or has_module_access(request.user, 'can_access_monitoring')
    result_groups = []

    def add_group(label, icon, queryset, title_fn, subtitle_fn, url_fn):
        items = [
            {'title': title_fn(item), 'subtitle': subtitle_fn(item), 'url': url_fn(item)}
            for item in queryset[:8]
        ]
        if items:
            result_groups.append({'label': label, 'icon': icon, 'items': items})

    if can_ops:
        from apps.operations.models import Shipment, Manifest
        add_group('POS / Resi', 'ph-package', Shipment.objects.filter(
            Q(resi_number__icontains=q) | Q(sender_name__icontains=q) |
            Q(receiver_name__icontains=q) | Q(origin__icontains=q) |
            Q(destination__icontains=q) | Q(client__name__icontains=q)
        ).select_related('client').order_by('-created_at'),
        lambda x: x.resi_number,
        lambda x: f"{x.get_tlc_origin} - {x.get_city_origin} → {x.get_tlc_dest} - {x.get_city_dest} · {x.get_status_display()}",
        lambda x: reverse('operations:shipment-detail', kwargs={'pk': x.pk}))
        add_group('Manifest', 'ph-file-text', Manifest.objects.filter(
            Q(manifest_number__icontains=q) | Q(destination_city__icontains=q) |
            Q(description__icontains=q) | Q(shipments__resi_number__icontains=q)
        ).distinct().order_by('-created_at'),
        lambda x: x.manifest_number,
        lambda x: f"{x.get_manifest_type_display()} · {x.get_status_display()}",
        lambda x: reverse('operations:manifest-detail', kwargs={'pk': x.pk}))

    if can_crm:
        from apps.crm.models import Client, Lead, Contract, Quotation
        add_group('Klien', 'ph-buildings', Client.objects.filter(
            Q(company_name__icontains=q) | Q(contact_person__icontains=q) |
            Q(phone__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q)
        ).order_by('-created_at'), lambda x: x.company_name,
        lambda x: f"{x.contact_person} · {x.city or 'Lokasi belum diisi'}",
        lambda x: reverse('crm:client-detail', kwargs={'pk': x.pk}))
        add_group('Lead', 'ph-user-focus', Lead.objects.filter(
            Q(client__company_name__icontains=q) | Q(shipping_origin__icontains=q) |
            Q(shipping_destination__icontains=q) | Q(notes__icontains=q)
        ).select_related('client').order_by('-id'), lambda x: str(x.client),
        lambda x: f"{x.shipping_origin or '-'} → {x.shipping_destination or '-'} · {x.get_status_display()}",
        lambda x: reverse('crm:lead-detail', kwargs={'pk': x.pk}))
        add_group('Kontrak', 'ph-file-lock', Contract.objects.filter(
            Q(contract_number__icontains=q) | Q(title__icontains=q) |
            Q(client__company_name__icontains=q) | Q(description__icontains=q)
        ).select_related('client').order_by('-created_at'), lambda x: x.contract_number,
        lambda x: f"{x.title} · {x.client.company_name}",
        lambda x: reverse('crm:contract-detail', kwargs={'pk': x.pk}))
        add_group('Quotation', 'ph-file-dashed', Quotation.objects.filter(
            Q(lead__client__company_name__icontains=q) | Q(origin__icontains=q) |
            Q(destination__icontains=q) | Q(notes__icontains=q)
        ).select_related('lead__client').order_by('-created_at'), lambda x: x.quotation_number,
        lambda x: f"{x.origin or '-'} → {x.destination or '-'} · {x.get_status_display()}",
        lambda x: reverse('crm:quotation-detail', kwargs={'pk': x.pk}))

    if can_fin:
        from apps.finance.models import Invoice, Vendor
        add_group('Invoice', 'ph-receipt', Invoice.objects.filter(
            Q(invoice_number__icontains=q) | Q(client_name__icontains=q) |
            Q(kode_pelanggan__icontains=q) | Q(sales_ae__icontains=q)
        ).order_by('-created_at'), lambda x: x.invoice_number,
        lambda x: f"{x.client_name} · {x.get_status_display()}",
        lambda x: reverse('finance:invoice_detail', kwargs={'invoice_id': x.pk}))
        add_group('Vendor', 'ph-storefront', Vendor.objects.filter(
            Q(name__icontains=q) | Q(contact_person__icontains=q) |
            Q(phone__icontains=q) | Q(city__icontains=q)
        ).order_by('-id'), lambda x: x.name,
        lambda x: f"{x.contact_person or '-'} · {x.city or '-'}",
        lambda x: reverse('finance:vendor_list'))

    if can_hr:
        from apps.employees.models import Employee
        add_group('Karyawan', 'ph-identification-card', Employee.objects.filter(
            Q(full_name__icontains=q) | Q(employee_id__icontains=q) | Q(phone_number__icontains=q)
        ).order_by('full_name'), lambda x: x.full_name,
        lambda x: f"{x.employee_id} · {x.position.name if x.position else 'Posisi belum diisi'}",
        lambda x: reverse('employees:employee_update', kwargs={'pk': x.pk}))

    # Master Data Group
    from apps.master.models import Bank, Customer, Vehicle, Coverage, Service, Price
    from apps.organizations.models import Branch

    add_group('Bank', 'ph-bank', Bank.objects.filter(
        Q(code__icontains=q) | Q(name__icontains=q) | Q(account_number__icontains=q) | Q(account_name__icontains=q)
    ).order_by('name'), lambda x: f"{x.name} ({x.code})",
    lambda x: f"No. Rek: {x.account_number or '-'} · a.n {x.account_name or '-'}",
    lambda x: reverse('master:master_detail', kwargs={'model_name': 'bank', 'pk': x.pk}))

    add_group('Customer (Master)', 'ph-users-three', Customer.objects.filter(
        Q(customer_code__icontains=q) | Q(name__icontains=q) | Q(pic_account__icontains=q) | Q(pic_phone__icontains=q) | Q(city__icontains=q)
    ).order_by('name'), lambda x: f"{x.name} ({x.customer_code})",
    lambda x: f"PIC: {x.pic_account or '-'} · {x.city or '-'}",
    lambda x: reverse('master:master_detail', kwargs={'model_name': 'customer', 'pk': x.pk}))

    add_group('Cabang (Branch)', 'ph-buildings', Branch.objects.filter(
        Q(code__icontains=q) | Q(name__icontains=q) | Q(address__icontains=q)
    ).order_by('name'), lambda x: f"{x.name} ({x.code})",
    lambda x: f"{x.address or 'Alamat belum diisi'}",
    lambda x: reverse('master:master_detail', kwargs={'model_name': 'branch', 'pk': x.pk}))

    add_group('Armada (Vehicle)', 'ph-truck', Vehicle.objects.filter(
        Q(plate_number__icontains=q) | Q(vehicle_type__icontains=q) | Q(brand_model__icontains=q)
    ).order_by('plate_number'), lambda x: f"{x.plate_number} - {x.brand_model or x.vehicle_type}",
    lambda x: f"Tipe: {x.vehicle_type} · Cabang: {x.branch.name if x.branch else '-'}",
    lambda x: reverse('master:master_detail', kwargs={'model_name': 'vehicle', 'pk': x.pk}))

    add_group('Wilayah (Coverage)', 'ph-map-pin', Coverage.objects.filter(
        Q(district__icontains=q) | Q(city__icontains=q) | Q(province__icontains=q) | Q(tlc__icontains=q) | Q(postal_code__icontains=q)
    ).order_by('city', 'district'), lambda x: f"{x.district}, {x.city}",
    lambda x: f"Provinsi: {x.province} · TLC: {x.tlc or '-'} · Kode Pos: {x.postal_code or '-'}",
    lambda x: reverse('master:master_detail', kwargs={'model_name': 'coverage', 'pk': x.pk}))

    return render(request, 'search_results.html', {
        'query': q,
        'result_groups': result_groups,
        'result_count': sum(len(group['items']) for group in result_groups),
        'is_universal_search': True,
    })


@login_required
def command_palette(request):
    """Return role-aware navigation shortcuts for the Ctrl+K command palette."""
    from django.http import JsonResponse
    from django.urls import reverse

    query = request.GET.get('q', '').strip().lower()
    can_ops = request.user.is_superuser or has_module_access(request.user, 'can_access_operations') or has_module_access(request.user, 'can_access_monitoring')
    can_crm = request.user.is_superuser or has_module_access(request.user, 'can_access_crm') or has_module_access(request.user, 'can_access_monitoring')
    can_fin = request.user.is_superuser or has_module_access(request.user, 'can_access_finance') or has_module_access(request.user, 'can_access_monitoring')
    can_hr = request.user.is_superuser or has_module_access(request.user, 'can_access_hr') or has_module_access(request.user, 'can_access_monitoring')

    items = [
        {'title': 'Dasbor Utama', 'subtitle': 'Ringkasan sistem dan monitoring pengiriman', 'type': 'Navigasi', 'icon': 'ph-gauge', 'url': reverse('dashboard')},
    ]
    if can_ops:
        items.extend([
            {'title': 'Buat Resi', 'subtitle': 'Buat shipment baru dari POS', 'type': 'Operasional', 'icon': 'ph-plus-circle', 'url': reverse('operations:shipment-create')},
            {'title': 'Data Shipment', 'subtitle': 'Cari dan kelola seluruh resi', 'type': 'Operasional', 'icon': 'ph-package', 'url': reverse('operations:shipment-list')},
            {'title': 'Scan Transit', 'subtitle': 'Perbarui status transit dengan scanner', 'type': 'Operasional', 'icon': 'ph-scan', 'url': reverse('operations:scan-transit')},
            {'title': 'Pick Up', 'subtitle': 'Kelola penjemputan barang', 'type': 'Operasional', 'icon': 'ph-truck', 'url': reverse('operations:pickup-list')},
            {'title': 'Tracking Pencarian', 'subtitle': 'Lacak resi dan riwayat perjalanan', 'type': 'Operasional', 'icon': 'ph-map-pin-line', 'url': reverse('operations:tracking')},
        ])
    if can_crm:
        items.extend([
            {'title': 'Klien', 'subtitle': 'Kelola data pelanggan', 'type': 'CRM', 'icon': 'ph-buildings', 'url': reverse('crm:client-list')},
            {'title': 'Peluang (Lead)', 'subtitle': 'Kelola peluang penjualan', 'type': 'CRM', 'icon': 'ph-funnel', 'url': reverse('crm:lead-list')},
        ])
    if can_fin:
        items.append({'title': 'Invoice', 'subtitle': 'Kelola invoice dan tagihan', 'type': 'Finance', 'icon': 'ph-receipt', 'url': reverse('finance:invoice_list')})
    if can_hr:
        items.append({'title': 'Karyawan', 'subtitle': 'Kelola data karyawan', 'type': 'HR & GA', 'icon': 'ph-identification-card', 'url': reverse('employees:employee_list')})

    if query:
        items = [item for item in items if query in f"{item['title']} {item['subtitle']} {item['type']}".lower()]
    return JsonResponse({'results': items[:12]})
