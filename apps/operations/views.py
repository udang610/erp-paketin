import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime as DateTime
from .models import Shipment, Manifest, Tracking, PickupOrder
from apps.master.models import Coverage
from apps.master.display import coverage_city_label

from .forms import ShipmentForm, ManifestForm, ShipmentItemFormSet, PickupOrderForm


def is_admin_or_superadmin(user):
    """Check if user has superuser, staff, admin, or internal CS/Operational role."""
    return (
        user.is_authenticated and (
            user.is_superuser
            or user.is_staff
            or getattr(user, 'user_type', '') in ['ADMIN', 'CS', 'OPS', 'MANAGER']
            or (hasattr(user, 'roles') and user.roles.filter(name__iregex=r'(admin|cs|customer service|operasional|manager)').exists())
        )
    )


def _tracking_occurred_at(request):
    """Parse optional backdated event date/time, falling back to now."""
    event_date = request.POST.get('event_date', '').strip()
    event_time = request.POST.get('event_time', '').strip()
    if event_date and event_time:
        try:
            local_dt = DateTime.strptime(
                f'{event_date} {event_time}', '%Y-%m-%d %H:%M'
            )
            return timezone.make_aware(local_dt, timezone.get_current_timezone())
        except ValueError:
            pass
    return timezone.now()

@login_required
def pickup_list(request):
    from apps.accounts.models import User
    from apps.master.models import Vehicle
    from apps.organizations.models import Branch
    from apps.finance.models import Vendor
    from .models import Manifest, PickupOrder
    from django.db.models import Q
    
    # Filter
    search = request.GET.get('q', '').strip() or request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    driver_filter = request.GET.get('driver', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    start_date = request.GET.get('start_date', '').strip() or request.GET.get('date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    base_pickups = PickupOrder.objects.filter(is_hidden=False)
    if search:
        matched_pickups = base_pickups.filter(
            Q(pickup_number__icontains=search) | 
            Q(client__name__icontains=search) | 
            Q(pic_name__icontains=search) |
            Q(pickup_address__icontains=search)
        )
        filtered_pickups = matched_pickups
        if status_filter:
            filtered_pickups = filtered_pickups.filter(status=status_filter)
        if driver_filter:
            filtered_pickups = filtered_pickups.filter(
                Q(manifests__driver_id=driver_filter) | Q(manifests__driver__first_name__icontains=driver_filter) | Q(manifests__driver__username__icontains=driver_filter)
            )
        if branch_filter:
            filtered_pickups = filtered_pickups.filter(branch_id=branch_filter)
            
        date_filtered_pickups = filtered_pickups
        if psd:
            date_filtered_pickups = date_filtered_pickups.filter(pickup_date__gte=psd)
        if ped:
            date_filtered_pickups = date_filtered_pickups.filter(pickup_date__lte=ped)
            
        if date_filtered_pickups.exists():
            base_pickups = date_filtered_pickups
        elif filtered_pickups.exists():
            base_pickups = filtered_pickups
        else:
            base_pickups = matched_pickups
    else:
        if status_filter:
            base_pickups = base_pickups.filter(status=status_filter)
        if driver_filter:
            base_pickups = base_pickups.filter(
                Q(manifests__driver_id=driver_filter) | Q(manifests__driver__first_name__icontains=driver_filter) | Q(manifests__driver__username__icontains=driver_filter)
            )
        if branch_filter:
            base_pickups = base_pickups.filter(branch_id=branch_filter)
        if psd:
            base_pickups = base_pickups.filter(pickup_date__gte=psd)
        if ped:
            base_pickups = base_pickups.filter(pickup_date__lte=ped)
    
    # Tab 1: Menunggu Penugasan (PENDING & CANCELLED)
    if status_filter:
        pending_pickups = base_pickups.order_by('-created_at')
    else:
        pending_pickups = base_pickups.filter(status__in=['PENDING', 'CANCELLED']).order_by('-created_at')
    
    # Tab 2 & 3: Manifests
    base_manifests = Manifest.objects.filter(manifest_type='PICKUP', is_hidden=False)
    if search:
        matched_manifests = base_manifests.filter(
            Q(manifest_number__icontains=search) |
            Q(driver__first_name__icontains=search) |
            Q(driver__username__icontains=search) |
            Q(vehicle__plate_number__icontains=search)
        )
        filtered_manifests = matched_manifests
        if driver_filter:
            filtered_manifests = filtered_manifests.filter(
                Q(driver_id=driver_filter) | Q(driver__first_name__icontains=driver_filter) | Q(driver__username__icontains=driver_filter)
            )
        if status_filter:
            filtered_manifests = filtered_manifests.filter(status=status_filter)
            
        date_filtered_manifests = filtered_manifests
        if psd:
            date_filtered_manifests = date_filtered_manifests.filter(created_at__date__gte=psd)
        if ped:
            date_filtered_manifests = date_filtered_manifests.filter(created_at__date__lte=ped)
            
        if date_filtered_manifests.exists():
            base_manifests = date_filtered_manifests
        elif filtered_manifests.exists():
            base_manifests = filtered_manifests
        else:
            base_manifests = matched_manifests
    else:
        if driver_filter:
            base_manifests = base_manifests.filter(
                Q(driver_id=driver_filter) | Q(driver__first_name__icontains=driver_filter) | Q(driver__username__icontains=driver_filter)
            )
        if psd:
            base_manifests = base_manifests.filter(created_at__date__gte=psd)
        if ped:
            base_manifests = base_manifests.filter(created_at__date__lte=ped)
        if status_filter:
            base_manifests = base_manifests.filter(status=status_filter)
        
    pickup_manifests = base_manifests.exclude(status='COMPLETED').order_by('-created_at')
    pickup_runsheets = base_manifests.all().order_by('-created_at')
    history_manifests = base_manifests.filter(status='COMPLETED').order_by('-created_at')
    
    vehicle_types = [
        'Blind Van',
        'Motorcycle',
        'Cold Diesel Double',
        'Cold Diesel Engkel',
        'Container',
        'Tronton',
        'Wingbox',
    ]
    master_vehicles = Vehicle.objects.filter(is_active=True).order_by('plate_number')
    branches = Branch.objects.all().order_by('name')
    vendors = Vendor.objects.filter(is_active=True).order_by('name')
    drivers = User.objects.filter(user_type='DRIVER').order_by('first_name', 'username')
    
    # List pickup orders untuk dropdown penugasan (hanya status PENDING)
    assignable_pickups = PickupOrder.objects.filter(status='PENDING', is_hidden=False).order_by('-created_at')
    
    has_active_filter = bool(search or status_filter or driver_filter or branch_filter or start_date or end_date)
    
    return render(request, 'operations/pickups/pickup_list.html', {
        'pending_pickups': pending_pickups,
        'pickup_manifests': pickup_manifests,
        'pickup_runsheets': pickup_runsheets,
        'history_manifests': history_manifests,
        'branches': branches,
        'vendors': vendors,
        'drivers': drivers,
        'vehicle_types': vehicle_types,
        'master_vehicles': master_vehicles,
        'assignable_pickups': assignable_pickups,
        'search': search,
        'status_filter': status_filter,
        'driver_filter': driver_filter,
        'branch_filter': branch_filter,
        'start_date': start_date,
        'end_date': end_date,
        'has_active_filter': has_active_filter,
    })

@login_required
def pickup_create(request):
    from .forms import PickupOrderForm
    from django.contrib import messages
    from apps.master.models import Customer
    from django.utils import timezone
    if request.method == 'POST':
        form = PickupOrderForm(request.POST, request.FILES)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.status = 'PENDING'
            pickup.save()
            messages.success(request, f'Order Pickup berhasil dibuat dengan nomor {pickup.pickup_number}!')
            return redirect('operations:pickup-list')
    else:
        now = timezone.localtime()
        form = PickupOrderForm(initial={
            'pickup_date': now.date(),
            'pickup_time': now.strftime('%H:%M'),
        })
    
    clients = Customer.objects.filter(is_active=True).order_by('name')
    return render(request, 'operations/pickups/pickup_edit.html', {
        'form': form,
        'clients': clients,
        'is_edit': False,
    })

@login_required
def pickup_update(request, pk):
    from django.shortcuts import get_object_or_404
    from .forms import PickupOrderForm
    from django.contrib import messages
    from apps.master.models import Customer
    pickup = get_object_or_404(PickupOrder, pk=pk)
    
    if request.method == 'POST':
        form = PickupOrderForm(request.POST, request.FILES, instance=pickup)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order Pickup {pickup.pickup_number} berhasil diperbarui!')
            return redirect('operations:pickup-list')
    else:
        form = PickupOrderForm(instance=pickup)
        
    clients = Customer.objects.filter(is_active=True).order_by('name')
    return render(request, 'operations/pickups/pickup_edit.html', {
        'form': form,
        'clients': clients,
        'is_edit': True,
        'pickup': pickup,
    })

@login_required
def pickup_delete(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    pickup = get_object_or_404(PickupOrder, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang dapat membatalkan (void) Pickup.")
        return redirect('operations:pickup-list')
        
    if request.method == 'POST':
        void_reason = request.POST.get('void_reason') or request.POST.get('reason')
        if not void_reason:
            messages.error(request, "Alasan VOID harus diisi.")
            return redirect('operations:pickup-list')
            
        pickup_num = f"#{pickup.pickup_number or pickup.id}"
        pickup.status = 'CANCELLED'
        if pickup.note:
            pickup.note = f"VOID REASON: {void_reason} | {pickup.note}"
        else:
            pickup.note = f"VOID REASON: {void_reason}"
        pickup.save()
        messages.success(request, f"Pickup {pickup_num} berhasil dibatalkan (void)!")
        return redirect('operations:pickup-list')
        
    return render(request, 'operations/pickups/pickup_delete.html', {'pickup': pickup})

@login_required
def pickup_hide(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    pickup = get_object_or_404(PickupOrder, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang memiliki akses untuk menghapus Pickup.")
        return redirect('operations:pickup-list')
        
    if request.method == 'POST':
        pickup.is_hidden = True
        pickup.save()
        messages.success(request, f"Data pickup order {pickup.pickup_number or pickup.id} yang sudah di-void berhasil dihapus dari daftar!")
        
    return redirect('operations:pickup-list')
def shipment_list(request):
    from django.db.models import Case, When, IntegerField
    
    base_qs = (
        Shipment.objects
        .filter(is_hidden=False)
        .annotate(
            is_void=Case(
                When(status='VOID', then=1),
                default=0,
                output_field=IntegerField()
            )
        )
        .select_related('client', 'created_by')
        .prefetch_related('items', 'collies', 'manifests')
    )
    
    if hasattr(request.user, 'user_type') and request.user.user_type == 'CUSTOMER':
        shipments = base_qs.filter(created_by=request.user).order_by('is_void', '-created_at')
    else:
        shipments = base_qs.all().order_by('is_void', '-created_at')
    
    # Collect unique routes for the filter dropdown
    routes = shipments.values_list('origin', flat=True).distinct()
    # Combine origin-destination for better filtering
    route_pairs = shipments.values('origin', 'destination').distinct()
    route_options = [f"{r['origin']} → {r['destination']}" for r in route_pairs if r['origin'] and r['destination']]
    
    # Apply filters
    q_search = request.GET.get('q', '').strip()
    resi = request.GET.get('resi', '').strip()
    customer = request.GET.get('customer', '').strip()
    route = request.GET.get('route', '').strip()
    status = request.GET.get('status', '').strip()
    payment_type = request.GET.get('payment_type', '').strip()
    start_date = request.GET.get('start_date', '').strip() or request.GET.get('date_from', '').strip()
    end_date = request.GET.get('end_date', '').strip() or request.GET.get('date_to', '').strip()
    service = request.GET.get('service', '').strip()
    
    if q_search:
        shipments = shipments.filter(
            Q(resi_number__icontains=q_search) |
            Q(reference_no__icontains=q_search) |
            Q(sender_name__icontains=q_search) |
            Q(receiver_name__icontains=q_search) |
            Q(sender_phone__icontains=q_search) |
            Q(receiver_phone__icontains=q_search) |
            Q(sender_address__icontains=q_search) |
            Q(receiver_address__icontains=q_search) |
            Q(destination__icontains=q_search) |
            Q(origin__icontains=q_search) |
            Q(client__name__icontains=q_search) |
            Q(status__icontains=q_search) |
            Q(service_type__icontains=q_search) |
            Q(payment_type__icontains=q_search)
        )
    if resi:
        shipments = shipments.filter(
            Q(resi_number__icontains=resi) | Q(reference_no__icontains=resi)
        )
    if customer:
        shipments = shipments.filter(
            Q(sender_name__icontains=customer) | 
            Q(receiver_name__icontains=customer) |
            Q(client__name__icontains=customer)
        )
    if route and ' → ' in route:
        origin, destination = route.split(' → ', 1)
        shipments = shipments.filter(origin=origin, destination=destination)
    if status:
        shipments = shipments.filter(status=status)
    if payment_type:
        shipments = shipments.filter(payment_type=payment_type)
    from apps.core.date_utils import parse_date_safe
    sd = parse_date_safe(start_date)
    ed = parse_date_safe(end_date)
    if sd:
        filtered_sd = shipments.filter(created_at__date__gte=sd)
        if not (q_search or resi) or filtered_sd.exists():
            shipments = filtered_sd
    if ed:
        filtered_ed = shipments.filter(created_at__date__lte=ed)
        if not (q_search or resi) or filtered_ed.exists():
            shipments = filtered_ed
    if service:
        shipments = shipments.filter(service_type=service)
    
    # Kumpulkan statistik (dari queryset yang sudah difilter, sebelum pagination)
    stats = {
        'total': shipments.count(),
        'pending': shipments.filter(status='PENDING').count(),
        'in_transit': shipments.filter(status__in=['TRANSFER', 'TRANSIT']).count(),
        'delivered': shipments.filter(status='POD').count(),
    }
    
    # Pagination
    paginator = Paginator(shipments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    active_filters = bool(customer or status or route or payment_type or service or start_date or end_date)

    return render(request, 'operations/shipments/shipment_list.html', {
        'shipments': page_obj,
        'page_obj': page_obj,
        'stats': stats,
        'routes': route_options,
        'selected_route': route,
        'status_choices': Shipment.STATUS_CHOICES,
        'selected_status': status,
        'service_choices': Shipment.SERVICE_CHOICES,
        'selected_service': service,
        'payment_type': payment_type,
        'payment_choices': getattr(Shipment, 'PAYMENT_TYPE_CHOICES', [('CASH', 'Cash'), ('CREDIT', 'Credit / Invoice'), ('COD', 'COD')]),
        'search_q': q_search or resi,
        'customer': customer,
        'start_date': start_date,
        'end_date': end_date,
        'active_filters': active_filters,
    })

import datetime
from django.shortcuts import redirect
from django.contrib import messages
from apps.master.models import Coverage, Customer, Service

@login_required
def cek_tarif(request):
    origin_id = request.GET.get('origin')
    destination_id = request.GET.get('destination')
    weight = request.GET.get('weight', 1)
    
    results = []
    if origin_id and destination_id:
        from apps.master.models import Price
        try:
            w = float(weight)
            prices = Price.objects.filter(
                origin_id=origin_id, 
                destination_id=destination_id,
                is_active=True
            ).select_related('service')
            
            for p in prices:
                billable_w = max(w, float(p.min_weight))
                total = billable_w * float(p.price_per_kg)
                results.append({
                    'service': p.service.name,
                    'service_code': p.service.code,
                    'price_per_kg': p.price_per_kg,
                    'min_weight': p.min_weight,
                    'etd': p.estimated_days or '-',
                    'total_cost': total,
                })
        except ValueError:
            pass
            
    coverages = Coverage.objects.all().order_by('city', 'district')
    return render(request, 'operations/tracking/cek_tarif.html', {'coverages': coverages})

@login_required
def pos_cash(request):
    from .forms import ShipmentForm, ShipmentItemFormSet
    from .models import ShipmentColly, Tracking, PickupOrder
    import decimal
    
    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        items_formset = ShipmentItemFormSet(request.POST)
        if form.is_valid() and items_formset.is_valid():
            shipment = form.save(commit=False)
            shipment.payment_type = 'CASH'
            shipment.client = None # Force null for cash
            shipment.created_by = request.user
            
            if not shipment.resi_number:
                today = datetime.date.today()
                branch_code = 'BKS'
                if hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    branch_code = request.user.employee_profile.branch.code
                
                date_short = today.strftime('%y%m%d')
                prefix = f"{branch_code}S-{date_short}-"
                last_shipment = Shipment.objects.filter(resi_number__startswith=prefix).order_by('resi_number').last()
                if last_shipment:
                    try:
                        last_num = int(last_shipment.resi_number.split('-')[-1])
                        count = last_num + 1
                    except Exception:
                        count = 1
                else:
                    count = 1
                    
                shipment.resi_number = f"{prefix}{count:04d}"
            
            # Pricing Engine & Chargeable Weight Calculation
            divisor = Shipment.SERVICE_DIVISOR.get(shipment.service_type, 5000)
            length = float(shipment.length or 0)
            width = float(shipment.width or 0)
            height = float(shipment.height or 0)
            vol = (length * width * height) / divisor
            shipment.volume_weight = vol
            
            actual_weight = float(shipment.weight or 0)
            main_qty = int(request.POST.get('main_colly', 1)) if actual_weight > 0 else 0
            main_packing = request.POST.get('main_packing', 'NONE')
            
            main_cw = max(actual_weight, vol) * (main_qty if main_qty > 0 else 0)
            
            PACKING_MULTIPLIER = { 'FULL': 4000, 'KAYU': 2500, 'BUSA_KARDUS': 2000, 'NONE': 0 }
            mult = PACKING_MULTIPLIER.get(main_packing, 0)
            main_packing_cost = 0
            if mult > 0 and main_qty > 0:
                main_packing_cost = ((length + width + height + 15) / 3.0) * mult * main_qty
            
            shipment.chargeable_weight = decimal.Decimal(main_cw)
            shipment.packing_cost = decimal.Decimal(main_packing_cost)
            shipment.status = 'PENDING'
            shipment.save()
            
            items_formset.instance = shipment
            items_formset.save()
            
            total_cw = main_cw
            total_packing = main_packing_cost
            
            # Generate barcodes for main item
            if main_qty > 0:
                for i in range(1, main_qty + 1):
                    barcode = f"{shipment.resi_number}-00-{i:02d}"
                    ShipmentColly.objects.create(
                        shipment=shipment,
                        barcode=barcode,
                        weight=shipment.weight,
                        status='PENDING'
                    )
            
            for item in shipment.items.all():
                item_vol = float(item.panjang * item.lebar * item.tinggi) / divisor
                item_cw = max(float(item.actual_weight), item_vol) * item.quantity
                total_cw += item_cw
                total_packing += float(item.get_packing_cost()) * item.quantity
                
                for i in range(1, item.quantity + 1):
                    barcode = f"{shipment.resi_number}-{item.id}-{i:02d}"
                    ShipmentColly.objects.create(
                        shipment=shipment,
                        barcode=barcode,
                        weight=item.actual_weight,
                        status='PENDING'
                    )
            
            shipment.chargeable_weight = decimal.Decimal(total_cw)
            shipment.packing_cost = decimal.Decimal(total_packing)
            shipment.save(update_fields=['chargeable_weight', 'packing_cost'])
            
            # Create initial Tracking history
            if shipment.pickup_number_ref:
                p_order = PickupOrder.objects.filter(pickup_number=shipment.pickup_number_ref).first()
                p_created = p_order.created_at if p_order else (shipment.created_at or timezone.now())
                p_loc = (p_order.city if p_order and p_order.city else shipment.origin) or 'Gudang Asal'
                
                # Get assigned branch warehouse from pickup manifest
                p_manifest = p_order.pickup_manifests.filter(branch__isnull=False).last() if p_order else None
                if p_manifest and p_manifest.branch:
                    pickup_branch_loc = p_manifest.branch.name
                elif hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    pickup_branch_loc = request.user.employee_profile.branch.name
                else:
                    pickup_branch_loc = shipment.origin or p_loc
                
                # 1. Status PENDING (Pickup order dibuat, menunggu barang diambil)
                Tracking.objects.create(
                    shipment=shipment,
                    status='PENDING',
                    location=p_loc,
                    description='Pickup order dibuat, menunggu barang diambil',
                    occurred_at=p_created,
                    step_order=10
                )
                
                # Update PickupOrder if exists
                if p_order and p_order.status != 'PICKED_UP':
                    p_order.status = 'PICKED_UP'
                    p_order.save(update_fields=['status'])
                
                # Advance shipment status to PICKUP
                shipment.status = 'PICKUP'
                shipment.save(update_fields=['status'])
                shipment.collies.all().update(status='PICKUP')
                
                # 2. Status PICKUP (Barang berhasil di-pickup, menunggu proses selanjutnya)
                Tracking.objects.create(
                    shipment=shipment,
                    status='PICKUP',
                    location=pickup_branch_loc,
                    description='Barang berhasil di-pickup, menunggu proses selanjutnya',
                    occurred_at=timezone.now(),
                    step_order=20
                )
            else:
                user_branch = None
                if hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    user_branch = request.user.employee_profile.branch.name
                branch_loc = user_branch or shipment.origin or 'Gudang Asal'
                
                Tracking.objects.create(
                    shipment=shipment,
                    status='PENDING',
                    location=branch_loc,
                    description='Paket telah diterima di gudang asal dan siap diproses',
                    occurred_at=shipment.created_at or timezone.now(),
                    step_order=10
                )
            
            messages.success(request, f'POS Cash berhasil! Resi: {shipment.resi_number}')
            return redirect('operations:shipment-list')
    else:
        form = ShipmentForm()
        items_formset = ShipmentItemFormSet()
        
    from apps.master.models import Customer, Service
    clients = Customer.objects.filter(is_active=True).order_by('name')
    pickup_orders = PickupOrder.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_TRANSIT']).order_by('-created_at')
    
    services = Service.objects.filter(is_active=True).order_by('name')
    service_choices = [(s.code, s.name) for s in services]
    service_divisors = {s.code: s.divisor for s in services}
    import json
    
    return render(request, 'operations/shipments/shipment_form_resi.html', {
        'form': form,
        'items_formset': items_formset,
        'is_edit': False,
        'shipment': None,
        'pos_type': 'CASH',
        'title': 'POS Cash (Tunai)',
        'clients': clients,
        'pickup_orders': pickup_orders,
        'services': services,
        'service_choices': service_choices,
        'service_divisors': json.dumps(service_divisors),
    })

@login_required
def pos_credit(request):
    from .forms import ShipmentForm, ShipmentItemFormSet
    from .models import ShipmentColly, Tracking, PickupOrder
    import decimal
    
    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        items_formset = ShipmentItemFormSet(request.POST)
        if form.is_valid() and items_formset.is_valid():
            shipment = form.save(commit=False)
            if not shipment.client:
                messages.error(request, 'POS Credit wajib memilih Klien (Perusahaan)!')
                return redirect('operations:pos-credit')
                
            shipment.payment_type = 'CREDIT'
            shipment.created_by = request.user
            
            if not shipment.resi_number:
                today = datetime.date.today()
                branch_code = 'BKS'
                if hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    branch_code = request.user.employee_profile.branch.code
                
                date_short = today.strftime('%y%m%d')
                prefix = f"{branch_code}C-{date_short}-"
                last_shipment = Shipment.objects.filter(resi_number__startswith=prefix).order_by('resi_number').last()
                if last_shipment:
                    try:
                        last_num = int(last_shipment.resi_number.split('-')[-1])
                        count = last_num + 1
                    except Exception:
                        count = 1
                else:
                    count = 1
                
                shipment.resi_number = f"{prefix}{count:04d}"
            
            # 1. PRICING ENGINE & CHARGEABLE WEIGHT (Backend Validation)
            divisor = Shipment.SERVICE_DIVISOR.get(shipment.service_type, 5000)
            length = float(shipment.length or 0)
            width = float(shipment.width or 0)
            height = float(shipment.height or 0)
            vol = (length * width * height) / divisor
            shipment.volume_weight = vol
            
            actual_weight = float(shipment.weight or 0)
            main_qty = int(request.POST.get('main_colly', 1)) if actual_weight > 0 else 0
            main_packing = request.POST.get('main_packing', 'NONE')
            
            main_cw = max(actual_weight, vol) * (main_qty if main_qty > 0 else 0)
            
            PACKING_MULTIPLIER = { 'FULL': 4000, 'KAYU': 2500, 'BUSA_KARDUS': 2000, 'NONE': 0 }
            mult = PACKING_MULTIPLIER.get(main_packing, 0)
            main_packing_cost = 0
            if mult > 0 and main_qty > 0:
                main_packing_cost = ((length + width + height + 15) / 3.0) * mult * main_qty
            
            shipment.chargeable_weight = decimal.Decimal(main_cw)
            shipment.packing_cost = decimal.Decimal(main_packing_cost)
            shipment.status = 'PENDING'
            
            # Cek Credit Limit (Plafon) - Fleksibel dengan Warning
            if hasattr(shipment.client, 'credit_limit') and shipment.client.credit_limit > 0:
                from apps.finance.models import Invoice
                from django.db.models import Sum
                unpaid = Invoice.objects.filter(
                    client_name=shipment.client.name, 
                    status__in=['SENT', 'PARTIAL']
                ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
                if unpaid > shipment.client.credit_limit:
                    messages.warning(request, f"BYPASS PERINGATAN: Klien melebihi Plafon Piutang! (Tunggakan: Rp{unpaid:,.0f} / Plafon: Rp{shipment.client.credit_limit:,.0f}). Transaksi ini akan tercatat di Audit Log.")
                    from apps.audit.utils import log_action
                    log_action(
                        user=request.user,
                        action=f"[CREDIT BYPASS] POS Credit {shipment.resi_number} melebihi limit",
                        module="Operations",
                        obj=shipment,
                        ip=request.META.get('REMOTE_ADDR')
                    )
            
            shipment.save()
            
            items_formset.instance = shipment
            items_formset.save()
            
            total_cw = main_cw
            total_packing = main_packing_cost
            
            # Generate barcodes for main item
            if main_qty > 0:
                for i in range(1, main_qty + 1):
                    barcode = f"{shipment.resi_number}-00-{i:02d}"
                    ShipmentColly.objects.create(
                        shipment=shipment,
                        barcode=barcode,
                        weight=shipment.weight,
                        status='PENDING'
                    )
            
            for item in shipment.items.all():
                item_vol = float(item.panjang * item.lebar * item.tinggi) / divisor
                item_cw = max(float(item.actual_weight), item_vol) * item.quantity
                total_cw += item_cw
                total_packing += float(item.get_packing_cost()) * item.quantity
                
                for i in range(1, item.quantity + 1):
                    barcode = f"{shipment.resi_number}-{item.id}-{i:02d}"
                    ShipmentColly.objects.create(
                        shipment=shipment,
                        barcode=barcode,
                        weight=item.actual_weight,
                        status='PENDING'
                    )
            
            shipment.chargeable_weight = decimal.Decimal(total_cw)
            shipment.packing_cost = decimal.Decimal(total_packing)
            shipment.save(update_fields=['chargeable_weight', 'packing_cost'])
            
            # Create initial Tracking history
            if shipment.pickup_number_ref:
                p_order = PickupOrder.objects.filter(pickup_number=shipment.pickup_number_ref).first()
                p_created = p_order.created_at if p_order else (shipment.created_at or timezone.now())
                p_loc = (p_order.city if p_order and p_order.city else shipment.origin) or 'Gudang Asal'
                
                # Get assigned branch warehouse from pickup manifest
                p_manifest = p_order.pickup_manifests.filter(branch__isnull=False).last() if p_order else None
                if p_manifest and p_manifest.branch:
                    pickup_branch_loc = p_manifest.branch.name
                elif hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    pickup_branch_loc = request.user.employee_profile.branch.name
                else:
                    pickup_branch_loc = shipment.origin or p_loc
                
                # 1. Status PENDING (Pickup order dibuat, menunggu barang diambil)
                Tracking.objects.create(
                    shipment=shipment,
                    status='PENDING',
                    location=p_loc,
                    description='Pickup order dibuat, menunggu barang diambil',
                    occurred_at=p_created,
                    step_order=10
                )
                
                # Update PickupOrder if exists
                if p_order and p_order.status != 'PICKED_UP':
                    p_order.status = 'PICKED_UP'
                    p_order.save(update_fields=['status'])
                
                # Advance shipment status to PICKUP
                shipment.status = 'PICKUP'
                shipment.save(update_fields=['status'])
                shipment.collies.all().update(status='PICKUP')
                
                # 2. Status PICKUP (Barang berhasil di-pickup, menunggu proses selanjutnya)
                Tracking.objects.create(
                    shipment=shipment,
                    status='PICKUP',
                    location=pickup_branch_loc,
                    description='Barang berhasil di-pickup, menunggu proses selanjutnya',
                    occurred_at=timezone.now(),
                    step_order=20
                )
            else:
                user_branch = None
                if hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                    user_branch = request.user.employee_profile.branch.name
                branch_loc = user_branch or shipment.origin or 'Gudang Asal'
                
                Tracking.objects.create(
                    shipment=shipment,
                    status='PENDING',
                    location=branch_loc,
                    description='Paket telah diterima di gudang asal dan siap diproses',
                    occurred_at=shipment.created_at or timezone.now(),
                    step_order=10
                )
            
            if not messages.get_messages(request):
                messages.success(request, f'POS Credit berhasil! Resi: {shipment.resi_number}')
            else:
                messages.success(request, f'Resi {shipment.resi_number} tetap berhasil dibuat dengan Bypass.')
                
            return redirect('operations:shipment-list')
    else:
        form = ShipmentForm()
        items_formset = ShipmentItemFormSet()
        
    from apps.master.models import Customer, Service
    # Hanya customer yang aktif
    clients = Customer.objects.filter(is_active=True).order_by('name')
    # Ambil pickup order yang masih aktif (belum selesai)
    pickup_orders = PickupOrder.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_TRANSIT']).order_by('-created_at')
    
    services = Service.objects.filter(is_active=True).order_by('name')
    service_choices = [(s.code, s.name) for s in services]
    service_divisors = {s.code: s.divisor for s in services}
    import json
    
    return render(request, 'operations/shipments/shipment_form_resi.html', {
        'form': form,
        'items_formset': items_formset,
        'is_edit': False,
        'shipment': None,
        'pos_type': 'CREDIT',
        'title': 'Buat Resi Baru (POS Credit)',
        'clients': clients,
        'pickup_orders': pickup_orders,
        'services': services,
        'service_choices': service_choices,
        'service_divisors': json.dumps(service_divisors),
    })

def shipment_create(request):
    return redirect('operations:shipment-list')

@login_required
def shipment_update(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if not request.user.is_superuser:
        messages.error(request, "Anda tidak memiliki akses untuk mengedit resi.")
        return redirect('operations:shipment-list')
        
    from .forms import ShipmentForm, ShipmentItemFormSet
    if request.method == 'POST':
        orig_resi = shipment.resi_number
        form = ShipmentForm(request.POST, instance=shipment)
        items_formset = ShipmentItemFormSet(request.POST, instance=shipment)
        if form.is_valid() and items_formset.is_valid():
            shipment = form.save(commit=False)
            if not shipment.resi_number:
                shipment.resi_number = orig_resi
            shipment.save()
            items_formset.save()
            
            # Recalculate price and chargeable weight
            divisor = Shipment.SERVICE_DIVISOR.get(shipment.service_type, 5000)
            length = float(shipment.length or 0)
            width = float(shipment.width or 0)
            height = float(shipment.height or 0)
            vol = (length * width * height) / divisor if (length and width and height) else 0.0
            actual_w = float(shipment.weight or 0)
            main_colly = int(request.POST.get('main_colly', 1)) if actual_w > 0 or vol > 0 else 0
            main_cw = max(actual_w, vol) * (main_colly if main_colly > 0 else (1 if actual_w > 0 else 0))
            
            has_items = shipment.items.exists()
            total_cw = 0 if has_items else main_cw
            total_packing = 0
            
            for item in shipment.items.all():
                i_p = float(item.panjang or 0)
                i_l = float(item.lebar or 0)
                i_t = float(item.tinggi or 0)
                item_vol = (i_p * i_l * i_t) / divisor if (i_p and i_l and i_t) else 0.0
                i_aw = float(item.actual_weight or 0)
                i_qty = item.quantity if item.quantity > 0 else 1
                item_cw = max(i_aw, item_vol) * i_qty
                total_cw += item_cw
                total_packing += float(item.get_packing_cost()) * i_qty
                
            if total_cw == 0 and actual_w > 0:
                total_cw = actual_w

            shipment.volume_weight = vol
            import decimal
            shipment.chargeable_weight = decimal.Decimal(str(round(total_cw, 2)))
            shipment.packing_cost = decimal.Decimal(str(round(total_packing, 2)))
            shipment.save(update_fields=['volume_weight', 'chargeable_weight', 'packing_cost'])
            
            messages.success(request, f"Resi {shipment.resi_number} berhasil diperbarui!")
            return redirect('operations:shipment-list')
    else:
        form = ShipmentForm(instance=shipment)
        items_formset = ShipmentItemFormSet(instance=shipment)
        
    from apps.master.models import Customer, Service
    clients = Customer.objects.filter(is_active=True).order_by('name')
    from .models import PickupOrder
    pickup_orders = PickupOrder.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_TRANSIT']).order_by('-created_at')
    
    services = Service.objects.filter(is_active=True).order_by('name')
    service_choices = [(s.code, s.name) for s in services]
    service_divisors = {s.code: s.divisor for s in services}
    
    import json
    return render(request, 'operations/shipments/shipment_form_resi.html', {
        'form': form,
        'items_formset': items_formset,
        'is_edit': True,
        'shipment': shipment,
        'pos_type': 'CREDIT',
        'title': f'Edit Resi: {shipment.resi_number}',
        'clients': clients,
        'pickup_orders': pickup_orders,
        'services': services,
        'service_choices': service_choices,
        'service_divisors': json.dumps(service_divisors),
    })

import pandas as pd
from django.http import HttpResponse

@login_required
def shipment_import_template(request):
    import io
    output = io.BytesIO()
    
    # Create a template dataframe
    columns = [
        'Customer / Shipper (Company Name)', 'Shipper Name', 'Shipper Attention', 
        'Shipper Phone', 'Shipper Address', 'Shipper City', 'Shipper District', 'Shipper Postal Code',
        'Receiver Name', 'Receiver Attention', 'Receiver Phone', 'Receiver Address', 
        'Receiver City', 'Receiver District', 'Receiver Postal Code',
        'Service (REG/ODS/SDS/RD/RL/RUC/RU/TRK)', 'Weight', 'Length', 'Width', 'Height', 'Total Colly',
        'Item Value', 'Description Item', 'Pickup No (Ref)'
    ]
    df = pd.DataFrame(columns=columns)
    
    # Write to excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template Import Resi')
        
        # Access the workbook and sheet to style
        workbook = writer.book
        worksheet = writer.sheets['Template Import Resi']
        
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
        
        # Style headers
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
        
        for col_num, column_title in enumerate(columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            # Adjust column width
            worksheet.column_dimensions[get_column_letter(col_num)].width = max(len(column_title) + 5, 15)
        
    output.seek(0)
    response = HttpResponse(
        output.read(), 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Template_Import_Resi.xlsx'
    return response

@login_required
def shipment_import(request):
    """Handle import from popup modal - POST only, GET redirects to list"""
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Please upload a file.')
            return redirect('operations:shipment-import')
            
        file = request.FILES['file']
        
        try:
            from django.db import transaction
            from apps.master.models import Customer
            
            df = pd.read_excel(file)
            success_count = 0
            
            today = datetime.date.today()
            date_str = today.strftime('%Y%m%d')
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Get or handle client using master.Customer model
                        client_name = str(row.get('Customer / Shipper (Company Name)', '')).strip()
                        client = None
                        if client_name and client_name != 'nan':
                            client = Customer.objects.filter(company_name__icontains=client_name, is_active=True).first() or Customer.objects.filter(name__icontains=client_name, is_active=True).first()
                        
                        # Generate Resi
                        last_shipment = Shipment.objects.filter(resi_number__startswith=f"IMP-{date_str}").order_by('resi_number').last()
                        count = int(last_shipment.resi_number.split('-')[-1]) + 1 if last_shipment else 1
                        resi_number = f"IMP-{date_str}-{count:04d}"
                        
                        service_val = str(row.get('Service (REG/ODS/SDS/RD/RL/RUC/RU/TRK)', 'REG')).strip().upper()
                        if service_val not in dict(Shipment.SERVICE_CHOICES):
                            service_val = 'REG'
                            
                        shipment = Shipment.objects.create(
                            resi_number=resi_number,
                            input_type='IMPORT',
                            created_by=request.user,
                            client=client,
                            sender_name=str(row.get('Shipper Name', '')).strip(),
                            sender_attention=str(row.get('Shipper Attention', '')).strip(),
                            sender_phone=str(row.get('Shipper Phone', '')).strip(),
                            sender_address=str(row.get('Shipper Address', '')).strip(),
                            sender_city=str(row.get('Shipper City', '')).strip(),
                            sender_district=str(row.get('Shipper District', '')).strip(),
                            sender_postal_code=str(row.get('Shipper Postal Code', '')).strip(),
                            origin=str(row.get('Shipper City', '')).strip(),
                            
                            receiver_name=str(row.get('Receiver Name', '')).strip(),
                            receiver_attention=str(row.get('Receiver Attention', '')).strip(),
                            receiver_phone=str(row.get('Receiver Phone', '')).strip(),
                            receiver_address=str(row.get('Receiver Address', '')).strip(),
                            receiver_city=str(row.get('Receiver City', '')).strip(),
                            receiver_district=str(row.get('Receiver District', '')).strip(),
                            receiver_postal_code=str(row.get('Receiver Postal Code', '')).strip(),
                            destination=str(row.get('Receiver City', '')).strip(),
                            
                            service_type=service_val,
                            weight=float(row.get('Weight', 0)) if not pd.isna(row.get('Weight')) else 0,
                            length=float(row.get('Length', 0)) if not pd.isna(row.get('Length')) else 0,
                            width=float(row.get('Width', 0)) if not pd.isna(row.get('Width')) else 0,
                            height=float(row.get('Height', 0)) if not pd.isna(row.get('Height')) else 0,
                            total_colly=int(row.get('Total Colly', 1)) if not pd.isna(row.get('Total Colly')) else 1,
                            
                            item_value=float(row.get('Item Value', 0)) if not pd.isna(row.get('Item Value')) else 0,
                            description_item=str(row.get('Description Item', '')).strip(),
                            pickup_number_ref=str(row.get('Pickup No (Ref)', '')).strip() if str(row.get('Pickup No (Ref)', '')) != 'nan' else None,
                            
                            status='PENDING',
                            payment_type='CREDIT'
                        )
                        
                        # Calculate CW
                        divisor = Shipment.SERVICE_DIVISOR.get(shipment.service_type, 5000)
                        vol = float(shipment.length * shipment.width * shipment.height) / divisor
                        actual = float(shipment.weight)
                        cw = max(actual, vol)
                        
                        shipment.volume_weight = vol
                        shipment.chargeable_weight = cw
                        shipment.save()
                        
                        # Create Colly
                        for i in range(1, shipment.total_colly + 1):
                            barcode = f"{shipment.resi_number}-1-{i:02d}"
                            ShipmentColly.objects.create(
                                shipment=shipment,
                                barcode=barcode,
                                weight=actual,
                                status='PENDING'
                            )
                            
                        # Create initial Tracking history
                        if shipment.pickup_number_ref:
                            p_order = PickupOrder.objects.filter(pickup_number=shipment.pickup_number_ref).first()
                            p_created = p_order.created_at if p_order else (shipment.created_at or timezone.now())
                            p_loc = (p_order.city if p_order and p_order.city else shipment.origin) or 'Gudang Asal'
                            
                            p_manifest = p_order.pickup_manifests.filter(branch__isnull=False).last() if p_order else None
                            if p_manifest and p_manifest.branch:
                                pickup_branch_loc = p_manifest.branch.name
                            elif hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                                pickup_branch_loc = request.user.employee_profile.branch.name
                            else:
                                pickup_branch_loc = shipment.origin or p_loc
                            
                            Tracking.objects.create(
                                shipment=shipment,
                                status='PENDING',
                                location=p_loc,
                                description='Pickup order dibuat, menunggu barang diambil',
                                occurred_at=p_created,
                                step_order=10
                            )
                            if p_order and p_order.status != 'PICKED_UP':
                                p_order.status = 'PICKED_UP'
                                p_order.save(update_fields=['status'])
                            
                            shipment.status = 'PICKUP'
                            shipment.save(update_fields=['status'])
                            shipment.collies.all().update(status='PICKUP')
                            
                            Tracking.objects.create(
                                shipment=shipment,
                                status='PICKUP',
                                location=pickup_branch_loc,
                                description='Barang berhasil di-pickup, menunggu proses selanjutnya',
                                occurred_at=timezone.now(),
                                step_order=20
                            )
                        else:
                            Tracking.objects.create(
                                shipment=shipment,
                                status='PENDING',
                                location=shipment.origin or 'Gudang Asal',
                                description='Paket telah diterima di gudang asal dan siap diproses',
                                occurred_at=shipment.created_at or timezone.now(),
                                step_order=10
                            )
                        
                        success_count += 1
                    except Exception as e:
                        print(f"Error importing row {index}: {str(e)}")
            messages.success(request, f'Successfully imported {success_count} shipments.')
        except Exception as e:
            messages.error(request, f'Error parsing file: {str(e)}')
            
    return redirect('operations:shipment-list')

@login_required
def shipment_void(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang dapat melakukan VOID resi.")
        return redirect('operations:shipment-list')
        
    if request.method == 'POST':
        void_reason = request.POST.get('void_reason')
        if void_reason:
            shipment.status = 'VOID'
            if shipment.description_item:
                shipment.description_item = f"VOID REASON: {void_reason} | {shipment.description_item}"
            else:
                shipment.description_item = f"VOID REASON: {void_reason}"
            shipment.save()
            messages.success(request, f"Resi {shipment.resi_number} berhasil di-VOID.")
        else:
            messages.error(request, "Alasan VOID harus diisi.")
    return redirect('operations:shipment-list')

@login_required
def shipment_delete(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang memiliki akses untuk menghapus resi.")
        return redirect('operations:shipment-list')
        
    if request.method == 'POST':
        resi = shipment.resi_number
        shipment.delete()
        messages.success(request, f"Resi {resi} berhasil dihapus!")
        return redirect('operations:shipment-list')
        
    return render(request, 'operations/shipments/shipment_delete.html', {
        'shipment': shipment
    })

@login_required
def shipment_hide(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang memiliki akses untuk menghapus resi.")
        return redirect('operations:shipment-list')
        
    if request.method == 'POST':
        shipment.is_hidden = True
        shipment.save()
        messages.success(request, f"Data resi {shipment.resi_number} yang sudah di-void berhasil dihapus dari daftar!")
        
    return redirect('operations:shipment-list')

@login_required
def shipment_detail(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status', 'TRANSIT')
        location = request.POST.get('location', '')
        description = request.POST.get('description', '')
        occurred_at = _tracking_occurred_at(request)
        set_current_status = request.POST.get('set_current_status') in ('1', 'on', 'true') or not request.POST.get('event_date')
        
        Tracking.objects.create(
            shipment=shipment,
            status=status,
            location=location,
            description=description,
            occurred_at=occurred_at,
        )
        if set_current_status:
            shipment.status = status
            shipment.save()
        
        # Audit Log: Rekam tindakan update manual
        from apps.audit.utils import log_action
        log_action(
            user=request.user,
            action=f"[MANUAL OVERRIDE] Update status resi ke {status} via Web",
            module="Operations",
            obj=shipment,
            ip=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f"Status resi {shipment.resi_number} berhasil diperbarui.")
        return redirect('operations:shipment-detail', pk=pk)
        
    tracking_history = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp')
    
    return render(request, 'operations/shipments/shipment_detail.html', {
        'shipment': shipment,
        'tracking_history': tracking_history,
        'event_date': timezone.localdate().isoformat(),
        'event_time': timezone.localtime().strftime('%H:%M'),
    })

@login_required
def shipment_print(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(Shipment, pk=pk)
    print_type = request.GET.get('type', 'reguler')
    
    if print_type == 'sticker_100x100':
        template = 'operations/shipments/shipment_print_100x100_pdf.html'
    elif print_type == 'sticker_100x150':
        template = 'operations/shipments/shipment_print_100x150_pdf.html'
    elif print_type == 'reguler':
        template = 'operations/shipments/shipment_print_reguler_a4_pdf.html'
    elif print_type == 'package_id':
        template = 'operations/shipments/shipment_print_package_id.html'
    else:
        template = 'operations/shipments/shipment_print_reguler_a4_pdf.html'
    
    if print_type in ['sticker_100x100', 'sticker_100x150', 'reguler', 'package_id'] or not print_type:
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from xhtml2pdf import pisa
        from apps.master.models import Coverage
        
        origin_coverage = Coverage.objects.filter(city=shipment.sender_city, district=shipment.sender_district).first() if shipment.sender_city else None
        dest_coverage = Coverage.objects.filter(city=shipment.receiver_city, district=shipment.receiver_district).first() if shipment.receiver_city else None
        colly_range = range(1, shipment.total_colly + 1) if shipment.total_colly > 0 else range(1, 2)
        
        flat_items = []
        if shipment.items.exists():
            for item in shipment.items.all():
                for _ in range(item.quantity):
                    flat_items.append(item)
        else:
            flat_items = [None] * max(1, shipment.total_colly)
        package_items = list(enumerate(flat_items, 1))

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-surat.png').replace('\\', '/')
        iso_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-iso.png').replace('\\', '/')
        scissor_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'scissor_left.png').replace('\\', '/')

        # Generate QR code data URI
        import qrcode, io, base64
        qr = qrcode.QRCode(box_size=4, border=0)
        qr.add_data(f"https://paketincargo.com/tracking/?resi={shipment.resi_number}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

        context = {
            'shipment': shipment,
            'colly_range': colly_range,
            'package_items': package_items,
            'origin_coverage': origin_coverage,
            'dest_coverage': dest_coverage,
            'logo_path': logo_path,
            'iso_logo_path': iso_logo_path,
            'scissor_path': scissor_path,
            'qr_data_uri': qr_data_uri,
        }
        html_string = render_to_string(template, context, request=request)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{print_type}_{shipment.resi_number}.pdf"'
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
        return response
    
    colly_range = range(1, shipment.total_colly + 1) if shipment.total_colly > 0 else range(1, 2)
    return render(request, template, {
        'shipment': shipment,
        'colly_range': colly_range,
    })

@login_required
def manifest_list(request):
    from apps.accounts.models import User
    from django.core.paginator import Paginator
    manifests = (
        Manifest.objects
        .filter(is_hidden=False)
        .select_related('driver', 'vendor', 'vehicle', 'branch', 'vendor_middle', 'created_by')
        .prefetch_related('pickup_orders', 'shipments', 'shipments__manifests')
        .order_by('-date', '-created_at')
    )
    
    # Apply filters
    q_search = request.GET.get('q', '').strip()
    manifest_number = request.GET.get('manifest_number', '').strip()
    driver_name = request.GET.get('driver', '').strip()
    status_filter = request.GET.get('status', '').strip()
    manifest_type = request.GET.get('type', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    if q_search:
        matched_manifests = manifests.filter(
            Q(manifest_number__icontains=q_search) |
            Q(driver__first_name__icontains=q_search) |
            Q(driver__username__icontains=q_search) |
            Q(vendor__name__icontains=q_search) |
            Q(vehicle__plate_number__icontains=q_search)
        )
        filtered_manifests = matched_manifests
        if manifest_number:
            filtered_manifests = filtered_manifests.filter(manifest_number__icontains=manifest_number)
        if driver_name:
            filtered_manifests = filtered_manifests.filter(
                Q(driver__first_name__icontains=driver_name) |
                Q(driver__username__icontains=driver_name)
            )
        if status_filter:
            filtered_manifests = filtered_manifests.filter(status=status_filter)
        if manifest_type:
            filtered_manifests = filtered_manifests.filter(manifest_type=manifest_type)
            
        date_filtered_manifests = filtered_manifests
        if psd:
            date_filtered_manifests = date_filtered_manifests.filter(created_at__date__gte=psd)
        if ped:
            date_filtered_manifests = date_filtered_manifests.filter(created_at__date__lte=ped)
            
        if date_filtered_manifests.exists():
            manifests = date_filtered_manifests
        elif filtered_manifests.exists():
            manifests = filtered_manifests
        else:
            manifests = matched_manifests
    else:
        if manifest_number:
            manifests = manifests.filter(manifest_number__icontains=manifest_number)
        if driver_name:
            manifests = manifests.filter(
                Q(driver__first_name__icontains=driver_name) |
                Q(driver__username__icontains=driver_name)
            )
        if status_filter:
            manifests = manifests.filter(status=status_filter)
        if manifest_type:
            manifests = manifests.filter(manifest_type=manifest_type)
        if psd:
            manifests = manifests.filter(created_at__date__gte=psd)
        if ped:
            manifests = manifests.filter(created_at__date__lte=ped)
    
    # Pagination
    paginator = Paginator(manifests, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Delivery values come from the scanned shipments.
    if manifest_type == 'DELIVERY':
        for manifest in page_obj:
            delivery_shipments = list(manifest.shipments.all())
            manifest.delivery_total_weight = sum(
                (shipment.chargeable_weight or shipment.weight or 0)
                for shipment in delivery_shipments
            )
            manifest.delivery_total_colly = sum(
                (shipment.total_colly or 1) for shipment in delivery_shipments
            )
            
    drivers = User.objects.filter(user_type='DRIVER').order_by('first_name', 'username')
    has_active_filter = bool(q_search or manifest_number or driver_name or status_filter or start_date or end_date)
    
    return render(request, 'operations/manifests/manifest_list.html', {
        'manifests': page_obj,
        'page_obj': page_obj,
        'manifest_number': manifest_number,
        'driver_name': driver_name,
        'manifest_type': manifest_type,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'q_search': q_search,
        'drivers': drivers,
        'has_active_filter': has_active_filter,
    })

@login_required
def manifest_detail(request, pk):
    from django.shortcuts import get_object_or_404
    manifest = get_object_or_404(Manifest, pk=pk)
    context = {'manifest': manifest}
    if manifest.manifest_type == 'DELIVERY':
        shipments = list(manifest.shipments.all())
        cod_shipments = [s for s in shipments if s.is_cod]
        context['cod_count'] = len(cod_shipments)
        context['total_cod'] = sum((s.cod_value or 0) for s in cod_shipments)

    return render(request, 'operations/manifests/manifest_detail.html', context)

@login_required
def manifest_print(request, pk):
    from django.shortcuts import get_object_or_404
    manifest = get_object_or_404(
        Manifest.objects.select_related('driver', 'vendor', 'created_by', 'branch').prefetch_related('shipments'),
        pk=pk,
    )

    if manifest.manifest_type == 'DELIVERY':
        shipments = list(manifest.shipments.all())
        cod_shipments = [shipment for shipment in shipments if shipment.is_cod]
        total_cod = sum((shipment.cod_value or 0) for shipment in cod_shipments)
        total_colly = sum((shipment.total_colly or 1) for shipment in shipments)
        total_weight = sum((shipment.chargeable_weight or shipment.weight or 0) for shipment in shipments)
        return render(request, 'operations/manifests/delivery_print.html', {
            'manifest': manifest,
            'shipments': shipments,
            'cod_count': len(cod_shipments),
            'total_cod': total_cod,
            'total_colly': total_colly,
            'total_weight': total_weight,
        })
    
    return render(request, 'operations/manifests/manifest_print.html', {
        'manifest': manifest,
    })

def manifest_print_bagtag(request, pk):
    from django.shortcuts import get_object_or_404
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from xhtml2pdf import pisa
    
    manifest = get_object_or_404(Manifest, pk=pk)
    
    colly_count = manifest.colly_cmo if manifest.colly_cmo and manifest.colly_cmo > 0 else 1
    colly_range = range(1, colly_count + 1)
    
    html_string = render_to_string('operations/manifests/manifest_bagtag_print.html', {
        'manifest': manifest,
        'colly_range': colly_range,
    }, request=request)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="BagTag_{manifest.manifest_number}.pdf"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@login_required
def print_manifest_linehaul(request, pk):
    from django.shortcuts import get_object_or_404
    
    manifest = get_object_or_404(Manifest, pk=pk)
    
    return render(request, 'operations/manifests/manifest_print_linehaul.html', {
        'manifest': manifest,
    })

@login_required
def manifest_update(request, pk):
    from django.shortcuts import get_object_or_404
    manifest = get_object_or_404(Manifest, pk=pk)
    
    # Only allow update if manifest is still in preparation
    if manifest.status != 'PREPARING':
        messages.info(request, "Manifest sudah berjalan, tidak dapat diubah.")
        return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
    
    from .forms import ManifestForm
    if request.method == 'POST':
        mode = request.GET.get('mode', '')
        form = ManifestForm(request.POST, instance=manifest)
        if form.is_valid():
            manifest = form.save(commit=False)
            
            if not manifest.manifest_number:
                import datetime
                today = datetime.date.today()
                date_str = today.strftime('%Y%m%d')
                
                if manifest.manifest_type == 'TRANSFER':
                    prefix = f"TRF-{date_str}-"
                elif manifest.manifest_type == 'DELIVERY':
                    prefix = f"DEL-{date_str}-"
                else:
                    prefix = f"MNF-{date_str}-"
                    
                last_manifest = Manifest.objects.filter(manifest_number__startswith=prefix).order_by('-manifest_number').first()
                if last_manifest:
                    try:
                        last_num = int(last_manifest.manifest_number.split('-')[-1])
                    except ValueError:
                        last_num = 0
                    new_num = last_num + 1
                else:
                    new_num = 1
                manifest.manifest_number = f"{prefix}{new_num:04d}"
                
            manifest.save()
            form.save_m2m()
            messages.success(request, f"Manifest {manifest.manifest_number} berhasil diperbarui!")
            return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
    else:
        form = ManifestForm(instance=manifest)
        
    mode = ''
    if manifest.manifest_type == 'TRANSFER':
        mode = manifest.get_transfer_mode
    elif manifest.manifest_type == 'OUTGOING':
        if manifest.is_bypass:
            mode = 'BYPASS'
        else:
            mode = 'BIASA'

    return render(request, 'operations/manifests/manifest_edit.html', {
        'form': form,
        'manifest_type': manifest.manifest_type,
        'mode': mode,
        'is_edit': True,
        'manifest': manifest
    })

@login_required
def manifest_delete(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    manifest = get_object_or_404(Manifest, pk=pk)
    
    is_admin = request.user.is_superuser or request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN' or (hasattr(request.user, 'roles') and request.user.roles.filter(name__icontains='admin').exists())
    if not is_admin:
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang dapat melakukan aksi ini.")
        return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
        
    if request.method == 'POST':
        action = request.POST.get('action')
        # If action is hide or if the manifest is already void/cancelled
        if action == 'hide' or manifest.status in ['CANCELLED', 'VOID']:
            manifest.is_hidden = True
            manifest.save()
            messages.success(request, f"Data manifest {manifest.manifest_number} yang sudah di-void berhasil dihapus dari daftar!")
            return redirect(f"/operations/manifests/?type={manifest.manifest_type}")

        void_reason = request.POST.get('void_reason') or request.POST.get('reason')
        if not void_reason:
            messages.error(request, "Alasan VOID harus diisi.")
            return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
            
        manifest_num = manifest.manifest_number
        manifest_type = manifest.manifest_type
        
        # Soft delete / Cancel instead of hard delete
        manifest.status = 'CANCELLED'
        if manifest.description:
            manifest.description = f"VOID REASON: {void_reason} | {manifest.description}"
        else:
            manifest.description = f"VOID REASON: {void_reason}"
        manifest.save()
        
        # Set all shipments in manifest back to proper status if needed (optional based on logic)
        
        messages.success(request, f"Manifest {manifest_num} berhasil di-void!")
        return redirect(f"/operations/manifests/?type={manifest_type}")
        
    return render(request, 'operations/manifests/manifest_delete.html', {
        'manifest': manifest
    })

@login_required
def manifest_hide(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    manifest = get_object_or_404(Manifest, pk=pk)
    
    is_admin = request.user.is_superuser or request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN' or (hasattr(request.user, 'roles') and request.user.roles.filter(name__icontains='admin').exists())
    if not is_admin:
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang dapat menghapus data manifest.")
        return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
        
    if request.method == 'POST':
        manifest.is_hidden = True
        manifest.save()
        messages.success(request, f"Data manifest {manifest.manifest_number} yang sudah di-void berhasil dihapus dari daftar!")
        
    return redirect(f"/operations/manifests/?type={manifest.manifest_type}")

@login_required
def api_verify_resi(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        resi_number = request.GET.get('resi_number', '').strip()
        purpose = request.GET.get('purpose', '').strip()
        if not resi_number:
            return JsonResponse({'status': 'error', 'message': 'Nomor resi kosong'}, status=400)
            
        try:
            # 1. Lookup by RTO number or AWB resi number
            rto_match = ReturnShipment.objects.filter(rto_number__iexact=resi_number).select_related('shipment').first()
            if rto_match:
                shipment = rto_match.shipment
            else:
                shipment = Shipment.objects.filter(resi_number__iexact=resi_number).first()
                if not shipment:
                    rto_match = ReturnShipment.objects.filter(rto_number__icontains=resi_number).select_related('shipment').first()
                    if rto_match:
                        shipment = rto_match.shipment

            if not shipment:
                raise Shipment.DoesNotExist
            
            # 1. Reject VOID shipments across all purposes
            if shipment.status == 'VOID':
                return JsonResponse({
                    'status': 'error',
                    'message': f'Resi {resi_number} berstatus VOID dan tidak dapat diproses.'
                }, status=400)
            
            # 2. Purpose-specific Anti-Double Scan Validations
            if purpose == 'transit':
                # ★ FLEKSIBEL (Scan Transit): Boleh discan berkali-kali untuk update status transit antar hub
                pass
            elif purpose == 'transfer':
                # Transfer Location (Manifest Transfer): Cegah double assignment ke Transfer Manifest lain
                active_transfer = shipment.manifests.filter(manifest_type='TRANSFER', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).first()
                if active_transfer:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah terdaftar di Transfer Manifest {active_transfer.manifest_number}!'
                    }, status=400)
                if shipment.status not in ['PENDING', 'PICKUP', 'INBOUND_ORIGIN', 'OUTGOING', 'TRANSFER', 'TRANSIT']:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} berstatus {shipment.get_status_display()}, tidak bisa dimasukkan ke Transfer Manifest.'
                    }, status=400)
            elif purpose == 'incoming':
                if shipment.status in ['INCOMING_DESTINATION', 'DELIVERY', 'POD', 'POD_BALIK']:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah berstatus {shipment.get_status_display()} dan tidak dapat di-scan Incoming kembali.'
                    }, status=400)
                active_inbound = shipment.inbound_sessions.filter(is_void=False, is_hidden=False).first()
                if active_inbound:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah tercatat pada dokumen Inbound {active_inbound.inbound_number}.'
                    }, status=400)
            elif purpose == 'delivery':
                if shipment.status in ['POD', 'POD_BALIK']:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah berstatus {shipment.get_status_display()} (pengiriman telah selesai).'
                    }, status=400)
                active_delivery = shipment.manifests.filter(manifest_type='DELIVERY', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).first()
                if active_delivery:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah terdaftar di Delivery Runsheet {active_delivery.manifest_number}.'
                    }, status=400)
            elif purpose == 'pod':
                if shipment.status in ['POD', 'POD_BALIK']:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah selesai berstatus {shipment.get_status_display()} (tidak dapat di-POD ulang).'
                    }, status=400)
            else:
                # Default / Outgoing Manifest: check if already in an active Outgoing manifest
                active_outgoing = shipment.manifests.filter(manifest_type='OUTGOING', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).first()
                if active_outgoing:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Resi {resi_number} sudah terdaftar di Outgoing Manifest {active_outgoing.manifest_number}.'
                    }, status=400)
                if shipment.status not in ['PENDING', 'PICKUP', 'INBOUND_ORIGIN', 'TRANSFER', 'TRANSIT']:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Resi {resi_number} berstatus {shipment.get_status_display()}, tidak bisa dimasukkan ke Outgoing Manifest.'
                    }, status=400)
                
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': shipment.id,
                    'resi_number': shipment.resi_number,
                    'scanned_code': resi_number,
                    'rto_number': rto_match.rto_number if rto_match else (shipment.return_record.rto_number if hasattr(shipment, 'return_record') and shipment.return_record else ''),
                    'origin': f"{shipment.get_tlc_origin} - {shipment.get_city_origin}",
                    'destination': f"{shipment.get_tlc_dest} - {shipment.get_city_dest}",
                    'service': shipment.get_service_type_display(),
                    'weight': float(shipment.chargeable_weight) if shipment.chargeable_weight else float(shipment.actual_weight),
                    'volume': float(shipment.volume_weight),
                    'colly': shipment.total_colly if shipment.total_colly else shipment.colly,
                    'is_cod': shipment.is_cod,
                    'cod_value': float(shipment.cod_value) if shipment.cod_value else 0,
                    'tipe': shipment.get_shipment_type_detail_display() if hasattr(shipment, 'get_shipment_type_detail_display') else '-'
                }
            })
        except Shipment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Resi {resi_number} tidak ditemukan!'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def api_verify_incoming(request):
    """Return eligible shipments from an Incoming Destination document."""
    from .models import InboundSession

    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        inbound_number = request.GET.get('inbound_number', '').strip()
        if not inbound_number:
            return JsonResponse({'status': 'error', 'message': 'Nomor Incoming kosong'}, status=400)

        try:
            inbound = InboundSession.objects.prefetch_related('shipments').get(
                inbound_number=inbound_number
            )
        except InboundSession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Incoming {inbound_number} tidak ditemukan.'}, status=404)

        if inbound.is_void:
            return JsonResponse({'status': 'error', 'message': f'Dokumen Inbound {inbound_number} berstatus VOID.'}, status=400)

        shipments = inbound.shipments.filter(status='INCOMING_DESTINATION')
        if not shipments.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Incoming {inbound_number} tidak memiliki resi yang siap Delivery.'
            }, status=400)

        data = []
        for shipment in shipments:
            data.append({
                'id': str(shipment.id),
                'resi_number': shipment.resi_number,
                'origin': f'{shipment.get_tlc_origin} - {shipment.get_city_origin}',
                'destination': f'{shipment.get_tlc_dest} - {shipment.get_city_dest}',
                'service': shipment.get_service_type_display(),
                'weight': float(shipment.chargeable_weight) if shipment.chargeable_weight else float(shipment.actual_weight),
                'colly': shipment.total_colly if shipment.total_colly else shipment.colly,
                'incoming_number': inbound.inbound_number,
                'is_cod': shipment.is_cod,
                'cod_value': float(shipment.cod_value) if shipment.cod_value else 0,
                'tipe': shipment.get_shipment_type_detail_display() if hasattr(shipment, 'get_shipment_type_detail_display') else '-'
            })
        return JsonResponse({'status': 'success', 'data': data})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def api_verify_manifest(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        manifest_number = request.GET.get('manifest_number', '').strip()
        purpose = request.GET.get('purpose', '').strip()
        if not manifest_number:
            return JsonResponse({'status': 'error', 'message': 'Nomor manifest kosong'}, status=400)
            
        try:
            if purpose == 'incoming':
                manifest = Manifest.objects.get(manifest_number=manifest_number)
            elif purpose == 'transit':
                # Scan Transit accepts Transfer manifests for flexible multi-scan checkpoints
                manifest = Manifest.objects.get(manifest_number=manifest_number, manifest_type='TRANSFER')
            elif purpose == 'transfer':
                # Transfer Location loads Outgoing manifests to be moved by a transfer manifest
                manifest = Manifest.objects.get(manifest_number=manifest_number, manifest_type='OUTGOING')
                active_transfer = Manifest.objects.filter(manifest_type='TRANSFER', is_hidden=False).exclude(status__in=['CANCELLED', 'VOID']).filter(shipments__in=manifest.shipments.all()).first()
                if active_transfer:
                    return JsonResponse({'status': 'error', 'message': f'Manifest Outgoing {manifest_number} sudah terdaftar pada Transfer Manifest {active_transfer.manifest_number}!'}, status=400)
            elif purpose in ('pod', 'delivery'):
                manifest = Manifest.objects.prefetch_related('shipments').get(manifest_number=manifest_number)
            else:
                manifest = Manifest.objects.get(manifest_number=manifest_number, manifest_type='OUTGOING')
            
            if manifest.status == 'CANCELLED':
                return JsonResponse({'status': 'error', 'message': f'Manifest {manifest_number} berstatus VOID/CANCELLED.'}, status=400)

            # Ambil semua ID resi yang ada di dalam manifest ini
            shipment_ids = list(manifest.shipments.values_list('id', flat=True))
            
            if not shipment_ids:
                return JsonResponse({'status': 'error', 'message': f'Manifest {manifest_number} kosong (tidak ada resi)'}, status=400)

            if purpose in ('pod', 'delivery'):
                shipments_data = []
                for s in manifest.shipments.all():
                    if s.status == 'VOID':
                        continue
                    if purpose == 'delivery' and s.status in ['POD', 'POD_BALIK']:
                        continue
                    shipments_data.append({
                        'id': str(s.id),
                        'resi_number': s.resi_number,
                        'origin': f"{s.get_tlc_origin} - {s.get_city_origin}",
                        'destination': f"{s.get_tlc_dest} - {s.get_city_dest}",
                        'service': s.get_service_type_display(),
                        'weight': float(s.chargeable_weight) if s.chargeable_weight else (float(s.actual_weight) if s.actual_weight else 0),
                        'colly': s.total_colly if s.total_colly else (s.colly if s.colly else 1),
                        'is_cod': s.is_cod,
                        'cod_value': float(s.cod_value) if s.cod_value else 0,
                        'tipe': s.get_shipment_type_detail_display() if hasattr(s, 'get_shipment_type_detail_display') else '-'
                    })
                if not shipments_data:
                    return JsonResponse({'status': 'error', 'message': f'Semua resi di Manifest {manifest_number} sudah selesai (POD) atau tidak valid.'}, status=400)
                return JsonResponse({
                    'status': 'success',
                    'data': {
                        'id': manifest.id,
                        'manifest_number': manifest.manifest_number,
                        'shipments': shipments_data,
                        'total_shipments': len(shipments_data)
                    }
                })

            # Transfer Location manifests can leave branch/destination_city
            # empty even though every shipment already has the canonical
            # origin and destination. Use that shipment route as the source
            # for the scan queue so TLC and city labels are always present.
            first_shipment = manifest.shipments.order_by('id').first()
            if first_shipment:
                origin_label = f"{first_shipment.get_tlc_origin} - {first_shipment.get_city_origin}"
                destination_label = f"{first_shipment.get_tlc_dest} - {first_shipment.get_city_dest}"
            else:
                origin_label = manifest.branch.name if manifest.branch else '-'
                destination_label = f"{manifest.get_tlc_dest} - {manifest.get_city_dest}"
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': manifest.id,
                    'manifest_number': manifest.manifest_number,
                    'origin': origin_label,
                    'hub': destination_label,
                    'destination': destination_label,
                    'colly': manifest.colly_cmo,
                    'weight': float(manifest.actual_weight),
                    'description': manifest.description or '-',
                    'shipment_ids': shipment_ids
                }
            })
        except Manifest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Manifest / Delivery {manifest_number} tidak ditemukan!'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ==============================================================================
# TRACKING MANAGER & TIMELINE APIS (Solutions 1, 2, 3)
# ==============================================================================

@login_required
def api_tracking_list(request, shipment_pk):
    """Return JSON list of tracking checkpoints for a shipment with chronological warnings."""
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak: Hanya Admin/Superadmin yang dapat mengakses kelola riwayat.'}, status=403)
        
    shipment = get_object_or_404(Shipment, pk=shipment_pk)
    history = shipment.tracking_history.all().order_by('step_order', 'occurred_at', 'timestamp')
    
    data = []
    prev_time = None
    for item in history:
        has_time_warning = False
        warning_msg = ""
        # Check time warning only if earlier by full minutes (ignoring sub-minute seconds difference on same minute)
        if prev_time and item.occurred_at.replace(second=0, microsecond=0) < prev_time.replace(second=0, microsecond=0):
            has_time_warning = True
            warning_msg = f"Waktu ({timezone.localtime(item.occurred_at).strftime('%d/%m/%Y %H:%M')}) lebih awal dari langkah sebelumnya ({timezone.localtime(prev_time).strftime('%d/%m/%Y %H:%M')})."
        prev_time = item.occurred_at

        data.append({
            'id': item.id,
            'status': item.status,
            'status_display': item.get_status_display(),
            'location': item.location,
            'formatted_location': item.formatted_location,
            'description': item.description or '',
            'occurred_at_raw': item.occurred_at.isoformat(),
            'event_date': timezone.localtime(item.occurred_at).strftime('%Y-%m-%d'),
            'event_time': timezone.localtime(item.occurred_at).strftime('%H:%M'),
            'occurred_at_formatted': timezone.localtime(item.occurred_at).strftime('%d %b %Y, %H:%M'),
            'step_order': item.step_order,
            'has_time_warning': has_time_warning,
            'warning_msg': warning_msg,
        })
        
    # Return newest at the top (descending: latest status at the top of modal table)
    data.reverse()
        
    return JsonResponse({
        'status': 'success',
        'shipment': {
            'id': shipment.id,
            'resi_number': shipment.resi_number,
            'status': shipment.status,
            'status_display': shipment.get_status_display(),
            'origin': f"{shipment.get_tlc_origin} - {shipment.get_city_origin}",
            'destination': f"{shipment.get_tlc_dest} - {shipment.get_city_dest}",
            'created_at_formatted': timezone.localtime(shipment.created_at).strftime('%d %b %Y, %H:%M'),
        },
        'checkpoints': data,
        'status_choices': [{'value': val, 'label': label} for val, label in Shipment.STATUS_CHOICES],
    })


@login_required
def api_tracking_update(request, pk):
    """Update an existing tracking checkpoint (Solusi 1 & 2)."""
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak: Hanya Admin/Superadmin yang dapat mengedit riwayat tracking.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method POST required'}, status=405)
        
    tracking = get_object_or_404(Tracking, pk=pk)
    shipment = tracking.shipment
    
    status = request.POST.get('status', tracking.status)
    location = request.POST.get('location', tracking.location).strip()
    description = request.POST.get('description', tracking.description).strip()
    event_date = request.POST.get('event_date', '').strip()
    event_time = request.POST.get('event_time', '').strip()
    step_order = request.POST.get('step_order')
    
    if event_date and event_time:
        try:
            local_dt = DateTime.strptime(f'{event_date} {event_time}', '%Y-%m-%d %H:%M')
            tracking.occurred_at = timezone.make_aware(local_dt, timezone.get_current_timezone())
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Format tanggal/jam kejadian tidak valid.'}, status=400)
            
    tracking.status = status
    tracking.location = location
    tracking.description = description
    if step_order is not None and str(step_order).isdigit():
        tracking.step_order = int(step_order)
    tracking.save()
    
    # Auto-sync shipment current status to the highest step / latest tracking (Solusi 1)
    latest_track = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp').first()
    if latest_track:
        shipment.status = latest_track.status
        shipment.save(update_fields=['status'])
        
    from apps.audit.utils import log_action
    log_action(
        user=request.user,
        action=f"[TRACKING EDIT] Mengubah riwayat ID #{tracking.id} ({tracking.get_status_display()}) pada resi {shipment.resi_number}",
        module="Operations",
        obj=shipment,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({'status': 'success', 'message': 'Riwayat tracking berhasil diperbarui!'})


@login_required
def api_tracking_create(request, shipment_pk):
    """Add a new tracking checkpoint to a shipment (Solusi 1 & 2)."""
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak: Hanya Admin/Superadmin yang dapat menambah riwayat tracking.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method POST required'}, status=405)
        
    shipment = get_object_or_404(Shipment, pk=shipment_pk)
    
    status = request.POST.get('status', 'TRANSIT')
    location = request.POST.get('location', '').strip()
    description = request.POST.get('description', '').strip()
    event_date = request.POST.get('event_date', '').strip()
    event_time = request.POST.get('event_time', '').strip()
    step_order = request.POST.get('step_order')
    
    occurred_at = timezone.now()
    if event_date and event_time:
        try:
            local_dt = DateTime.strptime(f'{event_date} {event_time}', '%Y-%m-%d %H:%M')
            occurred_at = timezone.make_aware(local_dt, timezone.get_current_timezone())
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Format tanggal/jam kejadian tidak valid.'}, status=400)
            
    if step_order and str(step_order).isdigit():
        order_val = int(step_order)
    else:
        max_order = shipment.tracking_history.aggregate(models.Max('step_order'))['step_order__max'] or 0
        order_val = max_order + 10
    
    new_track = Tracking.objects.create(
        shipment=shipment,
        status=status,
        location=location,
        description=description,
        occurred_at=occurred_at,
        step_order=order_val
    )
    
    # Auto-sync shipment status
    latest_track = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp').first()
    if latest_track:
        shipment.status = latest_track.status
        shipment.save(update_fields=['status'])
        
    from apps.audit.utils import log_action
    log_action(
        user=request.user,
        action=f"[TRACKING ADD] Menambah riwayat status {new_track.get_status_display()} pada resi {shipment.resi_number}",
        module="Operations",
        obj=shipment,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({'status': 'success', 'message': 'Titik riwayat baru berhasil ditambahkan!'})


@login_required
def api_tracking_delete(request, pk):
    """Delete a tracking checkpoint (Solusi 1)."""
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak: Hanya Admin/Superadmin yang dapat menghapus riwayat tracking.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method POST required'}, status=405)
        
    tracking = get_object_or_404(Tracking, pk=pk)
    shipment = tracking.shipment
    track_desc = f"{tracking.get_status_display()} di {tracking.location}"
    tracking.delete()
    
    # Auto-sync shipment status after deletion
    latest_track = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp').first()
    if latest_track:
        shipment.status = latest_track.status
    else:
        shipment.status = 'PENDING'
    shipment.save(update_fields=['status'])
    
    from apps.audit.utils import log_action
    log_action(
        user=request.user,
        action=f"[TRACKING DELETE] Menghapus riwayat ({track_desc}) pada resi {shipment.resi_number}",
        module="Operations",
        obj=shipment,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    return JsonResponse({'status': 'success', 'message': 'Log riwayat berhasil dihapus dan status resi disinkronkan.'})


@login_required
def api_tracking_reorder(request, shipment_pk):
    """Reorder tracking checkpoints manually by list of IDs in chronological order with workflow validation."""
    import json
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method POST required'}, status=405)
        
    shipment = get_object_or_404(Shipment, pk=shipment_pk)
    
    try:
        data = json.loads(request.body)
        ordered_ids = data.get('ordered_ids', [])
    except Exception:
        ordered_ids = request.POST.getlist('ordered_ids[]') or request.POST.getlist('ordered_ids')
        
    if not ordered_ids:
        return JsonResponse({'status': 'error', 'message': 'Daftar ID urutan kosong.'}, status=400)

    # Validasi: Status POD (Terkirim) tidak boleh ditaruh sebelum Delivery atau tahapan operasional aktif
    tracks_by_id = {t.id: t for t in shipment.tracking_history.all()}
    ordered_tracks = [tracks_by_id[int(t_id)] for t_id in ordered_ids if int(t_id) in tracks_by_id]
    
    seen_terminal = False
    for t in ordered_tracks:
        if t.status in ['POD', 'POD_BALIK', 'RETURNED']:
            seen_terminal = True
        elif seen_terminal and t.status in ['DELIVERY', 'INCOMING_DESTINATION', 'TRANSIT', 'TRANSFER', 'OUTGOING', 'INBOUND_ORIGIN', 'PICKUP', 'PENDING']:
            return JsonResponse({
                'status': 'error',
                'message': f'Status {t.get_status_display()} tidak dapat diletakkan setelah status Terkirim (POD). Status POD harus menjadi alur akhir pengantaran.'
            }, status=400)
        
    # ordered_ids is from Step 1 (earliest) to Step N (latest)
    for idx, track_id in enumerate(ordered_ids, 1):
        Tracking.objects.filter(id=track_id, shipment=shipment).update(step_order=idx * 10)
        
    # Auto-sync shipment status with the highest step order
    latest_track = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp').first()
    if latest_track:
        shipment.status = latest_track.status
        shipment.save(update_fields=['status'])
        
    return JsonResponse({'status': 'success', 'message': 'Urutan langkah alur pengiriman berhasil diperbarui!'})


@login_required
def api_tracking_auto_align(request, shipment_pk):
    """Auto-align step_order based on occurred_at and workflow hierarchy (Delivery before POD)."""
    from django.shortcuts import get_object_or_404
    if not is_admin_or_superadmin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Akses ditolak.'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method POST required'}, status=405)
        
    shipment = get_object_or_404(Shipment, pk=shipment_pk)
    
    STATUS_WORKFLOW_WEIGHT = {
        'PENDING': 10,
        'PICKUP': 20,
        'INBOUND_ORIGIN': 30,
        'OUTGOING': 40,
        'TRANSFER': 50,
        'TRANSIT': 60,
        'INCOMING_DESTINATION': 70,
        'DELIVERY': 80,
        'POD': 90,
        'POD_BALIK': 95,
        'RETURNED': 99,
        'VOID': 100,
    }
    
    tracks = list(shipment.tracking_history.all())
    # Sort primarily by minute-truncated occurred_at, then by workflow weight hierarchy, then actual seconds
    tracks.sort(key=lambda t: (
        t.occurred_at.replace(second=0, microsecond=0),
        STATUS_WORKFLOW_WEIGHT.get(t.status, 50),
        t.occurred_at,
        t.timestamp
    ))
    
    prev_dt = None
    for idx, track in enumerate(tracks, 1):
        track.step_order = idx * 10
        # If timestamp is slightly behind previous step within same minute, align to at least match previous step
        if prev_dt and track.occurred_at < prev_dt:
            track.occurred_at = prev_dt
        track.save(update_fields=['step_order', 'occurred_at'])
        prev_dt = track.occurred_at
        
    latest_track = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp').first()
    if latest_track:
        shipment.status = latest_track.status
        shipment.save(update_fields=['status'])
        
    return JsonResponse({'status': 'success', 'message': 'Urutan alur berhasil diselaraskan otomatis berdasarkan waktu kejadian!'})

@login_required
def manifest_create(request):
    from .forms import ManifestForm
    manifest_type = request.GET.get('type', 'OUTGOING')
    mode = request.POST.get('mode', request.GET.get('mode', ''))

    if request.method == 'POST':
        form = ManifestForm(request.POST)
        if form.is_valid():
            manifest = form.save(commit=False)
            
            if not manifest.manifest_number:
                import datetime
                today = datetime.date.today()
                date_str = today.strftime('%Y%m%d')
                
                if manifest.manifest_type == 'TRANSFER':
                    prefix = f"TRF-{date_str}-"
                elif manifest.manifest_type == 'DELIVERY':
                    prefix = f"DEL-{date_str}-"
                else:
                    prefix = f"MNF-{date_str}-"
                    
                last_manifest = Manifest.objects.filter(manifest_number__startswith=prefix).order_by('-manifest_number').first()
                if last_manifest:
                    try:
                        last_num = int(last_manifest.manifest_number.split('-')[-1])
                    except ValueError:
                        last_num = 0
                    new_num = last_num + 1
                else:
                    new_num = 1
                manifest.manifest_number = f"{prefix}{new_num:04d}"
            
            if mode == 'BYPASS':
                manifest.is_bypass = True
            elif mode == 'BIASA':
                manifest.is_bypass = False
                
            manifest.created_by = request.user
            manifest.save()
            form.save_m2m()

            if manifest.manifest_type == 'DELIVERY':
                delivery_shipments = manifest.shipments.all()
                manifest.actual_weight = sum(
                    (shipment.chargeable_weight or shipment.weight or 0)
                    for shipment in delivery_shipments
                )
                manifest.colly_cmo = sum(
                    (shipment.total_colly or 1) for shipment in delivery_shipments
                )
                manifest.save(update_fields=['actual_weight', 'colly_cmo'])
            
            # Delivery creates a delivery runsheet; other manifest types keep
            # their existing status transitions.
            if manifest.manifest_type == 'TRANSFER':
                target_status = 'TRANSFER'
            elif manifest.manifest_type == 'DELIVERY':
                target_status = 'DELIVERY'
            else:
                target_status = 'OUTGOING'
            for shipment in manifest.shipments.all():
                shipment.status = target_status
                shipment.save()
                
                if manifest.driver:
                    vehicle_text = f"Driver {manifest.driver.get_full_name() or manifest.driver.username}"
                elif manifest.vehicle:
                    vehicle_text = f"Kendaraan {manifest.vehicle.plate_number}"
                elif manifest.vendor:
                    vehicle_text = f"Vendor {manifest.vendor.name}"
                elif getattr(manifest, 'vendor_middle', None):
                    vehicle_text = f"Vendor {manifest.vendor_middle.name}"
                else:
                    vehicle_text = "Kurir Kargo"
                    
                Tracking.objects.create(
                    shipment=shipment,
                    status=target_status,
                    location=(manifest.branch.name if manifest.branch else vehicle_text),
                    description='Paket telah diberangkatkan ke kota tujuan'
                )
            
            messages.success(request, f"Manifest {manifest.manifest_number} berhasil diproses dengan {manifest.shipments.count()} resi!")
            return redirect(f"/operations/manifests/?type={manifest.manifest_type}")
    else:
        import datetime
        from apps.master.models import Coverage

        initial_data = {
            'manifest_type': manifest_type,
            'date': datetime.date.today(),
        }

        # Load preselected shipments if any
        raw_resi_ids = request.GET.getlist('resi_ids')
        resi_ids = []
        for r in raw_resi_ids:
            for item in str(r).split(','):
                if item.strip().isdigit():
                    resi_ids.append(int(item.strip()))
        preloaded_shipments = []
        if resi_ids:
            preloaded_shipments = list(Shipment.objects.filter(id__in=resi_ids).select_related('destination_coverage'))
            if preloaded_shipments:
                first_s = preloaded_shipments[0]
                dest_city = ''
                if first_s.destination_coverage and first_s.destination_coverage.city:
                    dest_city = first_s.destination_coverage.city
                elif first_s.receiver_city:
                    cov = Coverage.objects.filter(city__iexact=first_s.receiver_city, is_active=True).first()
                    if not cov:
                        cov = Coverage.objects.filter(city__icontains=first_s.receiver_city, is_active=True).first()
                    dest_city = cov.city if cov else first_s.receiver_city
                elif first_s.destination:
                    cov = Coverage.objects.filter(city__iexact=first_s.destination, is_active=True).first()
                    if not cov:
                        cov = Coverage.objects.filter(city__icontains=first_s.destination, is_active=True).first()
                    dest_city = cov.city if cov else first_s.destination

                initial_data['destination_city'] = dest_city
                initial_data['colly_cmo'] = sum((s.total_colly or 1) for s in preloaded_shipments)
                initial_data['actual_weight'] = sum((s.chargeable_weight or s.weight or 0) for s in preloaded_shipments)
                
                commodities = [s.description_item for s in preloaded_shipments if s.description_item]
                if commodities:
                    initial_data['commodity'] = commodities[0]

        form = ManifestForm(initial=initial_data)
        
    from django.core.paginator import Paginator
    delivery_history = Tracking.objects.filter(
        status='DELIVERY'
    ).select_related('shipment').prefetch_related(
        'shipment__tracking_history', 'shipment__manifests'
    ).order_by('-occurred_at', '-timestamp')
    delivery_page = Paginator(delivery_history, 10).get_page(request.GET.get('page'))

    return render(request, 'operations/manifests/manifest_edit.html', {
        'form': form,
        'manifest_type': manifest_type,
        'mode': mode,
        'is_edit': False,
        'preloaded_shipments': preloaded_shipments if 'preloaded_shipments' in locals() else [],
        'recent_deliveries': delivery_page if manifest_type == 'DELIVERY' else [],
    })


@login_required
def manifest_bulk_update_status(request):
    """Bulk update status for selected manifests and their shipments."""
    from django.contrib import messages
    from .models import Manifest, Tracking
    from django.utils import timezone
    
    if request.method != 'POST':
        return redirect('operations:manifest-list')
    
    raw_manifest_ids = request.POST.getlist('manifest_ids')
    manifest_ids = []
    for m in raw_manifest_ids:
        for item in str(m).split(','):
            if item.strip().isdigit():
                manifest_ids.append(int(item.strip()))
                
    action_type = request.POST.get('action_type', 'ON_THE_WAY')
    location = request.POST.get('location', '').strip()
    description = request.POST.get('description', '').strip()
    manifest_type = request.POST.get('manifest_type', 'OUTGOING')
    
    if not manifest_ids:
        messages.warning(request, "Pilih minimal satu manifest untuk diperbarui.")
        return redirect(f"/operations/manifests/?type={manifest_type}")
        
    manifests = Manifest.objects.filter(id__in=manifest_ids, is_hidden=False)
    updated_manifest_count = 0
    updated_shipment_count = 0
    
    for manifest in manifests:
        if action_type == 'ON_THE_WAY':
            manifest.status = 'ON_THE_WAY'
            manifest.save(update_fields=['status'])
            
            loc = location or (manifest.branch.name if manifest.branch else 'Hub Transit / Linehaul')
            desc = description or f"Manifest {manifest.manifest_number} dalam perjalanan (On The Way)"
            
            for shipment in manifest.shipments.all():
                shipment.status = 'ON_THE_WAY'
                shipment.save(update_fields=['status'])
                Tracking.objects.create(
                    shipment=shipment,
                    status='ON_THE_WAY',
                    location=loc,
                    description=desc,
                    occurred_at=timezone.now()
                )
                updated_shipment_count += 1
            updated_manifest_count += 1
            
        elif action_type == 'COMPLETED':
            manifest.status = 'COMPLETED'
            manifest.save(update_fields=['status'])
            updated_manifest_count += 1
            
    messages.success(request, f"Berhasil memperbarui {updated_manifest_count} manifest dan {updated_shipment_count} resi ke status {action_type}.")
    return redirect(f"/operations/manifests/?type={manifest_type}")


@login_required
def manifest_bulk_incoming(request):
    """Bulk process selected manifests (Outgoing / Transfer) directly into Incoming Destination."""
    from django.contrib import messages
    from .models import Manifest, Shipment, Tracking, InboundSession
    from django.utils import timezone
    
    if request.method != 'POST':
        return redirect('operations:incoming-list')
        
    raw_manifest_ids = request.POST.getlist('manifest_ids')
    manifest_ids = []
    for m in raw_manifest_ids:
        for item in str(m).split(','):
            if item.strip().isdigit():
                manifest_ids.append(int(item.strip()))
                
    location = request.POST.get('location', '').strip() or 'Gudang Tujuan (Destination Hub)'
    description = request.POST.get('description', '').strip() or 'Paket tiba dan diterima di Hub Tujuan'
    
    if not manifest_ids:
        messages.warning(request, "Pilih minimal satu manifest untuk diproses ke Incoming Destination.")
        return redirect('operations:incoming-list')
        
    manifests = Manifest.objects.filter(id__in=manifest_ids, is_hidden=False)
    all_shipments = Shipment.objects.filter(manifests__in=manifests, is_hidden=False).distinct()
    
    if not all_shipments.exists():
        messages.warning(request, "Tidak ada resi aktif di dalam manifest yang dipilih.")
        return redirect('operations:incoming-list')
        
    inbound_session = InboundSession.objects.create(
        location=location,
        description=description
    )
    
    count = 0
    for shipment in all_shipments:
        inbound_session.shipments.add(shipment)
        shipment.status = 'INCOMING_DESTINATION'
        shipment.save(update_fields=['status'])
        
        Tracking.objects.create(
            shipment=shipment,
            status='INCOMING_DESTINATION',
            location=location,
            description=description,
            occurred_at=timezone.now()
        )
        count += 1
        
    messages.success(request, f"Sukses! {count} resi dari {manifests.count()} manifest berhasil diproses ke Incoming Destination ({inbound_session.inbound_number}).")
    return redirect('operations:incoming-list')


@login_required
def bulk_pod_update(request):
    """Bulk update selected shipments or inbound sessions to POD / POD_BALIK."""
    from django.contrib import messages
    from .models import Shipment, Tracking
    from django.utils import timezone
    from datetime import datetime as DateTime
    
    if request.method != 'POST':
        return redirect('operations:pod_list')
        
    raw_shipment_ids = request.POST.getlist('shipment_ids')
    shipment_ids = []
    for s in raw_shipment_ids:
        for item in str(s).split(','):
            if item.strip().isdigit():
                shipment_ids.append(int(item.strip()))
                
    raw_inbound_ids = request.POST.getlist('inbound_ids')
    inbound_ids = []
    for i in raw_inbound_ids:
        for item in str(i).split(','):
            if item.strip().isdigit():
                inbound_ids.append(int(item.strip()))
                
    if inbound_ids:
        inbound_shipment_ids = Shipment.objects.filter(inbound_sessions__id__in=inbound_ids, is_hidden=False).values_list('id', flat=True)
        shipment_ids.extend(list(inbound_shipment_ids))
        
    shipment_ids = list(set(shipment_ids))
    
    if not shipment_ids:
        messages.warning(request, "Pilih minimal satu resi / inbound untuk diperbarui ke POD.")
        return redirect('operations:pod_list')
        
    pod_status = request.POST.get('pod_status', 'POD').strip() # 'POD' or 'POD_BALIK'
    receiver_name = request.POST.get('pod_receiver_name', '').strip()
    location = request.POST.get('location', '').strip()
    description = request.POST.get('description', '').strip()
    event_date = request.POST.get('event_date', '').strip()
    event_time = request.POST.get('event_time', '').strip()
    
    occurred_at = timezone.now()
    if event_date and event_time:
        try:
            occurred_at = timezone.make_aware(DateTime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M'))
        except Exception:
            pass
            
    uploaded_file = request.FILES.get('pod_image')
    processed_image = None
    if uploaded_file:
        processed_image = compress_pod_image(uploaded_file)
        
    shipments = Shipment.objects.filter(id__in=shipment_ids, is_hidden=False)
    success_count = 0
    
    for shipment in shipments:
        eff_receiver = receiver_name or shipment.receiver_name or "Penerima"
        eff_location = location or shipment.destination or "Tujuan"
        eff_desc = description or (f"Paket telah diserahkan dan diterima oleh {eff_receiver}" if pod_status == 'POD' else "POD Balik / Surat Jalan Kembali telah diterima")
        
        shipment.status = pod_status
        shipment.pod_receiver_name = eff_receiver
        shipment.pod_date = occurred_at
        if processed_image:
            shipment.pod_image = processed_image
        shipment.save()
        
        Tracking.objects.create(
            shipment=shipment,
            status=pod_status,
            location=eff_location,
            description=eff_desc,
            occurred_at=occurred_at
        )
        success_count += 1
        
    messages.success(request, f"Sukses! {success_count} resi berhasil diperbarui ke status {pod_status}.")
    return redirect('operations:pod_list')


@login_required
def tracking_view(request):
    query = request.GET.get('resi', '').strip()
    shipment = None
    tracking_history = None
    error_msg = None
    
    if query:
        try:
            shipment = Shipment.objects.get(resi_number=query)
            tracking_history = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp')
            
            # Jika belum ada riwayat tracking tapi resinya ada, kita buatkan data dummy otomatis (untuk demo)
            if not tracking_history.exists():
                from .models import Tracking
                # Riwayat 1: Dibuat
                Tracking.objects.create(
                    shipment=shipment,
                    status='PENDING',
                    location=shipment.origin,
                    description='Resi pengiriman telah diterbitkan, menunggu penjemputan',
                    step_order=10
                )
                
                if shipment.status in ['TRANSFER', 'POD']:
                    # Riwayat 2: Di jalan
                    Tracking.objects.create(
                        shipment=shipment,
                        status='TRANSIT',
                        location='Gudang Transit Pusat',
                        description='Paket sedang dalam perjalanan menuju tujuan',
                        step_order=20
                    )
                
                if shipment.status == 'POD':
                    # Riwayat 3: Terkirim
                    Tracking.objects.create(
                        shipment=shipment,
                        status='POD',
                        location=shipment.destination,
                        description=f'Paket telah diterima oleh {shipment.receiver_name}',
                        step_order=30
                    )
                
                tracking_history = shipment.tracking_history.all().order_by('-step_order', '-occurred_at', '-timestamp')
                
        except Shipment.DoesNotExist:
            error_msg = f"Resi dengan nomor {query} tidak ditemukan."
            
    return render(request, 'operations/tracking/tracking.html', {
        'shipment': shipment,
        'tracking_history': tracking_history,
        'query': query,
        'error_msg': error_msg
    })

@login_required
def scan_barcode(request):
    if request.method == 'POST':
        resi_number = request.POST.get('resi_number', '').strip()
        status = request.POST.get('status', 'TRANSIT')
        location = request.POST.get('location', '')
        description = request.POST.get('description', '')
        
        if resi_number:
            try:
                shipment = Shipment.objects.get(resi_number=resi_number)
                Tracking.objects.create(
                    shipment=shipment,
                    status=status,
                    location=location,
                    description=description
                )
                shipment.status = status
                shipment.save()
                messages.success(request, f"Resi {resi_number} berhasil diperbarui ke status {status}.")
            except Shipment.DoesNotExist:
                messages.error(request, f"Resi {resi_number} tidak ditemukan di sistem.")
        return redirect('operations:scan-barcode')
        
    return render(request, 'operations/tracking/scan_barcode.html')

def api_get_client_detail(request):
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'status': 'error', 'message': 'client_id is required'}, status=400)
        
    try:
        from apps.crm.models import Client
        client = Client.objects.get(pk=client_id)
        return JsonResponse({
            'status': 'success',
            'name': client.pic_name if hasattr(client, 'pic_name') and client.pic_name else client.company_name,
            'company': client.company_name,
            'address': client.address if hasattr(client, 'address') else '',
            'city': client.city if hasattr(client, 'city') else '',
            'postal_code': client.postal_code if hasattr(client, 'postal_code') else '',
            'phone': client.phone if hasattr(client, 'phone') else ''
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

from django.http import JsonResponse
from apps.crm.models import Contract, Quotation

from apps.master.models import Price

@login_required
def api_get_contract_price(request):
    client_id = request.GET.get('client_id')
    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    service_type = request.GET.get('service_type')
    
    # 1. Try Contract/Quotation if Client is provided
    if client_id:
        try:
            contracts = Contract.objects.filter(client_id=client_id)
            if contracts.exists():
                contract = contracts.first()
                return JsonResponse({
                    'price_per_kg': float(contract.harga),
                    'source': 'contract',
                    'asal': contract.asal,
                    'tujuan': contract.tujuan,
                    'service': contract.service
                })
                
            quotations = Quotation.objects.filter(lead__client_id=client_id, status='APPROVED')
            if quotations.exists():
                quotation = quotations.first()
                return JsonResponse({
                    'price_per_kg': float(quotation.price_per_kg),
                    'source': 'quotation',
                    'asal': quotation.origin,
                    'tujuan': quotation.destination,
                    'service': quotation.service
                })
        except Exception as e:
            pass  # Fall through to Master Price
            
    # 2. Fallback to Master Price
    if origin and destination and service_type:
        try:
            # check if origin and destination are numeric IDs
            query_kwargs = {'service__code': service_type}
            if origin.isdigit():
                query_kwargs['origin_id'] = int(origin)
            else:
                query_kwargs['origin__city__iexact'] = origin
                
            if destination.isdigit():
                query_kwargs['destination_id'] = int(destination)
            else:
                query_kwargs['destination__city__iexact'] = destination
                
            master_price = Price.objects.filter(**query_kwargs).first()
            
            if master_price:
                return JsonResponse({
                    'price_per_kg': float(master_price.price_per_kg),
                    'source': 'master_price',
                    'asal': str(master_price.origin),
                    'tujuan': str(master_price.destination),
                    'service': master_price.service.code
                })
        except Exception as e:
            return JsonResponse({'error': str(e), 'price_per_kg': 0, 'source': 'error'})
            
    return JsonResponse({'price_per_kg': 0, 'source': 'none'})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_driver_manifests(request):
    """
    Returns today's active manifests and shipments for the logged-in driver.
    """
    driver_name = request.user.get_full_name() or request.user.username
    
    # In a real system, driver matches exactly with the manifest driver ID.
    # For now, we search by name or just return active ones.
    manifests = Manifest.objects.filter(
        status__in=['PREPARING', 'ON_THE_WAY']
    ).order_by('-date')
    
    data = []
    for m in manifests:
        shipments_data = []
        for s in m.shipments.all():
            shipments_data.append({
                'id': s.id,
                'resi_number': s.resi_number,
                'receiver_name': s.receiver_name,
                'destination': s.destination,
                'receiver_address': s.receiver_address,
                'status': s.status,
                'weight': float(s.weight),
            })
            
        data.append({
            'id': m.id,
            'manifest_number': m.manifest_number,
            'driver_name': m.driver.first_name if m.driver else 'Tanpa Supir',
            'vehicle_number': m.vehicle.plate_number if m.vehicle else '-',
            'status': m.status,
            'shipments': shipments_data
        })
        
    return Response({'manifests': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_driver_update_status(request):
    """
    Update shipment status from mobile app.
    Payload: {'resi_number': '...', 'status': 'DELIVERED', 'location': '...', 'description': '...', 'pod_image': 'base64/url'}
    """
    resi_number = request.data.get('resi_number')
    status = request.data.get('status')
    location = request.data.get('location', '')
    description = request.data.get('description', '')
    
    if not resi_number or not status:
        return Response({'error': 'resi_number and status are required'}, status=400)
        
    try:
        shipment = Shipment.objects.get(resi_number=resi_number)
        
        # 1. Update Shipment Status
        shipment.status = status
        shipment.save() # This triggers auto_create_finance_transaction if DELIVERED!
        
        # 2. Add Tracking History
        Tracking.objects.create(
            shipment=shipment,
            status=status,
            location=location,
            description=description
        )
        
        # 3. Check if all shipments in its Manifest are DELIVERED, then close Manifest
        for manifest in shipment.manifests.all():
            if not manifest.shipments.exclude(status='POD').exists():
                manifest.status = 'COMPLETED'
                manifest.save()
                
        return Response({'success': True, 'message': f'Resi {resi_number} updated to {status}'})
        
    except Shipment.DoesNotExist:
        return Response({'error': 'Shipment not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@login_required
def print_bulky(request):
    from django.shortcuts import render
    from django.http import JsonResponse, HttpResponse
    from django.template.loader import render_to_string
    from django.utils import timezone
    from django.conf import settings
    from xhtml2pdf import pisa
    from .models import Shipment, Tracking, Manifest
    from apps.master.models import Coverage
    import os

    # 1. AJAX Check / Search Resi Numbers
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('action') == 'search':
        raw_resis = request.GET.get('resis', '') or request.POST.get('resis', '')
        # Split by newline, comma, space, semicolon
        import re
        tokens = [t.strip() for t in re.split(r'[\r\n,;\s]+', raw_resis) if t.strip()]
        
        found_shipments = []
        not_found = []
        
        if tokens:
            shipments_qs = Shipment.objects.filter(is_hidden=False, resi_number__in=tokens).select_related('client', 'service_master')
            shipments_map = {s.resi_number: s for s in shipments_qs}
            
            for token in tokens:
                if token in shipments_map:
                    s = shipments_map[token]
                    can_epod = s.status in ['POD', 'POD_BALIK', 'DELIVERED', 'DELIVERY'] or bool(s.pod_image or s.pod_date)
                    found_shipments.append({
                        'id': s.id,
                        'resi_number': s.resi_number,
                        'reference_no': s.reference_no or '-',
                        'customer_code': s.client.customer_code if s.client else '-',
                        'sender': s.client.name if (s.client and s.client.name) else (s.sender_name or '-'),
                        'receiver': s.receiver_name or '-',
                        'origin': f"{s.get_tlc_origin} - {s.get_city_origin}",
                        'destination': f"{s.get_tlc_dest} - {s.get_city_dest}",
                        'service': s.service_master.service_name if s.service_master else (s.service_type or 'REGULER'),
                        'colly': s.total_colly or 1,
                        'weight': float(s.chargeable_weight or s.weight or 0),
                        'status': s.status,
                        'status_display': s.get_status_display(),
                        'can_epod': can_epod,
                        'created_at': s.created_at.strftime('%d/%m/%Y %H:%M') if s.created_at else '-',
                    })
                else:
                    if token not in not_found:
                        not_found.append(token)
                        
        return JsonResponse({
            'success': True,
            'count': len(found_shipments),
            'shipments': found_shipments,
            'not_found': not_found
        })

    # 2. Generate Bulk PDF
    if request.GET.get('action') == 'pdf' or request.POST.get('action') == 'pdf':
        print_format = request.GET.get('format', 'reguler') or request.POST.get('format', 'reguler')
        raw_ids = request.GET.get('resi_ids', '') or request.POST.get('resi_ids', '')
        
        import re
        ids_list = [int(i.strip()) for i in re.split(r'[\r\n,;\s]+', raw_ids) if i.strip().isdigit()]
        
        if not ids_list:
            raw_resis = request.GET.get('resis', '') or request.POST.get('resis', '')
            tokens = [t.strip() for t in re.split(r'[\r\n,;\s]+', raw_resis) if t.strip()]
            if tokens:
                ids_list = list(Shipment.objects.filter(is_hidden=False, resi_number__in=tokens).values_list('id', flat=True))

        if not ids_list:
            return HttpResponse("Tidak ada data resi valid yang dipilih untuk dicetak.", status=400)

        shipments = (
            Shipment.objects.filter(is_hidden=False, id__in=ids_list)
            .select_related('client', 'service_master', 'created_by')
            .prefetch_related('items')
        )
        
        # Sort as requested
        shipments_dict = {s.id: s for s in shipments}
        ordered_shipments = [shipments_dict[sid] for sid in ids_list if sid in shipments_dict]

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-surat.png').replace('\\', '/')
        iso_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-iso.png').replace('\\', '/')
        scissor_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'scissor_left.png').replace('\\', '/')

        items_data = []
        for s in ordered_shipments:
            origin_cov = Coverage.objects.filter(city=s.sender_city, district=s.sender_district).first() if s.sender_city else None
            dest_cov = Coverage.objects.filter(city=s.receiver_city, district=s.receiver_district).first() if s.receiver_city else None
            colly_range = range(1, s.total_colly + 1) if s.total_colly > 0 else range(1, 2)
            
            flat_items = []
            if s.items.exists():
                for itm in s.items.all():
                    for _ in range(itm.quantity):
                        flat_items.append(itm)
            else:
                flat_items = [None] * max(1, s.total_colly)
            package_items = list(enumerate(flat_items, 1))

            # E-POD specific context
            effective_pod_date = s.pod_date
            pod_trk = Tracking.objects.filter(shipment=s, status__in=['POD', 'POD_BALIK', 'DELIVERED']).order_by('-occurred_at').first()
            if not effective_pod_date and pod_trk:
                effective_pod_date = pod_trk.occurred_at or pod_trk.timestamp
            if not effective_pod_date:
                first_t = s.tracking_history.first()
                if first_t:
                    effective_pod_date = first_t.occurred_at or first_t.timestamp

            deliv_man = s.manifests.filter(manifest_type='DELIVERY').first()

            photo_attachments = list(s.pod_attachments.filter(media_type='IMAGE'))
            photo_paths = []
            photo_urls = []
            for att in photo_attachments:
                if att.file:
                    try:
                        photo_paths.append(att.file.path)
                    except Exception:
                        pass
                    try:
                        photo_urls.append(att.file.url)
                    except Exception:
                        pass
            if not photo_paths and s.pod_image:
                try:
                    photo_paths.append(s.pod_image.path)
                except Exception:
                    pass
                try:
                    photo_urls.append(s.pod_image.url)
                except Exception:
                    pass

            # Generate QR code data URI
            import qrcode, io, base64
            qr = qrcode.QRCode(box_size=4, border=0)
            qr.add_data(f"https://paketincargo.com/tracking/?resi={s.resi_number}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

            items_data.append({
                'shipment': s,
                'origin_coverage': origin_cov,
                'dest_coverage': dest_cov,
                'colly_range': colly_range,
                'package_items': package_items,
                'logo_path': logo_path,
                'iso_logo_path': iso_logo_path,
                'scissor_path': scissor_path,
                'qr_data_uri': qr_data_uri,
                'effective_pod_date': effective_pod_date,
                'pod_tracking': pod_trk,
                'delivery_manifest': deliv_man,
                'photo_paths': photo_paths[:3],
                'photo_urls': photo_urls[:3],
            })

        context = {
            'print_format': print_format,
            'items': items_data,
            'logo_path': logo_path,
            'iso_logo_path': iso_logo_path,
            'scissor_path': scissor_path,
            'print_time': timezone.now(),
        }

        html_string = render_to_string('operations/shipments/print_bulky_pdf.html', context, request=request)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Bulk_{print_format}_{len(items_data)}_AWB.pdf"'
        
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return HttpResponse('Error saat generate PDF: <pre>' + html_string + '</pre>', status=500)
        return response

    # 3. Regular Page View (with optional preloaded resi_ids)
    initial_resi_ids = request.GET.getlist('resi_ids') or request.GET.get('resi_ids', '').split(',')
    initial_resi_ids = [int(i.strip()) for i in initial_resi_ids if i.strip().isdigit()]
    
    preloaded_resis = []
    if initial_resi_ids:
        preloaded_resis = list(Shipment.objects.filter(is_hidden=False, id__in=initial_resi_ids).values_list('resi_number', flat=True))

    recent_shipments = Shipment.objects.filter(is_hidden=False).order_by('-created_at')[:30]

    return render(request, 'operations/shipments/print_bulky.html', {
        'preloaded_resis': "\n".join(preloaded_resis),
        'recent_shipments': recent_shipments,
    })

@login_required
def pod_list(request):
    from django.core.paginator import Paginator
    from .models import Tracking
    tracking_list = (
        Tracking.objects
        .filter(status__in=['POD', 'POD_BALIK', 'DELIVERY_FAILED'], shipment__is_hidden=False)
        .select_related('shipment', 'shipment__client', 'shipment__created_by')
        .prefetch_related('shipment__manifests', 'shipment__manifests__driver')
        .order_by('-occurred_at', '-timestamp')
    )
    
    q_search = request.GET.get('q', '').strip()
    search_resi = request.GET.get('resi', '').strip()
    search_type = request.GET.get('type', '').strip() or request.GET.get('status', '').strip()
    start_date = request.GET.get('start_date', '').strip() or request.GET.get('date_from', '').strip()
    end_date = request.GET.get('end_date', '').strip() or request.GET.get('date_to', '').strip()
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    if q_search:
        matched_tracking = tracking_list.filter(
            Q(shipment__resi_number__icontains=q_search) |
            Q(shipment__receiver_name__icontains=q_search) |
            Q(shipment__sender_name__icontains=q_search) |
            Q(shipment__client__name__icontains=q_search) |
            Q(location__icontains=q_search) |
            Q(description__icontains=q_search)
        )
        filtered_tracking = matched_tracking
        if search_resi:
            filtered_tracking = filtered_tracking.filter(shipment__resi_number__icontains=search_resi)
        if search_type:
            filtered_tracking = filtered_tracking.filter(status=search_type)
            
        date_filtered_tracking = filtered_tracking
        if psd:
            date_filtered_tracking = date_filtered_tracking.filter(occurred_at__date__gte=psd)
        if ped:
            date_filtered_tracking = date_filtered_tracking.filter(occurred_at__date__lte=ped)
            
        if date_filtered_tracking.exists():
            tracking_list = date_filtered_tracking
        elif filtered_tracking.exists():
            tracking_list = filtered_tracking
        else:
            tracking_list = matched_tracking
    else:
        if search_resi:
            tracking_list = tracking_list.filter(shipment__resi_number__icontains=search_resi)
        if search_type:
            tracking_list = tracking_list.filter(status=search_type)
        if psd:
            tracking_list = tracking_list.filter(occurred_at__date__gte=psd)
        if ped:
            tracking_list = tracking_list.filter(occurred_at__date__lte=ped)
    
    has_active_filter = bool(q_search or search_resi or search_type or start_date or end_date)
    
    page_number = request.GET.get('page')
    page_obj = Paginator(tracking_list, 25).get_page(page_number)
    return render(request, 'operations/pod/pod_list.html', {
        'page_obj': page_obj,
        'q_search': q_search,
        'search_resi': search_resi,
        'search_type': search_type,
        'start_date': start_date,
        'end_date': end_date,
        'date_from': start_date,
        'date_to': end_date,
        'has_active_filter': has_active_filter,
    })

def process_pod_uploaded_file(uploaded_file, max_size=(1280, 1280), quality=75):
    """
    Process an uploaded POD attachment.
    If image: compress & optimize using Pillow.
    If video: pass through untouched.
    Returns (processed_file, media_type) where media_type is 'IMAGE' or 'VIDEO'.
    """
    if not uploaded_file:
        return None, None
    
    ext = uploaded_file.name.lower().rsplit('.', 1)[-1] if '.' in uploaded_file.name else ''
    video_exts = {'mp4', 'mov', 'webm', 'mkv', 'avi', 'm4v', '3gp'}
    content_type = getattr(uploaded_file, 'content_type', '') or ''
    
    if ext in video_exts or content_type.startswith('video/'):
        return uploaded_file, 'VIDEO'
    
    try:
        import io
        from PIL import Image, ImageOps
        from django.core.files.uploadedfile import InMemoryUploadedFile

        img = Image.open(uploaded_file)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)

        filename = uploaded_file.name
        base_name = filename.rsplit('.', 1)[0]
        new_filename = f"{base_name}.jpg"

        processed = InMemoryUploadedFile(
            buffer,
            'ImageField',
            new_filename,
            'image/jpeg',
            buffer.getbuffer().nbytes,
            None
        )
        return processed, 'IMAGE'
    except Exception as e:
        print(f"Image compression error: {e}")
        return uploaded_file, 'IMAGE'

def compress_pod_image(uploaded_file, max_size=(1280, 1280), quality=75):
    f, _ = process_pod_uploaded_file(uploaded_file, max_size, quality)
    return f

@login_required
def entry_pod(request):
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.utils import timezone
    from django.core.paginator import Paginator
    from .models import Shipment, Tracking, PODAttachment, ReturnShipment, Manifest
    import datetime

    if request.method == 'POST':
        delivery_outcome = request.POST.get('delivery_outcome', 'DELIVERED').strip() # 'DELIVERED' or 'FAILED'
        scanned_items = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        pod_receiver_name = request.POST.get('pod_receiver_name', '').strip()
        failed_reason = request.POST.get('failed_reason', 'RECIPIENT_NOT_HOME')
        failed_detail = request.POST.get('failed_detail', '').strip() or description
        pod_date = request.POST.get('event_date') or request.POST.get('event_date_failed')
        pod_time = request.POST.get('event_time') or request.POST.get('event_time_failed')
        
        raw_files = request.FILES.getlist('failed_image_upload') or request.FILES.getlist('pod_media') or request.FILES.getlist('pod_image') or ([request.FILES['pod_image']] if 'pod_image' in request.FILES else []) or ([request.FILES['failed_image_upload']] if 'failed_image_upload' in request.FILES else [])

        # Format occurred_at
        occurred_at = timezone.now()
        if pod_date and pod_time:
            dt_str = f"{pod_date} {pod_time}"
            try:
                occurred_at = timezone.make_aware(datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M'))
            except Exception:
                pass

        if scanned_items:
            success_count = 0
            processed_shipment_ids = set()
            for item_code in scanned_items:
                manifest_obj = Manifest.objects.filter(manifest_number=item_code).first()
                if manifest_obj:
                    shipments_to_process = list(manifest_obj.shipments.all())
                else:
                    rto_obj = ReturnShipment.objects.filter(rto_number=item_code).select_related('shipment').first()
                    if rto_obj and rto_obj.shipment:
                        shipments_to_process = [rto_obj.shipment]
                    else:
                        shipments_to_process = list(Shipment.objects.filter(resi_number=item_code))

                for shipment in shipments_to_process:
                    if shipment.id in processed_shipment_ids:
                        continue
                    if delivery_outcome == 'FAILED':
                        if shipment.status == 'VOID':
                            continue
                    else:
                        if shipment.status in ['POD', 'POD_BALIK', 'VOID']:
                            continue

                    processed_shipment_ids.add(shipment.id)
                    loc = location or shipment.destination or shipment.receiver_city or 'Hub Tujuan'

                    if delivery_outcome == 'FAILED':
                        # Gagal Antar (Undelivered)
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

                        # Buat atau update catatan di ReturnShipment (Masuk Tab Laporan Masuk)
                        active_rto = ReturnShipment.objects.filter(
                            shipment=shipment,
                            status__in=['HOLD_DESTINATION', 'SCHEDULED_REDELIVERY', 'CONFIRM_SHIPPER']
                        ).first()

                        if not active_rto:
                            active_rto = ReturnShipment.objects.create(
                                shipment=shipment,
                                reason=failed_reason,
                                reason_detail=failed_detail,
                                evidence_image=shipment.failed_image if shipment.failed_image else None,
                                status='HOLD_DESTINATION',
                                action_type='PENDING',
                                attempt_count=shipment.delivery_attempts,
                                created_by=request.user
                            )
                        else:
                            active_rto.reason = failed_reason
                            active_rto.attempt_count = shipment.delivery_attempts
                            active_rto.status = 'HOLD_DESTINATION'
                            active_rto.action_type = 'PENDING'
                            if shipment.failed_image:
                                active_rto.evidence_image = shipment.failed_image
                            active_rto.reason_detail = (active_rto.reason_detail or '') + f"\n[Percobaan #{shipment.delivery_attempts}]: {failed_detail}"
                            active_rto.save()

                        reason_label = dict(ReturnShipment.REASON_CHOICES).get(failed_reason, failed_reason)
                        Tracking.objects.create(
                            shipment=shipment,
                            status='DELIVERY_FAILED',
                            location=loc,
                            description=f"Gagal Antar (Percobaan #{shipment.delivery_attempts}): {reason_label}. {failed_detail}".strip(),
                            occurred_at=occurred_at,
                        )
                        success_count += 1
                    else:
                        # Sukses POD (Delivered)
                        shipment.status = 'POD'
                        shipment.pod_receiver_name = pod_receiver_name
                        shipment.pod_date = occurred_at
                        
                        # Process files (max 5)
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

                        # Jika sebelumnya ada RTO aktif yang redelivered, tandai selesai
                        ReturnShipment.objects.filter(
                            shipment=shipment,
                            status__in=['HOLD_DESTINATION', 'SCHEDULED_REDELIVERY', 'CONFIRM_SHIPPER']
                        ).update(status='CANCELLED_REDELIVERED')

                        Tracking.objects.create(
                            shipment=shipment,
                            status='POD',
                            location=loc,
                            description=f"Penerima: {pod_receiver_name} | {description}" if description else f"Penerima: {pod_receiver_name}",
                            occurred_at=occurred_at,
                        )

                        # Update Manifest to COMPLETED if all shipments are delivered
                        for manifest in shipment.manifests.all():
                            if not manifest.shipments.exclude(status__in=['POD', 'POD_BALIK', 'RETURNED']).exists():
                                manifest.status = 'COMPLETED'
                                manifest.save()
                        
                        success_count += 1
            
            if delivery_outcome == 'FAILED':
                messages.warning(request, f'Berhasil mencatat {success_count} resi Gagal Antar. Data dialihkan ke Menu Retur (RTO).')
                return redirect('operations:return-list')
            else:
                messages.success(request, f'Berhasil memproses {success_count} resi dengan status POD (Terkirim).')
                return redirect('operations:pod_list')
    
    # Recent POD & Failed history
    recent_pods_qs = Tracking.objects.filter(status__in=['POD', 'DELIVERY_FAILED']).select_related('shipment').order_by('-occurred_at', '-timestamp')
    page_number = request.GET.get('page')
    recent_pods = Paginator(recent_pods_qs, 15).get_page(page_number)
    
    return render(request, 'operations/pod/entry_pod.html', {
        'event_date': timezone.localtime().strftime('%Y-%m-%d'),
        'event_time': timezone.localtime().strftime('%H:%M'),
        'pod_type': 'POD',
        'reason_choices': ReturnShipment.REASON_CHOICES,
        'recent_pods': recent_pods,
    })

@login_required
def entry_pod_return(request):
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.utils import timezone
    from django.core.paginator import Paginator
    from .models import Shipment, Tracking, PODAttachment
    import datetime

    if request.method == 'POST':
        scanned_items = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        pod_receiver_name = request.POST.get('pod_receiver_name', '').strip()
        pod_date = request.POST.get('event_date')
        pod_time = request.POST.get('event_time')
        
        raw_files = request.FILES.getlist('pod_media') or request.FILES.getlist('pod_image') or ([request.FILES['pod_image']] if 'pod_image' in request.FILES else [])

        # Format occurred_at
        occurred_at = timezone.now()
        if pod_date and pod_time:
            dt_str = f"{pod_date} {pod_time}"
            try:
                occurred_at = timezone.make_aware(datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M'))
            except Exception:
                pass

        if scanned_items:
            success_count = 0
            processed_shipment_ids = set()
            for item_code in scanned_items:
                manifest_obj = Manifest.objects.filter(manifest_number=item_code).first()
                if manifest_obj:
                    shipments_to_process = list(manifest_obj.shipments.all())
                else:
                    shipments_to_process = list(Shipment.objects.filter(resi_number=item_code))

                for shipment in shipments_to_process:
                    if shipment.id in processed_shipment_ids or shipment.status in ['POD_BALIK', 'VOID']:
                        continue
                    processed_shipment_ids.add(shipment.id)
                    shipment.status = 'POD_BALIK'
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

                    loc = location or shipment.destination or shipment.receiver_city or ''
                    Tracking.objects.create(
                        shipment=shipment,
                        status='POD_BALIK',
                        location=loc,
                        description=f"POD Balik - Penerima: {pod_receiver_name} | {description}" if description else f"POD Balik - Penerima: {pod_receiver_name}",
                        occurred_at=occurred_at,
                    )

                    # Update Manifest to COMPLETED if all shipments are delivered
                    for manifest in shipment.manifests.all():
                        if not manifest.shipments.exclude(status__in=['POD', 'POD_BALIK', 'RETURNED']).exists():
                            manifest.status = 'COMPLETED'
                            manifest.save()
                    
                    success_count += 1
            
            messages.success(request, f'Berhasil memproses {success_count} POD Balik.')
            return redirect('operations:pod_list')
    
    # Recent POD Balik history
    recent_pods_qs = Tracking.objects.filter(status='POD_BALIK').select_related('shipment').order_by('-occurred_at', '-timestamp')
    page_number = request.GET.get('page')
    recent_pods = Paginator(recent_pods_qs, 15).get_page(page_number)
    
    return render(request, 'operations/pod/entry_pod.html', {
        'event_date': timezone.localtime().strftime('%Y-%m-%d'),
        'event_time': timezone.localtime().strftime('%H:%M'),
        'pod_type': 'POD_BALIK',
        'recent_pods': recent_pods,
    })

@login_required
def pod_detail(request, pk):
    from django.shortcuts import get_object_or_404
    shipment = get_object_or_404(
        Shipment.objects.select_related('client', 'created_by', 'service_master')
        .prefetch_related('items', 'manifests', 'manifests__driver', 'tracking_history', 'pod_attachments'),
        pk=pk
    )
    tracking_history = shipment.tracking_history.all().order_by('-occurred_at', '-timestamp')
    pod_tracking = shipment.tracking_history.filter(status__in=['POD', 'POD_BALIK']).first()
    delivery_manifest = shipment.manifests.filter(manifest_type='DELIVERY').first()
    
    effective_pod_date = shipment.pod_date
    if not effective_pod_date and pod_tracking:
        effective_pod_date = pod_tracking.occurred_at or pod_tracking.timestamp
    if not effective_pod_date and tracking_history.exists():
        first_t = tracking_history.first()
        effective_pod_date = first_t.occurred_at or first_t.timestamp
        
    pod_attachments = list(shipment.pod_attachments.all())
    
    return render(request, 'operations/pod/pod_detail.html', {
        'shipment': shipment,
        'tracking_history': tracking_history,
        'pod_tracking': pod_tracking,
        'delivery_manifest': delivery_manifest,
        'effective_pod_date': effective_pod_date,
        'pod_attachments': pod_attachments,
    })

@login_required
def pod_edit(request, pk):
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    from .models import PODAttachment
    import datetime
    
    shipment = get_object_or_404(Shipment, pk=pk)
    pod_tracking = shipment.tracking_history.filter(status__in=['POD', 'POD_BALIK']).first()
    
    if request.method == 'POST':
        receiver_name = request.POST.get('pod_receiver_name', '').strip()
        event_date = request.POST.get('event_date', '').strip()
        event_time = request.POST.get('event_time', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Deletions
        delete_attachment_ids = request.POST.getlist('delete_attachment')
        if delete_attachment_ids:
            PODAttachment.objects.filter(shipment=shipment, id__in=delete_attachment_ids).delete()
            
        delete_primary_image = request.POST.get('delete_image') == '1'
        if delete_primary_image:
            shipment.pod_image = None
            
        if receiver_name:
            shipment.pod_receiver_name = receiver_name
        
        occurred_at = None
        if event_date and event_time:
            try:
                local_dt = datetime.datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                occurred_at = timezone.make_aware(local_dt, timezone.get_current_timezone())
                shipment.pod_date = occurred_at
            except Exception:
                pass
        
        # Upload new files (up to max 5 total attachments)
        new_files = request.FILES.getlist('pod_media') or request.FILES.getlist('pod_image')
        current_count = shipment.pod_attachments.count()
        remaining_slots = max(0, 5 - current_count)
        
        for f in new_files[:remaining_slots]:
            proc_f, m_type = process_pod_uploaded_file(f)
            if proc_f and m_type:
                att = PODAttachment.objects.create(
                    shipment=shipment,
                    file=proc_f,
                    media_type=m_type
                )
                if not shipment.pod_image and m_type == 'IMAGE':
                    shipment.pod_image = att.file
                    
        # Populate pod_image if empty
        if not shipment.pod_image:
            first_img = shipment.pod_attachments.filter(media_type='IMAGE').first()
            if first_img:
                shipment.pod_image = first_img.file
                
        shipment.save()
        
        if pod_tracking:
            if occurred_at:
                pod_tracking.occurred_at = occurred_at
            if description or receiver_name:
                pod_tracking.description = f"Penerima: {shipment.pod_receiver_name} | {description}" if description else f"Penerima: {shipment.pod_receiver_name}"
            pod_tracking.save()
        
        messages.success(request, f"Data POD resi {shipment.resi_number} berhasil diperbarui.")
        return redirect('operations:pod-detail', pk=shipment.pk)
        
    initial_date = shipment.pod_date.strftime('%Y-%m-%d') if shipment.pod_date else timezone.localtime().strftime('%Y-%m-%d')
    initial_time = shipment.pod_date.strftime('%H:%M') if shipment.pod_date else timezone.localtime().strftime('%H:%M')
    
    desc_note = ""
    if pod_tracking and pod_tracking.description:
        if " | " in pod_tracking.description:
            desc_note = pod_tracking.description.split(" | ", 1)[1]
        elif not pod_tracking.description.startswith("Penerima:"):
            desc_note = pod_tracking.description

    pod_attachments = list(shipment.pod_attachments.all())

    return render(request, 'operations/pod/pod_edit.html', {
        'shipment': shipment,
        'pod_tracking': pod_tracking,
        'initial_date': initial_date,
        'initial_time': initial_time,
        'desc_note': desc_note,
        'pod_attachments': pod_attachments,
    })

@login_required
def print_e_pod(request, pk):
    from django.shortcuts import get_object_or_404
    from apps.master.models import Coverage
    from apps.master.display import coverage_city_label
    
    shipment = get_object_or_404(
        Shipment.objects.select_related('client', 'service_master')
        .prefetch_related('items', 'manifests', 'manifests__driver', 'pod_attachments'),
        pk=pk
    )
    pod_tracking = shipment.tracking_history.filter(status__in=['POD', 'POD_BALIK']).first()
    delivery_manifest = shipment.manifests.filter(manifest_type='DELIVERY').first()
    
    effective_pod_date = shipment.pod_date
    if not effective_pod_date and pod_tracking:
        effective_pod_date = pod_tracking.occurred_at or pod_tracking.timestamp
    if not effective_pod_date:
        first_t = shipment.tracking_history.first()
        if first_t:
            effective_pod_date = first_t.occurred_at or first_t.timestamp
            
    origin_coverage = Coverage.objects.filter(city=shipment.sender_city, district=shipment.sender_district).first() if shipment.sender_city else None
    dest_coverage = Coverage.objects.filter(city=shipment.receiver_city, district=shipment.receiver_district).first() if shipment.receiver_city else None

    as_html = request.GET.get('format') == 'html'
    
    from django.conf import settings
    import os
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-surat.webp')

    # Collect ONLY IMAGE attachments for print (up to 3 photos side-by-side, no videos)
    photo_attachments = list(shipment.pod_attachments.filter(media_type='IMAGE'))
    photo_paths = []
    photo_urls = []
    for att in photo_attachments:
        if att.file:
            try:
                photo_paths.append(att.file.path)
            except Exception:
                pass
            photo_urls.append(att.file.url)
            
    if not photo_paths and shipment.pod_image:
        try:
            photo_paths.append(shipment.pod_image.path)
        except Exception:
            pass
        photo_urls.append(shipment.pod_image.url)

    context = {
        'shipment': shipment,
        'pod_tracking': pod_tracking,
        'delivery_manifest': delivery_manifest,
        'origin_coverage': origin_coverage,
        'dest_coverage': dest_coverage,
        'effective_pod_date': effective_pod_date,
        'logo_path': logo_path,
        'print_time': timezone.localtime(),
        'photo_paths': photo_paths[:3],
        'photo_urls': photo_urls[:3],
    }
    
    if not as_html:
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from xhtml2pdf import pisa
        html_string = render_to_string('operations/pod/print_e_pod_pdf.html', context, request=request)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="E_POD_{shipment.resi_number}.pdf"'
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
        return response

    return render(request, 'operations/pod/print_e_pod.html', context)

@login_required
def void_cash(request):
    # Dummy implementation for Void AWB Cash
    return render(request, 'operations/void_cash.html')

@login_required
def void_credit(request):
    """Universal Void Center for Shipments/AWB."""
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/CS/Superadmin yang dapat mengakses menu Void.")
        return redirect('operations:shipment-list')

    search_query = request.GET.get('q', '').strip()
    selected_shipment = None
    can_void = False
    cannot_void_reason = ""

    if search_query:
        selected_shipment = Shipment.objects.filter(
            models.Q(resi_number__iexact=search_query) | models.Q(ref_no__iexact=search_query)
        ).first()

        if selected_shipment:
            if selected_shipment.status == 'VOID':
                cannot_void_reason = "Resi ini sudah berstatus VOID (Dibatalkan sebelumnya)."
            elif selected_shipment.status in ['OUTGOING', 'TRANSFER', 'TRANSIT', 'INCOMING_DESTINATION', 'DELIVERY', 'POD', 'POD_BALIK']:
                cannot_void_reason = f"Resi tidak dapat di-VOID karena sudah memasuki proses perjalanan ({selected_shipment.get_status_display()}). Gunakan proses Retur jika barang ditarik kembali."
            else:
                can_void = True
        else:
            messages.warning(request, f"Resi dengan nomor '{search_query}' tidak ditemukan.")

    if request.method == 'POST':
        resi_id = request.POST.get('shipment_id')
        void_reason_cat = request.POST.get('reason_category', '').strip()
        void_notes = request.POST.get('reason_notes', '').strip()
        
        full_reason = f"[{void_reason_cat}] {void_notes}".strip()
        
        if not resi_id or not full_reason:
            messages.error(request, "Silakan pilih resi dan isi alasan pembatalan (VOID).")
        else:
            shipment_to_void = get_object_or_404(Shipment, pk=resi_id)
            if shipment_to_void.status in ['OUTGOING', 'TRANSFER', 'TRANSIT', 'INCOMING_DESTINATION', 'DELIVERY', 'POD', 'POD_BALIK']:
                messages.error(request, f"Gagal VOID: Resi sudah dalam proses {shipment_to_void.get_status_display()}.")
            elif shipment_to_void.status == 'VOID':
                messages.warning(request, "Resi ini sudah berstatus VOID.")
            else:
                shipment_to_void.status = 'VOID'
                if shipment_to_void.description_item:
                    shipment_to_void.description_item = f"VOID: {full_reason} | {shipment_to_void.description_item}"
                else:
                    shipment_to_void.description_item = f"VOID: {full_reason}"
                shipment_to_void.save(update_fields=['status', 'description_item'])
                
                # Create a tracking checkpoint record for VOID
                Tracking.objects.create(
                    shipment=shipment_to_void,
                    status='VOID',
                    location=shipment_to_void.origin,
                    description=f"Dibatalkan (VOID) oleh {request.user.username}: {full_reason}",
                    occurred_at=timezone.now(),
                    step_order=999
                )
                
                from apps.audit.utils import log_action
                log_action(
                    user=request.user,
                    action=f"[VOID] Membatalkan resi {shipment_to_void.resi_number}. Alasan: {full_reason}",
                    module="Operations",
                    obj=shipment_to_void,
                    ip=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f"Resi {shipment_to_void.resi_number} berhasil dibatalkan (VOID).")
                return redirect('operations:void_credit')

    # Voided shipments list for audit monitoring
    voided_shipments = Shipment.objects.filter(status='VOID').select_related('client').order_by('-updated_at')[:50]

    return render(request, 'operations/void/void_universal.html', {
        'search_query': search_query,
        'selected_shipment': selected_shipment,
        'can_void': can_void,
        'cannot_void_reason': cannot_void_reason,
        'voided_shipments': voided_shipments,
    })

def incoming_by_resi(request):
    from .models import Shipment, Tracking, InboundSession
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        scanned_resis = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        occurred_at = _tracking_occurred_at(request)
        set_current_status = request.POST.get('set_current_status') in ('1', 'on', 'true') or not request.POST.get('event_date')
        
        if scanned_resis:
            success_count = 0
            
            for resi_number in scanned_resis:
                try:
                    shipment = Shipment.objects.get(resi_number=resi_number)
                    
                    # Cari apakah resi ini sudah punya InboundSession
                    existing_session = shipment.inbound_sessions.first()
                    
                    if existing_session:
                        inbound_session = existing_session
                        inbound_session.location = location
                        inbound_session.description = description
                        inbound_session.save()
                    else:
                        inbound_session = InboundSession.objects.create(
                            location=location,
                            description=description
                        )
                    
                    # Pastikan relasi M2M terbentuk
                    if not inbound_session.shipments.filter(id=shipment.id).exists():
                        inbound_session.shipments.add(shipment)
                    
                    # Create Tracking history regardless of previous status
                    Tracking.objects.create(
                        shipment=shipment,
                        status='INCOMING_DESTINATION',
                        location=location,
                        description=description
                    )
                    
                    # Update shipment status
                    shipment.status = 'INCOMING_DESTINATION'
                    shipment.save()
                    success_count += 1
                except Shipment.DoesNotExist:
                    messages.error(request, f"Resi {resi_number} tidak ditemukan.")
            
            if success_count > 0:
                request.session['incoming_location'] = location
                request.session['incoming_description'] = description
                messages.success(request, f"{success_count} resi berhasil diproses dan statusnya diperbarui.")
                
        return redirect('operations:incoming-by-resi')
        
    context = {
        'default_location': request.session.get('incoming_location', ''),
        'default_description': request.session.get('incoming_description', '')
    }
    return render(request, 'operations/incoming/incoming_by_resi.html', context)


def incoming_by_manifest(request):
    from .models import Manifest, Tracking, InboundSession
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        scanned_manifests = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        
        if scanned_manifests:
            success_count = 0
            
            for manifest_no in scanned_manifests:
                try:
                    manifest = Manifest.objects.get(manifest_number=manifest_no)
                    
                    # Cari apakah manifest ini (melalui resinya) sudah punya InboundSession
                    existing_session = None
                    first_shipment = manifest.shipments.first()
                    if first_shipment:
                        existing_session = first_shipment.inbound_sessions.first()
                    
                    if existing_session:
                        inbound_session = existing_session
                        inbound_session.location = location
                        inbound_session.description = description
                        inbound_session.save()
                    else:
                        inbound_session = InboundSession.objects.create(
                            location=location,
                            description=description
                        )
                    
                    # Update all shipments in the manifest
                    for shipment in manifest.shipments.all():
                        # Pastikan relasi M2M terbentuk
                        if not inbound_session.shipments.filter(id=shipment.id).exists():
                            inbound_session.shipments.add(shipment)
                        
                        Tracking.objects.create(
                            shipment=shipment,
                            status='INCOMING_DESTINATION',
                            location=location,
                            description=description
                        )
                        shipment.status = 'INCOMING_DESTINATION'
                        shipment.save()
                    
                    success_count += 1
                except Manifest.DoesNotExist:
                    messages.error(request, f"Manifest {manifest_no} tidak ditemukan.")
            
            if success_count > 0:
                request.session['incoming_location'] = location
                request.session['incoming_description'] = description
                # Karena bisa update banyak InboundSession, pesannya disesuaikan
                messages.success(request, f"{success_count} manifest berhasil diproses dan statusnya diperbarui.")
                
        return redirect('operations:incoming-by-manifest')
        
    context = {
        'default_location': request.session.get('incoming_location', ''),
        'default_description': request.session.get('incoming_description', '')
    }
    return render(request, 'operations/incoming/incoming_by_manifest.html', context)


@login_required
def incoming_create(request):
    """Process Incoming Destination scans from resi and manifest in one session."""
    from .models import Manifest, Tracking, InboundSession
    from django.contrib import messages
    from django.shortcuts import redirect

    if request.method == 'POST':
        scan_types = request.POST.getlist('scan_types')
        scan_values = request.POST.getlist('scanned_items')
        description = request.POST.get('description', '').strip()

        # One submit represents one inbound document, regardless of whether
        # the queue contains AWBs, manifests, or a mixture of both.
        inbound_session = None
        shipment_ids = set()
        destinations = set()
        for scan_type, scan_value in zip(scan_types, scan_values):
            try:
                if scan_type == 'manifest':
                    source_shipments = Manifest.objects.get(
                        manifest_number=scan_value
                    ).shipments.all()
                else:
                    source_shipments = Shipment.objects.filter(
                        resi_number=scan_value
                    )

                if not source_shipments.exists():
                    messages.error(request, f'{scan_value} tidak ditemukan atau tidak memiliki resi.')
                    continue

                if inbound_session is None:
                    inbound_session = InboundSession.objects.create(
                        location='',
                        description=description,
                    )

                for shipment in source_shipments:
                    if shipment.pk in shipment_ids:
                        continue
                    destination = f'{shipment.get_tlc_dest} - {shipment.get_city_dest}'
                    destinations.add(destination)
                    inbound_session.shipments.add(shipment)
                    Tracking.objects.create(
                        shipment=shipment,
                        status='INCOMING_DESTINATION',
                        location=destination,
                        description=description,
                    )
                    shipment.status = 'INCOMING_DESTINATION'
                    shipment.save(update_fields=['status'])
                    shipment_ids.add(shipment.pk)
                    inbound_session.location = (
                        next(iter(destinations))
                        if len(destinations) == 1
                        else 'Multi Destination'
                    )
                    inbound_session.save(update_fields=['location'])
            except (Manifest.DoesNotExist, Shipment.DoesNotExist):
                messages.error(request, f'{scan_value} tidak ditemukan.')

        if inbound_session and shipment_ids:
            request.session['incoming_description'] = description
            messages.success(
                request,
                f'{len(shipment_ids)} resi berhasil diproses ke {inbound_session.inbound_number}.'
            )

        return redirect('operations:incoming-create')

    from django.core.paginator import Paginator
    incoming_history = Tracking.objects.filter(
        status='INCOMING_DESTINATION'
    ).select_related('shipment').prefetch_related(
        'shipment__tracking_history', 'shipment__manifests'
    ).order_by('-occurred_at', '-timestamp')
    incoming_page = Paginator(incoming_history, 10).get_page(request.GET.get('page'))

    return render(request, 'operations/incoming/incoming_edit.html', {
        'default_description': request.session.get('incoming_description', ''),
        'recent_incomings': incoming_page,
    })



@login_required
def incoming_list(request):
    from .models import Tracking, Shipment, InboundSession
    from django.core.paginator import Paginator
    from apps.organizations.models import Branch
    
    q_search = request.GET.get('q', '').strip()
    inbound_number = request.GET.get('inbound_number', '').strip()
    resi = request.GET.get('resi', '').strip()
    customer = request.GET.get('customer', '').strip()
    location = request.GET.get('location', '').strip()
    start_date = request.GET.get('start_date', '').strip() or request.GET.get('date_from', '').strip()
    end_date = request.GET.get('end_date', '').strip() or request.GET.get('date_to', '').strip()
    status = request.GET.get('status', '').strip()
    
    inbounds = (
        InboundSession.objects
        .filter(is_hidden=False)
        .prefetch_related('shipments', 'shipments__manifests', 'shipments__collies')
        .order_by('-created_at')
    )
    
    from apps.core.date_utils import parse_date_safe
    psd = parse_date_safe(start_date)
    ped = parse_date_safe(end_date)
    
    if q_search:
        matched_inbounds = inbounds.filter(
            Q(inbound_number__icontains=q_search) |
            Q(shipments__resi_number__icontains=q_search) |
            Q(shipments__sender_name__icontains=q_search) |
            Q(shipments__receiver_name__icontains=q_search) |
            Q(location__icontains=q_search)
        )
        filtered_inbounds = matched_inbounds
        if inbound_number:
            filtered_inbounds = filtered_inbounds.filter(inbound_number__icontains=inbound_number)
        if resi:
            filtered_inbounds = filtered_inbounds.filter(shipments__resi_number__icontains=resi)
        if customer:
            filtered_inbounds = filtered_inbounds.filter(
                Q(shipments__sender_name__icontains=customer) |
                Q(shipments__receiver_name__icontains=customer)
            )
        if location:
            filtered_inbounds = filtered_inbounds.filter(location__icontains=location)
        if status == 'VOID':
            filtered_inbounds = filtered_inbounds.filter(is_void=True)
        elif status == 'ENTRY':
            filtered_inbounds = filtered_inbounds.filter(is_void=False, shipments__status='INCOMING_DESTINATION')
        elif status in ['SELESAI', 'COMPLETED']:
            filtered_inbounds = filtered_inbounds.filter(is_void=False, shipments__status__in=['DELIVERY', 'ON_DELIVERY', 'POD', 'POD_BALIK', 'COMPLETED', 'DELIVERED'])
            
        date_filtered_inbounds = filtered_inbounds
        if psd:
            date_filtered_inbounds = date_filtered_inbounds.filter(created_at__date__gte=psd)
        if ped:
            date_filtered_inbounds = date_filtered_inbounds.filter(created_at__date__lte=ped)
            
        if date_filtered_inbounds.exists():
            inbounds = date_filtered_inbounds
        elif filtered_inbounds.exists():
            inbounds = filtered_inbounds
        else:
            inbounds = matched_inbounds
    else:
        if inbound_number:
            inbounds = inbounds.filter(inbound_number__icontains=inbound_number)
        if resi:
            inbounds = inbounds.filter(shipments__resi_number__icontains=resi)
        if customer:
            inbounds = inbounds.filter(
                Q(shipments__sender_name__icontains=customer) |
                Q(shipments__receiver_name__icontains=customer)
            )
        if location:
            inbounds = inbounds.filter(location__icontains=location)
        if psd:
            inbounds = inbounds.filter(created_at__date__gte=psd)
        if ped:
            inbounds = inbounds.filter(created_at__date__lte=ped)
        if status == 'VOID':
            inbounds = inbounds.filter(is_void=True)
        elif status == 'ENTRY':
            inbounds = inbounds.filter(is_void=False, shipments__status='INCOMING_DESTINATION')
        elif status in ['SELESAI', 'COMPLETED']:
            inbounds = inbounds.filter(is_void=False, shipments__status__in=['DELIVERY', 'ON_DELIVERY', 'POD', 'POD_BALIK', 'COMPLETED', 'DELIVERED'])
        
    inbounds = inbounds.distinct()
    
    branches = Branch.objects.all().order_by('name')
    has_active_filter = bool(q_search or inbound_number or resi or customer or location or start_date or end_date or status)
    
    paginator = Paginator(inbounds, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'operations/incoming/incoming_list.html', {
        'inbounds': page_obj,
        'page_obj': page_obj,
        'q_search': q_search,
        'inbound_number': inbound_number,
        'resi': resi,
        'customer': customer,
        'location': location,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'branches': branches,
        'has_active_filter': has_active_filter,
    })

@login_required
def incoming_detail(request, pk):
    from .models import InboundSession
    from django.shortcuts import get_object_or_404
    session = get_object_or_404(InboundSession, pk=pk)
    return render(request, 'operations/incoming/incoming_detail.html', {'session': session})

@login_required
def incoming_update(request, pk):
    from .models import InboundSession
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    session = get_object_or_404(InboundSession, pk=pk)
    
    if request.method == 'POST':
        location = request.POST.get('location')
        description = request.POST.get('description')
        
        # Update session
        session.location = location
        session.description = description
        session.save()
        
        # Update tracking records associated with this session's shipments
        for shipment in session.shipments.all():
            tracking = shipment.tracking_history.filter(status='INCOMING_DESTINATION').first()
            if tracking:
                tracking.location = location
                tracking.description = description
                tracking.save()
            
        messages.success(request, f"Data Inbound {session.inbound_number} berhasil diperbarui!")
        return redirect('operations:incoming-list')
        
    return render(request, 'operations/incoming/incoming_update.html', {'session': session})

@login_required
def incoming_delete(request, pk):
    from .models import InboundSession
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    session = get_object_or_404(InboundSession, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang dapat membatalkan (void) data Inbound.")
        return redirect('operations:incoming-list')
        
    if request.method == 'POST':
        inbound_num = session.inbound_number
        # Hapus tracking INCOMING_DESTINATION terbaru dari semua resi di sesi ini
        for shipment in session.shipments.all():
            latest_incoming = shipment.tracking_history.filter(status='INCOMING_DESTINATION').first()
            if latest_incoming:
                latest_incoming.delete()
            
            # Revert status
            prev_tracking = shipment.tracking_history.first()
            if prev_tracking:
                shipment.status = prev_tracking.status
            else:
                shipment.status = 'PENDING'
            shipment.save()
            
        session.is_void = True
        session.save()
        messages.success(request, f"Dokumen Inbound {inbound_num} berhasil di-void.")
        return redirect('operations:incoming-list')
        
    return render(request, 'operations/incoming/incoming_delete.html', {'session': session})

@login_required
def incoming_hide(request, pk):
    from .models import InboundSession
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    session = get_object_or_404(InboundSession, pk=pk)
    
    if not is_admin_or_superadmin(request.user):
        messages.error(request, "Akses ditolak: Hanya Admin/Superadmin yang memiliki akses untuk menghapus data Inbound.")
        return redirect('operations:incoming-list')
        
    if request.method == 'POST':
        session.is_hidden = True
        session.save()
        messages.success(request, f"Data Inbound {session.inbound_number} yang sudah di-void berhasil dihapus dari daftar!")
        
    return redirect('operations:incoming-list')


@login_required
def pickup_assign(request):
    if request.method == 'POST':
        pickup_ids = request.POST.getlist('pickup_ids')
        assign_type = request.POST.get('assign_type')
        branch_id = request.POST.get('branch')
        vendor_id = request.POST.get('vendor')
        driver_id = request.POST.get('driver')
        vehicle_type = request.POST.get('vehicle_type')
        
        from django.contrib import messages
        from .models import PickupOrder, Manifest
        from apps.accounts.models import User
        from apps.organizations.models import Branch
        from apps.finance.models import Vendor
        from apps.master.models import Vehicle
        from django.db.models import Q
        
        if not pickup_ids:
            messages.error(request, 'Pilih minimal satu pickup order.')
            return redirect('operations:pickup-list')
            
        driver = User.objects.filter(id=driver_id).first() if driver_id else None
        
        branch = None
        vendor = None
        if assign_type == 'internal' and branch_id:
            branch = Branch.objects.filter(id=branch_id).first()
        elif assign_type == 'external' and vendor_id:
            vendor = Vendor.objects.filter(id=vendor_id).first()
            
        matched_vehicle = None
        if vehicle_type:
            plate_part = vehicle_type.split(' - ')[0].strip()
            matched_vehicle = Vehicle.objects.filter(is_active=True).filter(
                Q(plate_number__iexact=plate_part) | Q(vehicle_type__iexact=vehicle_type)
            ).first()
        
        # Buat Manifest tipe PICKUP
        import datetime
        today = datetime.date.today()
        date_str = today.strftime('%Y%m%d')
        prefix = f"PKPM-{date_str}-"
        last_manifest = Manifest.objects.filter(manifest_number__startswith=prefix).order_by('-manifest_number').first()
        if last_manifest:
            try:
                last_num = int(last_manifest.manifest_number.split('-')[-1])
            except ValueError:
                last_num = 0
            new_num = last_num + 1
        else:
            new_num = 1
        
        manifest_num = f"{prefix}{new_num:04d}"
        
        manifest = Manifest.objects.create(
            manifest_type='PICKUP',
            manifest_number=manifest_num,
            driver=driver,
            vehicle=matched_vehicle,
            branch=branch,
            vendor=vendor,
            transport_mode=vehicle_type,
            date=today
        )
        
        pickups = PickupOrder.objects.filter(id__in=pickup_ids)
        manifest.pickup_orders.set(pickups)
        
        # Update status pickup order
        pickups.update(
            status='ASSIGNED_TO_DRIVER',
            driver=driver,
        )
        
        messages.success(request, f'Penugasan pickup {manifest_num} berhasil dibuat untuk {pickups.count()} order!')
        return redirect('/operations/pickup/?tab=manifest')
        
    return redirect('operations:pickup-list')


@login_required
def pickup_manifest_edit(request):
    if request.method == 'POST':
        manifest_id = request.POST.get('manifest_id')
        assign_type = request.POST.get('assign_type')
        branch_id = request.POST.get('branch')
        vendor_id = request.POST.get('vendor')
        driver_id = request.POST.get('driver')
        vehicle_type = request.POST.get('vehicle_type')
        
        from django.contrib import messages
        from .models import Manifest
        from apps.accounts.models import User
        from apps.organizations.models import Branch
        from apps.finance.models import Vendor
        from apps.master.models import Vehicle
        from django.shortcuts import redirect
        from django.db.models import Q
        
        manifest = Manifest.objects.filter(id=manifest_id).first()
        if not manifest:
            messages.error(request, 'Manifest tidak ditemukan.')
            return redirect('operations:pickup-list')
            
        driver = User.objects.filter(id=driver_id).first() if driver_id else None
        
        branch = None
        vendor = None
        if assign_type == 'internal' and branch_id:
            branch = Branch.objects.filter(id=branch_id).first()
        elif assign_type == 'external' and vendor_id:
            vendor = Vendor.objects.filter(id=vendor_id).first()
            
        matched_vehicle = None
        if vehicle_type:
            plate_part = vehicle_type.split(' - ')[0].strip()
            matched_vehicle = Vehicle.objects.filter(is_active=True).filter(
                Q(plate_number__iexact=plate_part) | Q(vehicle_type__iexact=vehicle_type)
            ).first()
            
        manifest.driver = driver
        manifest.vehicle = matched_vehicle
        manifest.transport_mode = vehicle_type
        manifest.branch = branch
        manifest.vendor = vendor
        manifest.save()
        
        messages.success(request, f'Manifest {manifest.manifest_number} berhasil diupdate.')
        
    return redirect('/operations/pickup/?tab=manifest')

@login_required
def pickup_manifest_status(request):
    if request.method == 'POST':
        manifest_id = request.POST.get('manifest_id')
        new_status = request.POST.get('status')
        from .models import Manifest
        from django.contrib import messages
        man = Manifest.objects.filter(id=manifest_id).first()
        if man:
            man.status = new_status
            man.save()
            
            # If completed, update all related pickups to PICKED_UP and linked shipments to PICKUP
            if new_status == 'COMPLETED':
                from .models import Shipment, Tracking
                for p in man.pickup_orders.all():
                    p.status = 'PICKED_UP'
                    p.save(update_fields=['status'])
                    
                    # Update all shipments referencing this pickup order
                    linked_shipments = Shipment.objects.filter(pickup_number_ref=p.pickup_number)
                    for s in linked_shipments:
                        if s.status in ['PENDING', 'PICKUP']:
                            s.status = 'PICKUP'
                            s.save(update_fields=['status'])
                            
                            # Add Tracking checkpoint for PICKUP if not already present
                            if not s.tracking_history.filter(status='PICKUP').exists():
                                loc = s.origin or p.city or s.sender_city or (man.branch.name if man.branch else 'Gudang Asal')
                                Tracking.objects.create(
                                    shipment=s,
                                    status='PICKUP',
                                    location=loc,
                                    description='Barang berhasil di-pickup, menunggu proses selanjutnya'
                                )
                    
            messages.success(request, f"Status Manifest {man.manifest_number} berhasil diubah menjadi {man.get_status_display()}.")
    return redirect('/operations/pickup/?tab=manifest')

@login_required
def pickup_print_sppb(request, pk):
    from django.shortcuts import get_object_or_404
    from .models import Manifest
    
    manifest = get_object_or_404(Manifest, pk=pk, manifest_type='PICKUP')
    return render(request, 'operations/pickups/sppb_print.html', {
        'manifest': manifest,
    })

@login_required
def api_get_districts(request):
    city = request.GET.get('city')
    if not city:
        return JsonResponse({'districts': []})
    
    districts = Coverage.objects.filter(city=city, is_active=True).values('id', 'district', 'tlc').order_by('district').distinct()
    
    result = []
    seen = set()
    for d in districts:
        if d['district'] not in seen:
            seen.add(d['district'])
            tlc_with_id = d['tlc'][:2].upper() if d['tlc'] else ''
            label = f"{tlc_with_id}{d['id']:04d} - {d['district']}"
            result.append({'value': d['district'], 'label': label})
            
    return JsonResponse({'districts': result})

@login_required
def print_awb_reguler(request, pk):
    from django.shortcuts import get_object_or_404
    from .models import Shipment
    from apps.master.models import Coverage
    from apps.master.display import coverage_city_label
    
    shipment = get_object_or_404(Shipment, pk=pk)
    
    origin_coverage = Coverage.objects.filter(city=shipment.sender_city, district=shipment.sender_district).first() if shipment.sender_city else None
    dest_coverage = Coverage.objects.filter(city=shipment.receiver_city, district=shipment.receiver_district).first() if shipment.receiver_city else None

    colly_range = range(1, shipment.total_colly + 1) if shipment.total_colly > 0 else range(1, 2)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-surat.png').replace('\\', '/')
    iso_logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-iso.png').replace('\\', '/')
    scissor_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'scissor_left.png').replace('\\', '/')

    # Generate QR code data URI
    import qrcode, io, base64
    qr = qrcode.QRCode(box_size=4, border=0)
    qr.add_data(f"https://paketincargo.com/tracking/?resi={shipment.resi_number}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

    context = {
        'shipment': shipment,
        'origin_coverage': origin_coverage,
        'dest_coverage': dest_coverage,
        'colly_range': colly_range,
        'logo_path': logo_path,
        'iso_logo_path': iso_logo_path,
        'scissor_path': scissor_path,
        'qr_data_uri': qr_data_uri,
    }
    
    # Render PDF
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from xhtml2pdf import pisa
    
    html_string = render_to_string('operations/shipments/print_awb_reguler_pdf.html', context, request=request)
    
    response = HttpResponse(content_type='application/pdf')
    # Change attachment to inline to open in browser (Acrobat extension can intercept inline PDFs)
    response['Content-Disposition'] = f'inline; filename="AWB_{shipment.resi_number}.pdf"'
    
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@login_required
def scan_transit(request):
    from .models import Shipment, Tracking, Manifest
    from apps.master.models import Coverage
    from apps.master.display import coverage_city_label
    from django.contrib import messages
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        scanned_items = request.POST.getlist('scanned_items')
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        occurred_at = _tracking_occurred_at(request)
        set_current_status = (
            request.POST.get('set_current_status') in ('1', 'on', 'true')
            or not request.POST.get('event_date')
        )
        
        if scanned_items:
            success_count = 0
            
            for item_number in scanned_items:
                # Try resi first
                try:
                    shipment = Shipment.objects.get(resi_number=item_number)
                    Tracking.objects.create(
                        shipment=shipment,
                        status='TRANSIT',
                        location=location,
                        description=description,
                        occurred_at=occurred_at,
                    )
                    if set_current_status:
                        shipment.status = 'TRANSIT'
                        shipment.save()
                    success_count += 1
                except Shipment.DoesNotExist:
                    # Try manifest
                    try:
                        manifest = Manifest.objects.get(manifest_number=item_number)
                        for shipment in manifest.shipments.all():
                            Tracking.objects.create(
                                shipment=shipment,
                                status='TRANSIT',
                                location=location,
                                description=description,
                                occurred_at=occurred_at,
                            )
                            if set_current_status:
                                shipment.status = 'TRANSIT'
                                shipment.save()
                        success_count += 1
                    except Manifest.DoesNotExist:
                        messages.error(request, f"Item {item_number} tidak ditemukan.")
            
            if success_count > 0:
                messages.success(request, f"{success_count} item berhasil diproses Transit.")
                
        return redirect('operations:scan-transit')
        
    coverages = Coverage.objects.filter(is_active=True).order_by('city')
    seen_cities = set()
    city_choices = []
    for c in coverages:
        if c.city not in seen_cities:
            seen_cities.add(c.city)
            tlc = c.tlc.upper() if c.tlc else ''
            
            import re
            clean_city = re.sub(r'(?i)^kota\s+', '', c.city)
            clean_city = re.sub(r'(?i)^kabupaten\s+', 'Kab. ', clean_city)
            label = coverage_city_label(c)
            
            city_choices.append({'value': c.city, 'label': label})

    # Fetch transit history
    from django.core.paginator import Paginator
    transit_list = Tracking.objects.filter(status='TRANSIT').select_related('shipment').prefetch_related('shipment__tracking_history', 'shipment__manifests').order_by('-occurred_at', '-timestamp')
    paginator = Paginator(transit_list, 10)
    page_number = request.GET.get('page')
    recent_transits = paginator.get_page(page_number)

    context = {
        'default_location': '',
        'default_description': '',
        'cities': city_choices,
        'recent_transits': recent_transits,
        'event_date': timezone.localdate().isoformat(),
        'event_time': timezone.localtime().strftime('%H:%M'),
    }
    return render(request, 'operations/tracking/scan_transit.html', context)


# ==============================================================================
# REPORTING: REKAPITULASI RESI & PERFORMA SLA PENGIRIMAN
# ==============================================================================

SLA_DAYS_MAP = {
    'ODS': 1,
    'SDS': 1,
    'REG': 3,
    'RUC': 2,
    'RU': 2,
    'RD': 4,
    'TRK': 5,
    'RL': 10,
}

def _calculate_shipment_sla(shipment, now_time):
    target_days = SLA_DAYS_MAP.get(shipment.service_type, 3)
    
    # Check if delivered (POD)
    is_pod = shipment.status in ['POD', 'POD_BALIK'] or shipment.pod_date is not None
    
    if is_pod and shipment.pod_date and shipment.created_at:
        lead_time_seconds = (shipment.pod_date - shipment.created_at).total_seconds()
        lead_time_days = max(0.1, round(lead_time_seconds / 86400, 1))
        lead_time_hours = max(1, round(lead_time_seconds / 3600, 1))
        
        if lead_time_days <= target_days:
            sla_status = 'ON_TIME'
            sla_badge = 'bg-success text-white'
            sla_label = 'Tepat Waktu'
        else:
            sla_status = 'LATE'
            sla_badge = 'bg-danger text-white'
            sla_label = 'Terlambat'
            
        return {
            'is_pod': True,
            'sla_status': sla_status,
            'sla_badge': sla_badge,
            'sla_label': sla_label,
            'target_days': target_days,
            'lead_time_days': lead_time_days,
            'lead_time_hours': lead_time_hours,
            'lead_time_display': f"{lead_time_days} Hari ({lead_time_hours} Jam)"
        }
    else:
        # Not yet POD
        elapsed_seconds = (now_time - shipment.created_at).total_seconds() if shipment.created_at else 0
        elapsed_days = max(0, round(elapsed_seconds / 86400, 1))
        elapsed_hours = max(0, round(elapsed_seconds / 3600, 1))
        
        if shipment.status == 'VOID':
            return {
                'is_pod': False,
                'sla_status': 'VOID',
                'sla_badge': 'bg-secondary text-white',
                'sla_label': 'Resi Void',
                'target_days': target_days,
                'lead_time_days': elapsed_days,
                'lead_time_hours': elapsed_hours,
                'lead_time_display': '-'
            }
        elif elapsed_days > target_days:
            return {
                'is_pod': False,
                'sla_status': 'OVERDUE',
                'sla_badge': 'bg-warning text-dark',
                'sla_label': 'Melewati Batas (Overdue)',
                'target_days': target_days,
                'lead_time_days': elapsed_days,
                'lead_time_hours': elapsed_hours,
                'lead_time_display': f"{elapsed_days} Hari (Berjalan)"
            }
        else:
            return {
                'is_pod': False,
                'sla_status': 'IN_PROGRESS',
                'sla_badge': 'bg-info text-dark',
                'sla_label': 'On Track (Dalam Proses)',
                'target_days': target_days,
                'lead_time_days': elapsed_days,
                'lead_time_hours': elapsed_hours,
                'lead_time_display': f"{elapsed_days} Hari (Berjalan)"
            }



def _populate_shipment_details(s, now_time):
    """Populate comprehensive operational timeline and attributes for a shipment."""
    sla_info = _calculate_shipment_sla(s, now_time)
    s.sla_info = sla_info
    
    s.price_formatted = f"Rp {int(s.price or 0):,}".replace(',', '.')
    s.weight_formatted = f"{float(s.weight or s.chargeable_weight or 0):,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    s.cod_value_formatted = f"Rp {int(s.cod_value):,}".replace(',', '.') if (s.is_cod and s.cod_value) else ""
    s.creator_name = (s.created_by.get_full_name() or s.created_by.username) if s.created_by else ""

    # Resolve POD photo url
    pod_url = None
    if s.pod_image:
        pod_url = s.pod_image.url
    else:
        first_att = next((att for att in s.pod_attachments.all() if att.media_type == 'IMAGE'), None)
        if first_att and first_att.file:
            pod_url = first_att.file.url
    s.pod_photo_url = pod_url

    trackings = list(s.tracking_history.all()) if hasattr(s, 'tracking_history') else []
    manifests = list(s.manifests.all()) if hasattr(s, 'manifests') else []
    inbounds = list(s.inbound_sessions.all()) if hasattr(s, 'inbound_sessions') else []

    # 1. Entry Date & Verified Date (Inbound Origin)
    s.entry_date = s.created_at.strftime('%d/%m/%Y %H:%M') if s.created_at else ''
    inbound_origin_tr = next((t for t in trackings if t.status == 'INBOUND_ORIGIN'), None)
    s.verified_date = inbound_origin_tr.occurred_at.strftime('%d/%m/%Y %H:%M') if inbound_origin_tr else ''

    # 2. Outgoing Manifest & Date
    outgoing_m = next((m for m in manifests if m.manifest_type == 'OUTGOING'), None)
    outgoing_tr = next((t for t in trackings if t.status == 'OUTGOING'), None)
    s.outgoing_date = outgoing_m.date.strftime('%d/%m/%Y') if (outgoing_m and outgoing_m.date) else (outgoing_tr.occurred_at.strftime('%d/%m/%Y') if outgoing_tr else '')
    s.outgoing_manifest_no = outgoing_m.manifest_number if outgoing_m else (outgoing_tr.manifest_number if (outgoing_tr and outgoing_tr.manifest_number) else '')

    # 3. Incoming Destination (Inbound) & Date
    inbound_sess = inbounds[0] if inbounds else None
    incoming_tr = next((t for t in trackings if t.status == 'INCOMING_DESTINATION'), None)
    s.incoming_date = inbound_sess.created_at.strftime('%d/%m/%Y') if inbound_sess else (incoming_tr.occurred_at.strftime('%d/%m/%Y') if incoming_tr else '')
    s.incoming_manifest_no = inbound_sess.inbound_number if inbound_sess else (incoming_tr.manifest_number if (incoming_tr and incoming_tr.manifest_number) else '')

    # 4. Transfer / Transit (Incoming Transit & Outgoing Transit)
    transfer_m = next((m for m in manifests if m.manifest_type == 'TRANSFER'), None)
    transit_tr = next((t for t in trackings if t.status in ['TRANSIT', 'TRANSFER']), None)
    s.incoming_transit_date = transfer_m.date.strftime('%d/%m/%Y') if (transfer_m and transfer_m.date) else (transit_tr.occurred_at.strftime('%d/%m/%Y') if transit_tr else '')
    s.incoming_transit_manifest_no = transfer_m.manifest_number if transfer_m else (transit_tr.manifest_number if (transit_tr and transit_tr.manifest_number) else '')
    s.outgoing_transit_date = transfer_m.arrival_date.strftime('%d/%m/%Y') if (transfer_m and transfer_m.arrival_date) else (transfer_m.date.strftime('%d/%m/%Y') if (transfer_m and transfer_m.date) else '')
    s.outgoing_transit_manifest_no = transfer_m.manifest_number if transfer_m else ''
    s.transfer_manifest_no = transfer_m.manifest_number if transfer_m else ''

    # 5. Delivery & Courier
    delivery_m = next((m for m in manifests if m.manifest_type == 'DELIVERY'), None)
    delivery_tr = next((t for t in trackings if t.status == 'DELIVERY'), None)
    s.delivery_date = delivery_m.date.strftime('%d/%m/%Y') if (delivery_m and delivery_m.date) else (delivery_tr.occurred_at.strftime('%d/%m/%Y') if delivery_tr else '')
    s.delivery_manifest_no = delivery_m.manifest_number if delivery_m else (delivery_tr.manifest_number if (delivery_tr and delivery_tr.manifest_number) else '')
    if delivery_m:
        if delivery_m.driver:
            s.delivery_courier = delivery_m.driver.get_full_name() or delivery_m.driver.username
        elif delivery_m.vehicle:
            s.delivery_courier = delivery_m.vehicle.plate_number
        elif delivery_m.vendor:
            s.delivery_courier = delivery_m.vendor.name
        else:
            s.delivery_courier = ''
    else:
        s.delivery_courier = ''

    # 6. Delivery Return & POD Return
    return_tr = next((t for t in trackings if t.status == 'RETURNED'), None)
    s.delivery_return_date = return_tr.occurred_at.strftime('%d/%m/%Y') if return_tr else ''
    pod_balik_tr = next((t for t in trackings if t.status == 'POD_BALIK'), None)
    s.pod_return_date = s.do_balik_date.strftime('%d/%m/%Y') if s.do_balik_date else (pod_balik_tr.occurred_at.strftime('%d/%m/%Y') if pod_balik_tr else '')
    s.courier_delivery_return = delivery_m.driver.get_full_name() if (delivery_m and delivery_m.driver and return_tr) else ''

    # 7. Drop Points & Vendors
    s.last_mile_drop_point = s.get_city_dest
    s.middle_mile_drop_point = (outgoing_m.vendor.name if (outgoing_m and outgoing_m.vendor) else (transfer_m.vendor.name if (transfer_m and transfer_m.vendor) else ''))
    s.booking_id_drop_point = (outgoing_m.flight_no or outgoing_m.vessel_name or outgoing_m.vendor_ref_no) if outgoing_m else ((transfer_m.flight_no or transfer_m.vessel_name or transfer_m.vendor_ref_no) if transfer_m else '')
    s.connote_drop_point = (outgoing_m.vendor_ref_no if (outgoing_m and outgoing_m.vendor_ref_no) else (transfer_m.vendor_ref_no if (transfer_m and transfer_m.vendor_ref_no) else ''))

    # 8. Aging OS & POD Longlate
    s.aging_os = f"{sla_info['lead_time_days']} Hari" if sla_info['lead_time_days'] is not None else ''
    s.pod_longlate = f"{sla_info['lead_time_hours']} Jam" if sla_info['lead_time_hours'] is not None else ''
    return s


@login_required
def shipment_sla_report(request):
    """
    Report Rekapitulasi Resi & SLA Pengiriman Operasional.
    Comprehensive 56-column report matching legacy format with SLA indicators and interactive preview.
    """
    # Filter parameters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    service_type = request.GET.get('service_type', '')
    payment_type = request.GET.get('payment_type', '')
    status_filter = request.GET.get('status', '')
    sla_filter = request.GET.get('sla_status', '')
    search_query = request.GET.get('q', '').strip()

    queryset = Shipment.objects.filter(is_hidden=False).select_related(
        'client', 'created_by', 'origin_coverage', 'destination_coverage'
    ).prefetch_related(
        'manifests__driver', 'manifests__vehicle', 'manifests__vendor',
        'inbound_sessions', 'tracking_history', 'pod_attachments'
    ).order_by('-created_at')

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    if origin:
        queryset = queryset.filter(origin__icontains=origin)
    if destination:
        queryset = queryset.filter(destination__icontains=destination)
    if service_type:
        queryset = queryset.filter(service_type=service_type)
    if payment_type:
        queryset = queryset.filter(payment_type=payment_type)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search_query:
        queryset = queryset.filter(
            Q(resi_number__icontains=search_query) |
            Q(sender_name__icontains=search_query) |
            Q(receiver_name__icontains=search_query) |
            Q(client__name__icontains=search_query)
        )

    now_time = timezone.now()

    # Process SLA metrics across all matching queryset items before pagination
    all_shipments = list(queryset)
    total_count = len(all_shipments)
    total_weight = sum([float(s.weight or s.chargeable_weight or 0) for s in all_shipments])
    total_colly = sum([int(s.total_colly or 1) for s in all_shipments])
    total_omset = sum([float(s.price or 0) for s in all_shipments])

    pod_count = 0
    on_time_count = 0
    late_count = 0
    overdue_count = 0
    in_progress_count = 0
    void_count = 0
    total_lead_time_days = 0.0

    # Daily volume aggregation for chart
    daily_volume = {}
    service_distribution = {}
    status_distribution = {}
    route_distribution = {}

    processed_shipments = []
    for s in all_shipments:
        _populate_shipment_details(s, now_time)
        sla_info = s.sla_info

        # Filter by sla_status if selected
        if sla_filter and sla_info['sla_status'] != sla_filter:
            continue

        processed_shipments.append(s)

        # KPI Counters
        sla_st = sla_info['sla_status']
        if sla_info['is_pod']:
            pod_count += 1
            total_lead_time_days += sla_info['lead_time_days']
            if sla_st == 'ON_TIME':
                on_time_count += 1
            elif sla_st == 'LATE':
                late_count += 1
        elif sla_st == 'OVERDUE':
            overdue_count += 1
        elif sla_st == 'IN_PROGRESS':
            in_progress_count += 1
        elif sla_st == 'VOID':
            void_count += 1

        # Chart Stats
        d_str = s.created_at.strftime('%Y-%m-%d') if s.created_at else 'Unknown'
        daily_volume[d_str] = daily_volume.get(d_str, 0) + 1

        svc = s.get_service_type_display() if hasattr(s, 'get_service_type_display') else s.service_type
        service_distribution[svc] = service_distribution.get(svc, 0) + 1

        st_label = s.get_status_display() if hasattr(s, 'get_status_display') else s.status
        status_distribution[st_label] = status_distribution.get(st_label, 0) + 1

        r_key = f"{s.get_tlc_origin} → {s.get_tlc_dest}"
        route_distribution[r_key] = route_distribution.get(r_key, 0) + 1

    # Calculate rates
    on_time_rate = round((on_time_count / pod_count) * 100, 1) if pod_count > 0 else 0.0
    avg_lead_time = round(total_lead_time_days / pod_count, 1) if pod_count > 0 else 0.0

    # Formatted strings for clean display & POD photo resolution
    total_omset_display = f"Rp {int(total_omset):,}".replace(',', '.')
    total_weight_display = f"{total_weight:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Sort daily volume chronologically
    sorted_daily = sorted(daily_volume.items())
    chart_dates = [k for k, v in sorted_daily]
    chart_volumes = [v for k, v in sorted_daily]

    # Top 5 Routes
    top_routes = sorted(route_distribution.items(), key=lambda x: x[1], reverse=True)[:5]

    # Pagination for table view (50 items per page by default)
    try:
        per_page = int(request.GET.get('per_page', 50))
    except (ValueError, TypeError):
        per_page = 50
    paginator = Paginator(processed_shipments, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Coverage cities for filter dropdown
    coverages = Coverage.objects.filter(is_active=True).order_by('city')
    seen_cities = set()
    city_choices = []
    for c in coverages:
        if c.city not in seen_cities:
            seen_cities.add(c.city)
            city_choices.append({'value': c.city, 'label': coverage_city_label(c)})

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'filtered_count': len(processed_shipments),
        'total_weight': total_weight,
        'total_weight_display': total_weight_display,
        'total_colly': total_colly,
        'total_omset': total_omset,
        'total_omset_display': total_omset_display,
        'pod_count': pod_count,
        'on_time_count': on_time_count,
        'late_count': late_count,
        'overdue_count': overdue_count,
        'in_progress_count': in_progress_count,
        'void_count': void_count,
        'on_time_rate': on_time_rate,
        'avg_lead_time': avg_lead_time,
        'cities': city_choices,
        'service_choices': Shipment.SERVICE_CHOICES,
        'status_choices': Shipment.STATUS_CHOICES,
        'payment_choices': Shipment.PAYMENT_CHOICES,
        'start_date': start_date,
        'end_date': end_date,
        'origin': origin,
        'destination': destination,
        'service_type': service_type,
        'payment_type': payment_type,
        'status_filter': status_filter,
        'sla_filter': sla_filter,
        'search_query': search_query,
        'chart_dates': chart_dates,
        'chart_volumes': chart_volumes,
        'status_dist_labels': list(status_distribution.keys()),
        'status_dist_values': list(status_distribution.values()),
        'service_dist_labels': list(service_distribution.keys()),
        'service_dist_values': list(service_distribution.values()),
        'top_routes': top_routes,
    }
    return render(request, 'operations/reports/shipment_sla_report.html', context)


@login_required
def shipment_sla_export_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    from django.db.models import Q
    import datetime

    # Filter parameters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    service_type = request.GET.get('service_type', '')
    payment_type = request.GET.get('payment_type', '')
    status_filter = request.GET.get('status', '')
    sla_filter = request.GET.get('sla_status', '')
    search_query = request.GET.get('q', '').strip()

    queryset = Shipment.objects.filter(is_hidden=False).select_related(
        'client', 'created_by', 'origin_coverage', 'destination_coverage'
    ).prefetch_related(
        'manifests__driver', 'manifests__vehicle', 'manifests__vendor',
        'inbound_sessions', 'tracking_history', 'pod_attachments'
    ).order_by('-created_at')

    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    if origin:
        queryset = queryset.filter(origin__icontains=origin)
    if destination:
        queryset = queryset.filter(destination__icontains=destination)
    if service_type:
        queryset = queryset.filter(service_type=service_type)
    if payment_type:
        queryset = queryset.filter(payment_type=payment_type)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search_query:
        queryset = queryset.filter(
            Q(resi_number__icontains=search_query) |
            Q(sender_name__icontains=search_query) |
            Q(receiver_name__icontains=search_query) |
            Q(client__name__icontains=search_query)
        )

    now_time = timezone.now()
    all_shipments = list(queryset)

    # Create Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rekapitulasi Resi & SLA"

    # Styling definitions
    title_font = Font(name='Calibri', size=16, bold=True, color='1F2937')
    subtitle_font = Font(name='Calibri', size=10, italic=True, color='6B7280')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='DC2626', end_color='DC2626', fill_type='solid') # Red Brand
    kpi_title_font = Font(name='Calibri', size=9, bold=True, color='6B7280')
    kpi_val_font = Font(name='Calibri', size=13, bold=True, color='1F2937')
    kpi_fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
    data_font = Font(name='Calibri', size=10)
    
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    # Title Block
    ws['A1'] = "LAPORAN REKAPITULASI RESI & PERFORMA SLA OPERASIONAL"
    ws['A1'].font = title_font
    ws['A2'] = f"Periode: {start_date or 'Semua'} s/d {end_date or 'Semua'} | Diekspor: {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')} oleh {request.user.get_full_name() or request.user.username}"
    ws['A2'].font = subtitle_font

    # KPI Summary Header Cards
    pod_count = 0
    on_time_count = 0
    total_omset = 0
    total_weight = 0

    rows_data = []
    for s in all_shipments:
        _populate_shipment_details(s, now_time)
        sla_info = s.sla_info
        if sla_filter and sla_info['sla_status'] != sla_filter:
            continue
        
        if sla_info['is_pod']:
            pod_count += 1
            if sla_info['sla_status'] == 'ON_TIME':
                on_time_count += 1

        price_val = float(s.price or 0)
        weight_val = float(s.weight or s.chargeable_weight or 0)
        cod_val = float(s.cod_value or 0) if s.is_cod else 0
        total_omset += price_val
        total_weight += weight_val

        rows_data.append([
            len(rows_data) + 1,
            s.resi_number,
            s.reference_no or '',
            s.pickup_number_ref or '',
            s.created_at.strftime('%d/%m/%Y') if s.created_at else '',
            s.get_tlc_origin,
            s.client.customer_code if (s.client and hasattr(s.client, 'customer_code')) else '',
            s.client.name if s.client else '',
            s.sender_name or (s.client.name if s.client else ''),
            int(s.total_colly or 1),
            weight_val,
            cod_val,
            s.get_service_type_display() if hasattr(s, 'get_service_type_display') else s.service_type,
            s.get_shipment_type_detail_display() if hasattr(s, 'get_shipment_type_detail_display') else 'Package',
            s.get_tlc_dest,
            s.get_city_dest,
            s.receiver_name or '',
            s.receiver_attention or s.receiver_name or '',
            s.receiver_address or '',
            s.receiver_phone or '',
            s.description_item or '',
            s.special_instruction or '',
            s.get_payment_type_display() if hasattr(s, 'get_payment_type_display') else s.payment_type,
            s.client.get_type_industry_display() if (s.client and hasattr(s.client, 'get_type_industry_display')) else '',
            s.creator_name,
            s.get_status_display() if hasattr(s, 'get_status_display') else s.status,
            'TERKIRIM' if (s.pod_date or s.status in ['POD', 'POD_BALIK']) else (s.get_status_display() if hasattr(s, 'get_status_display') else s.status),
            sla_info['sla_label'],
            s.pod_receiver_name or '',
            'Penerima Langsung' if s.pod_receiver_name else '',
            s.pod_date.strftime('%d/%m/%Y %H:%M') if s.pod_date else '',
            'Ada Foto' if s.pod_photo_url else '',
            s.entry_date,
            s.verified_date,
            s.outgoing_date,
            s.outgoing_manifest_no,
            s.incoming_date,
            s.incoming_manifest_no,
            s.incoming_transit_date,
            s.incoming_transit_manifest_no,
            s.outgoing_transit_date,
            s.outgoing_transit_manifest_no,
            s.delivery_date,
            s.delivery_return_date,
            s.pod_return_date,
            s.delivery_manifest_no,
            s.resi_number,
            s.transfer_manifest_no,
            s.last_mile_drop_point,
            s.middle_mile_drop_point,
            s.booking_id_drop_point,
            s.connote_drop_point,
            s.delivery_courier,
            s.courier_delivery_return,
            s.aging_os,
            s.pod_longlate,
        ])

    on_time_rate = f"{round((on_time_count / pod_count) * 100, 1)}%" if pod_count > 0 else "0%"

    # KPI Row (Row 4-5)
    kpis = [
        ("TOTAL RESI", len(rows_data), "A4", "B5"),
        ("TOTAL BERAT", f"{total_weight:,.1f} Kg", "C4", "D5"),
        ("TOTAL OMSET", f"Rp {total_omset:,.0f}", "E4", "F5"),
        ("POD SELESAI", f"{pod_count} Resi", "G4", "H5"),
        ("SLA ON-TIME", on_time_rate, "I4", "J5"),
    ]
    for title, val, c1, c2 in kpis:
        col_start, row_start = c1[0], int(c1[1])
        col_end, row_end = c2[0], int(c2[1])
        ws.merge_cells(f"{c1}:{c2}")
        top_left = ws[f"{col_start}{row_start}"]
        top_left.value = f"{title}\n{val}"
        top_left.font = kpi_val_font
        top_left.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        top_left.fill = kpi_fill
        for r in range(row_start, row_end + 1):
            for col_idx in [openpyxl.utils.column_index_from_string(col_start), openpyxl.utils.column_index_from_string(col_end)]:
                ws.cell(row=r, column=col_idx).border = thin_border

    # Headers at row 7 (Full 56 Columns)
    headers = [
        "No", "No. Resi", "Referensi", "No Pickup", "Tanggal", "Asal", "Kode Akun",
        "Nama Akun", "Nama Pengirim", "Koli", "Berat (Kg)", "Nilai COD", "Layanan",
        "Jenis Kiriman", "Tujuan", "Kota Tujuan", "Nama Penerima", "Pic Penerima",
        "Alamat Tujuan", "No Hp Penerima", "Deskripsi Barang", "Intruksi Khusus",
        "Tipe Transaksi", "Tipe Industri", "User Entry", "Status Terakhir",
        "Status Pod", "Keterangan Pod", "Di Terima Oleh", "Status Penerima",
        "POD Date", "POD Photo", "Entry Date", "Verified Date", "Outgoing Date", "No Manifest Outgoing",
        "Incoming Date", "No Manifest Incoming", "Incoming Transit Date", "No Manifest Incoming Transit",
        "Outgoing Transit Date", "No Manifest Outgoing Transit", "Delivery Date", "Delivery Return Date",
        "POD Return Date", "No Manifest Delivery", "No POD", "Transfer Location No",
        "List Mile Drop Point", "Middle Mile Drop Point", "Booking ID Drop Point", "Connote Drop Point",
        "Courier Delivery", "Courier Delivery Return", "Aging OS", "Pod Longlate"
    ]

    header_row = 7
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border

    ws.row_dimensions[header_row].height = 28

    # Populate Data
    start_row = 8
    for row_idx, r_data in enumerate(rows_data, start=start_row):
        for col_idx, val in enumerate(r_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = data_font
            cell.border = thin_border
            
            # Alignments
            if col_idx in [1, 5, 6, 7, 10, 15, 27, 28]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif col_idx in [11, 12]:
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if col_idx == 12:
                    cell.number_format = '#,##0'
                elif col_idx == 11:
                    cell.number_format = '#,##0.0'
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center')

            # Highlight SLA status
            if col_idx == 28:
                if val == 'Tepat Waktu':
                    cell.fill = PatternFill(start_color='DCFCE7', end_color='DCFCE7', fill_type='solid') # Soft Green
                    cell.font = Font(name='Calibri', size=10, bold=True, color='166534')
                elif val == 'Terlambat':
                    cell.fill = PatternFill(start_color='FEE2E2', end_color='FEE2E2', fill_type='solid') # Soft Red
                    cell.font = Font(name='Calibri', size=10, bold=True, color='991B1B')
                elif 'Overdue' in str(val):
                    cell.fill = PatternFill(start_color='FEF3C7', end_color='FEF3C7', fill_type='solid') # Soft Yellow
                    cell.font = Font(name='Calibri', size=10, bold=True, color='92400E')

    # Auto-adjust column widths based only on header and data (ignoring merged top title)
    for col_idx in range(1, len(headers) + 1):
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        if col_idx == 1:
            ws.column_dimensions[col_letter].width = 6
        else:
            max_len = max(len(str(ws.cell(row=r, column=col_idx).value or '')) for r in range(header_row, ws.max_row + 1)) if ws.max_row >= header_row else len(headers[col_idx-1])
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    # Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Rekap_Resi_SLA_{timezone.localdate().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

