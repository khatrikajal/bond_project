# Backend/apps/authentication/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid

class OTPRequest(models.Model):
    """
    Stores OTP request metadata for audit logging and rate limiting.
    The actual OTP code is stored in Redis cache, not in the database.
    """
    
    class StatusChoices(models.TextChoices):
        SENT = 'sent', 'Sent'
        VERIFIED = 'verified', 'Verified'
        EXPIRED = 'expired', 'Expired'
        FAILED = 'failed', 'Failed'
    
    class PurposeChoices(models.TextChoices):
        REGISTRATION = 'registration', 'Registration'
        LOGIN = 'login', 'Login'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        PHONE_VERIFICATION = 'phone_verification', 'Phone Verification'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = PhoneNumberField(
        help_text="Phone number with country code"
    )
    purpose = models.CharField(
        max_length=20,
        choices=PurposeChoices.choices,
        default=PurposeChoices.REGISTRATION
    )
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.SENT
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    # Tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    
    # External service tracking (for future Twilio integration)
    external_reference = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="External service reference (e.g., Twilio SID)"
    )
    
    class Meta:
        db_table = 'auth_otp_requests'
        ordering = ['-created_at']
        
        # Database indexes for performance
        indexes = [
            models.Index(fields=['phone_number', 'purpose'], name='otp_phone_purpose_idx'),
            models.Index(fields=['phone_number', 'status'], name='otp_phone_status_idx'),
            models.Index(fields=['created_at'], name='otp_created_idx'),
            models.Index(fields=['expires_at'], name='otp_expires_idx'),
            models.Index(fields=['status', 'created_at'], name='otp_status_created_idx'),
        ]
        
        constraints = [
            models.CheckConstraint(
                check=models.Q(attempt_count__gte=0), 
                name='otp_attempt_count_positive'
            ),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone_number} - {self.purpose} - {self.status}"
    
    def is_expired(self):
        """Check if the OTP request has expired"""
        return timezone.now() > self.expires_at
    
    def mark_as_verified(self):
        """Mark the OTP as verified"""
        self.status = self.StatusChoices.VERIFIED
        self.verified_at = timezone.now()
        self.save(update_fields=['status', 'verified_at'])
    
    def mark_as_expired(self):
        """Mark the OTP as expired"""
        self.status = self.StatusChoices.EXPIRED
        self.save(update_fields=['status'])
    
    def increment_attempt(self):
        """Increment the attempt count"""
        self.attempt_count += 1
        self.save(update_fields=['attempt_count'])


class OTPAttempt(models.Model):
    """
    Tracks individual OTP verification attempts for security analysis
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    otp_request = models.ForeignKey(
        OTPRequest,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    
    # Attempt details (we don't store the actual OTP code for security)
    is_successful = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_otp_attempts'
        ordering = ['-attempted_at']
        
        indexes = [
            models.Index(fields=['otp_request', 'attempted_at'], name='otp_attempt_request_time_idx'),
            models.Index(fields=['attempted_at'], name='otp_attempt_time_idx'),
            models.Index(fields=['is_successful'], name='otp_attempt_success_idx'),
        ]
    
    def __str__(self):
        return f"Attempt for {self.otp_request.phone_number} - {'Success' if self.is_successful else 'Failed'}"

