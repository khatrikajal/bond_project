from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.UserModel import User
from .models.OtpModel import Otp

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ("mobile_number", "email", "mobile_verified", "email_verified", "role")
    list_filter = ("role", "mobile_verified", "email_verified", "is_active")

    fieldsets = (
        (None, {"fields": ("mobile_number", "email", "password")}),
        ("Verification", {"fields": ("mobile_verified", "email_verified")}),
        ("Role", {"fields": ("role",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Timestamps", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "mobile_number",
                    "email",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )

    search_fields = ("mobile_number", "email")
    ordering = ("mobile_number",)




@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ("recipient", "otp_code", "otp_type", "created_at", "expires_at", "is_used")
    list_filter = ("otp_type", "is_used")
    search_fields = ("recipient", "otp_code")
