from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.authentication.issureauth.models import User,Otp
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "mobile_number",
        "kyc_status",
        "is_active",
        "email_verified",
        "mobile_verified",
        "created_at",
    )
    list_filter = ("kyc_status", "is_active", "email_verified", "mobile_verified")
    search_fields = ("email", "mobile_number", "kyc_id")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "mobile_number", "password")}),
        ("KYC Info", {"fields": ("kyc_id", "kyc_status")}),
        ("Account Status", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "email_verified",
                "mobile_verified",
            )
        }),
        ("Security", {"fields": ("password_hash", "password_salt")}),
        ("Audit Info", {"fields": ("created_at", "updated_at", "user_id_updated_by")}),
    )

    readonly_fields = ("created_at", "updated_at")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "mobile_number", "password1", "password2"),
            },
        ),
    )


# ✅ Register OTP model
@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = (
        "otp_id",
        "user",
        "otp_code",
        "otp_type",
        "is_used",
        "expiry_time",
        "created_at",
    )
    list_filter = ("otp_type", "is_used", "is_del")
    search_fields = ("otp_code", "user__email", "user__mobile_number")
    ordering = ("-created_at",)