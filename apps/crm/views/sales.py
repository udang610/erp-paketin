"""
Sales views: Client, Lead, and Contract CRUD with RBAC enforcement.
All views enforce owner-based data isolation for regular users.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.utils import timezone

from apps.core.mixins import OwnerRequiredMixin, OwnerOrAdminMixin, SetOwnerMixin, is_admin, AdminOnlyMixin
from apps.crm.models import Client, Lead, Contract
from apps.crm.forms.sales import ClientForm, LeadForm, ContractForm


# ─── Client Views ───────────────────────────────────────────────

class ClientListView(OwnerRequiredMixin, ListView):
    model = Client
    template_name = 'crm/clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '').strip()
        status = self.request.GET.get('status', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        company = self.request.GET.get('company', '').strip()
        
        from apps.core.date_utils import parse_date_safe
        psd = parse_date_safe(start_date)
        ped = parse_date_safe(end_date)
        
        # Exclude DEVELOPMENT testing data
        qs = qs.exclude(company_name__iexact='DEVELOPMENT')

        if search:
            search_upper = search.upper()
            if 'CLI-' in search_upper and search_upper.split('CLI-')[1].isdigit():
                matched_qs = qs.filter(pk=int(search_upper.split('CLI-')[1]))
            else:
                from django.db.models import Q
                matched_qs = qs.filter(
                    Q(company_name__icontains=search) |
                    Q(contact_person__icontains=search) |
                    Q(phone__icontains=search) |
                    Q(email__icontains=search) |
                    Q(city__icontains=search) |
                    Q(province__icontains=search) |
                    Q(npwp__icontains=search)
                )
            
            filtered_qs = matched_qs
            if category:
                filtered_qs = filtered_qs.filter(customer_category=category)
            if status:
                filtered_qs = filtered_qs.filter(customer_status=status)
            if company:
                filtered_qs = filtered_qs.filter(company_name__icontains=company)
                
            date_filtered_qs = filtered_qs
            if psd:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__gte=psd)
            if ped:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__lte=ped)
                
            if date_filtered_qs.exists():
                return date_filtered_qs
            elif filtered_qs.exists():
                return filtered_qs
            return matched_qs
            
        if category:
            qs = qs.filter(customer_category=category)
        if status:
            qs = qs.filter(customer_status=status)
        if psd:
            qs = qs.filter(created_at__date__gte=psd)
        if ped:
            qs = qs.filter(created_at__date__lte=ped)
        if company:
            qs = qs.filter(company_name__icontains=company)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['company_query'] = self.request.GET.get('company', '')
        context['category_choices'] = Client.CustomerCategory.choices
        context['status_choices'] = Client.CustomerStatus.choices
        return context


class ClientDetailView(OwnerOrAdminMixin, DetailView):
    model = Client
    template_name = 'crm/clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contracts'] = Contract.objects.filter(client=self.object).order_by('-created_at')[:5]
        return context


class ClientCreateView(LoginRequiredMixin, SetOwnerMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/clients/client_edit.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, 'Klien berhasil ditambahkan. Silakan buat Peluang (Lead) baru.')
        return super().form_valid(form)


class ClientUpdateView(OwnerOrAdminMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/clients/client_edit.html'
    success_url = reverse_lazy('crm:client-list')

    def form_valid(self, form):
        messages.success(self.request, 'Client berhasil diperbarui.')
        return super().form_valid(form)


class ClientDeleteView(AdminOnlyMixin, DeleteView):
    model = Client
    template_name = 'crm/clients/client_delete.html'
    success_url = reverse_lazy('crm:client-list')

    def form_valid(self, form):
        messages.success(self.request, 'Client berhasil dihapus.')
        return super().form_valid(form)




# ─── Lead Views ─────────────────────────────────────────────────

class LeadListView(OwnerRequiredMixin, ListView):
    model = Lead
    template_name = 'crm/leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related('client', 'owner')
        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        source = self.request.GET.get('source', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        company = self.request.GET.get('company', '').strip()
        
        from apps.core.date_utils import parse_date_safe
        psd = parse_date_safe(start_date)
        ped = parse_date_safe(end_date)
        
        # Exclude DEVELOPMENT testing data
        qs = qs.exclude(client__company_name__iexact='DEVELOPMENT')

        if search:
            search_upper = search.upper()
            if 'LD-' in search_upper and search_upper.split('LD-')[1].isdigit():
                matched_qs = qs.filter(pk=int(search_upper.split('LD-')[1]))
            else:
                from django.db.models import Q
                matched_qs = qs.filter(
                    Q(client__company_name__icontains=search) |
                    Q(client__contact_person__icontains=search) |
                    Q(shipping_origin__icontains=search) |
                    Q(shipping_destination__icontains=search) |
                    Q(notes__icontains=search)
                )
            filtered_qs = matched_qs
            if status:
                filtered_qs = filtered_qs.filter(status=status)
            if source:
                filtered_qs = filtered_qs.filter(lead_source=source)
            if company:
                filtered_qs = filtered_qs.filter(client__company_name__icontains=company)
                
            date_filtered_qs = filtered_qs
            if psd:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__gte=psd)
            if ped:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__lte=ped)
                
            if date_filtered_qs.exists():
                return date_filtered_qs
            elif filtered_qs.exists():
                return filtered_qs
            return matched_qs
            
        if status:
            qs = qs.filter(status=status)
        if source:
            qs = qs.filter(lead_source=source)
        if psd:
            qs = qs.filter(created_at__date__gte=psd)
        if ped:
            qs = qs.filter(created_at__date__lte=ped)
        if company:
            qs = qs.filter(client__company_name__icontains=company)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_source'] = self.request.GET.get('source', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['company_query'] = self.request.GET.get('company', '')
        context['status_choices'] = Lead.Status.choices
        context['source_choices'] = Lead.LeadSource.choices
        return context


class LeadDetailView(OwnerOrAdminMixin, DetailView):
    model = Lead
    template_name = 'crm/leads/lead_detail.html'
    context_object_name = 'lead'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.object.activities.all()[:10]
        context['quotations'] = self.object.quotations.all()[:5]
        context['contracts'] = self.object.contracts.all()[:5]
        context['whatsapp_url'] = self.object.get_whatsapp_followup_url()
        return context


class LeadCreateView(LoginRequiredMixin, SetOwnerMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/leads/lead_edit.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get('client')
        if client_id:
            initial['client'] = client_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Peluang berhasil ditambahkan. Silakan buat Penawaran atau catat Aktivitas.')
        return super().form_valid(form)


class LeadUpdateView(OwnerOrAdminMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/leads/lead_edit.html'
    success_url = reverse_lazy('crm:lead-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Lead berhasil diperbarui.')
        return super().form_valid(form)


class LeadDeleteView(AdminOnlyMixin, DeleteView):
    model = Lead
    template_name = 'crm/leads/lead_delete.html'
    success_url = reverse_lazy('crm:lead-list')

    def form_valid(self, form):
        messages.success(self.request, 'Peluang berhasil dihapus.')
        return super().form_valid(form)


class LeadQuickStatusView(LoginRequiredMixin, View):
    """Quick action to change lead status from detail page."""

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        if not is_admin(request.user) and lead.owner != request.user:
            messages.error(request, 'Anda tidak memiliki akses.')
            return redirect('crm:lead-list')

        new_status = request.POST.get('status')
        if new_status in dict(Lead.Status.choices):
            lead.status = new_status
            if new_status == Lead.Status.WON and not lead.closed_at:
                lead.closed_at = timezone.now()
                
                # MENGGUNAKAN ORM KARENA SUDAH 1 PROJECT
                from apps.finance.models import KpiFinance, KpiSheet, KpiFile
                try:
                    latest_quotation = lead.quotations.order_by('-id').first()
                    aktual = 0
                    vol = 0
                    p = l = t = 0
                    total_koli = 0
                    harga_per_kg = 0

                    if latest_quotation:
                        aktual = float(latest_quotation.actual_weight) * float(latest_quotation.quantity or 1) if latest_quotation.actual_weight else 0
                        vol = float(latest_quotation.volumetric_weight) if latest_quotation.volumetric_weight else 0
                        p = float(latest_quotation.panjang) if latest_quotation.panjang else 0
                        l = float(latest_quotation.lebar) if latest_quotation.lebar else 0
                        t = float(latest_quotation.tinggi) if latest_quotation.tinggi else 0
                        total_koli = latest_quotation.quantity or 1
                        harga_per_kg = float(latest_quotation.price_per_kg) if latest_quotation.price_per_kg else 0

                        for item in latest_quotation.items.all():
                            total_koli += (item.quantity or 1)
                            if item.actual_weight:
                                aktual += float(item.actual_weight) * float(item.quantity or 1)

                    if aktual == 0 and lead.shipping_estimated_weight:
                        aktual = float(lead.shipping_estimated_weight)
                    
                    # Cek if service method exist
                    svc_display = ""
                    if hasattr(lead, 'get_shipping_service_display'):
                        svc_display = lead.get_shipping_service_display()
                    elif hasattr(lead, 'get_shipping_service_display_list'):
                        svc_list = lead.get_shipping_service_display_list()
                        svc_display = ", ".join(svc_list) if svc_list else ""

                    # Create direct to Finance
                    from apps.finance.utils import get_primary_kpi_sheet
                    sheet_obj = get_primary_kpi_sheet(lead.closed_at.date() if lead.closed_at else None)
                    
                    KpiFinance.objects.create(
                        sheet=sheet_obj,
                        tanggal_pickup=lead.closed_at.date(),
                        awb=lead.lead_id, # as placeholder
                        nama=lead.client.paketin_group or "",
                        pengirim=lead.client.company_name,
                        penerima="",
                        asal_pickup=latest_quotation.origin if latest_quotation and latest_quotation.origin else lead.shipping_origin,
                        tujuan=latest_quotation.destination if latest_quotation and latest_quotation.destination else lead.shipping_destination,
                        service=svc_display,
                        aktual=aktual,
                        vol=vol,
                        p=p,
                        l=l,
                        t=t,
                        koil=total_koli,
                        harga=harga_per_kg,
                        source='import',
                        row_status='new'
                    )
                    messages.success(request, 'Data berhasil dikirim ke modul Finance secara internal (ORM).')
                except Exception as e:
                    messages.warning(request, f'Data Lead berhasil WON, namun integrasi internal Finance gagal: {str(e)}')
                    
            elif new_status == Lead.Status.LOST:
                lost_reason = request.POST.get('lost_reason')
                if lost_reason:
                    timestamp = timezone.localtime(timezone.now()).strftime("%d-%m-%Y %H:%M")
                    new_note = f"\n\n--- [EVALUASI LOST - {timestamp}] ---\nAlasan: {lost_reason}"
                    lead.notes = (lead.notes + new_note).strip()
                if not lead.closed_at:
                    lead.closed_at = timezone.now()
            lead.save()
            status_label = lead.get_status_display()
            messages.success(request, f'Status berhasil diubah menjadi "{status_label}".')
        return redirect('crm:lead-detail', pk=pk)


class ClientSyncToMasterView(LoginRequiredMixin, View):
    """Kirim / Sinkronisasi data Client ke Master Customer ERP via Validasi Button."""
    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        if not is_admin(request.user) and client.owner != request.user:
            messages.error(request, 'Anda tidak memiliki akses.')
            return redirect('crm:client-detail', pk=pk)
        
        from apps.crm.services import sync_client_to_master
        try:
            master_cust, created = sync_client_to_master(client, user=request.user)
            if created:
                messages.success(request, f'Berhasil divalidasi! Customer baru terdaftar di Master Data ERP: {master_cust.customer_code} ({master_cust.name}).')
            else:
                messages.success(request, f'Berhasil disinkronkan! Master Data ERP telah diperbarui: {master_cust.customer_code} ({master_cust.name}).')
        except Exception as e:
            messages.error(request, f'Gagal melakukan validasi sinkronisasi: {str(e)}')
            
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
        return redirect('crm:client-detail', pk=pk)


class LeadWhatsAppFollowUpView(LoginRequiredMixin, View):
    """Redirect to WhatsApp with pre-filled follow-up message."""

    def get(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        if not is_admin(request.user) and lead.owner != request.user:
            messages.error(request, 'Anda tidak memiliki akses.')
            return redirect('crm:lead-list')

        whatsapp_url = lead.get_whatsapp_followup_url()

        # Log the WhatsApp follow-up as an activity
        from apps.crm.models import Activity
        Activity.objects.create(
            owner=request.user,
            lead=lead,
            activity_type=Activity.ActivityType.WHATSAPP,
            description=f'Follow-up via WhatsApp ke {lead.client.contact_person} ({lead.client.phone})',
            result='Pesan WhatsApp dikirim melalui CRM',
        )

        messages.success(request, f'Follow-up WhatsApp ke {lead.client.contact_person} tercatat.')
        return redirect(whatsapp_url)


class LeadExportCSVView(OwnerRequiredMixin, ListView):
    """Export Leads to CSV."""
    model = Lead

    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Perusahaan', 'Status', 'Sumber', 'Estimasi Nilai (Rp)', 
            'Jenis Pengiriman', 'Asal', 'Tujuan', 'Respon', 'PIC',
            'Tanggal Dibuat', 'Tanggal Update'
        ])

        # Filter same as list view
        qs = self.get_queryset().select_related('client', 'owner')

        search = self.request.GET.get('q', '')
        status = self.request.GET.get('status', '')
        if search:
            qs = qs.filter(client__company_name__icontains=search)
        if status:
            qs = qs.filter(status=status)

        for lead in qs:
            writer.writerow([
                lead.id,
                lead.client.company_name,
                lead.get_status_display(),
                lead.get_lead_source_display(),
                lead.estimated_value,
                lead.get_shipping_service_display() if lead.shipping_service else '-',
                lead.shipping_origin or '-',
                lead.shipping_destination or '-',
                lead.get_interested_display(),
                lead.owner.get_full_name() or lead.owner.username,
                lead.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                lead.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response


class LeadExportExcelView(OwnerRequiredMixin, ListView):
    """Export Leads to Excel (.xlsx) with styling and filters."""
    model = Lead

    def get(self, request, *args, **kwargs):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from django.http import HttpResponse
        from django.utils import timezone

        # Create a workbook and select the active worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Leads Export"

        # Define styles
        title_font = Font(size=16, bold=True, color="000000")
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
        border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")

        # Title
        ws.merge_cells('A1:L1')
        title_cell = ws['A1']
        title_cell.value = "DATA LEADS PIPELINE"
        title_cell.font = title_font
        title_cell.alignment = align_center

        # Export Timestamp
        ws.merge_cells('A2:L2')
        info_cell = ws['A2']
        info_cell.value = f"Diekspor pada: {timezone.now().strftime('%d %b %Y')}"
        info_cell.alignment = align_center

        # Empty row 3
        ws.append([])

        # Header row
        headers = [
            'ID', 'Perusahaan', 'Status', 'Sumber', 'Estimasi Nilai (Rp)', 
            'Jenis Pengiriman', 'Asal', 'Tujuan', 'Respon', 'PIC',
            'Tanggal Dibuat', 'Tanggal Update'
        ]
        ws.append(headers)

        # Style the header (row 4)
        for cell in ws[4]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = align_center

        # Filter same as list view
        qs = self.get_queryset().select_related('client', 'owner')

        search = self.request.GET.get('q', '')
        status = self.request.GET.get('status', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        company = self.request.GET.get('company', '')

        if search:
            search_upper = search.upper()
            if 'LD-' in search_upper and search_upper.split('LD-')[1].isdigit():
                qs = qs.filter(pk=int(search_upper.split('LD-')[1]))
            else:
                from django.db.models import Q
                qs = qs.filter(
                    Q(client__company_name__icontains=search) |
                    Q(client__contact_person__icontains=search) |
                    Q(shipping_origin__icontains=search) |
                    Q(shipping_destination__icontains=search) |
                    Q(notes__icontains=search)
                )
        if status:
            qs = qs.filter(status=status)
        if start_date:
            qs = qs.filter(created_at__gte=f"{start_date} 00:00:00")
        if end_date:
            qs = qs.filter(created_at__lte=f"{end_date} 23:59:59")
        if company:
            qs = qs.filter(client__company_name__icontains=company)

        # Write data rows
        for row_num, lead in enumerate(qs, start=5):
            row_data = [
                lead.lead_id,
                lead.client.company_name,
                lead.get_status_display(),
                lead.get_lead_source_display(),
                float(lead.estimated_value) if lead.estimated_value else 0,
                lead.get_shipping_service_display() if lead.shipping_service else '-',
                lead.shipping_origin or '-',
                lead.shipping_destination or '-',
                lead.get_interested_display(),
                lead.owner.get_full_name() or lead.owner.username,
                lead.created_at.strftime('%d %b %Y'),
                lead.updated_at.strftime('%d %b %Y'),
            ]
            ws.append(row_data)
            
            # Style data cells
            for cell in ws[row_num]:
                cell.border = border
                if cell.column in [1, 3, 4, 9, 11, 12]:  # Center align ID, Status, Sumber, dll
                    cell.alignment = align_center
                else:
                    cell.alignment = align_left

        # Adjust column widths
        column_widths = {
            'A': 12, 'B': 30, 'C': 15, 'D': 15, 'E': 20,
            'F': 20, 'G': 15, 'H': 15, 'I': 15, 'J': 20,
            'K': 20, 'L': 20
        }
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # Enable AutoFilter for the header and all data rows
        ws.auto_filter.ref = f"A4:L{ws.max_row}"

        # Prepare HTTP response with Excel content type
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="leads_export_{timezone.now().strftime("%Y%m%d")}.xlsx"'

        # Save workbook to response
        wb.save(response)

        return response


# ─── Contract Views ─────────────────────────────────────────────

class ContractListView(OwnerRequiredMixin, ListView):
    model = Contract
    template_name = 'crm/contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related('client', 'lead', 'owner')
        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        company = self.request.GET.get('company', '').strip()
        
        from apps.core.date_utils import parse_date_safe
        psd = parse_date_safe(start_date)
        ped = parse_date_safe(end_date)
        
        # Exclude DEVELOPMENT testing data
        qs = qs.exclude(client__company_name__iexact='DEVELOPMENT')

        if search:
            from django.db.models import Q
            matched_qs = qs.filter(
                Q(contract_number__icontains=search) |
                Q(title__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(client__contact_person__icontains=search)
            )
            filtered_qs = matched_qs
            if status:
                filtered_qs = filtered_qs.filter(status=status)
            if company:
                filtered_qs = filtered_qs.filter(client__company_name__icontains=company)
                
            date_filtered_qs = filtered_qs
            if psd:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__gte=psd)
            if ped:
                date_filtered_qs = date_filtered_qs.filter(created_at__date__lte=ped)
                
            if date_filtered_qs.exists():
                return date_filtered_qs
            elif filtered_qs.exists():
                return filtered_qs
            return matched_qs
            
        if status:
            qs = qs.filter(status=status)
        if psd:
            qs = qs.filter(created_at__date__gte=psd)
        if ped:
            qs = qs.filter(created_at__date__lte=ped)
        if company:
            qs = qs.filter(client__company_name__icontains=company)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['company_query'] = self.request.GET.get('company', '')
        context['status_choices'] = Contract.ContractStatus.choices
        return context


class ContractDetailView(OwnerOrAdminMixin, DetailView):
    model = Contract
    template_name = 'crm/contracts/contract_detail.html'
    context_object_name = 'contract'


import threading

def sync_contract_penerima_to_finance(contract_id):
    from django.conf import settings
    import requests
    from apps.crm.models import Contract
    try:
        contract = Contract.objects.select_related('lead', 'client', 'lead__owner').get(pk=contract_id)
        lead = contract.lead
        if not lead or lead.status != 'WON':
            return
            
        if hasattr(settings, 'FINANCE_WEBHOOK_URL') and settings.FINANCE_WEBHOOK_URL:
            latest_quotation = lead.quotations.order_by('-id').first()
            aktual = 0
            vol = 0
            p = l = t = 0
            total_koli = 0
            harga_per_kg = 0

            if latest_quotation:
                aktual = float(latest_quotation.actual_weight) * float(latest_quotation.quantity or 1) if latest_quotation.actual_weight else 0
                vol = float(latest_quotation.volumetric_weight) if latest_quotation.volumetric_weight else 0
                p = float(latest_quotation.panjang) if latest_quotation.panjang else 0
                l = float(latest_quotation.lebar) if latest_quotation.lebar else 0
                t = float(latest_quotation.tinggi) if latest_quotation.tinggi else 0
                total_koli = latest_quotation.quantity or 1
                harga_per_kg = float(latest_quotation.price_per_kg) if latest_quotation.price_per_kg else 0

                for item in latest_quotation.items.all():
                    total_koli += (item.quantity or 1)
                    if item.actual_weight:
                        aktual += float(item.actual_weight) * float(item.quantity or 1)

            if aktual == 0 and lead.shipping_estimated_weight:
                aktual = float(lead.shipping_estimated_weight)

            payload = {
                "crm_lead_id": lead.lead_id,
                "tanggal_pickup": lead.closed_at.strftime('%Y-%m-%d') if lead.closed_at else contract.start_date.strftime('%Y-%m-%d'),
                "nama": lead.client.paketin_group or "",
                "ip_perusahaan": lead.client.paketin_group or "",
                "pengirim": lead.client.company_name,
                "sales": lead.owner.get_full_name() or lead.owner.username,
                "penerima": contract.penerima,
                "asal_pickup": latest_quotation.origin if latest_quotation and latest_quotation.origin else lead.shipping_origin,
                "tujuan": latest_quotation.destination if latest_quotation and latest_quotation.destination else lead.shipping_destination,
                "service": lead.get_shipping_service_display(),
                "via": "",
                "jenis_barang": contract.lead.client.get_industry_display() if contract.lead and contract.lead.client.industry else contract.client.get_industry_display() if contract.client.industry else "",
                "aktual": aktual,
                "vol": vol,
                "p": p,
                "l": l,
                "t": t,
                "koil": total_koli,
                "harga": harga_per_kg
            }
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": getattr(settings, 'FINANCE_API_KEY', '')
            }
            requests.post(settings.FINANCE_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Finance Webhook Contract Sync Exception: {str(e)}")


class ContractCreateView(LoginRequiredMixin, SetOwnerMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'crm/contracts/contract_edit.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super().get_initial()
        lead_id = self.request.GET.get('lead')
        if lead_id:
            lead = Lead.objects.select_related('client').filter(pk=lead_id).first()
            if lead:
                initial['lead'] = lead.pk
                initial['client'] = lead.client.pk
                initial['value'] = lead.estimated_value
                initial['title'] = f'Kontrak - {lead.client.company_name}'
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Auto-generate contract number if not provided
        if not form.instance.contract_number:
            form.instance.contract_number = form.instance.generate_contract_number()
        response = super().form_valid(form)
        messages.success(self.request, 'Kontrak berhasil dibuat.')
        threading.Thread(target=sync_contract_penerima_to_finance, args=(self.object.id,)).start()
        return response


class ContractUpdateView(OwnerOrAdminMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'crm/contracts/contract_edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Kontrak berhasil diperbarui.')
        threading.Thread(target=sync_contract_penerima_to_finance, args=(self.object.id,)).start()
        return response


class ContractDeleteView(AdminOnlyMixin, DeleteView):
    model = Contract
    template_name = 'crm/contracts/contract_delete.html'
    success_url = reverse_lazy('crm:contract-list')

    def form_valid(self, form):
        messages.success(self.request, 'Kontrak berhasil dihapus.')
        return super().form_valid(form)


# ─── Export Views ────────────────────────────────────────────────

class ClientExportExcelView(OwnerRequiredMixin, ListView):
    """Export Clients to Excel (.xlsx) with styling."""
    model = Client

    def get(self, request, *args, **kwargs):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from django.http import HttpResponse
        from django.utils import timezone as tz

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Clients Export"

        title_font = Font(size=16, bold=True, color="000000")
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
        border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")

        ws.merge_cells('A1:J1')
        ws['A1'].value = "DATA KLIEN"
        ws['A1'].font = title_font
        ws['A1'].alignment = align_center

        ws.merge_cells('A2:J2')
        ws['A2'].value = f"Diekspor pada: {tz.now().strftime('%d %b %Y')}"
        ws['A2'].alignment = align_center
        ws.append([])

        headers = [
            'ID', 'Nama Perusahaan', 'Contact Person', 'Telepon', 'Email',
            'Kota', 'Kategori', 'Status', 'PIC', 'Tanggal Dibuat'
        ]
        ws.append(headers)
        for cell in ws[4]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = align_center

        qs = self.get_queryset().select_related('owner')
        search = request.GET.get('q', '')
        category = request.GET.get('category', '')
        status = request.GET.get('status', '')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(company_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(phone__icontains=search)
            )
        if category:
            qs = qs.filter(customer_category=category)
        if status:
            qs = qs.filter(customer_status=status)

        for row_num, client in enumerate(qs, start=5):
            row_data = [
                client.client_id,
                client.company_name,
                client.contact_person,
                client.phone,
                client.email or '-',
                client.city or '-',
                client.get_customer_category_display(),
                client.get_customer_status_display(),
                client.owner.get_full_name() or client.owner.username,
                client.created_at.strftime('%d %b %Y'),
            ]
            ws.append(row_data)
            for cell in ws[row_num]:
                cell.border = border
                cell.alignment = align_center if cell.column in [1, 7, 8, 10] else align_left

        widths = {'A': 12, 'B': 30, 'C': 25, 'D': 18, 'E': 25, 'F': 15, 'G': 18, 'H': 18, 'I': 20, 'J': 18}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
        ws.auto_filter.ref = f"A4:J{ws.max_row}"

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="clients_export_{tz.now().strftime("%Y%m%d")}.xlsx"'
        wb.save(response)
        return response


class ContractExportExcelView(OwnerRequiredMixin, ListView):
    """Export Contracts to Excel (.xlsx) with styling."""
    model = Contract

    def get(self, request, *args, **kwargs):
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from django.http import HttpResponse
        from django.utils import timezone as tz

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Contracts Export"

        title_font = Font(size=16, bold=True, color="000000")
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
        border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")

        ws.merge_cells('A1:J1')
        ws['A1'].value = "DATA KONTRAK"
        ws['A1'].font = title_font
        ws['A1'].alignment = align_center

        ws.merge_cells('A2:J2')
        ws['A2'].value = f"Diekspor pada: {tz.now().strftime('%d %b %Y')}"
        ws['A2'].alignment = align_center
        ws.append([])

        headers = [
            'No. Kontrak', 'Judul', 'Klien', 'Status', 'Nilai (Rp)',
            'Tanggal Mulai', 'Tanggal Berakhir', 'Sisa Hari', 'PIC', 'Dibuat'
        ]
        ws.append(headers)
        for cell in ws[4]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = align_center

        qs = self.get_queryset().select_related('client', 'owner')

        search = request.GET.get('q', '')
        status = request.GET.get('status', '')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(contract_number__icontains=search) |
                Q(title__icontains=search) |
                Q(client__company_name__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)

        for row_num, c in enumerate(qs, start=5):
            row_data = [
                c.contract_number,
                c.title,
                c.client.company_name,
                c.get_status_display(),
                float(c.value) if c.value else 0,
                c.start_date.strftime('%d %b %Y'),
                c.end_date.strftime('%d %b %Y'),
                c.days_remaining,
                c.owner.get_full_name() or c.owner.username,
                c.created_at.strftime('%d %b %Y'),
            ]
            ws.append(row_data)
            for cell in ws[row_num]:
                cell.border = border
                cell.alignment = align_center if cell.column in [1, 4, 6, 7, 8, 10] else align_left

        widths = {'A': 18, 'B': 30, 'C': 25, 'D': 15, 'E': 20, 'F': 18, 'G': 18, 'H': 12, 'I': 20, 'J': 18}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
        ws.auto_filter.ref = f"A4:J{ws.max_row}"

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="contracts_export_{tz.now().strftime("%Y%m%d")}.xlsx"'
        wb.save(response)
        return response

