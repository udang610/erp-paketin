from django import forms
from .models import DocumentCategory, Document

class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Folder'}),
            'parent': forms.HiddenInput(),
        }

class DocumentForm(forms.ModelForm):
    # In a real system, you'd have a FileField here for upload handling
    # file_upload = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Document
        fields = ['title', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama File'}),
            'category': forms.HiddenInput(),
        }
