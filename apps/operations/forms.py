from django import forms
from .models import Shipment, Manifest, ShipmentItem, PickupOrder
from apps.master.display import coverage_city_label, coverage_district_label

class PickupOrderForm(forms.ModelForm):
    class Meta:
        model = PickupOrder
        fields = [
            'status', 'pickup_date', 'pickup_time', 'client', 'vehicle', 'driver',
            'reff_doc_no', 'pic_name', 'pic_phone', 'city', 'district',
            'pickup_address', 'weight', 'colly', 'shipment_type',
            'description_item', 'req_packing', 'insurance', 'note', 'file_upload'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pickup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(choices=[
                ('', '-- Pilih Armada --'),
                ('Blind Van', 'Blind Van'),
                ('Motorcycle', 'Motorcycle'),
                ('Cold Diesel Double', 'Cold Diesel Double'),
                ('Cold Diesel Engkel', 'Cold Diesel Engkel'),
                ('Container', 'Container'),
                ('Tronton', 'Tronton'),
                ('Wingbox', 'Wingbox')
            ], attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'reff_doc_no': forms.TextInput(attrs={'class': 'form-control'}),
            'pic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'pic_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'pickup_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'colly': forms.NumberInput(attrs={'class': 'form-control'}),
            'shipment_type': forms.Select(choices=[
                ('Package', 'Package'),
                ('Document', 'Document')
            ], attrs={'class': 'form-select'}),
            'description_item': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'req_packing': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-select'}),
            'insurance': forms.Select(choices=[(True, 'Yes'), (False, 'No')], attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.master.models import Coverage
        
        self.fields['client'].empty_label = "Ketik/Pilih Kustomer"
        self.fields['reff_doc_no'].required = False
        
        # Populate City from Coverage to include TLC
        coverages = Coverage.objects.filter(is_active=True).order_by('city')
        seen_cities = set()
        city_choices = [('', 'Pilih Kota...')]
        for c in coverages:
            if c.city not in seen_cities and c.city:
                seen_cities.add(c.city)
                label = coverage_city_label(c)
                city_choices.append((c.city, label))
        
        self.fields['city'].widget = forms.Select(choices=city_choices, attrs={'class': 'form-select select2-tags'})

        district_choices = [('', 'Pilih Kecamatan...')]
        seen_districts = set()
        for c in coverages:
            if c.district not in seen_districts and c.district:
                seen_districts.add(c.district)
                label = coverage_district_label(c)
                district_choices.append((c.district, label))
                
        self.fields['district'].widget = forms.Select(choices=district_choices, attrs={'class': 'form-select select2-tags'})


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'client', 'contract', 'quotation',
            
            # Shipper Detail
            'sender_name', 'sender_attention', 'sender_phone', 'sender_address', 
            'sender_city', 'sender_district', 'sender_postal_code', 'shipper_same_as_pickup',
            
            # Receiver Detail
            'receiver_name', 'receiver_attention', 'receiver_phone', 'receiver_address',
            'receiver_city', 'receiver_district', 'receiver_postal_code',
            
            # Shipment Info
            'is_cod', 'cod_value', 'insurance_type', 'item_value',
            'surcharge_type', 'surcharge_cost', 'handling_cost',
            
            # Package Detail
            'shipment_type_detail', 'pickup_number_ref', 'reference_no',
            'special_instruction', 'description_item',
            
            # Core Routing & Pricing
            'origin', 'destination', 'service_type', 'is_manual_override', 'resi_number',
            'weight', 'length', 'width', 'height', 'total_colly', 'price'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resi_number'].required = False
        self.fields['origin'].required = False
        self.fields['destination'].required = False
        self.fields['cod_value'].required = False
        
        # Set default for shipper same as pickup to True
        self.fields['shipper_same_as_pickup'].initial = True
        
        from apps.master.models import Coverage
        coverages = Coverage.objects.filter(is_active=True).order_by('city')
        seen_cities = set()
        city_choices = [('', 'Pilih Kota...')]
        for c in coverages:
            if c.city not in seen_cities and c.city:
                seen_cities.add(c.city)
                label = coverage_city_label(c)
                city_choices.append((c.city, label))

        district_choices = [('', 'Pilih Kecamatan...')]
        seen_districts = set()
        for c in coverages:
            if c.district not in seen_districts and c.district:
                seen_districts.add(c.district)
                label = coverage_district_label(c)
                district_choices.append((c.district, label))

        for field in ['sender_city', 'receiver_city', 'origin', 'destination']:
            if field in self.fields:
                self.fields[field].widget = forms.Select(choices=city_choices, attrs={'class': 'form-select select2-tags'})

        for field in ['sender_district', 'receiver_district']:
            if field in self.fields:
                val = getattr(self.instance, field) if self.instance and hasattr(self.instance, field) else ''
                self.fields[field].widget = forms.Select(choices=district_choices, attrs={'class': 'form-select select2-tags', 'data-current-val': val or ''})

        from apps.master.models import Service
        services = Service.objects.filter(is_active=True).order_by('name')
        if 'service_type' in self.fields:
            self.fields['service_type'].choices = [(s.code, s.name) for s in services]

    def clean(self):
        cleaned_data = super().clean()
        
        # Populate origin and destination if empty
        if not cleaned_data.get('origin'):
            cleaned_data['origin'] = cleaned_data.get('sender_city')
        if not cleaned_data.get('destination'):
            cleaned_data['destination'] = cleaned_data.get('receiver_city')
        
        return cleaned_data


class ShipmentItemForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ['actual_weight', 'quantity', 'panjang', 'lebar', 'tinggi', 'packing', 'description']
        widgets = {
            'actual_weight': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control calc-trigger'}),
            'panjang': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'step': '0.01'}),
            'lebar': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'step': '0.01'}),
            'tinggi': forms.NumberInput(attrs={'class': 'form-control calc-trigger', 'step': '0.01'}),
            'packing': forms.Select(attrs={'class': 'form-select calc-trigger'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        decimal_fields = ['actual_weight', 'panjang', 'lebar', 'tinggi']
        for field in decimal_fields:
            if cleaned_data.get(field) is None:
                cleaned_data[field] = 0
        if cleaned_data.get('quantity') is None:
            cleaned_data['quantity'] = 1
        return cleaned_data

ShipmentItemFormSet = forms.inlineformset_factory(
    Shipment,
    ShipmentItem,
    form=ShipmentItemForm,
    extra=0,
    can_delete=True
)

class ManifestForm(forms.ModelForm):
    # Field khusus untuk memilih resi-resi yang belum masuk manifest atau terlewat (Fleksibilitas Manual)
    shipments = forms.ModelMultipleChoiceField(
        queryset=Shipment.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        label="Pilih Resi (Tahan CTRL untuk pilih lebih dari 1)",
        required=False
    )

    manifest_number = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan No Manifest (Otomatis jika kosong)'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.master.models import Coverage
        coverages = Coverage.objects.filter(is_active=True).order_by('city')
        seen_cities = set()
        city_choices = [('', 'Pilih atau Ketik Tujuan...')]
        for c in coverages:
            if c.city not in seen_cities and c.city:
                seen_cities.add(c.city)
                label = coverage_city_label(c)
                city_choices.append((c.city, label))
        
        self.fields['destination_city'].widget.choices = city_choices
        self.fields['destination_city'].widget.attrs.update({
            'class': 'form-select select2-searchable',
            'data-placeholder': 'Pilih atau Cari Tujuan...'
        })
        
        from apps.organizations.models import Branch
        self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
        self.fields['branch'].label_from_instance = lambda obj: f"{obj.code} - {obj.name}" if obj.code else obj.name
        self.fields['branch'].widget.attrs.update({
            'class': 'form-select select2-searchable',
            'data-placeholder': 'Pilih atau Cari Cabang...'
        })
        
        # Adjust transport_mode choices based on manifest type
        m_type = self.data.get('manifest_type') or self.initial.get('manifest_type', '')
        if hasattr(self, 'instance') and self.instance.pk:
            m_type = self.instance.manifest_type

        if m_type == 'DELIVERY':
            self.fields['colly_cmo'].required = False
            self.fields['actual_weight'].required = False
            
        if m_type == 'TRANSFER':
            self.fields['transport_mode'].widget.choices = [
                ('', '- Select an option -'),
                ('Darat', 'Darat'), 
                ('Laut', 'Laut'), 
                ('Udara', 'Udara'),
                ('Kereta', 'Kereta')
            ]

    class Meta:
        model = Manifest
        fields = [
            'manifest_type', 'manifest_number', 'driver', 'vehicle', 'vendor', 'vendor_ref_no', 'flight_no', 'vessel_name', 
            'destination_city', 'branch', 'colly_cmo', 'actual_weight', 'commodity', 'description', 'date', 
            'departure_time', 'arrival_date', 'arrival_time', 'transport_mode', 'vendor_middle', 'shipments', 'pic'
        ]
        widgets = {
            'manifest_type': forms.HiddenInput(),
            'manifest_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan No Manifest'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'vendor_ref_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No. Resi / SPK Vendor'}),
            'flight_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: GA-123 / SMU-9908'}),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: KM Kelimutu / BL-8871'}),
            'destination_city': forms.Select(attrs={'class': 'form-select select2-tags', 'data-placeholder': 'Pilih atau Ketik Tujuan...'}),
            'branch': forms.Select(attrs={'class': 'form-select select2-searchable', 'data-placeholder': 'Pilih atau Cari Cabang...'}),
            'colly_cmo': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
            'actual_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': 0}),
            'commodity': forms.Select(choices=[
                ('', '-- Pilih Komoditas --'),
                ('GENERAL CARGO', 'GENERAL CARGO'),
                ('VALUABLE GOODS', 'VALUABLE GOODS'),
                ('DANGEROUS GOODS', 'DANGEROUS GOODS'),
                ('HEAVY CARGO (75KG - 250KG)', 'HEAVY CARGO (75KG - 250KG)')
            ], attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Deskripsi / Alasan'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'arrival_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'arrival_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'transport_mode': forms.Select(choices=[
                ('Air Freight Manifest (UDR)', 'Air Freight Manifest (UDR)'), 
                ('Land Manifest (DRT)', 'Land Manifest (DRT)'), 
                ('Sea Manifest (SEA)', 'Sea Manifest (SEA)')
            ], attrs={'class': 'form-select'}),
            'vendor_middle': forms.Select(attrs={'class': 'form-select'}),
            'pic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama PIC / Penanggung Jawab'}),
        }
