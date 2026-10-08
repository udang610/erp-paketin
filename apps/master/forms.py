from django import forms
from .models import Bank, Coverage, Service, Price, Vehicle, Customer
from apps.organizations.models import Branch
from apps.crm.models import Client
from apps.finance.models import Vendor
import re

from apps.master.display import clean_branch_label

class CleanBranchChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return clean_branch_label(obj)

class VendorForm(forms.ModelForm):
    branch = CleanBranchChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        required=False,
        empty_label="-- Pilih Cabang --",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    class Meta:
        model = Vendor
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if type(field.widget) in (forms.CheckboxInput, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-check-input'
            elif type(field.widget) == forms.Select:
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['company_name', 'contact_person', 'email', 'phone', 'address', 'owner', 'branch', 'customer_status', 'customer_category']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['customer_status', 'customer_category', 'owner', 'branch']:
                field.widget.attrs['class'] = 'form-select'

class BankForm(forms.ModelForm):
    branch = CleanBranchChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        required=False,
        empty_label="-- Pilih Cabang --",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    class Meta:
        model = Bank
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CoverageForm(forms.ModelForm):
    class Meta:
        model = Coverage
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_covered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PriceForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'destination': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_days': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VehicleForm(forms.ModelForm):
    branch = CleanBranchChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        required=False,
        empty_label="-- Pilih Cabang --",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    class Meta:
        model = Vehicle
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control'}),
            'brand_model': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacity_cbm': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'kir_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class CustomerForm(forms.ModelForm):
    branch = CleanBranchChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        required=False,
        empty_label="-- Pilih Cabang --",
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    class Meta:
        model = Customer
        fields = '__all__'
        # customer_code digenerate otomatis oleh Customer.save() (CUST-XXXX)
        exclude = ['created_by', 'created_at', 'updated_at', 'customer_code']
        widgets = {
            'effective_start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'effective_end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Alamat Kantor Lengkap'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if type(field.widget) in (forms.CheckboxInput, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-check-input'
            elif type(field.widget) == forms.Select:
                field.widget.attrs['class'] = 'form-select select2'
            else:
                field.widget.attrs['class'] = 'form-control'
                
        from apps.master.models import Coverage
        from apps.master.display import coverage_city_label, coverage_district_label
        
        # City Choices
        coverages = Coverage.objects.filter(is_active=True).order_by('city')
        seen_cities = set()
        city_choices = [('', 'Pilih Kota...')]
        for c in coverages:
            if c.city not in seen_cities and c.city:
                seen_cities.add(c.city)
                label = coverage_city_label(c)
                city_choices.append((c.city, label))
        self.fields['city'].widget = forms.Select(choices=city_choices, attrs={'class': 'form-select select2'})

        # District Choices
        current_city = self.data.get('city') or (self.instance.city if self.instance else '')
        current_dist = self.data.get('district') or (self.instance.district if self.instance else '')
        
        seen_districts = set()
        district_choices = [('', 'Pilih Kecamatan...')]
        if current_city:
            clean_city = re.sub(r'^(Kota|Kabupaten|Kab\.)\s+', '', current_city, flags=re.IGNORECASE)
            from django.db.models import Q
            cov_districts = Coverage.objects.filter(is_active=True).filter(Q(city__iexact=current_city) | Q(city__icontains=clean_city)).order_by('district')
            for d in cov_districts:
                if d.district not in seen_districts and d.district:
                    seen_districts.add(d.district)
                    label = coverage_district_label(d)
                    district_choices.append((d.district, label))
        elif current_dist:
            district_choices.append((current_dist, current_dist))
            
        self.fields['district'].widget = forms.Select(choices=district_choices, attrs={'class': 'form-select select2'})