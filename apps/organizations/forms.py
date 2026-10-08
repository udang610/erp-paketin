from django import forms
from .models import Branch, Department, Position

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'code', 'address', 'timezone', 'attendance_radius_meters', 'clock_in_time', 'clock_out_time', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Cabang'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kode (ex: JKT-01)'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'timezone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asia/Jakarta'}),
            'attendance_radius_meters': forms.NumberInput(attrs={'class': 'form-control'}),
            'clock_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'clock_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }
