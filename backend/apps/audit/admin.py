from django.contrib import admin
from .models import AuditChainState, AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in AuditLog._meta.fields]
    list_display = ("timestamp", "event_type", "outcome", "user", "resource_type")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(AuditChainState)
class AuditChainStateAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "last_hash")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
