"""
Admin configuration for BondEstimationApplication model.
Provides detailed view, filtering, and searching options.
"""

from django.contrib import admin
from apps.bond_estimate.model.BondEstimationApplicationModel import BondEstimationApplication


@admin.register(BondEstimationApplication)
class BondEstimationApplicationAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing Bond Estimation Applications
    """

    # Columns displayed in the list view
    list_display = [
        'application_id',
        'company_name_display',
        'user_display',
        'status',
        'last_accessed_step',
        'submitted_at',
        'created_at',
        'updated_at',
    ]

    # Searchable fields
    search_fields = [
        'application_id',
        'company__company_name',
        'user__email',   # ✅ changed from username to email
        'status',
    ]

    # Filters on the right-hand side
    list_filter = [
        'status',
        'created_at',
        'updated_at',
    ]

    # Read-only fields (auto-managed)
    readonly_fields = [
        'application_id',
        'created_at',
        'updated_at',
        'submitted_at',
    ]

    # Default ordering
    ordering = ['-created_at']

    # Organized form layout
    fieldsets = (
        ("Application Info", {
            'fields': (
                'application_id',
                'user',
                'company',
                'status',
                'last_accessed_step',
            )
        }),
        ("Progress & Metadata", {
            'fields': (
                'step_progress',
                'submitted_at',
                'created_at',
                'updated_at',
            )
        }),
    )

    # ---------------------------------------------
    # Custom display helper methods
    # ---------------------------------------------

    def company_name_display(self, obj):
        """Show company name in list display"""
        return obj.company.company_name if obj.company else "-"
    company_name_display.short_description = "Company"

    def user_display(self, obj):
        """Show user identifier (email or fallback)"""
        user = obj.user
        if not user:
            return "-"
        # ✅ Handle both custom and standard user models safely
        if hasattr(user, "username") and user.username:
            return user.username
        elif hasattr(user, "email") and user.email:
            return user.email
        elif hasattr(user, "id"):
            return f"User {user.id}"
        return str(user)
    user_display.short_description = "User"
