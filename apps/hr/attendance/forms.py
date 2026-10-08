from django import forms
from .models import AttendancePolicy

class AttendancePolicyForm(forms.ModelForm):
    class Meta:
        model = AttendancePolicy
        fields = [
            'name', 'branch', 'work_mode', 'check_in_time', 'check_out_time', 
            'late_threshold_minutes', 'gps_required', 'allowed_radius_meters',
            'face_verification_required', 'device_verification_required'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'late_threshold_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'gps_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allowed_radius_meters': forms.NumberInput(attrs={'class': 'form-control'}),
            'face_verification_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'device_verification_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
