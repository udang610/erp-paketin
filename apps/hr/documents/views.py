from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import DocumentCategory, Document, DocumentVersion
from .serializers import DocumentCategorySerializer, DocumentSerializer, DocumentVersionSerializer
from .forms import DocumentCategoryForm, DocumentForm
from apps.accounts.views import IsSuperAdminOrReadOnly

class DocumentCategoryViewSet(viewsets.ModelViewSet):
    queryset = DocumentCategory.objects.all().order_by('name')
    serializer_class = DocumentCategorySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().select_related('category', 'owner', 'uploaded_by').order_by('-created_at')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.roles.filter(name='HRGA').exists():
            return super().get_queryset()
        
        # Employees see their own documents
        qs = super().get_queryset()
        if hasattr(user, 'employee_profile'):
            qs = qs.filter(owner=user.employee_profile)
        else:
            qs = qs.none()
        return qs

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class DocumentVersionViewSet(viewsets.ModelViewSet):
    queryset = DocumentVersion.objects.all().select_related('document', 'uploaded_by').order_by('-created_at')
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings

def document_list(request):
    folder_id = request.GET.get('folder')
    search_q = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category_filter', '').strip()
    file_type_filter = request.GET.get('file_type', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_folder':
            form = DocumentCategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Folder berhasil dibuat.')
        elif action == 'upload_file':
            # handle multiple files
            if 'file_upload' in request.FILES:
                files = request.FILES.getlist('file_upload')
                category_id = request.POST.get('category')
                category = DocumentCategory.objects.filter(id=category_id).first() if category_id else None
                
                fs = FileSystemStorage()
                for f in files:
                    # Save file physically
                    filename = fs.save(f'documents/{f.name}', f)
                    file_url = fs.url(filename)
                    
                    # Create document record
                    Document.objects.create(
                        title=f.name,
                        category=category,
                        owner=request.user.employee_profile if hasattr(request.user, 'employee_profile') else None,
                        uploaded_by=request.user,
                        file_path=file_url,
                        size_bytes=f.size,
                        mime_type=f.content_type
                    )
                messages.success(request, f'{len(files)} file berhasil diunggah.')
            else:
                messages.error(request, 'Tidak ada file yang dipilih.')
        elif action == 'rename_item':
            item_type = request.POST.get('item_type')
            item_id = request.POST.get('item_id')
            new_name = request.POST.get('new_name')
            
            if item_type == 'folder':
                folder = DocumentCategory.objects.filter(id=item_id).first()
                if folder:
                    folder.name = new_name
                    folder.save()
                    messages.success(request, 'Nama folder berhasil diubah.')
            elif item_type == 'file':
                doc = Document.objects.filter(id=item_id).first()
                if doc:
                    doc.title = new_name
                    doc.save()
                    messages.success(request, 'Nama file berhasil diubah.')
        elif action == 'delete_item':
            item_type = request.POST.get('item_type')
            item_id = request.POST.get('item_id')
            
            if item_type == 'folder':
                folder = DocumentCategory.objects.filter(id=item_id).first()
                if folder:
                    folder.delete()
                    messages.success(request, 'Folder berhasil dihapus.')
            elif item_type == 'file':
                doc = Document.objects.filter(id=item_id).first()
                if doc:
                    doc.delete()
                    messages.success(request, 'File berhasil dihapus.')
        elif action == 'delete_bulk':
            folder_ids = request.POST.getlist('selected_folders')
            file_ids = request.POST.getlist('selected_files')
            
            if folder_ids:
                DocumentCategory.objects.filter(id__in=folder_ids).delete()
            if file_ids:
                Document.objects.filter(id__in=file_ids).delete()
            
            messages.success(request, f'{len(folder_ids)} folder dan {len(file_ids)} file berhasil dihapus.')
        
        # Redirect to same folder to prevent resubmission
        url = request.path
        if folder_id:
            url += f'?folder={folder_id}'
        return redirect(url)
    
    all_categories = DocumentCategory.objects.all().order_by('name')

    active_filters = bool(category_filter or file_type_filter or start_date or end_date)

    # Base query
    if search_q or active_filters:
        # Global search mode across all folders if filtered
        current_folder = None
        folders = DocumentCategory.objects.none() if (category_filter or file_type_filter or start_date or end_date) else DocumentCategory.objects.filter(name__icontains=search_q)
        documents = Document.objects.all().select_related('category', 'uploaded_by')
        
        from apps.core.date_utils import parse_date_safe
        psd = parse_date_safe(start_date)
        ped = parse_date_safe(end_date)
        
        if search_q:
            matched_docs = documents.filter(title__icontains=search_q)
            filtered_docs = matched_docs
            if category_filter:
                filtered_docs = filtered_docs.filter(category_id=category_filter)
            if file_type_filter:
                if file_type_filter == 'pdf':
                    filtered_docs = filtered_docs.filter(title__iendswith='.pdf')
                elif file_type_filter == 'word':
                    filtered_docs = filtered_docs.filter(title__iregex=r'\.(docx?|rtf)$')
                elif file_type_filter == 'excel':
                    filtered_docs = filtered_docs.filter(title__iregex=r'\.(xlsx?|csv)$')
                elif file_type_filter == 'image':
                    filtered_docs = filtered_docs.filter(title__iregex=r'\.(png|jpe?g|webp|gif)$')
                elif file_type_filter == 'archive':
                    filtered_docs = filtered_docs.filter(title__iregex=r'\.(zip|rar|7z|tar|gz)$')
            date_filtered_docs = filtered_docs
            if psd:
                date_filtered_docs = date_filtered_docs.filter(created_at__date__gte=psd)
            if ped:
                date_filtered_docs = date_filtered_docs.filter(created_at__date__lte=ped)
                
            if date_filtered_docs.exists():
                documents = date_filtered_docs
            elif filtered_docs.exists():
                documents = filtered_docs
            else:
                documents = matched_docs
        else:
            if category_filter:
                documents = documents.filter(category_id=category_filter)
            if file_type_filter:
                if file_type_filter == 'pdf':
                    documents = documents.filter(title__iendswith='.pdf')
                elif file_type_filter == 'word':
                    documents = documents.filter(title__iregex=r'\.(docx?|rtf)$')
                elif file_type_filter == 'excel':
                    documents = documents.filter(title__iregex=r'\.(xlsx?|csv)$')
                elif file_type_filter == 'image':
                    documents = documents.filter(title__iregex=r'\.(png|jpe?g|webp|gif)$')
                elif file_type_filter == 'archive':
                    documents = documents.filter(title__iregex=r'\.(zip|rar|7z|tar|gz)$')
            if psd:
                documents = documents.filter(created_at__date__gte=psd)
            if ped:
                documents = documents.filter(created_at__date__lte=ped)
                
        breadcrumbs = []
        folder_form = DocumentCategoryForm()
        file_form = DocumentForm()
    elif folder_id:
        current_folder = DocumentCategory.objects.filter(id=folder_id).first()
        folders = DocumentCategory.objects.filter(parent=current_folder).order_by('name')
        documents = Document.objects.filter(category=current_folder).select_related('uploaded_by').order_by('-created_at')
        
        breadcrumbs = []
        node = current_folder
        while node is not None:
            breadcrumbs.insert(0, node)
            node = node.parent
            
        folder_form = DocumentCategoryForm(initial={'parent': current_folder})
        file_form = DocumentForm(initial={'category': current_folder})
    else:
        current_folder = None
        folders = DocumentCategory.objects.filter(parent__isnull=True).order_by('name')
        documents = Document.objects.filter(category__isnull=True).select_related('uploaded_by').order_by('-created_at')
        breadcrumbs = []
        
        folder_form = DocumentCategoryForm()
        file_form = DocumentForm()
        
    total_folders = folders.count()
    total_documents = documents.count()
        
    context = {
        'current_folder': current_folder,
        'folders': folders,
        'documents': documents,
        'breadcrumbs': breadcrumbs,
        'folder_form': folder_form,
        'file_form': file_form,
        'all_categories': all_categories,
        'search_q': search_q,
        'category_filter': category_filter,
        'file_type_filter': file_type_filter,
        'start_date': start_date,
        'end_date': end_date,
        'active_filters': active_filters,
        'total_folders': total_folders,
        'total_documents': total_documents,
    }
    return render(request, 'hrga/documents/document_list.html', context)
