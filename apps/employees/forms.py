from django import forms
from .models import Employee, EmploymentStatus
from django.contrib.auth import get_user_model
from apps.organizations.models import Branch, Department, Position

User = get_user_model()

class EmployeeForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_superuser=False).order_by('username'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select select2', 'id': 'id_user_select'}),
        label='Pilih Akun Pengguna / User',
        empty_label='--- Pilih Akun User Terdaftar ---',
        help_text='Pilih akun login yang sudah dibuat oleh Superadmin/Master Data.'
    )
    
    class Meta:
        model = Employee
        fields = [
            'user', 'employee_id', 'full_name', 'phone_number', 'profile_picture',
            'nik', 'npwp', 'branch', 'department', 'position', 'supervisor',
            'status', 'join_date', 'contract_end_date',
            'document_ktp', 'document_contract',
            'bank_name', 'bank_account_number', 'bank_account_holder',
            'emergency_contact_name', 'emergency_contact_relation', 'emergency_contact_phone',
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIP / ID Pegawai (e.g. EMP-001)'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap Sesuai KTP'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xx-xxxx-xxxx'}),
            'nik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '16 digit NIK'}),
            'npwp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor Pokok Wajib Pajak'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'document_ktp': forms.FileInput(attrs={'class': 'form-control'}),
            'document_contract': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BCA / Mandiri / BRI / BNI'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nomor Rekening Payroll'}),
            'bank_account_holder': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Atas Nama Rekening'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Kontak Darurat'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Orang Tua / Pasangan / Saudara'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xx-xxxx-xxxx'}),
        }
        labels = {
            'employee_id': 'NIP / ID Pegawai',
            'full_name': 'Nama Lengkap Pegawai',
            'phone_number': 'Nomor HP Pegawai',
            'nik': 'No. KTP / NIK',
            'npwp': 'NPWP',
            'branch': 'Cabang Penempatan',
            'department': 'Departemen',
            'position': 'Posisi / Jabatan',
            'supervisor': 'Atasan Langsung',
            'status': 'Status Kepegawaian',
            'join_date': 'Tanggal Bergabung',
            'contract_end_date': 'Tanggal Berakhir Kontrak',
            'document_ktp': 'Unggah Dokumen KTP',
            'document_contract': 'Unggah Berkas Kontrak / CV',
            'profile_picture': 'Foto Profil Pegawai',
            'bank_name': 'Nama Bank',
            'bank_account_number': 'Nomor Rekening',
            'bank_account_holder': 'Atas Nama Rekening',
            'emergency_contact_name': 'Nama Kontak Darurat',
            'emergency_contact_relation': 'Hubungan Kontak Darurat',
            'emergency_contact_phone': 'Nomor HP Darurat',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and getattr(self.instance, 'user_id', None):
            self.fields['user'].initial = self.instance.user
            # In edit mode, disable changing user to avoid data confusion
            self.fields['user'].widget.attrs['readonly'] = 'readonly'
            self.fields['user'].widget.attrs['style'] = 'pointer-events: none; background-color: #f8f9fa;'

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not self.instance.pk:
            existing = Employee.objects.filter(user=user).first()
            if existing:
                self.instance = existing
        return user
