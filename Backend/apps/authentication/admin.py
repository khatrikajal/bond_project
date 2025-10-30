# Backend/apps/authentication/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q

from .models import OTPRequest, OTPAttempt


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    """Admin interface for OTP requests with enhanced functionality"""
    
    list_display = [
        'phone_number', 'purpose', 'status_badge', 'attempt_count',
        'created_at', 'expires_at', 'time_status', 'external_reference'
    ]
    
    list_filter = [
        'status', 'purpose', 'created_at', 'expires_at',
        ('verified_at', admin.DateFieldListFilter),
    ]
    
    search_fields = ['phone_number', 'external_reference']
    
    readonly_fields = [
        'id', 'created_at', 'verified_at', 'is_expired_display',
        'attempts_count', 'client_info'
    ]
    
    ordering = ['-created_at']
    
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_expired', 'cleanup_old_records']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'phone_number', 'purpose', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'verified_at', 'expires_at', 'is_expired_display')
        }),
        ('Tracking', {
            'fields': ('attempt_count', 'attempts_count', 'external_reference')
        }),
        ('Client Information', {
            'fields': ('client_info', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'sent': 'blue',
            'verified': 'green', 
            'expired': 'orange',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def time_status(self, obj):
        """Show if expired or time remaining"""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        else:
            remaining = (obj.expires_at - timezone.now()).total_seconds()
            if remaining > 0:
                minutes = int(remaining // 60)
                return format_html(
                    '<span style="color: green;">{}m remaining</span>', 
                    minutes
                )
            else:
                return format_html('<span style="color: orange;">Just expired</span>')
    time_status.short_description = 'Time Status'
    
    def is_expired_display(self, obj):
        """Display expiration status"""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Is Expired'
    
    def attempts_count(self, obj):
        """Show total attempts count"""
        return obj.attempts.count()
    attempts_count.short_description = 'Total Attempts'
    
    def client_info(self, obj):
        """Display formatted client information"""
        info = []
        if obj.ip_address:
            info.append(f"IP: {obj.ip_address}")
        if obj.user_agent:
            # Truncate long user agents
            ua = obj.user_agent[:100] + "..." if len(obj.user_agent) > 100 else obj.user_agent
            info.append(f"User Agent: {ua}")
        return "\n".join(info) if info else "No client info"
    client_info.short_description = 'Client Information'
    
    def mark_as_expired(self, request, queryset):
        """Admin action to mark selected requests as expired"""
        updated = queryset.filter(
            status=OTPRequest.StatusChoices.SENT
        ).update(status=OTPRequest.StatusChoices.EXPIRED)
        
        self.message_user(
            request,
            f"Successfully marked {updated} OTP requests as expired."
        )
    mark_as_expired.short_description = "Mark selected requests as expired"
    
    def cleanup_old_records(self, request, queryset):
        """Admin action to cleanup old records"""
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_requests = queryset.filter(created_at__lt=cutoff_date)
        count = old_requests.count()
        old_requests.delete()
        
        self.message_user(
            request,
            f"Successfully deleted {count} old OTP requests."
        )
    cleanup_old_records.short_description = "Cleanup old records (30+ days)"
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related to avoid N+1 queries"""
        return super().get_queryset(request).prefetch_related('attempts')


@admin.register(OTPAttempt)
class OTPAttemptAdmin(admin.ModelAdmin):
    """Admin interface for OTP attempts"""
    
    list_display = [
        'otp_request_phone', 'otp_request_purpose', 'success_badge', 
        'attempted_at', 'ip_address'
    ]
    
    list_filter = [
        'is_successful', 'attempted_at',
        'otp_request__purpose', 'otp_request__status'
    ]
    
    search_fields = [
        'otp_request__phone_number', 'ip_address'
    ]
    
    readonly_fields = ['id', 'attempted_at', 'otp_request_link']
    
    ordering = ['-attempted_at']
    
    date_hierarchy = 'attempted_at'
    
    def otp_request_phone(self, obj):
        """Display phone number from related OTP request"""
        return obj.otp_request.phone_number
    otp_request_phone.short_description = 'Phone Number'
    
    def otp_request_purpose(self, obj):
        """Display purpose from related OTP request"""
        return obj.otp_request.get_purpose_display()
    otp_request_purpose.short_description = 'Purpose'
    
    def success_badge(self, obj):
        """Display success status with color"""
        if obj.is_successful:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    success_badge.short_description = 'Result'
    
    def otp_request_link(self, obj):
        """Link to related OTP request"""
        url = reverse('admin:authentication_otprequest_change', args=[obj.otp_request.id])
        return format_html('<a href="{}">View OTP Request</a>', url)
    otp_request_link.short_description = 'Related OTP Request'
    
    def get_queryset(self, request):
        """Optimize queryset to avoid N+1 queries"""
        return super().get_queryset(request).select_related('otp_request')


# Custom admin site configuration
class OTPAnalyticsAdmin:
    """Custom admin view for OTP analytics (can be added as a separate page)"""
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist with analytics"""
        from datetime import timedelta
        
        # Get analytics for last 7 days
        last_7_days = timezone.now() - timedelta(days=7)
        
        analytics = OTPRequest.objects.filter(
            created_at__gte=last_7_days
        ).aggregate(
            total=Count('id'),
            verified=Count('id', filter=Q(status=OTPRequest.StatusChoices.VERIFIED)),
            failed=Count('id', filter=Q(status=OTPRequest.StatusChoices.FAILED)),
            expired=Count('id', filter=Q(status=OTPRequest.StatusChoices.EXPIRED)),
        )
        
        # Calculate success rate
        total = analytics['total'] or 1
        analytics['success_rate'] = (analytics['verified'] / total) * 100
        
        extra_context = extra_context or {}
        extra_context['analytics'] = analytics
        
        return super().changelist_view(request, extra_context=extra_context)