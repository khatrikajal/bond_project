from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.UserModel import User,Role
from .models.OtpModel import Otp



@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "mobile_number", "get_roles", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "roles")
    search_fields = ("email", "mobile_number")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "mobile_number", "password")}),
        ("Verification", {"fields": ("mobile_verified", "email_verified")}),
        ("Roles", {"fields": ("roles",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "mobile_number",
                    "password1",
                    "password2",
                    "roles",
                )
            },
        ),
    )

    filter_horizontal = ("roles", "groups", "user_permissions")

    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])
    get_roles.short_description = "Roles"



@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ("recipient", "otp_code", "otp_type", "created_at", "expires_at", "is_used")
    list_filter = ("otp_type", "is_used")
    search_fields = ("recipient", "otp_code")
