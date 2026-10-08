"""
Sales forms with Bootstrap styling and validation.
"""
from django import forms
from apps.core.mixins import is_admin
from apps.crm.models import Client, Lead, Contract


SERVICE_TYPE_CHOICES = Lead.ServiceType.choices


class ClientForm(forms.ModelForm):
    """Form for creating/updating a Client with cascading region support."""
    province = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select select2', 'id': 'id_province'}))
    city = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select select2', 'id': 'id_city'}))
    district = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select select2', 'id': 'id_district'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['industry'].required = True
        
        from apps.master.models import Coverage, Province
        from apps.master.display import coverage_city_label, coverage_district_label
        
        # Province Choices
        provinces = Province.objects.all().order_by('name')
        if provinces.exists():
            prov_choices = [('', 'Pilih Provinsi...')] + [(p.name, p.name) for p in provinces]
        else:
            coverages_prov = Coverage.objects.filter(is_active=True).values_list('province', flat=True).distinct().order_by('province')
            prov_choices = [('', 'Pilih Provinsi...')] + [(p, p) for p in coverages_prov if p]
        self.fields['province'].widget.choices = prov_choices

        # Initial City Choices
        current_prov = self.data.get('province') or (self.instance.province if self.instance else '')
        current_city = self.data.get('city') or (self.instance.city if self.instance else '')
        current_dist = self.data.get('district') or (self.instance.district if self.instance else '')
        
        city_choices = [('', 'Pilih Kota / Kabupaten...')]
        if current_prov:
            cov_cities = Coverage.objects.filter(province__iexact=current_prov, is_active=True).order_by('city')
            seen_cities = set()
            for c in cov_cities:
                if c.city not in seen_cities and c.city:
                    seen_cities.add(c.city)
                    label = coverage_city_label(c)
                    city_choices.append((c.city, label))
        elif current_city:
            city_choices.append((current_city, current_city))
        self.fields['city'].widget.choices = city_choices

        # Initial District Choices
        district_choices = [('', 'Pilih Kecamatan...')]
        if current_city:
            cov_districts = Coverage.objects.filter(city__icontains=current_city, is_active=True).order_by('district')
            seen_districts = set()
            for d in cov_districts:
                if d.district not in seen_districts and d.district:
                    seen_districts.add(d.district)
                    label = coverage_district_label(d)
                    district_choices.append((d.district, label))
        elif current_dist:
            district_choices.append((current_dist, current_dist))
        self.fields['district'].widget.choices = district_choices

    class Meta:
        model = Client
        fields = [
            'paketin_group', 'account_type', 'company_name', 'divisi',
            'contact_person', 'phone', 'email', 'industry',
            'address', 'province', 'city', 'district', 'postal_code',
            'pic_pickup', 'pic_pickup_phone',
            'term_of_payment', 'payment_type',
            'npwp', 'website', 'customer_category', 'customer_status',
            'notes',
        ]
        widgets = {
            'paketin_group': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Perusahaan'}),
            'divisi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Divisi / Departemen'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama PIC Utama'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xxxxxxxxxx'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@company.com'}),
            'industry': forms.Select(attrs={'class': 'form-select select2-industry', 'data-placeholder': 'Pilih atau Cari Industri...'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Alamat kantor / gudang'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kode Pos'}),
            'pic_pickup': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama PIC Pickup di Lapangan'}),
            'pic_pickup_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No. Telepon PIC Pickup'}),
            'term_of_payment': forms.Select(attrs={'class': 'form-select'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'npwp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX.XXX.XXX.X-XXX.XXX'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.example.com'}),
            'customer_category': forms.Select(attrs={'class': 'form-select'}),
            'customer_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Catatan tambahan'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        if phone and len(phone) < 8:
            raise forms.ValidationError('Nomor telepon terlalu pendek.')
        return phone


class LeadForm(forms.ModelForm):
    """Form for creating/updating a Lead."""

    estimated_value = forms.CharField(
        label='Estimasi Nilai (Rp)',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )

    class Meta:
        model = Lead
        fields = [
            'client', 'lead_source', 'status', 'estimated_value',
            'shipping_service', 'shipping_origin', 'shipping_destination',
            'shipping_estimated_weight', 'shipping_frequency', 'shipping_notes',
            'responds_fast', 'interested', 'decision_maker',
            'budget_available', 'competitor_exists', 'closed_at', 'notes',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'lead_source': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'shipping_service': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'shipping_origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kota/Wilayah asal'}),
            'shipping_destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kota/Wilayah tujuan'}),
            'shipping_estimated_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '0.01'}),
            'shipping_frequency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: 2x seminggu'}),
            'shipping_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Detail pengiriman tambahan'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responds_fast': forms.Select(attrs={'class': 'form-select'}),
            'interested': forms.Select(attrs={'class': 'form-select'}),
            'decision_maker': forms.Select(attrs={'class': 'form-select'}),
            'budget_available': forms.Select(attrs={'class': 'form-select'}),
            'competitor_exists': forms.Select(attrs={'class': 'form-select'}),
            'closed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Only show user's own clients in the dropdown
        if user and not is_admin(user):
            self.fields['client'].queryset = Client.objects.filter(owner=user)
        
        # Make shipping weight optional
        self.fields['shipping_estimated_weight'].required = False

        # Override shipping_service as MultipleChoiceField for checkbox support
        self.fields['shipping_service'] = forms.MultipleChoiceField(
            label='Jenis Pengiriman',
            choices=SERVICE_TYPE_CHOICES,
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        )
        # Restore initial value from instance (JSONField stores list)
        if self.instance and self.instance.pk and self.instance.shipping_service:
            self.initial['shipping_service'] = self.instance.shipping_service

    def clean_estimated_value(self):
        val = self.cleaned_data.get('estimated_value')
        if not val:
            return 0
        
        # Hapus titik (sebagai pemisah ribuan)
        val = str(val).replace('.', '').replace(',', '')
        try:
            return float(val)
        except ValueError:
            raise forms.ValidationError('Masukkan angka yang valid.')


class ContractForm(forms.ModelForm):
    """Form for creating/updating a Contract."""

    class Meta:
        model = Contract
        fields = [
            'lead', 'client', 'contract_number', 'title', 'description',
            'value', 'start_date', 'end_date', 'status', 'terms', 'penerima',
            'document', 'renewal_reminder_days',
        ]
        widgets = {
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'contract_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generate jika kosong'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Kontrak'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deskripsi kontrak'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Syarat dan ketentuan'}),
            'penerima': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Penerima'}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'renewal_reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not is_admin(user):
            self.fields['lead'].queryset = Lead.objects.filter(owner=user, status=Lead.Status.WON)
            self.fields['client'].queryset = Client.objects.filter(owner=user)
        else:
            self.fields['lead'].queryset = Lead.objects.filter(status=Lead.Status.WON)

        # Make contract_number not required (auto-generated)
        self.fields['contract_number'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('Tanggal berakhir harus setelah tanggal mulai.')
        return cleaned_data
