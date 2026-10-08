"""
Quotation form with Bootstrap styling.
"""
from django import forms
from apps.core.mixins import is_admin
from apps.crm.models import Quotation, QuotationItem
from apps.crm.models import Lead

SERVICE_TYPE_CHOICES = Quotation.ServiceType.choices


class QuotationForm(forms.ModelForm):
    """Form for creating/updating a Quotation."""
    manual_total_price = forms.CharField(
        label='Total Harga (Manual)',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rupiah-input', 'placeholder': 'Rp (Contoh: 1.000.000)'})
    )
    origin_input = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select select2-tags'}))
    destination_input = forms.CharField(required=False, widget=forms.Select(attrs={'class': 'form-select select2-tags'}))
    is_manual_override = forms.BooleanField(label='Input Manual (Bypass)', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Quotation
        fields = [
            'lead', 'attachment', 'manual_total_price', 'panjang', 'lebar', 'tinggi', 'actual_weight',
            'service', 'is_manual_override',
            'quantity', 'price_per_kg', 'insurance', 'packing', 'discount', 'notes',
        ]
        widgets = {
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'panjang': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.01'}),
            'lebar': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.01'}),
            'tinggi': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'cm', 'step': '0.01'}),
            'actual_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kg', 'step': '0.01'}),
            'service': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Jumlah Koli'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rp', 'step': '0.01'}),
            'insurance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rp', 'step': '0.01'}),
            'packing': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rp', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rp', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate initial choices for Select2 from Master Data
        from apps.master.models import Coverage
        coverage_choices = [('', 'Pilih atau Ketik Baru...')] + [(str(c.id), str(c)) for c in Coverage.objects.all()]
        self.fields['origin_input'].widget.choices = coverage_choices
        self.fields['destination_input'].widget.choices = coverage_choices
        
        if self.instance and self.instance.pk:
            if self.instance.origin_coverage:
                self.initial['origin_input'] = str(self.instance.origin_coverage.id)
            else:
                self.initial['origin_input'] = self.instance.origin
                
            if self.instance.destination_coverage:
                self.initial['destination_input'] = str(self.instance.destination_coverage.id)
            else:
                self.initial['destination_input'] = self.instance.destination
        
        # Auto-create DEVELOPMENT client and lead for testing if they don't exist
        if user and user.is_authenticated:
            try:
                from apps.crm.models import Client, Lead
                # Use first() in case it was created by someone else so we don't duplicate
                dev_client = Client.objects.filter(company_name='DEVELOPMENT').first()
                if not dev_client:
                    dev_client = Client.objects.create(
                        company_name='DEVELOPMENT',
                        owner=user,
                        contact_person='Testing User',
                        email='test@development.local',
                        phone='0000000000'
                    )
                
                # Check for lead
                dev_lead = Lead.objects.filter(client=dev_client).first()
                if not dev_lead:
                    Lead.objects.create(
                        client=dev_client,
                        owner=user,
                        status='new',
                        estimated_value=0,
                        shipping_origin='TEST',
                        shipping_destination='TEST'
                    )
            except Exception as e:
                import logging
                logging.error(f"Error creating DEVELOPMENT data: {e}")

        if user and not is_admin(user):
            self.fields['lead'].queryset = Lead.objects.filter(owner=user)

        # Override service as MultipleChoiceField for checkbox support
        self.fields['service'] = forms.MultipleChoiceField(
            label='Layanan',
            choices=SERVICE_TYPE_CHOICES,
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        )
        
        # Restore initial value from instance
        if self.instance and self.instance.pk:
            if self.instance.service:
                self.initial['service'] = self.instance.service
            
            # Format manual total price to avoid decimals breaking JS (e.g. 5000000.00 -> 5000000)
            if self.instance.manual_total_price is not None:
                val = self.instance.manual_total_price
                if val == val.to_integral_value():
                    self.initial['manual_total_price'] = str(int(val))
                else:
                    self.initial['manual_total_price'] = str(val).replace('.', ',')

    def clean_manual_total_price(self):
        val = self.cleaned_data.get('manual_total_price')
        if val is not None:
            # If the user typed it with dots or commas as thousand separator, we need to handle it.
            # However, since Django's DecimalField automatically fails validation if there are letters,
            # we must process it from self.data directly because self.cleaned_data will be None if validation failed.
            pass
        return val

    def clean(self):
        cleaned_data = super().clean()
        
        # Master Data processing for Origin and Destination
        is_manual = cleaned_data.get('is_manual_override', False)
        origin_val = cleaned_data.get('origin_input')
        destination_val = cleaned_data.get('destination_input')
        
        from apps.master.models import Coverage
        
        def process_coverage(val, field_name):
            if not val:
                return None, ""
                
            if is_manual:
                return None, val # coverage is None, text is val
            
            if val.isdigit():
                try:
                    cov = Coverage.objects.get(id=int(val))
                    return cov, str(cov)
                except Coverage.DoesNotExist:
                    pass
            
            # Auto-create draft coverage
            parts = val.split(',')
            city = parts[0].strip()
            district = parts[1].strip() if len(parts) > 1 else city
            cov = Coverage.objects.create(city=city, district=district, province='Auto-created', is_verified=False)
            return cov, val
            
        origin_cov, origin_text = process_coverage(origin_val, 'Asal')
        dest_cov, dest_text = process_coverage(destination_val, 'Tujuan')
        
        self.processed_origin_cov = origin_cov
        self.processed_origin_text = origin_text
        self.processed_dest_cov = dest_cov
        self.processed_dest_text = dest_text
        
        # Manual Total Price handling
        manual_price = self.data.get('manual_total_price')
        if manual_price:
            # Remove dots
            clean_val = manual_price.replace('.', '')
            try:
                from decimal import Decimal
                cleaned_data['manual_total_price'] = Decimal(clean_val)
            except:
                self.add_error('manual_total_price', 'Format angka tidak valid.')
        else:
            cleaned_data['manual_total_price'] = None

        # Replace None with 0 for non-nullable DecimalFields
        decimal_fields = ['panjang', 'lebar', 'tinggi', 'actual_weight', 'insurance', 'packing', 'price_per_kg', 'discount']
        for field in decimal_fields:
            if cleaned_data.get(field) is None:
                cleaned_data[field] = 0

        # Also for quantity
        if cleaned_data.get('quantity') is None:
            cleaned_data['quantity'] = 1

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.origin_coverage = getattr(self, 'processed_origin_cov', None)
        instance.origin = getattr(self, 'processed_origin_text', "")
        instance.destination_coverage = getattr(self, 'processed_dest_cov', None)
        instance.destination = getattr(self, 'processed_dest_text', "")
        if commit:
            instance.save()
        return instance

class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['actual_weight', 'quantity', 'panjang', 'lebar', 'tinggi', 'packing', 'description']
        widgets = {
            'actual_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'panjang': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lebar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tinggi': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'packing': forms.Select(attrs={'class': 'form-select'}),
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

QuotationItemFormSet = forms.inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=0,
    can_delete=True
)
