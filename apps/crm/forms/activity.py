"""
Activity and Reminder forms with Bootstrap styling.
"""
from django import forms
from apps.core.mixins import is_admin
from apps.crm.models import Activity, Reminder
from apps.crm.models import Lead


class ActivityForm(forms.ModelForm):
    """Form for logging a sales activity."""

    class Meta:
        model = Activity
        fields = ['lead', 'activity_type', 'description', 'result', 'next_followup']
        widgets = {
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deskripsi aktivitas'}),
            'result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hasil dari aktivitas'}),
            'next_followup': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not is_admin(user):
            self.fields['lead'].queryset = Lead.objects.filter(owner=user)


class ReminderForm(forms.ModelForm):
    """Form for creating a reminder."""

    class Meta:
        model = Reminder
        fields = ['title', 'description', 'due_date', 'reminder_time', 'notify_before', 'completed']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul Reminder'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Deskripsi'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reminder_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notify_before': forms.Select(attrs={'class': 'form-select'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
