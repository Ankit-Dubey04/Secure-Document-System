from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class SecureUserAdmin(UserAdmin):
    model = User
    ordering = ("email",)
    list_display = ("email", "name", "role", "department", "account_active", "is_staff")
    list_filter = ("role", "clearance_level", "account_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("Security profile", {"fields": ("name", "role", "department", "clearance_level", "account_active", "created_at", "updated_at")} ),)
    readonly_fields = ("created_at", "updated_at")
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2", "role", "department", "clearance_level")} ),)

# Register your models here.
