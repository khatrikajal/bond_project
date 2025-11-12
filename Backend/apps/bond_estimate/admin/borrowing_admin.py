"""
Admin interface for Borrowing Details.
Optimized with search, filters, actions, formatted fields, and summary insights.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from ..models.borrowing_details import BorrowingDetails


@admin.register(BorrowingDetails)
class BorrowingDetailsAdmin(admin.ModelAdmin):
    """
    Admin configuration for Borrowing Details model.
    """

    # Columns shown in admin list view
    list_display = [
        'borrowing_id',
        'company_id',
        'lender_name',
        'formatted_amount',
        'borrowing_type',
        'repayment_terms',
        'formatted_interest_rate',
        'status_badge',
        'created_at',
    ]

    # Filters on the right-hand side
    list_filter = [
        'borrowing_type',
        'repayment_terms',
        'is_del',
        'created_at',
    ]

    # Search functionality
    search_fields = [
        'lender_name',
        'company_id',
    ]

    # Read-only fields (cannot be modified manually)
    readonly_fields = [
        'borrowing_id',
        'created_at',
        'updated_at',
    ]

    # Detail view grouping
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'borrowing_id',
                'company_id',
                'lender_name',
            )
        }),
        ('Financial Details', {
            'fields': (
                'lender_amount',
                'borrowing_type',
                'repayment_terms',
                'monthly_principal_payment',
                'interest_payment_percentage',
                'monthly_interest_payment',
            )
        }),
        ('Status & Tracking', {
            'fields': (
                'is_del',
                'user_id_updated_by',
                'created_at',
                'updated_at',
            )
        }),
    )

    # Sorting, pagination, and date hierarchy
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'

    # Custom bulk actions
    actions = [
        'soft_delete_selected',
        'restore_selected',
        'export_to_csv',
    ]

    # -----------------------------------------------------------
    # Custom Display Fields
    # -----------------------------------------------------------

    def formatted_amount(self, obj):
        """Display formatted lender amount with ₹ sign"""
        if obj.lender_amount is not None:
            amount_str = f"₹{obj.lender_amount:,.2f}"
            return format_html("<strong>{}</strong>", amount_str)
        return "-"
    formatted_amount.short_description = 'Lender Amount'
    formatted_amount.admin_order_field = 'lender_amount'

    def formatted_interest_rate(self, obj):
        """Display formatted interest rate with %"""
        if obj.interest_payment_percentage is not None:
            return f"{obj.interest_payment_percentage:.2f}%"
        return "-"
    formatted_interest_rate.short_description = 'Interest Rate'
    formatted_interest_rate.admin_order_field = 'interest_payment_percentage'

    def status_badge(self, obj):
        """Display active/deleted badge"""
        if obj.is_del == 0:
            return format_html(
                '<span style="background-color:#28a745; color:white; '
                'padding:3px 10px; border-radius:4px;">Active</span>'
            )
        return format_html(
            '<span style="background-color:#dc3545; color:white; '
            'padding:3px 10px; border-radius:4px;">Deleted</span>'
        )
    status_badge.short_description = 'Status'

    # -----------------------------------------------------------
    # Query Optimization
    # -----------------------------------------------------------

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset

    # -----------------------------------------------------------
    # Custom Admin Actions
    # -----------------------------------------------------------

    def soft_delete_selected(self, request, queryset):
        """Soft delete selected borrowings"""
        user_id = request.user.id if request.user.is_authenticated else None
        updated = queryset.filter(is_del=0).update(
            is_del=1,
            user_id_updated_by=user_id
        )
        self.message_user(request, f'{updated} borrowing(s) soft deleted successfully.')
    soft_delete_selected.short_description = 'Soft delete selected borrowings'

    def restore_selected(self, request, queryset):
        """Restore previously deleted borrowings"""
        user_id = request.user.id if request.user.is_authenticated else None
        updated = queryset.filter(is_del=1).update(
            is_del=0,
            user_id_updated_by=user_id
        )
        self.message_user(request, f'{updated} borrowing(s) restored successfully.')
    restore_selected.short_description = 'Restore selected borrowings'

    def export_to_csv(self, request, queryset):
        """Export selected borrowings to CSV file"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="borrowings.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Borrowing ID', 'Company ID', 'Lender Name', 'Amount',
            'Borrowing Type', 'Repayment Terms', 'Monthly Principal',
            'Interest Rate %', 'Monthly Interest', 'Status', 'Created At'
        ])

        for obj in queryset:
            writer.writerow([
                obj.borrowing_id,
                obj.company_id,
                obj.lender_name,
                obj.lender_amount,
                obj.borrowing_type,
                obj.repayment_terms,
                obj.monthly_principal_payment,
                obj.interest_payment_percentage or '',
                obj.monthly_interest_payment,
                'Active' if obj.is_del == 0 else 'Deleted',
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response
    export_to_csv.short_description = 'Export selected borrowings to CSV'

    # -----------------------------------------------------------
    # Summary Bar (at top of changelist)
    # -----------------------------------------------------------

    def changelist_view(self, request, extra_context=None):
        """
        Add financial summary at top of admin list view
        """
        extra_context = extra_context or {}
        queryset = self.get_queryset(request).filter(is_del=0)

        summary = queryset.aggregate(
            total_lender_amount=Sum('lender_amount'),
            total_monthly_principal=Sum('monthly_principal_payment'),
            total_monthly_interest=Sum('monthly_interest_payment'),
        )

        # Format totals for display
        def format_currency(value):
            if value:
                return f"₹{value:,.2f}"
            return "₹0.00"

        extra_context['summary'] = {
            'total_lender_amount': format_currency(summary['total_lender_amount']),
            'total_monthly_principal': format_currency(summary['total_monthly_principal']),
            'total_monthly_interest': format_currency(summary['total_monthly_interest']),
        }

        return super().changelist_view(request, extra_context=extra_context)
