from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "classification", "owner", "is_active", "created_at")
    list_filter = ("document_type", "classification", "is_active")
    search_fields = ("title", "original_filename", "owner__email")
    readonly_fields = ("id", "original_filename", "file_size", "content_type", "created_at", "updated_at")

# Register your models here.
