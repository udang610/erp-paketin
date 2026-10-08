from django.contrib import admin
from .models import DocumentCategory, Document, DocumentVersion

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'owner', 'current_version', 'expiration_date')
    list_filter = ('category', 'expiration_date')
    search_fields = ('title', 'owner__full_name')
    inlines = [DocumentVersionInline]

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'uploaded_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title',)
